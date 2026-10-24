"""
markdown.py: header-aware chunking for prose, with protected blocks.

Pipeline
  1. mask      fenced code, $$math$$ and pipe tables are replaced by placeholders so no later step can
               split them or mistake a "# comment" inside code for a heading.
  2. sections  split on Markdown headings, keeping the heading stack (header / parent / top header).
  3. blocks    each section is cut at the placeholders: prose is split by token budget, protected blocks
               come back whole. A block over budget is split *structurally*: a table by rows (header row
               repeated), Python code by AST (see code.py), other code at blank lines (fence repeated).
  4. merge     adjacent small chunks of the same header and type are joined up to the budget.
"""

import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

from rag_template.chunking.base import (
    Chunk,
    ChunkConfig,
    ContentType,
    TextSplitter,
    breadcrumb,
    finalize_chunks,
    make_chunk,
    pack_lines,
)
from rag_template.tables import inherit_row_labels
from rag_template.tokens import count_tokens

_FENCE = re.compile(r"^(```|~~~)[ \t]*([\w+#.-]*)")
_HEADING = re.compile(r"^(#{1,6})\s+(.*)")
# "Table 1. Ablation of ...", "_Table 2._ ...", "**TABLE III:** ...": the caption of the table next to it
_TABLE_CAPTION = re.compile(
    r"^[\s_*]*table\s+(?:\d+|[ivxlc]+)\b\s*[_*]*\s*(?:[.:\-–—]|(?-i:(?=[A-Z])))", re.IGNORECASE
)  # "Table 1. X", "Table 1: X", "Table 3 Generation settings"
_MASK_LINE = re.compile(r"^__MASK_[0-9a-f]+__$")
_MASK_SPLIT = re.compile(r"(__MASK_[0-9a-f]+__)")

MaskStore = Dict[str, Tuple[str, ContentType]]


