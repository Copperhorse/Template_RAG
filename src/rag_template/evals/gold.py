"""
gold.py: gold queries and the relevance judgement.

A gold item is `{file, snippet}`: the text (a sentence or a few lines) that answers the query, and where it
lives. A retrieved chunk is relevant when it comes from `file` and contains the snippet (compared on
lower-cased alphanumerics, so whitespace, indentation and fence differences do not matter). Judging by
snippet instead of chunk id means the same gold set scores *any* chunker, which is what makes "AST vs fixed
windows" a fair comparison.

Unanswerable queries (`answerable: false`) have no gold; they test that answering refuses.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Sequence, Set

_NON_ALNUM = re.compile(r"[^0-9a-z]")


def norm(text: str) -> str:
    return _NON_ALNUM.sub("", text.lower())


@dataclass
class GoldItem:
    file: str
    snippet: str

    def covered_by(self, source: str, content_norm: str) -> bool:
        return source == self.file and norm(self.snippet) in content_norm


@dataclass
class Query:
    id: str
    query: str
    type: str = "doc"  # doc | code | none
    style: str = "natural"  # natural | keyword | paraphrase
    answerable: bool = True
    gold: List[GoldItem] = field(default_factory=list)
    answer_contains: List[str] = field(default_factory=list)  # any of these (case-insensitive) in a correct answer
    origin: str = "handwritten"
    kind: str = ""  # unanswerable queries only: far (unrelated) | near (adjacent topic) | premise (a real component, a feature it lacks)
    absent_terms: List[str] = field(
        default_factory=list
    )  # unanswerable queries only: whole words that must occur nowhere in the corpus


def load_gold(path: str | Path) -> List[Query]:
    out = []
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        out.append(
            Query(
                id=d["id"],
                query=d["query"],
                type=d.get("type", "doc"),
                style=d.get("style", "natural"),
                answerable=d.get("answerable", True),
                gold=[GoldItem(**g) for g in d.get("gold", [])],
                answer_contains=d.get("answer_contains", []),
                origin=d.get("origin", "handwritten"),
                kind=d.get("kind", ""),
                absent_terms=d.get("absent_terms", []),
            )
        )
    return out


def save_gold(queries: Sequence[Query], path: str | Path) -> None:
    rows = [
        {
            "id": q.id,
            "type": q.type,
            "style": q.style,
            "query": q.query,
            "answerable": q.answerable,
            "gold": [{"file": g.file, "snippet": g.snippet} for g in q.gold],
            "answer_contains": q.answer_contains,
            "origin": q.origin,
            "kind": q.kind,
            "absent_terms": q.absent_terms,
        }
        for q in queries
    ]
    Path(path).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")


def covered_items(query: Query, source: str, content: str) -> Set[int]:
    c = norm(content)
    return {i for i, g in enumerate(query.gold) if g.covered_by(source, c)}


@dataclass
class Reachability:
    """Where each gold snippet lives in an index: in a usable chunk (retrievable), only in chunks the
    quality gate rejected, or nowhere (the chunker split it across two chunks)."""

    reachable: int = 0
    gated_out: int = 0
    split: int = 0
    details: Dict[str, str] = field(default_factory=dict)


def check_reachability(queries: Sequence[Query], chunks: Sequence[Dict]) -> Reachability:
    """`chunks`: dicts with source, content, should_use (Database.iter_chunks)."""
    normed = [(c["source"], norm(c["content"]), c["should_use"], c.get("reject_reason")) for c in chunks]
    r = Reachability()
    for q in queries:
        for i, g in enumerate(q.gold):
            hits = [(use, why) for src, c, use, why in normed if g.covered_by(src, c)]
            key = f"{q.id}#{i}"
            if any(use for use, _ in hits):
                r.reachable += 1
            elif hits:
                r.gated_out += 1
                r.details[key] = f"rejected by the quality gate: {hits[0][1]}"
            else:
                r.split += 1
                r.details[key] = "snippet not contained in any single chunk"
    return r
