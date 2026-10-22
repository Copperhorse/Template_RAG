"""
pages.py: which PDF page(s) a chunk came from, so an answer can say "p. 5" and a reader can check it.

The converters write a marker line `<!-- page N -->` before each page's text. `split_pages` removes the markers again and keeps where
each page starts as an offset into the document's letters and digits (so later whitespace and Markdown changes do not move it).
`assign_pages` finds each chunk's start and end in that text and writes `page` (and `page_end` when the chunk crosses a page break)
into its metadata. A chunk that cannot be located (a caption moved next to its table, a prefixed row label) gets no page rather than a
wrong one.
"""

import bisect
import re
from typing import Any, Dict, List, Sequence, Tuple

PAGE_MARK = "<!-- page {} -->"
PAGE_LINE = re.compile(r"^<!-- page (\d+) -->$")
_NON_ALNUM = re.compile(r"[^0-9a-z]")
_PROBE = 48  # letters and digits of a chunk's start / end used to locate it


def _norm(text: str) -> str:
    return _NON_ALNUM.sub("", text.lower())


def mark_pages(pages: Sequence[Tuple[int, str]]) -> str:
    """[(page number, markdown)] -> one Markdown string with a marker line before each page."""
    return "\n\n".join(f"{PAGE_MARK.format(n)}\n\n{text.strip()}" for n, text in pages if text.strip())


def split_pages(markdown: str) -> Tuple[str, List[List[int]]]:
    """(markdown without marker lines, [[offset, page], ...]) with offsets counted in letters and digits of the returned text."""
    kept: List[str] = []
    marks: List[List[int]] = []
    seen = 0
    for line in markdown.split("\n"):
        m = PAGE_LINE.match(line.strip())
        if m:
            marks.append([seen, int(m.group(1))])
            continue
        kept.append(line)
        seen += len(_norm(line))
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip() + "\n", marks


def assign_pages(chunks: Sequence[Dict[str, Any]], text: str, marks: Sequence[Sequence[int]]) -> int:
    """Set metadata `page` / `page_end` on every chunk that can be located in `text`. Returns how many were. Chunks come in document order,
    so the search resumes where the previous chunk began."""
    if not marks:
        return 0
    flat = _norm(text)
    starts = [m[0] for m in marks]
    page_of = lambda pos: marks[max(0, bisect.bisect_right(starts, pos) - 1)][1]  # noqa: E731
    cursor, found = 0, 0
    for c in chunks:
        body = _norm(c["content"])
        if len(body) < 12:
            continue
        pos = flat.find(body[:_PROBE], cursor)
        if pos < 0:
            pos = flat.find(body[:_PROBE])  # out of order (a caption moved): search the whole text
        if pos < 0:
            continue
        end = flat.find(body[-_PROBE:], pos)
        last = (end if end >= 0 else pos) + min(len(body), _PROBE) - 1
        first_page, last_page = page_of(pos), page_of(last)
        c["metadata"]["page"] = first_page
        if last_page != first_page:
            c["metadata"]["page_end"] = last_page
        cursor, found = last + 1, found + 1  # chunks do not overlap: the next one starts after this one ends
    return found


def page_label(metadata: Dict[str, Any]) -> str:
    """"p. 5", "pp. 5-6" or "" for a chunk without a page."""
    page, end = metadata.get("page"), metadata.get("page_end")
    if not page:
        return ""
    return f"pp. {page}-{end}" if end else f"p. {page}"
