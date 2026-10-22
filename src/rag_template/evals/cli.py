"""
cli.py: `python -m rag_template.evals <command>`

    retrieval   run the retrieval ablations on a gold set -> evals/results/retrieval.{json,md}
    synth       generate extra gold queries with the LLM (needs a running server)
    answers     answer-level evaluation: grounding, refusals, attribution (needs a running server)
    gates       adversarial test of the answer gates (no model needed)
    pool        retrieval over every corpus in ONE index: per corpus, pooled, and the wrong-document rate
"""

import argparse
import dataclasses
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

from rag_template import env
from rag_template.config import PdfSettings, Settings
from rag_template.evals import report as R
from rag_template.evals.gold import Query, check_reachability, load_gold
from rag_template.evals.retrieval import System, SystemResult, compare, evaluate_system, to_json
from rag_template.evals.workspace import Workspace
from rag_template.rerankers import default_rerank_mode
from rag_template.store.embedders import HashingEmbedder, SentenceTransformerEmbedder, TruncatedEmbedder

log = logging.getLogger("rag_template.evals")
GEMMA = "google/embeddinggemma-2"
BGE = "BAAI/bge-small-en-v1.5"


def build_embedders(settings: Settings, only: List[str]) -> Dict[str, object]:
    out: Dict[str, object] = {}
    gemma = SentenceTransformerEmbedder(settings.embed_model, dtype=settings.embed_dtype)
    if "gemma" in only:
        out["gemma"] = gemma
    if "gemma256" in only:
        out["gemma256"] = TruncatedEmbedder(gemma, 256)
    if "bge" in only:
        out["bge"] = SentenceTransformerEmbedder(BGE)
    if "hash" in only:
        out["hash"] = HashingEmbedder()
    return out


def systems_for(chunker: str, full: bool, top: Optional[int] = None) -> List[System]:
    c = chunker
    base = [
        System(f"{c}/bm25", lexical=True, dense=False, chunker=c),
        System(f"{c}/gemma dense", "gemma", lexical=False, chunker=c),
        System(f"{c}/gemma RRF", "gemma", chunker=c),
        System(f"{c}/gemma RRF+rerank", "gemma", rerank=True, rerank_top=top, chunker=c),
    ]
    if not full:
        return base
    return base + [
        System(f"{c}/bm25+rerank", lexical=True, dense=False, rerank=True, rerank_top=top, chunker=c),
        System(f"{c}/gemma dense+rerank", "gemma", lexical=False, rerank=True, rerank_top=top, chunker=c),
        System(f"{c}/gemma(code task) dense", "gemma", lexical=False, query_task="code retrieval", chunker=c),
        System(f"{c}/gemma(code task) RRF+rerank", "gemma", rerank=True, rerank_top=top, query_task="code retrieval", chunker=c),
        System(f"{c}/gemma@256 dense", "gemma256", lexical=False, chunker=c),
        System(f"{c}/gemma@256 RRF", "gemma256", chunker=c),
        System(f"{c}/bge dense", "bge", lexical=False, chunker=c),
        System(f"{c}/bge RRF", "bge", chunker=c),
        System(f"{c}/bge RRF+rerank", "bge", rerank=True, rerank_top=top, chunker=c),
        System(f"{c}/hash dense (floor)", "hash", lexical=False, chunker=c),
    ]


def _reranker(settings: Settings):
    from rag_template.rerankers import make_reranker

    return make_reranker(settings.rerank_model, settings.rerank_revision, settings.rerank_trust_remote_code)


def cmd_retrieval(args) -> int:
    settings = Settings.from_env()
    queries = [q for q in load_gold(args.gold) if args.only_origin in (None, q.origin)]
    answerable = [q for q in queries if q.answerable]
    by_id = {q.id: q for q in queries}
    reranker = _reranker(settings)
    results: Dict[str, SystemResult] = {}
    meta: Dict[str, dict] = {"gold": {"file": str(args.gold), "answerable": len(answerable), "doc": sum(q.type == "doc" for q in answerable), "code": sum(q.type == "code" for q in answerable)}}
    sections: List[str] = []

    for chunker, budget, full in (("ast", 500, True), ("naive", 500, False), ("naive", 250, False)):
        label = chunker if chunker == "ast" else f"naive{budget}"
        if label != "ast" and not args.baselines:
            continue
        ws = Workspace(args.corpus, chunker=chunker, max_tokens=budget)
        ws.ingest()
        meta[label] = ws.chunk_stats()
        reach = check_reachability(answerable, ws.db.iter_chunks())
        meta[label]["gold_reachable"] = reach.reachable
        meta[label]["gold_gated_out"] = reach.gated_out
        meta[label]["gold_split"] = reach.split
        needed = ["gemma"] + (["gemma256", "bge", "hash"] if full else [])
        for key, emb in build_embedders(settings, needed).items():
            secs = ws.add_embedder(key, emb)
            meta[label][f"embed_s_{key}"] = round(secs, 1)
            log.info("%s: embedded with %s in %.1fs", label, key, secs)
        for system in systems_for(label, full, args.rerank_top):
            system = System(**{**system.__dict__, "name": system.name.replace(chunker + "/", label + "/", 1) if label != chunker else system.name})
            t = time.monotonic()
            res = evaluate_system(ws, system, queries, reranker)
            results[system.name] = res
            s = res.summary(with_ci=False)
            log.info("%-36s r@1 %.3f r@5 %.3f r@10 %.3f mrr %.3f (%.0fs)", system.name, s["recall@1"]["mean"], s["recall@5"]["mean"], s["recall@10"]["mean"], s["mrr@10"]["mean"], time.monotonic() - t)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps({"meta": meta, "systems": {n: to_json(r) for n, r in results.items()}}, indent=1))
    out.with_suffix(".md").write_text(render_retrieval(results, meta, by_id))
    print(f"wrote {out.with_suffix('.md')} and .json")
    return 0


