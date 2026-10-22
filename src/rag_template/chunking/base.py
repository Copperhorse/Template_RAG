"""
base.py: the chunk record, shared config and the helpers every chunker uses.

A chunk is a plain dict (it goes straight into SQLite and JSON):

    {
      "content":          str,              # exactly what is stored, embedded and quoted
      "estimated_tokens": int,
      "metadata": {
          "content_type":   "prose" | "code" | "math" | "table",
          "section_header": str,            # nearest heading, or the code symbol ("Class.method")
          "parent_section": str | None,     # enclosing heading / class
          "top_header":     str,            # top-level heading, or the file path for code
          "breadcrumb":     str,            # "top > parent > header", prepended when embedding
          ... chunker-specific extras (language, kind, qualname, start_line, end_line, ...)
      },
      "chunk_id", "chunk_index", "prev_chunk_id", "next_chunk_id"   # added by finalize_chunks
    }
"""

import re
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from rag_template.tokens import count_tokens

Chunk = Dict[str, Any]


class ContentType(str, Enum):
    CODE = "code"
    MATH = "math"
    TABLE = "table"
    PROSE = "prose"


@dataclass
class ChunkConfig:
    max_chunk_tokens: int = 500
    min_chunk_tokens: int = 50  # code: units smaller than this are merged with a neighbour
    merge_short_chunks: bool = True


def make_chunk(content: str, content_type: ContentType | str, **metadata: Any) -> Chunk:
    ctype = content_type.value if isinstance(content_type, ContentType) else content_type
    return {
        "content": content,
        "estimated_tokens": count_tokens(content),
        "metadata": {"content_type": ctype, **metadata},
    }


def breadcrumb(*parts: Optional[str]) -> str:
    seen: List[str] = []
    for p in parts:
        if p and p not in seen:
            seen.append(p)
    return " > ".join(seen)


def finalize_chunks(chunks: List[Chunk]) -> List[Chunk]:
    """Assign ids, positions and prev/next links."""
    for i, c in enumerate(chunks):
        c["chunk_id"] = str(uuid.uuid4())
        c["chunk_index"] = i
        c["prev_chunk_id"] = chunks[i - 1]["chunk_id"] if i > 0 else None
        c["next_chunk_id"] = None
    for i in range(len(chunks) - 1):
        chunks[i]["next_chunk_id"] = chunks[i + 1]["chunk_id"]
    return chunks


# --------------------------------------------------------------------------- text splitting

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def hard_split(text: str, max_tokens: int, length: Callable[[str], int] = count_tokens) -> List[str]:
    """Last resort for text with nothing to split on (base64, minified code, a 10 000 character
    token): bisect by characters until every piece fits. The tokens-per-character ratio of such text
    is unpredictable (1 to 4), so a fixed step cannot guarantee the budget; bisection does."""
    if len(text) <= 1 or length(text) <= max_tokens:
        return [text]
    mid = len(text) // 2
    return hard_split(text[:mid], max_tokens, length) + hard_split(text[mid:], max_tokens, length)


class TextSplitter:
    """Recursive splitter: paragraphs, then lines, then sentences, then words, then characters.

    Pieces are packed greedily up to `max_tokens`; a piece that is still too large is split with the
    next, finer separator. Sentence punctuation is kept (the split is a lookbehind), so chunks end
    with their full stop.
    """

    _LEVELS: List[tuple] = [
        (re.compile(r"\n\s*\n"), "\n\n"),
        (re.compile(r"\n"), "\n"),
        (_SENTENCE_END, " "),
        (re.compile(r" "), " "),
    ]

    def __init__(self, max_tokens: int, length: Callable[[str], int] = count_tokens):
        self.max_tokens = max_tokens
        self._len = length

    def split_text(self, text: str) -> List[str]:
        return [c for c in (p.strip() for p in self._split(text, 0)) if c]

    def _split(self, text: str, level: int) -> List[str]:
        if self._len(text) <= self.max_tokens:
            return [text]
        if level >= len(self._LEVELS):
            return hard_split(text, self.max_tokens, self._len)
        pattern, joiner = self._LEVELS[level]
        out: List[str] = []
        current: List[str] = []
        current_len = 0
        for piece in pattern.split(text):
            if not piece.strip():
                continue
            n = self._len(piece)
            if n > self.max_tokens:
                if current:
                    out.append(joiner.join(current))
                    current, current_len = [], 0
                out.extend(self._split(piece, level + 1))
            elif current_len + n > self.max_tokens:
                out.append(joiner.join(current))
                current, current_len = [piece], n
            else:
                current.append(piece)
                current_len += n
        if current:
            out.append(joiner.join(current))
        return out


def pack_lines(text: str, max_tokens: int) -> List[str]:
    """Split code/text into parts of at most `max_tokens`, cutting at a blank line when one is near,
    otherwise between lines. Never cuts inside a line unless a single line is over the limit."""
    lines = text.split("\n")
    parts: List[str] = []
    buf: List[str] = []
    buf_tokens = 0
    last_blank = -1  # index in buf of the last blank line
    for line in lines:
        n = count_tokens(line) + 1
        if n > max_tokens:  # a single huge line (minified code, data): hard split
            if buf:
                parts.append("\n".join(buf))
                buf, buf_tokens, last_blank = [], 0, -1
            parts.extend(hard_split(line, max_tokens))
            continue
        if buf_tokens + n > max_tokens and buf:
            if last_blank > len(buf) // 2:
                parts.append("\n".join(buf[:last_blank]))
                buf = buf[last_blank + 1 :]
            else:
                parts.append("\n".join(buf))
                buf = []
            buf_tokens = sum(count_tokens(b) + 1 for b in buf)
            last_blank = -1
            for i, b in enumerate(buf):
                if not b.strip():
                    last_blank = i
        buf.append(line)
        buf_tokens += n
        if not line.strip():
            last_blank = len(buf) - 1
    if buf:
        parts.append("\n".join(buf))
    return [p.strip("\n") for p in parts if p.strip()]
