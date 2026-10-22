"""
retrieval.py: run retrieval systems over a gold set and score them.

A *system* is a retrieval configuration (which stages run, with which embedder and task prefix). For every
answerable query we keep the full ranked list, so any metric can be recomputed later without re-running.
"""

import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence

from rag_template.evals import metrics as M
from rag_template.evals.gold import Query, covered_items, norm
from rag_template.evals.workspace import Workspace
from rag_template.retrieve import Reranker

KS = (1, 3, 5, 10, 20)


@dataclass(frozen=True)
class System:
    name: str
    embedder: str = ""  # key registered with Workspace.add_embedder ("" = no dense stage)
    dense: bool = True
    lexical: bool = True
    rerank: bool = False
    query_task: Optional[str] = None
    weights: tuple = (1.0, 1.0)
    chunker: str = "ast"
    rerank_top: Optional[int] = None
    rerank_mode: str = "replace"
    fusion: str = "rrf"
    reranker: str = ""  # key into the rerankers given to evaluate_system ("" = the default one)


@dataclass
class QueryResult:
    id: str
    type: str
    style: str
    ranked: List[Dict[str, Any]]  # per rank: chunk_id, source, rel (gold indices), ranks, scores
    n_gold: int
    n_relevant_chunks: int
    metrics: Dict[str, float]
    latency_ms: float


@dataclass
class SystemResult:
    system: System
    queries: List[QueryResult] = field(default_factory=list)

    def values(self, metric: str, where: Optional[Callable[[QueryResult], bool]] = None) -> List[float]:
        return [q.metrics[metric] for q in self.queries if where is None or where(q)]

    def summary(self, where: Optional[Callable[[QueryResult], bool]] = None, with_ci: bool = True) -> Dict[str, Any]:
        out: Dict[str, Any] = {"n": len([q for q in self.queries if where is None or where(q)])}
        for m in [f"recall@{k}" for k in KS] + ["mrr@10", "ndcg@10", "map@10"]:
            vals = self.values(m, where)
            mean, lo, hi = M.bootstrap_ci(vals) if with_ci else (M.mean(vals), 0.0, 0.0)
            out[m] = {"mean": mean, "lo": lo, "hi": hi}
        lat = [q.latency_ms for q in self.queries if where is None or where(q)]
        out["latency_ms"] = {"mean": M.mean(lat), "p95": M.percentile(lat, 0.95)}
        return out


def evaluate_system(ws: Workspace, system: System, queries: Sequence[Query], reranker: Optional[Reranker] = None, k: int = 20, rerankers: Optional[Dict[str, Reranker]] = None) -> SystemResult:
    if system.reranker and rerankers:
        reranker = rerankers[system.reranker]
    chunks = ws.db.iter_chunks()
    normed = [(c["chunk_id"], c["source"], norm(c["content"]), c["should_use"]) for c in chunks]
    retriever = ws.retriever(system.embedder, reranker if system.rerank else None, system.query_task) if system.dense else None
    if retriever is None:  # lexical only: any workspace store will do, the dense stage is off
        key = next(iter(ws.stores))
        retriever = ws.retriever(key, reranker if system.rerank else None)

    result = SystemResult(system)
    for q in queries:
        if not q.answerable:
            continue
        started = time.monotonic()
        hits = retriever.search(
            q.query, k=k, dense=system.dense, lexical=system.lexical, rerank=system.rerank,
            weights=system.weights, rerank_top=system.rerank_top, rerank_mode=system.rerank_mode, fusion=system.fusion,
        )
        latency = (time.monotonic() - started) * 1000
        ranked, rel, covered = [], [], []
        for h in hits:
            cov = covered_items(q, h.source, h.content)
            ranked.append({
                "chunk_id": h.chunk_id, "source": h.source, "label": h.label, "rel": sorted(cov),
                "dense_rank": h.dense_rank, "lexical_rank": h.lexical_rank, "rerank_score": h.rerank_score, "rrf": h.rrf_score,
            })
            rel.append(bool(cov))
            covered.append(cov)
        n_rel = sum(1 for cid, src, c, use in normed if use and any(g.covered_by(src, c) for g in q.gold))
        result.queries.append(
            QueryResult(q.id, q.type, q.style, ranked, len(q.gold), n_rel, M.query_metrics(rel, covered, len(q.gold), n_rel, KS), latency)
        )
    return result


def compare(a: SystemResult, b: SystemResult, metric: str = "recall@5", where: Optional[Callable[[QueryResult], bool]] = None) -> Dict[str, float]:
    """Paired bootstrap of a - b on the queries both systems answered."""
    by_id = {q.id: q for q in b.queries}
    pairs = [(q.metrics[metric], by_id[q.id].metrics[metric]) for q in a.queries if q.id in by_id and (where is None or where(q))]
    return M.paired_bootstrap([x for x, _ in pairs], [y for _, y in pairs])


def to_json(res: SystemResult) -> Dict[str, Any]:
    return {"system": asdict(res.system), "summary": res.summary(), "by_type": {t: res.summary(lambda q, t=t: q.type == t) for t in sorted({"doc", "code"} | {q.type for q in res.queries})},
            "by_style": {s: res.summary(lambda q, s=s: q.style == s, with_ci=False) for s in ("natural", "keyword", "paraphrase")},
            "queries": [asdict(q) for q in res.queries]}