def render_retrieval(results: Dict[str, SystemResult], meta: dict, by_id: Dict[str, Query]) -> str:
    g = lambda n: results[n]  # noqa: E731
    has = lambda *ns: all(n in results for n in ns)  # noqa: E731
    parts = [f"# Retrieval evaluation\n\nGold: `{meta['gold']['file']}`: {meta['gold']['answerable']} answerable queries ({meta['gold']['doc']} documentation, {meta['gold']['code']} code, {meta['gold']['answerable'] - meta['gold']['doc'] - meta['gold']['code']} other kinds). "
             "Values are percentages with a 95% bootstrap half-width (±). Relevance = the retrieved chunk is from the gold file and contains the gold snippet.\n"]
    parts.append("## Index\n\n| chunker | files | chunks | usable | mean chars | gold reachable / gated out / split |\n|---|---:|---:|---:|---:|---|")
    for label in [k for k in meta if k != "gold"]:
        m = meta[label]
        parts.append(f"| {label} | {m['files']} | {m['chunks']} | {m['usable']} | {m['mean_chars']:.0f} | {m['gold_reachable']} / {m['gold_gated_out']} / {m['gold_split']} |")
    parts.append("\n## All systems\n\n" + R.metrics_table(list(results.values())))
    ast = [r for n, r in results.items() if n.startswith("ast/")]
    if ast:
        parts.append("\n## Documentation queries only\n\n" + R.metrics_table(ast, lambda q: q.type == "doc"))
        parts.append("\n## Code queries only\n\n" + R.metrics_table(ast, lambda q: q.type == "code"))
        kinds = sorted({q.type for q in by_id.values() if q.answerable} - {"doc", "code", "none"})
        for kind in kinds:  # gold files that label queries by document kind (statute, tables, math, scan, ...)
            parts.append(f"\n## `{kind}` queries only\n\n" + R.metrics_table(ast, lambda q, kind=kind: q.type == kind))
    pairs = []
    def add(label, a, b):
        if has(a, b):
            pairs.append((label, g(a), g(b)))
    add("hybrid RRF vs dense only (gemma)", "ast/gemma RRF", "ast/gemma dense")
    add("hybrid RRF vs BM25 only", "ast/gemma RRF", "ast/bm25")
    add("dense only vs BM25 only (gemma)", "ast/gemma dense", "ast/bm25")
    add("+ cross-encoder rerank vs RRF", "ast/gemma RRF+rerank", "ast/gemma RRF")
    add("+ cross-encoder rerank on BM25 vs BM25", "ast/bm25+rerank", "ast/bm25")
    add("EmbeddingGemma 2 vs bge-small (dense)", "ast/gemma dense", "ast/bge dense")
    add("EmbeddingGemma 2 vs bge-small (RRF+rerank)", "ast/gemma RRF+rerank", "ast/bge RRF+rerank")
    add("gemma 768d vs 256d (dense)", "ast/gemma dense", "ast/gemma@256 dense")
    add("code task prefix vs search prefix (dense)", "ast/gemma(code task) dense", "ast/gemma dense")
    add("AST chunks vs fixed 500-token windows (RRF+rerank)", "ast/gemma RRF+rerank", "naive500/gemma RRF+rerank")
    add("AST chunks vs fixed 250-token windows (RRF+rerank)", "ast/gemma RRF+rerank", "naive250/gemma RRF+rerank")
    add("AST chunks vs fixed 250-token windows (dense)", "ast/gemma dense", "naive250/gemma dense")
    if pairs:
        parts.append("\n## Paired comparisons (percentage points; bold = 95% interval excludes 0)\n\n" + R.comparisons_table(pairs))
        code_pairs = [p for p in pairs if "AST" in p[0] or "code task" in p[0] or "rerank" in p[0]]
        parts.append("\n### Same comparisons, code queries only\n\n" + R.comparisons_table(code_pairs, where=lambda q: q.type == "code"))
        parts.append("\n### Same comparisons, documentation queries only\n\n" + R.comparisons_table(code_pairs, where=lambda q: q.type == "doc"))
    best = "ast/gemma RRF+rerank" if "ast/gemma RRF+rerank" in results else next(iter(results))
    parts.append(f"\n## Error analysis: `{best}`\n\n" + R.failures(results[best], by_id))
    return "\n".join(parts) + "\n"


def cmd_ablations(args) -> int:
    """Chunking controls: are AST's gains boundaries or metadata, and how small may chunks be merged? (Rerankers: `rerankers`.)"""
    settings = Settings.from_env()
    queries = load_gold(args.gold)
    by_id = {q.id: q for q in queries}
    gemma = SentenceTransformerEmbedder(settings.embed_model, dtype=settings.embed_dtype)
    results: Dict[str, SystemResult] = {}
    meta: Dict[str, dict] = {}

    def run(ws: Workspace, systems: List[System]) -> None:
        for sys_ in systems:
            res = evaluate_system(ws, sys_, queries)
            results[sys_.name] = res
            s = res.summary(with_ci=False)
            log.info("%-44s r@5 %.3f r@10 %.3f mrr %.3f", sys_.name, s["recall@5"]["mean"], s["recall@10"]["mean"], s["mrr@10"]["mean"])

    def workspace(label: str, **kw) -> Workspace:
        ws = Workspace(args.corpus, **kw)
        ws.ingest()
        ws.add_embedder("gemma", gemma)
        st = ws.chunk_stats()
        meta[label] = {"chunks": st["chunks"], "usable": st["usable"], "mean_chars": round(st["mean_chars"])}
        return ws

    base = workspace("ast (default: max 500, merge < 50 tokens)")
    run(base, [System("BM25", lexical=True, dense=False), System("dense", "gemma", lexical=False), System("RRF", "gemma")])
    nocrumb = workspace("ast, breadcrumb removed", breadcrumb=False)
    run(nocrumb, [System("nocrumb BM25", lexical=True, dense=False), System("nocrumb dense", "gemma", lexical=False), System("nocrumb RRF", "gemma")])
    naive = workspace("fixed 250-token windows", chunker="naive", max_tokens=250)
    run(naive, [System("naive250 BM25", lexical=True, dense=False), System("naive250 dense", "gemma", lexical=False), System("naive250 RRF", "gemma")])
    for mt in (0, 25, 100, 200):
        ws = workspace(f"ast, merge threshold {mt}", min_tokens=mt)
        run(ws, [System(f"merge<{mt} dense", "gemma", lexical=False), System(f"merge<{mt} RRF", "gemma")])

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps({"meta": meta, "systems": {n: to_json(r) for n, r in results.items()}}, indent=1))
    out.with_suffix(".md").write_text(render_ablations(results, meta, [], by_id))
    print(f"wrote {out.with_suffix('.md')}")
    return 0


class _MemoReranker:
    """Remembers scores per (query, candidate list). `replace` and `fuse` mode read identical candidates, so within one
    evaluation run the second mode costs nothing. Used only by the evals: the library always scores fresh."""

    def __init__(self, inner):
        self.inner, self.name, self._memo = inner, inner.name, {}

    def rerank(self, query, texts):
        key = (query, tuple(texts))
        if key not in self._memo:
            self._memo[key] = self.inner.rerank(query, texts)
        return list(self._memo[key])


def _short(model_id: str) -> str:
    return model_id.rsplit("/", 1)[-1]


