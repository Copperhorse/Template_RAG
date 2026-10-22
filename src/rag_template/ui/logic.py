"""
logic.py: everything the UI computes that is not drawing. Pure functions, unit-tested without Streamlit.
"""

import html
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from rag_template import evidence


def quote_span(content: str, quote: str, content_type: str = "prose") -> Optional[Tuple[int, int]]:
    """Character span of `quote` inside `content`: an exact match, else the span of the text the quote
    is located to (alphanumeric-normalised, as the answer gate does)."""
    if not quote:
        return None
    i = content.find(quote)
    if i >= 0:
        return i, i + len(quote)
    exact = evidence.locate(quote, content, content_type)
    if exact and (j := content.find(exact)) >= 0:
        return j, j + len(exact)
    return None


def highlight_html(content: str, quotes: Sequence[str], content_type: str = "prose") -> str:
    """The chunk as HTML-safe text with each verified quote wrapped in <mark>. All user/document text is escaped."""
    spans = sorted(s for q in quotes if (s := quote_span(content, q, content_type)))
    merged: List[List[int]] = []
    for a, b in spans:
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    out, pos = [], 0
    for a, b in merged:
        out.append(html.escape(content[pos:a]))
        out.append(f"<mark>{html.escape(content[a:b])}</mark>")
        pos = b
    out.append(html.escape(content[pos:]))
    return "<div style='white-space:pre-wrap;font-family:var(--font-mono,monospace);font-size:0.85rem'>" + "".join(out) + "</div>"


def looks_tabular(text: str) -> bool:
    """True for Markdown table rows (lines that start and end with a pipe)."""
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    return bool(lines) and all(ln.startswith("|") and ln.endswith("|") for ln in lines)


def quote_lines(content: str, quote: str, content_type: str = "code") -> Optional[Tuple[int, int]]:
    """1-based line range of the quote within the chunk (for 'lines a-b' captions next to code)."""
    span = quote_span(content, quote, content_type)
    if span is None:
        return None
    return content.count("\n", 0, span[0]) + 1, content.count("\n", 0, span[1]) + 1


def hit_rows(hits: Sequence[Any]) -> List[Dict[str, Any]]:
    """One table row per hit, showing what each retrieval stage thought of it."""
    return [
        {
            "#": i, "chunk": h.label, "type": h.content_type, "dense #": h.dense_rank, "BM25 #": h.lexical_rank,
            "RRF": round(h.rrf_score, 4), "rerank": None if h.rerank_score is None else round(h.rerank_score, 2),
            "final": round(h.score, 4), "found by": "+".join(h.via),
        }
        for i, h in enumerate(hits, 1)
    ]


def chunk_rows(rows: Sequence[Dict[str, Any]], rejected_only: bool = False) -> List[Dict[str, Any]]:
    out = []
    for r in rows:
        if rejected_only and r["should_use"]:
            continue
        out.append({
            "#": r["chunk_index"], "usable": bool(r["should_use"]), "type": r["content_type"], "tokens": r["estimated_tokens"],
            "quality": round(r.get("quality_score") or 0), "section": r["section_header"][:60], "why rejected": r.get("reject_reason") or "",
            "chunk_id": r["chunk_id"],
        })
    return out


def verdict(answer: Any) -> Tuple[str, str]:
    """(level, text) for the answer's gate badge: level is success | warning | info."""
    if answer.refused and answer.grounded:
        if answer.reason:  # refused before the model was called (relevance gate, nothing retrieved)
            return "info", f"No answer was generated: {answer.reason}."
        return "info", "The model declined: the sources do not contain the answer."
    if answer.grounded:
        return "success", f"Passed every gate: {len(answer.quotes)} verified quote(s), {len(answer.citations)} citation(s)."
    return "warning", f"Flagged: {answer.reason}"


def result_files(results_dir: str | Path) -> List[Path]:
    d = Path(results_dir)
    return sorted(d.glob("*.md")) if d.is_dir() else []


def recall_frame(json_path: str | Path) -> Optional[List[Dict[str, Any]]]:
    """Rows [{system, recall@1.. }] from an evals/results/retrieval.json for a chart (None if it has another shape)."""
    try:
        data = json.loads(Path(json_path).read_text())
        systems = data["systems"]
    except (OSError, ValueError, KeyError):
        return None
    ks = ("recall@1", "recall@5", "recall@10")
    return [{"system": name, **{k: round(100 * s["summary"][k]["mean"], 1) for k in ks}} for name, s in systems.items() if "summary" in s]
