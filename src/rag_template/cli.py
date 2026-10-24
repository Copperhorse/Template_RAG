"""
cli.py: `rag` command.

    rag ingest PATH [PATH ...]    files or directories (directories are walked, junk dirs skipped)
    rag index                     embed chunks into the vector store
    rag run PATH [...]            ingest + index   (--enrich also runs the optional enrichment stage)
    rag search "query" [-k 5]     bi-encoder + BM25 -> RRF -> cross-encoder; --quotes shows the evidence
    rag ask "question" [-k 5]     answer that must quote its sources (--strict refuses ungrounded answers)
    rag enrich                    OPTIONAL: LLM summaries/tags + gated Q&A pairs for everything pending
    rag chunks FILE               preview how a file is chunked and what the quality gate says
    rag ui [--port 8501]          the Streamlit app
    rag status | docs | rejections | reconcile | delete DOC_ID
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from rag_template.convcheck import ConversionReport
from rag_template.rag import RAG
from rag_template.retrieve import source_id
from rag_template.store.embedders import embedder_id


def _print_ingest(name: str, r) -> None:
    if r.ok:
        print(f"  ok         {name} ({r.usable_chunks}/{r.chunks} chunks usable)")
        report = ConversionReport.from_dict(r.conversion) if r.conversion else None
        if report and report.flagged:
            print("             " + report.summary().replace("\n", "\n             "))
    else:
        print(f"  {r.status:<10} {name}: {r.message}")


def cmd_ingest(rag: RAG, paths, replace: bool) -> None:
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            for name, r in rag.ingest_directory(p, replace=replace).items():
                _print_ingest(name, r)
        else:
            _print_ingest(str(p), rag.ingest_path(p, replace=replace))


def cmd_chunks(rag: RAG, file: str, as_json: bool) -> None:
    from rag_template.chunking import chunk_file

    text = Path(file).read_text(errors="replace")
    stats = rag.evaluator.evaluate_chunks(chunk_file(file, text, rag.chunk_config, source=file))
    if as_json:
        print(json.dumps(stats["evaluated_chunks"], indent=2, default=str))
        return
    for c in stats["evaluated_chunks"]:
        m, ev = c["metadata"], c["evaluation"]
        mark = "+" if ev["should_use"] else "-"
        lines = f"L{m['start_line']}-{m['end_line']} " if "start_line" in m else ""
        why = "" if ev["should_use"] else f"  [{ev['reason']}]"
        print(
            f"{mark} {c['chunk_index']:>3} {m['content_type']:<5} {c['estimated_tokens']:>4}t {lines}{m['section_header'][:60]}{why}"
        )
    print(f"\n{stats['accepted_chunks']}/{stats['total_chunks']} usable, mean quality {stats['average_quality_score']}")
    for reason, n in stats["rejection_reasons"].items():
        print(f"  rejected x{n}: {reason}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="rag", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-v", "--verbose", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)

    for name in ("ingest", "run"):
        p = sub.add_parser(name)
        p.add_argument("paths", nargs="+")
        p.add_argument("--replace", action="store_true", help="replace a stored document with the same source")
        if name == "run":
            p.add_argument("--enrich", action="store_true", help="also run the optional LLM enrichment stage")
    sub.add_parser("enrich")
    p = sub.add_parser("index")
    p.add_argument("--all", action="store_true", help="re-embed every document, not only those without vectors")
    p.add_argument(
        "--reset-embedder",
        action="store_true",
        help="forget which embedder built the vectors (after you emptied the vector store to switch models)",
    )
    for name in ("search", "ask"):
        p = sub.add_parser(name)
        p.add_argument("query")
        p.add_argument("-k", type=int, default=5)
        p.add_argument("--no-rerank", action="store_true", help="skip the cross-encoder")
        p.add_argument(
            "--min-rerank-score", type=float, default=None, help="drop hits the cross-encoder scores below this"
        )
        if name == "search":
            p.add_argument("--quotes", action="store_true", help="show the best supporting span of each hit")
        if name == "ask":
            p.add_argument("--strict", action="store_true", help="replace a flagged answer with a refusal")
            p.add_argument(
                "--policy",
                choices=["strict", "tolerant", "balanced", "lenient"],
                default=None,
                help="how strict the answer gate is (default: RAG_ANSWER_POLICY)",
            )
    p = sub.add_parser("chunks")
    p.add_argument("file")
    p.add_argument("--json", action="store_true")
    for name in ("status", "docs", "rejections", "reconcile"):
        sub.add_parser(name)
    p = sub.add_parser("delete")
    p.add_argument("doc_id")
    p = sub.add_parser("ui")
    p.add_argument("--port", type=int, default=8501)
    p.add_argument("--host", default="127.0.0.1")

    args = ap.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING, format="%(levelname)s %(name)s: %(message)s"
    )
    if args.cmd == "ui":
        import os

        app = Path(__file__).parent / "ui" / "app.py"
        print(f"RAG template UI: http://{args.host}:{args.port}", flush=True)
        # --server.headless also skips Streamlit's first-run "enter your email" prompt, which blocks forever without a terminal
        os.execvp(
            sys.executable,
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(app),
                "--server.headless",
                "true",
                "--server.port",
                str(args.port),
                "--server.address",
                args.host,
                "--browser.gatherUsageStats",
                "false",
            ],
        )
    rag = RAG()

    if args.cmd == "ingest":
        cmd_ingest(rag, args.paths, args.replace)
    elif args.cmd == "enrich":
        report = rag.enrich()
        print(
            f"enriched {report.documents} document(s)"
            + ("; LLM server went away, rerun to resume" if report.server_down else "")
        )
        return 1 if report.server_down else 0
    elif args.cmd == "index":
        if args.reset_embedder:
            rag.db.set_meta("embedder:default", embedder_id(rag.embedder))
        print(f"indexed {rag.index(everything=args.all)} vector(s)")
    elif args.cmd == "run":
        cmd_ingest(rag, args.paths, args.replace)
        if args.enrich:
            report = rag.enrich()
            print(f"enriched {report.documents} document(s)")
            if report.server_down:
                print("LLM server went away; rerun `rag run --enrich` to resume")
                return 1
        print(f"indexed {rag.index()} vector(s)")
    elif args.cmd == "search":
        kw = dict(rerank=not args.no_rerank, min_rerank_score=args.min_rerank_score)
        for i, h in enumerate(rag.search(args.query, k=args.k, quotes=args.quotes, **kw), 1):
            q = f"  (matches: {h.matched_question})" if h.matched_question else ""
            ranks = f"dense#{h.dense_rank or '-'} bm25#{h.lexical_rank or '-'}" + (
                f" rerank={h.rerank_score:.2f}" if h.rerank_score is not None else ""
            )
            print(f"[{i}] {h.located}  ({ranks}){q}")
            shown = h.quote.text if h.quote else h.content[:200]
            print("    " + ("> " if h.quote else "") + shown.replace("\n", "\n    "))
    elif args.cmd == "ask":
        a = rag.ask(
            args.query,
            k=args.k,
            strict=args.strict,
            policy=args.policy,
            rerank=not args.no_rerank,
            min_rerank_score=args.min_rerank_score,
        )
        print(a.text)
        for i, h in enumerate(a.sources, 1):
            print(f"  [{source_id(i)}] {h.located}")
        for q in a.quotes:
            note = {
                "loose": " (approximate: the model's quote was one word off)",
                "extracted": " (extracted: the model gave no quote)",
            }.get(q.how, "")
            print(f"  quote from [{source_id(q.source)}]{note}: {q.text[:160]!r}")
        if a.missing_terms:
            print(f"  not in any source: {', '.join(a.missing_terms)}")
        for n, claimed in a.unverified_quotes:
            print(f"  DROPPED quote for [{source_id(n)}] (not found in the source): {claimed[:80]!r}")
        if not a.grounded:
            print(f"\nWARNING: not grounded: {a.reason}", file=sys.stderr)
    elif args.cmd == "chunks":
        cmd_chunks(rag, args.file, args.json)
    elif args.cmd == "status":
        print(json.dumps(rag.status(), indent=2))
    elif args.cmd == "docs":
        for d in rag.db.list_documents():
            print(f"{d['doc_id']}  {d['usable_chunks']:>4}/{d['chunks']:<4} chunks  {d['source']}")
    elif args.cmd == "rejections":
        for reason, n in rag.db.rejection_summary().items():
            print(f"{n:>5}  {reason}")
    elif args.cmd == "reconcile":
        rep = rag.reconcile()
        print(json.dumps(rep, indent=2))
        return 0 if not any(rep.values()) else 1
    elif args.cmd == "delete":
        print("deleted" if rag.delete(args.doc_id) else "no such document")
    return 0


if __name__ == "__main__":
    sys.exit(main())