def cmd_rerankers(args) -> int:
    """Compare rerankers head to head on one gold set: model x mode (replace/fuse) x candidates read, plus order stability."""
    import torch

    from rag_template.evals.rerank_stability import order_sensitivity
    from rag_template.evals.retrieval import compare
    from rag_template.rerankers import make_reranker

    settings = Settings.from_env()
    queries = load_gold(args.gold)
    by_id = {q.id: q for q in queries}
    cuda = torch.cuda.is_available()
    ws = Workspace(args.corpus)
    ws.ingest()
    ws.add_embedder("gemma", SentenceTransformerEmbedder(settings.embed_model, dtype=settings.embed_dtype))
    base_vram = torch.cuda.memory_allocated() / 2**20 if cuda else 0.0

    rerankers: Dict[str, object] = {}
    notes: List[str] = [f"Gold: `{args.gold}`. Embedder loaded: {base_vram:.0f} MB GPU memory before any reranker."]
    vram: Dict[str, float] = {}
    for model in args.models:
        key = _short(model)
        try:
            before = torch.cuda.memory_allocated() / 2**20 if cuda else 0.0
            rerankers[key] = _MemoReranker(make_reranker(model, settings.rerank_revision if model == settings.rerank_model else "", settings.rerank_trust_remote_code))
            vram[key] = (torch.cuda.memory_allocated() / 2**20 - before) if cuda else 0.0
        except Exception as e:  # noqa: BLE001 - reported in the report, not silently skipped
            notes.append(f"reranker `{model}` could not be loaded: {type(e).__name__}: {str(e)[:160]}")

    systems = [System("RRF", "gemma")]
    for key in rerankers:
        for mode in ("replace", "fuse"):
            for top in args.tops:
                systems.append(System(f"RRF + {key} ({mode}, top {top})", "gemma", rerank=True, rerank_mode=mode, rerank_top=top, reranker=key))
    results: Dict[str, SystemResult] = {}
    peak: Dict[str, float] = {}
    for sys_ in systems:
        if cuda:
            torch.cuda.reset_peak_memory_stats()
        res = evaluate_system(ws, sys_, queries, rerankers=rerankers)
        results[sys_.name] = res
        peak[sys_.name] = torch.cuda.max_memory_allocated() / 2**20 if cuda else 0.0
        s = res.summary(with_ci=False)
        log.info("%-48s r@5 %.3f mrr %.3f  %4.0f ms  peak %5.0f MB", sys_.name, s["recall@5"]["mean"], s["mrr@10"]["mean"], s["latency_ms"]["mean"], peak[sys_.name])

    stability: Dict[str, dict] = {}
    retriever = ws.retriever("gemma")
    sample = [q for q in queries if q.answerable][: args.stability_queries]
    for key, rr in rerankers.items():
        per_query = []
        for q in sample:
            hits = retriever.search(q.query, k=args.tops[-1] if args.tops else 20)
            if len(hits) >= 3:
                per_query.append(order_sensitivity(rr.inner.rerank, q.query, [h.content for h in hits[: max(args.tops)]], n_shuffles=args.shuffles))
        if per_query:
            stability[key] = {m: sum(p[m] for p in per_query) / len(per_query) for m in ("tau", "top1_agree")} | {"max_score_delta": max(p["max_score_delta"] for p in per_query), "queries": len(per_query)}

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps({"notes": notes, "vram_load_mb": vram, "peak_mb": peak, "stability": stability, "systems": {n: to_json(r) for n, r in results.items()}}, indent=1))
    out.with_suffix(".md").write_text(render_rerankers(results, notes, vram, peak, stability, by_id, list(rerankers)))
    print(f"wrote {out.with_suffix('.md')}")
    return 0


def render_rerankers(results, notes, vram, peak, stability, by_id, keys) -> str:
    n_ans = sum(q.answerable for q in by_id.values())
    parts = ["# Reranker comparison\n", f"{n_ans} answerable queries; relevance = the chunk holds the gold snippet; ± = 95% bootstrap half-width; every system is hybrid RRF (EmbeddingGemma 2 + BM25) plus the named reranker. "
             "`replace` orders candidates by the reranker alone, `fuse` makes it a third voter next to dense and BM25, `top N` is how many fused candidates it reads.\n"]
    parts += [f"> {n}\n" for n in notes]
    parts.append("## Memory\n\n| reranker | GPU memory to load (MB) |\n|---|---:|\n" + "\n".join(f"| {k} | {v:.0f} |" for k, v in vram.items()))
    parts.append("\n## All systems\n\n" + R.metrics_table(list(results.values())))
    parts.append("\n**Reading the `ms/query` column:** scores were cached within the run, because `replace` and `fuse` read identical candidates, so the "
                 "`fuse` rows show only retrieval plus fusion (~21 ms) and exclude the reranker. The cost of a reranker is the `replace` row's latency at the same `top N`.")
    parts.append("\nPeak GPU memory per system (MB, includes the embedder and the LLM-free eval process): " + ", ".join(f"{n}: {v:.0f}" for n, v in peak.items() if n != "RRF"))
    pairs = [(f"{n} vs RRF", r, results["RRF"]) for n, r in results.items() if n != "RRF"]
    for title, where in (("all queries", None), ("code queries", lambda q: q.type == "code"), ("documentation queries", lambda q: q.type == "doc")):
        parts.append(f"\n## Paired differences vs plain RRF, {title} (points; bold = 95% interval excludes 0)\n\n" + R.comparisons_table(pairs, ("recall@1", "recall@5", "mrr@10"), where))
    if len(keys) >= 2:
        a, b = keys[0], keys[1]
        head = [(f"{a} vs {b} ({m}, top {t})", results[f"RRF + {a} ({m}, top {t})"], results[f"RRF + {b} ({m}, top {t})"]) for m in ("replace", "fuse") for t in sorted({int(n.rsplit('top ', 1)[1].rstrip(')')) for n in results if n != "RRF"}) if f"RRF + {a} ({m}, top {t})" in results and f"RRF + {b} ({m}, top {t})" in results]
        if head:
            parts.append(f"\n## {a} vs {b}, head to head (points)\n\n" + R.comparisons_table(head, ("recall@1", "recall@5", "mrr@10")))
    if stability:
        parts.append("\n## Candidate-order stability\n\nThe same candidates scored again in shuffled order. tau = Kendall rank correlation with the original order (1.0 = identical ranking), top-1 = share of shuffles with the same best candidate.\n\n| reranker | queries | mean tau | top-1 unchanged | largest score change |\n|---|---:|---:|---:|---:|\n" + "\n".join(f"| {k} | {v['queries']} | {v['tau']:.3f} | {100 * v['top1_agree']:.0f}% | {v['max_score_delta']:.3g} |" for k, v in stability.items()))
    return "\n".join(parts) + "\n"


def _llm(settings: Settings, json_mode: str = "off"):
    from dataclasses import replace

    from rag_template.enrichment.llm import LLMClient

    mode = json_mode if json_mode not in ("", None, False) else settings.llm.json_mode
    llm = LLMClient(replace(settings.llm, json_mode="json_object" if mode is True else mode))
    llm.check_health()
    return llm


def query_signals(retriever, dense_retriever, query: str, rerank_top: int) -> Dict[str, float]:
    """Numbers available BEFORE the LLM is called. Higher = more likely answerable, for every signal."""
    from rag_template.enrichment import verify

    hits = retriever.search(query, k=10, rerank=True, rerank_top=rerank_top)
    scored = sorted((h.rerank_score for h in hits if h.rerank_score is not None), reverse=True)
    dense = dense_retriever.search(query, k=5, lexical=False, rerank=False)
    terms = verify.question_terms(query)
    ctx = [f"{h.label}\n{h.content}" for h in hits[:5]]
    missing = verify.missing_question_terms(query, ctx)
    return {
        "rerank top-1": scored[0] if scored else float("-inf"),
        "rerank mean top-3": sum(scored[:3]) / len(scored[:3]) if scored else float("-inf"),
        "dense cosine top-1": max((h.dense_score for h in dense if h.dense_score is not None), default=-1.0),
        "RRF top score": max((h.rrf_score for h in hits), default=0.0),
        "question-term coverage (top 5)": 1.0 - (len(missing) / len(terms)) if terms else 1.0,
    }


