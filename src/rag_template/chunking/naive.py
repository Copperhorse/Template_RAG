"""
naive.py: the baseline the structure-aware chunkers are measured against.

Fixed-size windows of whole lines, with no knowledge of headings, functions or classes: what a
"split every N tokens" pipeline does. Chunks only carry their file path and line range. Not registered in
the router; pass `chunk_fn=naive_chunk_file` to `ingest` (the evals do).
"""

from typing import List, Optional

from rag_template.chunking.base import Chunk, ChunkConfig, ContentType, breadcrumb, finalize_chunks, make_chunk
from rag_template.chunking.router import is_code_file
from rag_template.tokens import count_tokens


def naive_chunk_file(path: str, text: str, config: Optional[ChunkConfig] = None, source: Optional[str] = None) -> List[Chunk]:
    config = config or ChunkConfig()
    source = source if source is not None else path
    ctype = ContentType.CODE if is_code_file(path) else ContentType.PROSE
    lines = text.replace("\r\n", "\n").split("\n")
    chunks: List[Chunk] = []
    start, buf, used = 1, [], 0
    for no, line in enumerate(lines, 1):
        n = count_tokens(line) + 1
        if buf and used + n > config.max_chunk_tokens:
            chunks.append(_make(buf, start, no - 1, source, ctype))
            start, buf, used = no, [], 0
        buf.append(line)
        used += n
    if buf:
        chunks.append(_make(buf, start, len(lines), source, ctype))
    return finalize_chunks([c for c in chunks if c["content"].strip()])


def _make(lines: List[str], lo: int, hi: int, source: str, ctype: ContentType) -> Chunk:
    return make_chunk(
        "\n".join(lines).strip("\n"), ctype,
        section_header=f"{source}:{lo}-{hi}", parent_section=source, top_header=source,
        breadcrumb=breadcrumb(source), source=source, start_line=lo, end_line=hi,
    )