class MarkdownChunker:
    def __init__(self, config: Optional[ChunkConfig] = None):
        self.config = config or ChunkConfig()
        self.splitter = TextSplitter(self.config.max_chunk_tokens)
        self.block_patterns = [
            (re.compile(r"```[\s\S]*?```"), ContentType.CODE),
            (re.compile(r"\$\$[\s\S]*?\$\$"), ContentType.MATH),
            # Linear-time table pattern: consecutive lines that start and end with a pipe. (A greedy
            # variant hangs on the large tables found in survey papers.)
            (re.compile(r"(?:^\|.*?\|\s*$(?:\n^\|.*?\|\s*$)+)", re.MULTILINE), ContentType.TABLE),
        ]

    # ------------------------------------------------------------------ 1. masking

    def _mask_content(self, text: str) -> Tuple[str, MaskStore]:
        store: MaskStore = {}
        for pattern, c_type in self.block_patterns:

            def replacer(match, c_type=c_type):
                mask_id = f"__MASK_{uuid.uuid4().hex[:8]}__"
                store[mask_id] = (match.group(0), c_type)
                return f"\n{mask_id}\n"

            text = pattern.sub(replacer, text)
        return text, store

    # ------------------------------------------------------------------ 2. sections

    def _split_sections(self, text: str) -> List[Dict[str, Any]]:
        sections: List[Dict[str, Any]] = []
        content: List[str] = []
        stack: Dict[int, str] = {}  # heading level -> title
        level = 0

        def flush() -> None:
            body = "\n".join(content).strip()
            if not body:
                return
            header = stack.get(level, "Root")
            parent = next((stack[k] for k in range(level - 1, 0, -1) if k in stack), None)
            sections.append(
                {
                    "header": header,
                    "section_level": level,
                    "parent": parent,
                    "top_header": stack.get(1, header),
                    "content": body,
                }
            )

        for line in text.split("\n"):
            m = _HEADING.match(line.strip())
            if m and not _MASK_LINE.match(line.strip()):
                flush()
                content = []
                level = len(m.group(1))
                stack[level] = m.group(2).strip()
                for k in [k for k in stack if k > level]:
                    del stack[k]
            else:
                content.append(line)
        flush()
        return sections

    # ------------------------------------------------------------------ 3. blocks

    def _split_table(self, table: str) -> List[str]:
        """Split an oversize table by rows. Every part repeats the header and the caption, and a row whose label only continues the
        previous one (`+ SSD`, `w/ ACT`) is prefixed with that label ("Qwen3-30B-Thinking / + SSD"), so a row chunk says what it is a row of."""
        lines = table.split("\n")
        first = next((i for i, ln in enumerate(lines) if ln.lstrip().startswith("|")), 0)
        last = max((i for i, ln in enumerate(lines) if ln.lstrip().startswith("|")), default=len(lines) - 1)
        caption = "\n".join(ln for ln in lines[:first] + lines[last + 1 :] if ln.strip())
        lines = lines[first : last + 1]
        prefix = caption + "\n\n" if caption else ""
        if len(lines) < 4:
            return pack_lines(table, self.config.max_chunk_tokens)
        head, rows = "\n".join(lines[:2]), inherit_row_labels(lines[2:])
        budget = max(1, self.config.max_chunk_tokens - count_tokens(prefix + head))
        parts, buf, used = [], [], 0
        for row in rows:
            n = count_tokens(row) + 1
            if buf and used + n > budget:
                parts.append(prefix + head + "\n" + "\n".join(buf))
                buf, used = [], 0
            buf.append(row)
            used += n
        if buf:
            parts.append(prefix + head + "\n" + "\n".join(buf))
        return parts

    def _split_code_block(self, block: str) -> List[Tuple[str, Dict[str, Any]]]:
        """Split an oversized fenced block. Returns (text, extra metadata) pairs."""
        lines = block.split("\n")
        m = _FENCE.match(lines[0]) or re.match(r"^(```)\s*(\S*)", lines[0])
        fence, lang = (m.group(1), m.group(2)) if m else ("```", "")
        body = "\n".join(lines[1:-1] if lines[-1].strip().startswith(fence) else lines[1:])

        if lang.lower() in ("python", "py", "python3"):
            from rag_template.chunking.code import PythonASTChunker

            ast_chunks = PythonASTChunker(self.config).process(body, source="", finalize=False)
            if len(ast_chunks) > 1 or ast_chunks[0]["metadata"].get("parse_error") is None:
                return [(f"{fence}{lang}\n{c['content']}\n{fence}", _code_meta(c, lang)) for c in ast_chunks]
        parts = pack_lines(body, self.config.max_chunk_tokens - 10)
        return [(f"{fence}{lang}\n{p}\n{fence}", {"language": lang}) for p in parts]

    def _attach_table_captions(self, parts: List[str], store: MaskStore) -> List[str]:
        """Move a table's caption into the table's own chunk. The caption is the only text that names the table
        ("Table 1: Ablation of ...") and a question usually does; left in the neighbouring prose chunk, it matches
        the question while the numbers sit in a chunk that does not. Looks above the table first, then below."""

        def paragraphs(j: int) -> List[str]:  # the paragraphs of the prose part at index j, or []
            return parts[j].split("\n\n") if 0 <= j < len(parts) and parts[j] and parts[j] not in store else []

        for i, part in enumerate(parts):
            if part not in store or store[part][1] != ContentType.TABLE:
                continue
            original, c_type = store[part]
            before, after = paragraphs(i - 1), paragraphs(i + 1)
            if before and _TABLE_CAPTION.match(before[-1]):
                j, rest, merged = i - 1, "\n\n".join(before[:-1]).strip(), f"{before[-1].strip()}\n\n{original}"
            elif after and _TABLE_CAPTION.match(after[0]):
                next_is_table = (
                    i + 2 < len(parts) and parts[i + 2] in store and store[parts[i + 2]][1] == ContentType.TABLE
                )
                if len(after) == 1 and next_is_table:
                    continue  # the only paragraph between two tables is the second one's caption (captions go above tables)
                j, rest, merged = i + 1, "\n\n".join(after[1:]).strip(), f"{original}\n\n{after[0].strip()}"
            else:
                continue
            store[part], parts[j] = (
                (merged, c_type),
                rest,
            )  # an oversize table is split by rows later and each part keeps the caption
        return parts

    def _process_section(self, section: Dict[str, Any], store: MaskStore) -> List[Chunk]:
        header, parent, top = section["header"], section["parent"], section["top_header"]
        base = {
            "section_header": header,
            "parent_section": parent,
            "top_header": top,
            "breadcrumb": breadcrumb(top, parent, header),
        }
        out: List[Chunk] = []
        parts = self._attach_table_captions([p.strip() for p in _MASK_SPLIT.split(section["content"])], store)
        for part in parts:
            if not part:
                continue
            if part not in store:
                out.extend(make_chunk(t, ContentType.PROSE, **base) for t in self.splitter.split_text(part))
                continue
            original, c_type = store[part]
            if count_tokens(original) <= self.config.max_chunk_tokens:
                out.append(make_chunk(original, c_type, **base))
            elif c_type == ContentType.TABLE:
                out.extend(make_chunk(t, c_type, **base) for t in self._split_table(original))
            elif c_type == ContentType.CODE:
                out.extend(make_chunk(t, c_type, **base, **extra) for t, extra in self._split_code_block(original))
            else:  # math: never split a formula, even when it is large
                out.append(make_chunk(original, c_type, **base))
        return out

    # ------------------------------------------------------------------ 4. merge + entry point

    def _merge(self, chunks: List[Chunk]) -> List[Chunk]:
        merged: List[Chunk] = []
        buf: Optional[Chunk] = None
        for chunk in chunks:
            if buf is None:
                buf = chunk
                continue
            same = (
                buf["metadata"]["section_header"] == chunk["metadata"]["section_header"]
                and buf["metadata"]["content_type"] == chunk["metadata"]["content_type"]
                and buf["metadata"]["content_type"] == ContentType.PROSE.value
            )
            if same and buf["estimated_tokens"] + chunk["estimated_tokens"] <= self.config.max_chunk_tokens:
                buf["content"] += "\n\n" + chunk["content"]
                buf["estimated_tokens"] += chunk["estimated_tokens"]
            else:
                merged.append(buf)
                buf = chunk
        if buf is not None:
            merged.append(buf)
        return merged

    def process(self, markdown_text: str, source: str = "") -> List[Chunk]:
        masked, store = self._mask_content(markdown_text)
        chunks: List[Chunk] = []
        for section in self._split_sections(masked):
            chunks.extend(self._process_section(section, store))
        if self.config.merge_short_chunks:
            chunks = self._merge(chunks)
        if source:
            for c in chunks:
                c["metadata"]["source"] = source
        return finalize_chunks(chunks)


def _code_meta(ast_chunk: Chunk, lang: str) -> Dict[str, Any]:
    m = ast_chunk["metadata"]
    keep = ("symbol", "qualname", "kind", "signature")
    return {"language": lang, **{k: m[k] for k in keep if k in m}}


def chunk_markdown(text: str, **kwargs) -> List[Chunk]:
    return MarkdownChunker(ChunkConfig(**kwargs)).process(text)