def cmd_answerability(args) -> int:
    from rag_template.evals import answerability as AB
    from rag_template.rerankers import make_reranker

    settings = Settings.from_env()
    tune = [q for q in load_gold(args.gold) if q.answerable]
    heldout = [q for q in load_gold(args.synthetic_gold) if q.answerable]
    negatives = [q for q in load_gold(args.gold) if not q.answerable] + load_gold(args.unanswerable)
    for q in negatives:
        q.kind = q.kind or "legacy"
    ws = Workspace(args.corpus)
    ws.ingest()
    ws.add_embedder("gemma", SentenceTransformerEmbedder(settings.embed_model, dtype=settings.embed_dtype))
    dense_retriever = ws.retriever("gemma")
    reports, per_query = [], {}
    for model in args.models:
        short = _short(model)
        try:
            rr = make_reranker(model, settings.rerank_revision if model == settings.rerank_model else "", settings.rerank_trust_remote_code)
        except Exception as e:  # noqa: BLE001 - reported, not silently skipped
            print(f"skipping {model}: {type(e).__name__}: {str(e)[:120]}")
            continue
        retriever = ws.retriever("gemma", rr)
        retriever.rerank_mode = default_rerank_mode(model) if settings.rerank_mode == "auto" else settings.rerank_mode
        sig: Dict[str, Dict[str, List[float]]] = {}
        for group, qs in (("tune", tune), ("heldout", heldout), ("neg", negatives)):
            rows = []
            for i, q in enumerate(qs):
                rows.append(query_signals(retriever, dense_retriever, q.query, args.rerank_top))
                if i % 50 == 0:
                    log.info("%s %s %d/%d", short, group, i, len(qs))
            sig[group] = rows
            per_query.setdefault(short, {})[group] = [{"id": q.id, "kind": q.kind, **r} for q, r in zip(qs, rows)]
        names = list(sig["tune"][0])
        for name in names:
            label = name if name.startswith(("dense", "RRF", "question")) else f"{name} ({short})"
            if any(label == r["signal"] for r in reports):
                continue  # model-independent signals are identical for every reranker run
            by_kind: Dict[str, List[float]] = {}
            for q, r in zip(negatives, sig["neg"]):
                by_kind.setdefault(q.kind, []).append(r[name])
            reports.append(AB.signal_report(label, [r[name] for r in sig["tune"]], [r[name] for r in sig["heldout"]], by_kind))
        del rr
    counts = {"tune": len(tune), "heldout": len(heldout), "neg": len(negatives), "by_kind": {k: sum(q.kind == k for q in negatives) for k in sorted({q.kind for q in negatives})}}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".md").write_text(AB.markdown(reports, counts) + "\n")
    out.with_suffix(".json").write_text(json.dumps({"counts": counts, "reports": reports, "per_query": per_query}, indent=1, default=str))
    print(AB.markdown(reports, counts)[:2500])
    return 0


def cmd_gate_stability(args) -> int:
    """Does candidate order change which questions the relevance gate would refuse, and does averaging orders fix it?
    (Needs a listwise reranker.)"""
    import random as _random

    from rag_template.evals import answerability as AB
    from rag_template.rerankers import make_reranker

    settings = Settings.from_env()
    pos = [q for q in load_gold(args.gold) if q.answerable][: args.queries]
    neg = (load_gold(args.unanswerable) + [q for q in load_gold(args.gold) if not q.answerable])[: args.queries]
    ws = Workspace(args.corpus)
    ws.ingest()
    ws.add_embedder("gemma", SentenceTransformerEmbedder(settings.embed_model, dtype=settings.embed_dtype))
    rr = make_reranker(settings.rerank_model, settings.rerank_revision, settings.rerank_trust_remote_code)
    retriever = ws.retriever("gemma", rr)
    rng = _random.Random(0)
    groups: Dict[str, List[List[float]]] = {"answerable": [], "unanswerable": []}
    dense: Dict[str, List[float]] = {"answerable": [], "unanswerable": []}
    for label, qs in (("answerable", pos), ("unanswerable", neg)):
        for i, q in enumerate(qs):
            hits = retriever.search(q.query, k=args.top, rerank=False)  # the natural fused order, before any reranking
            texts = [h.content for h in hits]
            if len(texts) < 3:
                continue
            scores = [max(rr.rerank(q.query, texts))]
            for _ in range(args.shuffles):
                perm = list(range(len(texts)))
                rng.shuffle(perm)
                scores.append(max(rr.rerank(q.query, [texts[j] for j in perm])))
            groups[label].append(scores)
            d = retriever.search(q.query, k=5, lexical=False, rerank=False)
            dense[label].append(max((h.dense_score for h in d if h.dense_score is not None), default=-1.0))
            if i % 20 == 0:
                log.info("%s %d/%d", label, i, len(qs))
    rows = []
    for t in args.thresholds:
        for label, sc in groups.items():
            rows.append({"threshold": t, "group": label, **AB.decision_stability(sc, t)})
    natural = lambda g: [s[0] for s in groups[g]]  # noqa: E731
    mean_k = lambda g, k: [sum(s[:k]) / len(s[:k]) for s in groups[g]]  # noqa: E731
    aucs = {"natural order (one pass)": AB.bootstrap_auc(natural("answerable"), natural("unanswerable"))}
    for k in (2, 3, len(groups["answerable"][0]) if groups["answerable"] else 6):
        aucs[f"mean over {k} orders ({k} passes)"] = AB.bootstrap_auc(mean_k("answerable", k), mean_k("unanswerable", k))
    aucs["dense cosine top-1 (order-free, no reranker)"] = AB.bootstrap_auc(dense["answerable"], dense["unanswerable"])
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    md = ["# Does candidate order change the relevance gate's decision?", "",
          f"{settings.rerank_model}, {args.top} candidates, {len(groups['answerable'])} answerable and {len(groups['unanswerable'])} unanswerable questions. The best score is re-computed "
          f"under {args.shuffles} random candidate orders; the first is the natural fused order the system uses. A query is *unstable* when some order lands on the other side of the threshold.", "",
          "| threshold | group | queries | unstable | largest score spread | mean spread |", "|---:|---|---:|---:|---:|---:|"]
    md += [f"| {r['threshold']:g} | {r['group']} | {r['queries']} | {100 * r['unstable']:.0f}% ({r['unstable_k']}) | {r['max_spread']:.3f} | {r['mean_spread']:.3f} |" for r in rows]
    md += ["", "## Does averaging over candidate orders help?", "", "ROC-AUC for separating answerable from unanswerable questions, 95% bootstrap interval. More passes cost proportionally more latency.", "",
           "| signal | AUC (95% CI) |", "|---|---:|"] + [f"| {k} | {a:.3f} ({lo:.3f}-{hi:.3f}) |" for k, (a, lo, hi) in aucs.items()]
    out.with_suffix(".md").write_text("\n".join(md) + "\n")
    out.with_suffix(".json").write_text(json.dumps({"rows": rows, "auc": {k: v for k, v in aucs.items()}, "scores": groups, "dense": dense}, indent=1))
    print("\n".join(md))
    return 0


