"""
mdclean.py: generic repairs for the Markdown a PDF converter produces. Nothing here knows about a particular document.

Why it exists (evals/results/pdf_backends.md, evals/results/pdfs_*.md): converters write presentation, not text.
pymupdf4llm wraps table cells as `constant<br>compute`, so word matching and quote verification fail on every
table; it turns bold fragments into headings (`engage.—`), sprinkles `<sup>`/`<u>` and `**`, and breaks a sentence
with a blank line at a page or column break. Docling leaves `<!-- image -->` markers.

Fenced code is never modified. Every rule only removes markup or joins text; no words are changed or reordered. Superscripts become ^N (a footnote call
keeps its link to the note; an exponent reads naturally).
"""

import re
from typing import List, Tuple

from rag_template.pages import PAGE_LINE

FENCE = re.compile(r"^\s*(```|~~~)")
_SUP = re.compile(
    r"<sup>\s*([^<\s]{1,3})\s*</sup>", re.I
)  # footnote calls and exponents: kept as ^N so the link to "N. Inserted vide ..." survives
TAGS = re.compile(r"</?(?:sup|sub|u|i|b|em|strong|span|mark|small|ins|del|br)(?:\s[^>]*)?>", re.I)
_BR = re.compile(r"<br\s*/?>", re.I)
_PLACEHOLDER = re.compile(
    r"^\s*(?:<!--\s*image\s*-->|\*{0,2}={2,}>\s*picture.*?<={2,}\*{0,2}|!\[[^\]]*\]\([^)]*\))\s*$", re.I
)
_BOLD = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*")  # `**` only: `__init__` and snake__case are text, not markup
_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_BLOCK_START = re.compile(r"^\s*(#{1,6}\s|[-*+]\s|\d+[.)]\s|>|\||```|~~~|<)")
_SEPARATOR = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(?:\|\s*:?-{2,}:?\s*)*\|?\s*$")  # |-----|:---:|---|
_TERMINAL = re.compile(r"[.!?:;)\]”\"'»]\s*$")


def _clean_heading(text: str) -> str:
    text = TAGS.sub("", text)
    text = re.sub(r"[*_`]+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _is_fragment(title: str) -> bool:
    """A "heading" that is half a sentence or just a number: starts in lower case, ends mid-clause, or has no letters."""
    if not title or not re.search(r"[A-Za-z]", title):
        return True
    if title[0].islower():
        return True
    return bool(re.search(r"[,;]$|[—–-]$|\.[—–-]+$", title))


def clean_markdown(md: str) -> str:
    out: List[str] = []
    in_fence = False
    for line in md.split("\n"):
        if FENCE.match(line):
            in_fence = not in_fence
            out.append(line.rstrip())
            continue
        if in_fence:
            out.append(line)
            continue
        if _PLACEHOLDER.match(line):
            continue
        is_row = line.lstrip().startswith("|")
        line = _BR.sub(" " if is_row else "\n", line)
        line = TAGS.sub("", _SUP.sub(r"^\1", line))
        m = _HEADING.match(line)
        if m:
            title = _clean_heading(m.group(2))
            line = title if _is_fragment(title) else f"{m.group(1)} {title}"
        else:
            line = _BOLD.sub(r"\1", line)
            if is_row:
                line = re.sub(r"[ \t]{2,}", " ", line)
                if _SEPARATOR.match(
                    line
                ):  # converters pad the separator to the column width; it carries only the column count
                    line = "|" + "---|" * (line.strip().strip("|").count("|") + 1)
        out.extend(line.rstrip().split("\n"))

    return _join_broken_paragraphs("\n".join(out))


def _blocks(md: str) -> List[Tuple[str, str]]:
    """(kind, text) blocks: a fenced code block is one opaque "fence" block however many blank lines it holds; the rest is split on
    blank lines into "prose" blocks."""
    blocks: List[Tuple[str, str]] = []
    cur: List[str] = []
    in_fence = False

    def flush_prose() -> None:
        for b in re.split(r"\n{2,}", "\n".join(cur)):
            b = b.strip("\n")  # the blank lines next to a fence are separators, not content
            if b.strip():
                blocks.append(("prose", b))
        cur.clear()

    for line in md.split("\n"):
        if FENCE.match(line):
            if not in_fence:
                flush_prose()
            cur.append(line)
            if in_fence:
                blocks.append(("fence", "\n".join(cur)))
                cur.clear()
            in_fence = not in_fence
        else:
            cur.append(line)
    if in_fence:
        blocks.append(("fence", "\n".join(cur)))  # an unclosed fence runs to the end
    else:
        flush_prose()
    return blocks


def _join_broken_paragraphs(md: str) -> str:
    """`...banking companies\\n\\nmay be called...`: a blank line inside a sentence. Joined only when the first
    paragraph ends without terminal punctuation and the next one starts in lower case, and neither is a heading,
    list item, table, quote or code. A page marker between the two (`<!-- page N -->`) does not stop the join: it moves
    inside the joined paragraph, on its own line, so page numbers still know where the new page starts."""
    plain = lambda b: not _BLOCK_START.match(b) and "```" not in b  # noqa: E731
    merged: List[str] = []
    kinds: List[str] = []
    marks: List[str] = []
    for kind, block in _blocks(md):
        if kind == "prose" and PAGE_LINE.match(block.strip()):
            marks.append(block.strip())
            continue
        if (
            kind == "prose"
            and merged
            and kinds[-1] == "prose"
            and plain(merged[-1])
            and plain(block)
            and not _TERMINAL.search(merged[-1])
            and block.lstrip()[:1].islower()
        ):
            merged[-1] = merged[-1].rstrip() + ("\n" + "\n".join(marks) + "\n" if marks else " ") + block.lstrip()
        else:
            merged.extend(marks)
            kinds.extend(["prose"] * len(marks))
            merged.append(block)
            kinds.append(kind)
        marks = []
    merged.extend(marks)
    return "\n\n".join(merged).strip() + "\n"
