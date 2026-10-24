"""report.py: render evaluation results as Markdown tables."""

from typing import Any, Callable, Dict, Optional, Sequence

from rag_template.evals.retrieval import KS, QueryResult, SystemResult, compare


def pct(x: float) -> str:
    return f"{100 * x:.1f}"


def cell(d: Dict[str, float]) -> str:
    return f"{pct(d['mean'])} ±{pct((d['hi'] - d['lo']) / 2)}"


def metrics_table(
    results: Sequence[SystemResult],
    where: Optional[Callable[[QueryResult], bool]] = None,
    cols: Optional[Sequence[str]] = None,
) -> str:
    cols = cols or [f"recall@{k}" for k in KS] + ["mrr@10", "ndcg@10", "map@10"]
    head = "| system | " + " | ".join(cols) + " | ms/query |\n|---|" + "---:|" * (len(cols) + 1)
    rows = []
    for r in results:
        s = r.summary(where)
        rows.append(
            f"| {r.system.name} | " + " | ".join(cell(s[c]) for c in cols) + f" | {s['latency_ms']['mean']:.0f} |"
        )
    return head + "\n" + "\n".join(rows)


def comparisons_table(
    pairs: Sequence[tuple],
    metrics: Sequence[str] = ("recall@5", "mrr@10"),
    where: Optional[Callable[[QueryResult], bool]] = None,
) -> str:
    """pairs: [(label, SystemResult a, SystemResult b)] -> diff of a - b in points, 95% CI, one-sided p."""
    head = "| comparison (A − B) | " + " | ".join(f"Δ {m}" for m in metrics) + " |\n|---|" + "---:|" * len(metrics)
    rows = []
    for label, a, b in pairs:
        cells = []
        for m in metrics:
            c = compare(a, b, m, where)
            sig = "**" if c["lo"] > 0 or c["hi"] < 0 else ""
            cells.append(
                f"{sig}{100 * c['diff']:+.1f}{sig} [{100 * c['lo']:+.1f}, {100 * c['hi']:+.1f}] p={c['p']:.3f}"
            )
        rows.append(f"| {label} | " + " | ".join(cells) + " |")
    return head + "\n" + "\n".join(rows)


def failures(res: SystemResult, queries_by_id: Dict[str, Any], k: int = 10, limit: int = 12) -> str:
    out = []
    for q in res.queries:
        rank = next((i for i, r in enumerate(q.ranked, 1) if r["rel"]), None)
        if rank is None or rank > k:
            gold = queries_by_id[q.id].gold[0]
            top = "; ".join(r["label"][:50] for r in q.ranked[:3])
            out.append(
                f"- `{q.id}` ({q.type}, {q.style}) **{queries_by_id[q.id].query}**  \n  gold: `{gold.file}`; found at rank {rank or '>' + str(len(q.ranked))}; top-3: {top}"
            )
    return (
        f"{len(out)} queries without a relevant chunk in the top {k}:\n\n"
        + "\n".join(out[:limit])
        + ("\n- …" if len(out) > limit else "")
    )