def cmd_gates(args) -> int:
    from rag_template.evals.gates import build_scenarios, run_gate_eval

    ws = Workspace(args.corpus)
    ws.ingest()
    scenarios = build_scenarios(load_gold(args.gold), ws.db.iter_chunks())
    rep = run_gate_eval(scenarios)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    body = (f"# Answer-gate adversarial evaluation\n\n{len(scenarios)} scenarios (one per answerable gold query: gold chunk + 2 distractors). Each row corrupts the same clean answer in one way; "
            f"each column is a gate policy (`retrieve.POLICIES`: strict = quotes must be verbatim, support checked against the quotes; tolerant = also accepts a quote that is one word off; "
            f"lenient = support checked against the cited chunk, and a missing quote is replaced by the chunk's best-matching span).\n\n{rep.markdown()}\n")
    missed = "\n".join(f"- **{k}**: " + "; ".join(v) for k, v in rep.examples.items() if v)
    if missed:
        body += f"\n## Examples where the gate did not behave as expected\n\n{missed}\n"
    out.with_suffix(".md").write_text(body)
    out.with_suffix(".json").write_text(json.dumps({"rows": rep.rows, "examples": rep.examples}, indent=1))
    print(rep.markdown())
    return 0


def cmd_quotes(args) -> int:
    from rag_template.evals import quotes as Q

    ws = Workspace(args.corpus)
    ws.ingest()
    rows = Q.run_quote_tolerance(load_gold(args.gold), ws.db.iter_chunks())
    body = ("# Quote-matching tolerance\n\nReal gold snippets, damaged the way a small model slips (`slip`) or the way a fabrication looks (`fabrication`); "
            "does the locator find the quote in its chunk? Good = slips accepted, fabrications rejected.\n\n" + Q.markdown(rows) + "\n")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".md").write_text(body)
    out.with_suffix(".json").write_text(json.dumps(rows, indent=1))
    print(Q.markdown(rows))
    return 0


def cmd_summarize(args) -> int:
    """Build evals/results/answer_policies.md from the saved result files (no model calls, no hand-typed numbers)."""
    import re as _re

    from rag_template.evals import answers as A
    from rag_template.retrieve import POLICIES

    res = Path(args.results)
    hw, syn = load_gold(args.gold), load_gold(args.synthetic_gold)

    class _Span:  # replaying needs a span scorer only for the lenient policy's extraction
        def span_scorer(self):
            return lambda q, ts: [float(len(set(_re.findall(r"\w+", q.lower())) & set(_re.findall(r"\w+", t.lower())))) for t in ts]

    def table(name: str, queries):
        path = res / f"{name}.json"
        if not path.exists():
            return f"_(missing: {path.name})_"
        recs = A.load_records(str(path))
        runs = {n: A.regate(recs, queries, _Span(), p) for n, p in POLICIES.items()}
        return A.policy_markdown(A.policy_table(runs))

    def gate_table(name: str, queries):
        path = res / f"{name}.json"
        if not path.exists():
            return f"_(missing: {path.name})_"
        import json as _json

        return A.policy_markdown(_json.load(open(path))["policies"]) if "policies" in _json.load(open(path)) else "_(no policy table in this file)_"

    gates = (res / "gates.md").read_text().split("\n\n", 2)[-1] if (res / "gates.md").exists() else "_(run `evals gates`)_"
    quotes = (res / "quote_tolerance.md").read_text().split("\n\n", 2)[-1] if (res / "quote_tolerance.md").exists() else "_(run `evals quotes`)_"
    body = f"""# Answer gate: formats, policies and what they cost

Generated by `python -m rag_template.evals summarize` from the saved replies of **Gemma 4 E2B** (llama.cpp, temperature 0.1) on
the QuestionPrep corpus, retrieval = EmbeddingGemma 2 + BM25 + RRF + cross-encoder (fuse), k=5. Every table re-judges the *same recorded
replies* with the *current* gate code, so differences between columns of one table are due to the policy alone, and differences
between tables are due to the reply format alone.

**How to read it.** "Correct" = the answer contains a hand-written key phrase, a coarse proxy: reading the answers by hand, roughly
40% of the answers it calls wrong are acceptable paraphrases, so *errors missed* overstates real misses and *false alarms* is a
lower bound on wasted flags. n is small (70 answerable, 15 unanswerable); treat differences of a few answers as noise.

## 1. Reply format (hand-written gold, 70 answerable + 15 unanswerable)

**Plain JSON reply** (the model is asked politely):

{table("answers_handwritten", hw)}

**Schema-enforced reply, answer first** (`LLM_JSON_MODE=schema`):

{table("answers_schema", hw)}

**Schema-enforced reply, quotes first** (the shipped default):

{table("answers_schema_quotes_first", hw)}

## 2. The shipped configuration, re-run end to end

Hand-written gold (the set the format and policy were chosen on, so optimistic):

{table("answers_final_handwritten", hw)}

Synthetic gold (149 questions written by the model from corpus chunks; **not** used to choose anything; no key phrases, so
only the attribution columns are meaningful; see evals/README.md for its biases):

{table("answers_final_synthetic", syn)}

## 2b. With jina-reranker-v3.5, the extended unanswerable set, and the pre-LLM relevance gate

70 answerable + 59 unanswerable questions (15 + 44 new: far-off, near-miss, false-premise). The `relevance gate` rows refuse, *without calling the
LLM*, any question whose best reranker score is below the value shown; the replies are the same recorded ones, so only the gate differs. Thresholds
come from `evals/results/answerability.md` (chosen from the hand-written answerable questions only).

{gate_table("answers_jina", hw)}

## 3. What each policy still catches (adversarial, no model)

{gates}

## 4. Quote-matching tolerance

{quotes}

## Caveats

- One corpus, one small model, one run per configuration at temperature 0.1: the model's sampling noise is not averaged out.
- The format and policy were chosen on the hand-written set; section 2's synthetic table is the only held-out check.
- The gates verify provenance and support. None of the policies can tell that a supported answer addresses a different question.
"""
    out = res / "answer_policies.md"
    out.write_text(body)
    print(f"wrote {out}")
    return 0


def cmd_synth(args) -> int:
    from rag_template.evals.gold import save_gold
    from rag_template.evals.synth import generate_queries

    settings = Settings.from_env()
    llm = _llm(settings, json_mode="json_object")
    ws = Workspace(args.corpus)
    ws.ingest()
    log_every = lambda i, kept, st: print(f"\r  {i} chunks tried, {kept} queries kept", end="", flush=True)  # noqa: E731
    queries, stats = generate_queries(ws.db.iter_chunks(), llm, n=args.n, seed=args.seed, max_shared_words=args.max_shared_words, on_progress=log_every)
    save_gold(queries, args.out)
    print(f"\nwrote {len(queries)} queries to {args.out}; attempted {stats.attempted}; rejected: {stats.rejected}")
    return 0


_CONVERSION_COLUMNS = [
    ("fused #", "fused_numeric"), ("novel #", "novel_numeric"), ("dropped nums", "dropped_numeric_ratio"), ("word recall", "word_recall"),
    ("6-run recall", "run6_recall"), ("order gap", "order_gap"), ("spaced runs", "spaced_letter_runs"), ("ragged tables", "ragged_tables"),
    ("flat code", "flattened_code_blocks"),
]


