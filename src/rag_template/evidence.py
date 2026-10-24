"""
evidence.py: source quotations for retrieved chunks.

Two ways to get a quote, both guaranteed to be verbatim text of the chunk:

  extract_quote    extractive, no LLM. The chunk is cut into sentences (prose) or short line windows
                   (code); a scorer (the cross-encoder reranker, or bi-encoder similarity) ranks them
                   against the query and the best span is returned as an exact substring of the chunk.
                   Use it to show *why* a chunk was retrieved, or to gate retrieval on evidence.

  verify_quotes    for quotes a generator produced. Each quote is located in the chunk it claims to come
                   from (alphanumeric-normalised, fuzzy fallback) and replaced by the exact chunk text;
                   a quote that cannot be located is dropped and reported. This is the provenance gate
                   of the enrichment pipeline, applied to answers.
"""

import re
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence, Tuple

from rag_template.enrichment import verify

Scorer = Callable[[str, Sequence[str]], List[float]]  # (query, texts) -> one relevance score per text


@dataclass
class Quote:
    text: str  # verbatim chunk text
    start: int  # character offsets in the chunk
    end: int
    score: Optional[float] = None


def _prose_units(content: str) -> List[Tuple[int, int]]:
    return verify._sentence_spans(content)


def _code_units(content: str, window: int = 4) -> List[Tuple[int, int]]:
    """Sliding windows of up to `window` consecutive non-blank lines (a single line is rarely enough to
    show what code does, a whole function is rarely a useful quote)."""
    lines = [(m.start(), m.end()) for m in re.finditer(r"[^\n]+", content) if m.group().strip()]
    units = []
    for i in range(len(lines)):
        units.append((lines[i][0], lines[min(i + window, len(lines)) - 1][1]))
        if i + window >= len(lines):
            break
    return units or [(0, len(content))]


def extract_quote(query: str, content: str, content_type: str, scorer: Scorer, min_chars: int = 20) -> Optional[Quote]:
    """The span of `content` that best answers `query`, or None if the chunk has no usable span."""
    units = _code_units(content) if content_type == "code" else _prose_units(content)
    units = [(a, b) for a, b in units if len(content[a:b].strip()) >= min_chars] or (
        [(0, len(content))] if content.strip() else []
    )
    if not units:
        return None
    scores = scorer(query, [content[a:b] for a, b in units])
    best = max(range(len(units)), key=scores.__getitem__)
    a, b = units[best]
    return Quote(content[a:b].strip(), a, b, float(scores[best]))


def embedding_scorer(embedder) -> Scorer:
    """Bi-encoder cosine similarity as a scorer (when no cross-encoder is available)."""

    def score(query: str, texts: Sequence[str]) -> List[float]:
        q = embedder.embed_query(query)
        return [sum(x * y for x, y in zip(q, v)) for v in embedder.embed_documents(list(texts))]

    return score


def locate(quote: str, content: str, content_type: str) -> Optional[str]:
    """Exact chunk text for a generated quote (whole lines for code, whole sentences otherwise)."""
    got = verify.locate_quote_ex(quote, content, code=content_type == "code")
    return got[0] if got else None


_FIRST_INT = re.compile(r"\d+")


def parse_source(value) -> Optional[int]:
    """The source number from whatever a model wrote: 1, "1", [1], "[1]", "source 1", ["1"]. None if there is none.
    Small models routinely write the number as a list; discarding such a quote would flag a correct answer."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, (list, tuple)):
        return parse_source(value[0]) if value else None
    m = _FIRST_INT.search(str(value))
    return int(m.group()) if m else None


def verify_quotes(
    candidates: Sequence[Tuple[int, str]], contents: Sequence[Tuple[str, str]], loose: bool = False
) -> Tuple[List[Tuple[int, str, str]], List[Tuple[int, str]]]:
    """candidates: [(source number starting at 1, claimed quote)]; contents: [(chunk text, content type)] in source
    order. Returns (verified [(source, exact chunk text, how)], rejected [(source, claimed quote)]), where `how` is
    exact | fuzzy | loose (see verify.locate_quote_ex). The text is always the chunk's, never the claimed wording."""
    ok, bad = [], []
    for n, quote in candidates:
        if not 1 <= n <= len(contents) or not str(quote).strip():
            bad.append((n, str(quote)))
            continue
        content, ctype = contents[n - 1]
        got = verify.locate_quote_ex(str(quote), content, code=ctype == "code", loose=loose)
        if got:
            ok.append((n, got[0], got[1]))
        else:
            bad.append((n, str(quote)))
    return ok, bad