def cmd_conversion(args) -> int:
    """Convert every PDF with each backend and run the conversion check on the result (calibration and regression test of
    `convcheck`). Docling needs the GPU for a moment; stop other GPU jobs for large files."""
    from rag_template import convcheck, converters

    pdfs = sorted(p for d in args.corpus for p in Path(d).rglob("*.pdf"))
    detail = []
    for pdf in pdfs:
        for backend in args.backends:
            t = time.time()
            info, md = converters.convert_pdf(pdf, dataclasses.replace(PdfSettings.from_env(), backend=backend))
            secs = time.time() - t
            rep = convcheck.ConversionReport.from_dict(info["conversion_check"]) if "conversion_check" in info else convcheck.check_conversion(pdf, md)
            detail.append({"pdf": pdf.name, "backend": backend, "seconds": round(secs, 1), **rep.as_dict()})
            print(f"{pdf.name:36s} {backend:12s} {rep.verdict:7s} " + ("; ".join(rep.warnings)[:140] if rep.warnings else rep.reason), flush=True)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Conversion check", "", "Each PDF converted by each backend, then compared with Poppler's `pdftotext` text (see `convcheck.py`).", "",
             "| pdf | backend | verdict | " + " | ".join(c for c, _ in _CONVERSION_COLUMNS) + " | convert s |",
             "|---|---|---|" + "---:|" * (len(_CONVERSION_COLUMNS) + 1)]
    for d in detail:
        cells = [d["metrics"].get(key, "-") for _, key in _CONVERSION_COLUMNS]
        lines.append("| " + " | ".join(str(c) for c in [d["pdf"], d["backend"], d["verdict"], *cells, d["seconds"]]) + " |")
    lines += ["", "## Warnings and examples", ""]
    for d in detail:
        if d["warnings"]:
            lines.append(f"- **{d['pdf']} / {d['backend']}**: " + "; ".join(d["warnings"]))
            for k, v in d["examples"].items():
                lines.append(f"    - {k}: " + " | ".join(str(x)[:130] for x in v[:3]))
    out.with_suffix(".md").write_text("\n".join(lines) + "\n")
    out.with_suffix(".json").write_text(json.dumps(detail, ensure_ascii=False, indent=1))
    print("wrote", out.with_suffix(".md"))
    return 0


def cmd_golden(args) -> int:
    """Score an already ingested store (the live one, or a copy) against an external golden QA file, through the same
    RAG facade the UI uses. `--ingest PDF` first ingests a file into the (fresh) data dir."""
    from rag_template.evals import golden as G
    from rag_template.rag import RAG

    os.environ["RAG_DATA_DIR"] = str(args.data_dir)  # Settings reads the environment; there is no other channel yet
    if args.json_mode:
        os.environ["LLM_JSON_MODE"] = args.json_mode

    settings = Settings.from_env()
    rag = RAG(settings)
    if args.ingest:
        res = rag.ingest_path(args.ingest, replace=True)
        print("ingest:", res.status, res.message, f"{res.chunks} chunks, {res.usable_chunks} usable", dict(res.rejection_reasons or {}), flush=True)
        rag.index()
    rows = G.load_golden(args.golden)
    if args.split != "all":  # evals/split.py: tune on dev, judge on test
        from rag_template.evals.split import select

        rows = select(rows, lambda r: r.question, args.split)
    rows = rows[: args.limit or None]
    audit = G.audit_evidence(rag.db.iter_chunks(), rows, fuzzy=args.fuzzy_evidence)
    records = G.run(rag, rows, audit, k=args.k, policy=args.policy, fuzzy=args.fuzzy_evidence, max_context_tokens=args.max_context_tokens, expand_section=args.expand_section)
    stats = rag.db.stats()
    meta = {"label": args.label or Path(args.out).name, "golden": str(args.golden), "store": str(args.data_dir), "chunks": stats["chunks"], "usable": stats["usable_chunks"],
            "json_mode": str(settings.llm.json_mode), "policy": args.policy or settings.answer_policy, "k": args.k, "split": args.split, "max_context_tokens": args.max_context_tokens or 3000, "expand_section": args.expand_section}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps({"meta": meta, "records": records}, ensure_ascii=False, indent=1))  # first: the run is expensive, the report is not
    out.with_suffix(".md").write_text(G.render(records, meta))
    print("wrote", out.with_suffix(".md"))
    return 0


def cmd_answers(args) -> int:
    """Ask the real LLM every gold query once, record its replies, then re-judge the SAME replies under every gate policy."""
    from rag_template.evals import answers as A
    from rag_template.retrieve import POLICIES

    settings = Settings.from_env()
    llm = _llm(settings, json_mode=args.json_mode or "")
    quotes_first = settings.answer_quotes_first if args.quotes_first is None else args.quotes_first
    ws = Workspace(args.corpus)
    ws.ingest()
    ws.add_embedder("gemma", SentenceTransformerEmbedder(settings.embed_model, dtype=settings.embed_dtype))
    reranker = _reranker(settings)
    retriever = ws.retriever("gemma", reranker, settings.query_task)
    retriever.rerank_mode = default_rerank_mode(settings.rerank_model) if settings.rerank_mode == "auto" else settings.rerank_mode
    queries = load_gold(args.gold)[: args.limit or None]
    for extra in args.extra_gold:
        queries += load_gold(extra)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    stream = out.with_suffix(".partial.jsonl")
    stream.write_text("")

    def on_record(r) -> None:  # one line per finished query, so a long run can be inspected while it goes
        from dataclasses import asdict

        with open(stream, "a") as f:
            f.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")
        print(f"  {r.id}: {'refused' if r.refused else ('pass' if r.grounded else 'flag: ' + r.reason[:70])} {r.latency_s:.1f}s", flush=True)

    recs = A.run_answer_eval(retriever, llm, queries, k=args.k, on_record=on_record, policy="strict", quotes_first=quotes_first)
    runs = {name: A.regate(recs, queries, retriever, p) for name, p in POLICIES.items()}
    for t in args.relevance_thresholds:  # the optional pre-LLM gate on top of the default policy, same replies
        runs[f"balanced + relevance gate {t:g}"] = A.regate(recs, queries, retriever, POLICIES["balanced"], min_relevance=t)
    rows = A.policy_table(runs)
    summary = A.summarize(runs["strict"])
    out.with_suffix(".md").write_text(A.markdown(summary, runs["strict"]) + "\n## Gate policies, same replies re-judged\n\n" + A.policy_markdown(rows) + "\n")
    out.with_suffix(".json").write_text(json.dumps({"policies": rows, **A.to_json(summary, recs)}, indent=1, default=str))
    print("\n" + A.policy_markdown(rows))
    print(f"wrote {out.with_suffix('.md')}")
    return 0


def cmd_pool(args) -> int:
    from rag_template.evals import pooled as P

    settings = Settings.from_env()
    root, labels = Path.cwd(), args.corpora
    tmp, pool_dir, alias, corpus_of_file = P.temp_pool(labels, root)
    systems = [System("pool/bm25", lexical=True, dense=False), System("pool/gemma RRF", "gemma"), System("pool/gemma RRF+rerank", "gemma", rerank=True, rerank_top=args.rerank_top)]
    if args.fusion:  # per-query z-score fusion against RRF: candidate quality (recall@20) and the final result after the reranker
        for label, weights in (("z(1,1)", (1.0, 1.0)), ("z(dense x2)", (2.0, 1.0)), ("z(lexical x2)", (1.0, 2.0))):
            systems.append(System(f"pool/gemma {label}", "gemma", fusion="zscore", weights=weights))
            systems.append(System(f"pool/gemma {label}+rerank", "gemma", rerank=True, rerank_top=args.rerank_top, fusion="zscore", weights=weights))
    ws = Workspace(pool_dir)
    t0 = time.monotonic()
    ws.ingest()
    log.info("pooled ingest: %.0fs, %d files", time.monotonic() - t0, len(ws.results))
    ws.add_embedder("gemma", build_embedders(settings, ["gemma"])["gemma"])
    pool = P.load_pool(labels, root, ws.db.iter_chunks(), alias)
    reranker = _reranker(settings)
    results = {s.name: evaluate_system(ws, s, pool.queries, reranker) for s in systems}
    best = results["pool/gemma RRF+rerank"]
    by_id = {q.id: q for q in pool.queries}
    where = lambda c: (lambda q: pool.corpus_of[q.id] == c)  # noqa: E731

    parts = [f"# Pooled retrieval evaluation\n\nOne index over {len(ws.results)} files ({', '.join(labels)}), {len(pool.queries)} answerable queries from every corpus's gold file. "
             "Relevance = the chunk is from the gold file and contains the gold snippet. Values are percentages with a 95% bootstrap half-width.\n"]
    drop = ", ".join(f"{c}: {n} unreachable" for c, n in pool.unreachable.items()) or "none"
    parts.append(f"Golden-format questions dropped because no usable chunk holds their evidence verbatim: {drop}. Partial/unanswerable golden rows are not retrieval queries.\n")
    parts.append("## Pooled\n\n" + R.metrics_table(list(results.values())))
    for label in labels:
        parts.append(f"\n## {label} ({sum(1 for q in pool.queries if pool.corpus_of[q.id] == label)} queries)\n\n" + R.metrics_table(list(results.values()), where(label)))
    dup = "; ".join(f"`{a}` = `{b}`" for a, b in alias.items()) or "none"
    parts.append(f"Byte-identical files indexed once (gold names mapped to the kept copy): {dup}.\n")
    if args.fusion:
        pairs = [(f"{lab} vs RRF", results[f"pool/gemma {lab}"], results["pool/gemma RRF"]) for lab in ("z(1,1)", "z(dense x2)", "z(lexical x2)")]
        pairs += [(f"{lab}+rerank vs RRF+rerank", results[f"pool/gemma {lab}+rerank"], best) for lab in ("z(1,1)", "z(dense x2)", "z(lexical x2)")]
        parts.append("\n## Score fusion against RRF (paired bootstrap, A - B, points; bold = interval excludes 0)\n\n" + R.comparisons_table(pairs, metrics=("recall@20", "recall@5", "mrr@10")))
        for lab in ("z(1,1)", "z(dense x2)", "z(lexical x2)"):
            for c in labels:
                d = compare(results[f"pool/gemma {lab}+rerank"], best, "recall@5", where(c))
                parts.append(f"- {lab}+rerank vs RRF+rerank, {c}: recall@5 {100 * d['diff']:+.1f} [{100 * d['lo']:+.1f}, {100 * d['hi']:+.1f}]")
    rows = ["| corpus | queries | top-1 from another corpus | top-1 not from a gold file | no gold-file hit in the top 5 |", "|---|---:|---:|---:|---:|"]
    wrong = {}
    for label in labels + ["all"]:
        qs = [q for q in best.queries if label == "all" or pool.corpus_of[q.id] == label]
        w1 = [P.wrong_document(q.ranked, {g.file for g in by_id[q.id].gold}, 1) for q in qs]
        w5 = [P.wrong_document(q.ranked, {g.file for g in by_id[q.id].gold}, 5) for q in qs]
        x1 = [bool(q.ranked) and q.ranked[0]["source"] not in {g.file for g in by_id[q.id].gold} and corpus_of_file.get(q.ranked[0]["source"]) != pool.corpus_of[q.id] for q in qs]  # a shared file is the answer for both corpora that hold it
        wrong[label] = (len(qs), sum(x1), sum(w1), sum(w5))
        pc = lambda n: f"{n} ({100 * n / max(1, len(qs)):.1f}%)"  # noqa: E731
        rows.append(f"| {label} | {len(qs)} | {pc(sum(x1))} | {pc(sum(w1))} | {pc(sum(w5))} |")
    parts.append("\n## Wrong-document rates (`pool/gemma RRF+rerank`; inside one corpus another file is often a legitimate neighbour topic, another corpus never is)\n\n" + "\n".join(rows))
    isolated = {}
    if args.isolated:
        iso_rows = ["| corpus | isolated recall@5 | pooled recall@5 | difference |", "|---|---:|---:|---:|"]
        for label in labels:
            sub_tmp, sub_dir, sub_alias, _ = P.temp_pool([label], root)
            try:
                sub = Workspace(sub_dir)
                sub.ingest()
                sub.add_embedder("gemma", ws.embedders["gemma"])
                sub_pool = P.load_pool([label], root, sub.db.iter_chunks(), sub_alias)
                if not sub_pool.queries:
                    continue
                iso = evaluate_system(sub, systems[2], sub_pool.queries, reranker)
            finally:
                sub_tmp.cleanup()
            a = list(iso.values("recall@5"))
            ids = {q.id.split(":", 1)[1] for q in iso.queries}
            b = [q.metrics["recall@5"] for q in best.queries if pool.corpus_of[q.id] == label and q.id.split(":", 1)[1] in ids]
            isolated[label] = (sum(a) / len(a), sum(b) / max(1, len(b)))
            iso_rows.append(f"| {label} | {100 * isolated[label][0]:.1f} | {100 * isolated[label][1]:.1f} | {100 * (isolated[label][1] - isolated[label][0]):+.1f} |")
        parts.append("\n## Cost of sharing the index (same queries, same system, one corpus alone vs all together)\n\n" + "\n".join(iso_rows))
    parts.append("\n## Misses (`pool/gemma RRF+rerank`, no relevant chunk in the top 10)\n\n" + R.failures(best, by_id, 10, 25))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".md").write_text("\n".join(parts) + "\n")
    out.with_suffix(".json").write_text(json.dumps({"corpora": labels, "queries": len(pool.queries), "unreachable": pool.unreachable, "wrong_document": wrong, "isolated": isolated,
                                                    "systems": {n: {"all": r.summary(with_ci=False), **{c: r.summary(where(c), with_ci=False) for c in labels}} for n, r in results.items()}}, indent=1))
    print("\n".join(parts[:3]))
    print(f"wrote {out.with_suffix('.md')}")
    tmp.cleanup()
    return 0


def main(argv=None) -> int:
    env.load_dotenv()
    ap = argparse.ArgumentParser(prog="python -m rag_template.evals", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-v", "--verbose", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("retrieval")
    p.add_argument("--corpus", default="evals/corpus/questionprep")
    p.add_argument("--gold", default="evals/gold/handwritten.jsonl")
    p.add_argument("--out", default="evals/results/retrieval")
    p.add_argument("--no-baselines", dest="baselines", action="store_false", help="skip the fixed-window chunker baselines")
    p.add_argument("--rerank-top", type=int, default=20, help="how many fused candidates the reranker reads (the earlier ms-marco results used 60)")
    p.add_argument("--only-origin", default=None, help="restrict to gold queries of one origin (handwritten | synthetic)")
    p = sub.add_parser("ablations")
    p.add_argument("--corpus", default="evals/corpus/questionprep")
    p.add_argument("--gold", default="evals/gold/handwritten.jsonl")
    p.add_argument("--out", default="evals/results/ablations")
    p = sub.add_parser("answerability")
    p.add_argument("--corpus", default="evals/corpus/questionprep")
    p.add_argument("--gold", default="evals/gold/handwritten.jsonl")
    p.add_argument("--synthetic-gold", default="evals/gold/synthetic.jsonl")
    p.add_argument("--unanswerable", default="evals/gold/unanswerable.jsonl")
    p.add_argument("--out", default="evals/results/answerability")
    p.add_argument("--models", nargs="+", default=["jinaai/jina-reranker-v3.5", "cross-encoder/ms-marco-MiniLM-L-6-v2"], help="rerankers whose scores are tested as signals")
    p.add_argument("--rerank-top", type=int, default=20)
    p = sub.add_parser("gate-stability")
    p.add_argument("--corpus", default="evals/corpus/questionprep")
    p.add_argument("--gold", default="evals/gold/handwritten.jsonl")
    p.add_argument("--unanswerable", default="evals/gold/unanswerable.jsonl")
    p.add_argument("--out", default="evals/results/gate_stability")
    p.add_argument("--queries", type=int, default=70, help="answerable and unanswerable queries each (at most)")
    p.add_argument("--shuffles", type=int, default=5)
    p.add_argument("--top", type=int, default=20)
    p.add_argument("--thresholds", nargs="+", type=float, default=[0.183, 0.211, 0.304])
    p = sub.add_parser("rerankers")
    p.add_argument("--corpus", default="evals/corpus/questionprep")
    p.add_argument("--gold", default="evals/gold/handwritten.jsonl")
    p.add_argument("--out", default="evals/results/rerankers")
    p.add_argument("--models", nargs="+", default=["jinaai/jina-reranker-v3.5", "cross-encoder/ms-marco-MiniLM-L-6-v2"], help="Hugging Face ids, each loaded only if you list it here")
    p.add_argument("--tops", nargs="+", type=int, default=[20], help="how many fused candidates the reranker reads")
    p.add_argument("--shuffles", type=int, default=5)
    p.add_argument("--stability-queries", type=int, default=30)
    p = sub.add_parser("gates")
    p.add_argument("--corpus", default="evals/corpus/questionprep")
    p.add_argument("--gold", default="evals/gold/handwritten.jsonl")
    p.add_argument("--out", default="evals/results/gates")
    p = sub.add_parser("pool", help="retrieval over all corpora in one index")
    p.add_argument("--corpora", nargs="+", default=["questionprep", "pdfs", "banking", "pera", "trm", "ssd"])
    p.add_argument("--out", default="evals/results/pooled")
    p.add_argument("--rerank-top", type=int, default=20)
    p.add_argument("--isolated", action="store_true", help="also run each corpus alone, to measure what sharing the index costs")
    p.add_argument("--fusion", action="store_true", help="also run per-query z-score fusion in place of RRF (three weightings, with and without the reranker)")
    p = sub.add_parser("quotes")
    p.add_argument("--corpus", default="evals/corpus/questionprep")
    p.add_argument("--gold", default="evals/gold/handwritten.jsonl")
    p.add_argument("--out", default="evals/results/quote_tolerance")
    p = sub.add_parser("summarize")
    p.add_argument("--results", default="evals/results")
    p.add_argument("--gold", default="evals/gold/handwritten.jsonl")
    p.add_argument("--synthetic-gold", default="evals/gold/synthetic.jsonl")
    p = sub.add_parser("synth")
    p.add_argument("--corpus", default="evals/corpus/questionprep")
    p.add_argument("--out", default="evals/gold/synthetic.jsonl")
    p.add_argument("-n", type=int, default=150)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--max-shared-words", type=int, default=4)
    p = sub.add_parser("conversion", help="convert PDFs with each backend and run the conversion check")
    p.add_argument("--corpus", nargs="+", default=["evals/corpus/pdfs", "evals/corpus/trm", "evals/corpus/pera"])
    p.add_argument("--backends", nargs="+", default=["pymupdf4llm", "docling"])
    p.add_argument("--out", default="evals/results/conversion_check")
    p = sub.add_parser("golden", help="score an ingested store against an external golden QA jsonl")
    p.add_argument("--golden", required=True)
    p.add_argument("--data-dir", default="data", help="the store to evaluate (copy the live one first if the app is running)")
    p.add_argument("--ingest", default=None, help="ingest this file into --data-dir before evaluating")
    p.add_argument("--out", default="evals/results/golden")
    p.add_argument("--label", default="")
    p.add_argument("-k", type=int, default=5)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--policy", default=None)
    p.add_argument("--json-mode", choices=["off", "json_object", "schema"], default=None)
    p.add_argument("--split", choices=["dev", "test", "all"], default="all", help="only the dev (60%%) or test (40%%) questions of evals/split.py")
    p.add_argument("--expand-section", type=int, default=0, help="add up to N chunks that continue a retrieved chunk in the same section")
    p.add_argument("--max-context-tokens", type=int, default=None, help="token budget for the sources in the prompt (Answerer default 3000)")
    p.add_argument("--fuzzy-evidence", action="store_true", help="count a chunk as holding an evidence quote when it contains >= 80%% of the quote's tokens (for golden files whose quotes are renderings of the source)")
    p = sub.add_parser("answers")
    p.add_argument("--corpus", default="evals/corpus/questionprep")
    p.add_argument("--gold", default="evals/gold/handwritten.jsonl")
    p.add_argument("--out", default="evals/results/answers")
    p.add_argument("-k", type=int, default=5)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--extra-gold", nargs="*", default=[], help="more gold files (e.g. evals/gold/unanswerable.jsonl) asked after --gold")
    p.add_argument("--relevance-thresholds", nargs="*", type=float, default=[0.183, 0.211, 0.304], help="pre-LLM relevance gate values to replay (reranker score)")
    p.add_argument("--json-mode", choices=["off", "json_object", "schema"], default=None, help="constrain the reply format (default: LLM_JSON_MODE)")
    p.add_argument("--quotes-first", action=argparse.BooleanOptionalAction, default=None, help="ask for the evidence before the answer (default: RAG_ANSWER_QUOTES_FIRST)")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING, format="%(message)s")
    return {"retrieval": cmd_retrieval, "gates": cmd_gates, "gate-stability": cmd_gate_stability, "answerability": cmd_answerability, "rerankers": cmd_rerankers, "quotes": cmd_quotes, "summarize": cmd_summarize, "ablations": cmd_ablations, "synth": cmd_synth, "answers": cmd_answers, "golden": cmd_golden, "conversion": cmd_conversion, "pool": cmd_pool}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
