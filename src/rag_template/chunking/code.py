"""
code.py: split source code along its syntax tree instead of at arbitrary line counts.

PythonASTChunker  uses the stdlib `ast` module. Every top-level function and class is a chunk, with its
                  decorators and the comment block directly above it. A class that fits in the token
                  budget stays whole; one that does not is cut into a class header (docstring, class
                  attributes) plus one chunk per method, recursively for nested classes. A function that
                  is still too big is cut between statements, never mid-statement, and each later part
                  starts with a comment naming the function. Whatever lies between definitions (imports,
                  constants, module docstring, `if __name__ == "__main__":`) becomes module chunks, so
                  every line of the file lands in exactly one chunk. Tiny neighbours (a 3-line helper, a
                  section comment) are merged up to the budget.

LineCodeChunker   the fallback for every other language, and for Python that does not parse: top-level
                  blocks delimited by blank lines followed by an unindented line, packed to the budget.
                  A tree-sitter based chunker for another language only has to return the same chunk
                  dicts; register it with `chunking.router.register_chunker`.

Chunk metadata adds to the common fields (see base.py): language, kind (module | class | function |
method | block), symbol, qualname, signature, docstring, decorators, start_line, end_line, and
`part` ("2/3") when a unit had to be cut. `section_header` is the qualified name, so retrieval results
and citations read "pkg/service.py > Service.handle_request".
"""

import ast
import re
import textwrap
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from rag_template.chunking.base import (
    Chunk,
    ChunkConfig,
    ContentType,
    breadcrumb,
    finalize_chunks,
    make_chunk,
    pack_lines,
)
from rag_template.tokens import count_tokens

_DEF_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


@dataclass
class _Unit:
    lo: int  # 1-based inclusive line range in the original source
    hi: int
    kind: str  # module | class | function | method
    qualname: str
    scope: str  # qualified name of the enclosing class ("" at module level)
    text: str
    signature: str = ""
    docstring: str = ""
    decorators: List[str] = field(default_factory=list)
    symbols: List[str] = field(default_factory=list)
    part: Optional[Tuple[int, int]] = None

    @property
    def tokens(self) -> int:
        return count_tokens(self.text)


def _signature(node: ast.AST) -> str:
    if isinstance(node, ast.ClassDef):
        bases = [ast.unparse(b) for b in [*node.bases, *node.keywords]]
        return f"class {node.name}({', '.join(bases)})" if bases else f"class {node.name}"
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
        ret = f" -> {ast.unparse(node.returns)}" if node.returns else ""
        return f"{prefix} {node.name}({ast.unparse(node.args)}){ret}"
    return ""


def _first_doc_line(node: ast.AST) -> str:
    try:
        doc = ast.get_docstring(node)  # type: ignore[arg-type]
    except TypeError:
        return ""
    return doc.strip().split("\n", 1)[0][:200] if doc else ""


def _is_docstring(stmt: ast.stmt) -> bool:
    return isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str)


class PythonASTChunker:
    def __init__(self, config: Optional[ChunkConfig] = None):
        self.config = config or ChunkConfig()

    # ------------------------------------------------------------------ entry point

    def process(self, text: str, source: str = "", finalize: bool = True) -> List[Chunk]:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        if not text.strip():
            return []
        try:
            tree = ast.parse(text)
        except (SyntaxError, ValueError, RecursionError) as e:
            chunks = LineCodeChunker(self.config).process(text, source, language="python")
            for c in chunks:
                c["metadata"]["parse_error"] = f"{type(e).__name__}: {e}"
            return finalize_chunks(chunks) if finalize else chunks

        self._lines = text.split("\n")
        units = self._scope_units(tree.body, 1, len(self._lines), scope="", owner=tree)
        if self.config.merge_short_chunks:
            units = self._merge_small(units)
        chunks = [self._to_chunk(u, source) for u in units]
        return finalize_chunks(chunks) if finalize else chunks

    # ------------------------------------------------------------------ line helpers

    def _slice(self, lo: int, hi: int) -> str:
        return textwrap.dedent("\n".join(self._lines[lo - 1 : hi])).strip("\n").rstrip()

    def _node_start(self, node: ast.AST, floor: int) -> int:
        """First line of a definition: its first decorator, then any comment block directly above."""
        start = min([node.lineno, *(d.lineno for d in getattr(node, "decorator_list", []))])
        while start - 1 >= floor and self._lines[start - 2].lstrip().startswith("#"):
            start -= 1
        return max(start, floor)

    # ------------------------------------------------------------------ AST walk

    def _scope_units(self, body: List[ast.stmt], lo: int, hi: int, scope: str, owner: ast.AST) -> List[_Unit]:
        """Units for lines lo..hi: each def/class in `body` plus the gaps between them."""
        units: List[_Unit] = []
        cursor = lo
        for node in (n for n in body if isinstance(n, _DEF_NODES)):
            start = self._node_start(node, cursor)
            if start > cursor:
                units.extend(self._gap(cursor, start - 1, scope, owner))
            units.extend(self._def_units(node, start, node.end_lineno, scope, owner))
            cursor = node.end_lineno + 1
        if cursor <= hi:
            units.extend(self._gap(cursor, hi, scope, owner))
        return self._cap(units)

    def _gap(self, lo: int, hi: int, scope: str, owner: ast.AST) -> List[_Unit]:
        text = self._slice(lo, hi)
        if not text.strip():
            return []
        if scope:  # the head of a class that was cut into methods: signature, docstring, attributes
            return [
                _Unit(lo, hi, "class", scope, scope, text, _signature(owner), _first_doc_line(owner), symbols=[scope])
            ]
        doc = _first_doc_line(owner) if lo == 1 else ""
        return [_Unit(lo, hi, "module", "<module>", "", text, docstring=doc, symbols=["<module>"])]

    def _def_units(self, node: ast.AST, start: int, end: int, scope: str, owner: ast.AST) -> List[_Unit]:
        name = node.name  # type: ignore[attr-defined]
        qual = f"{scope}.{name}" if scope else name
        is_class = isinstance(node, ast.ClassDef)
        kind = "class" if is_class else ("method" if isinstance(owner, ast.ClassDef) else "function")
        text = self._slice(start, end)
        unit = _Unit(
            start,
            end,
            kind,
            qual,
            scope,
            text,
            _signature(node),
            _first_doc_line(node),
            [ast.unparse(d) for d in getattr(node, "decorator_list", [])],
            symbols=[qual],
        )
        if unit.tokens <= self.config.max_chunk_tokens:
            return [unit]
        if is_class:
            return self._scope_units(node.body, start, end, scope=qual, owner=node)  # type: ignore[attr-defined]
        return self._split_function(node, unit)  # type: ignore[arg-type]

    # ------------------------------------------------------------------ oversized units

    def _split_function(self, node: ast.AST, unit: _Unit) -> List[_Unit]:
        """Cut between statements: [signature + docstring] [stmts...] [stmts...]. A statement that is
        itself over budget (a huge dict literal, a 300-line `if`) is cut at blank lines."""
        budget = self.config.max_chunk_tokens
        body: List[ast.stmt] = node.body  # type: ignore[attr-defined]
        stmts = body[1:] if _is_docstring(body[0]) else body
        if not stmts:
            return self._cut_text(unit)
        header_end = min([stmts[0].lineno, *(d.lineno for d in getattr(stmts[0], "decorator_list", []))]) - 1
        windows: List[Tuple[int, int]] = [(unit.lo, header_end)]
        cur_lo, cur_hi = None, None
        prev_end = header_end
        for stmt in stmts:
            s_lo, s_hi = prev_end + 1, stmt.end_lineno
            prev_end = s_hi
            if count_tokens(self._slice(s_lo, s_hi)) > budget:
                if cur_lo is not None:
                    windows.append((cur_lo, cur_hi))
                    cur_lo = cur_hi = None
                windows.append((s_lo, s_hi))
                continue
            if cur_lo is not None and count_tokens(self._slice(cur_lo, s_hi)) > budget:
                windows.append((cur_lo, cur_hi))
                cur_lo = None
            cur_lo = s_lo if cur_lo is None else cur_lo
            cur_hi = s_hi
        if cur_lo is not None:
            windows.append((cur_lo, cur_hi))
        # A signature-only header is not a useful chunk: glue it to the first body part even if that
        # part ends up over budget (the final cap cuts it again, with the header still on top).
        if len(windows) > 1 and count_tokens(self._slice(*windows[0])) < self.config.min_chunk_tokens:
            windows = [(windows[0][0], windows[1][1]), *windows[2:]]
        windows = self._merge_windows(windows, budget)

        parts: List[_Unit] = []
        for i, (lo, hi) in enumerate(windows):
            body_text = self._slice(lo, hi)
            if i > 0:
                body_text = f"# ... continued: {unit.signature}\n{body_text}"
            parts.append(
                _Unit(
                    lo,
                    hi,
                    unit.kind,
                    unit.qualname,
                    unit.scope,
                    body_text,
                    unit.signature,
                    unit.docstring,
                    unit.decorators,
                    [unit.qualname],
                    part=(i + 1, len(windows)),
                )
            )
        return self._cap(parts)

    def _merge_windows(self, windows: List[Tuple[int, int]], budget: int) -> List[Tuple[int, int]]:
        merged: List[Tuple[int, int]] = []
        for lo, hi in windows:
            if hi < lo:  # empty header (cannot happen for valid defs, kept for safety)
                continue
            if merged and count_tokens(self._slice(merged[-1][0], hi)) <= budget:
                merged[-1] = (merged[-1][0], hi)
            else:
                merged.append((lo, hi))
        return merged

    def _cut_text(self, unit: _Unit) -> List[_Unit]:
        pieces = pack_lines(unit.text, self.config.max_chunk_tokens)
        if len(pieces) <= 1:
            return [unit]
        out = []
        for i, piece in enumerate(pieces):
            text = piece if i == 0 else f"# ... continued: {unit.signature or unit.qualname}\n{piece}"
            out.append(
                _Unit(
                    unit.lo,
                    unit.hi,
                    unit.kind,
                    unit.qualname,
                    unit.scope,
                    text,
                    unit.signature,
                    unit.docstring,
                    unit.decorators,
                    unit.symbols,
                    part=(i + 1, len(pieces)),
                )
            )
        return out

    def _cap(self, units: List[_Unit]) -> List[_Unit]:
        """Last resort for any unit still over budget (a giant constant, an unsplittable statement)."""
        out: List[_Unit] = []
        for u in units:
            out.extend(self._cut_text(u) if u.tokens > self.config.max_chunk_tokens else [u])
        return out

    # ------------------------------------------------------------------ merging and output

    def _merge_small(self, units: List[_Unit]) -> List[_Unit]:
        cfg = self.config
        merged: List[_Unit] = []
        for u in units:
            prev = merged[-1] if merged else None
            can = (
                prev is not None
                and prev.scope == u.scope
                and prev.part is None
                and u.part is None
                and (prev.tokens < cfg.min_chunk_tokens or u.tokens < cfg.min_chunk_tokens)
                and prev.tokens + u.tokens <= cfg.max_chunk_tokens
            )
            if can:
                prev.text += "\n\n" + u.text
                prev.hi = u.hi
                prev.symbols += u.symbols
                prev.kind = prev.kind if prev.kind == u.kind else "group"
                prev.decorators = []
            else:
                merged.append(u)
        return merged

    def _to_chunk(self, u: _Unit, source: str) -> Chunk:
        symbols = list(dict.fromkeys(u.symbols))
        header = (
            u.qualname
            if len(symbols) <= 1
            else ", ".join(symbols[:3]) + (f" (+{len(symbols) - 3})" if len(symbols) > 3 else "")
        )
        meta: Dict[str, Any] = {
            "section_header": header,
            "parent_section": u.scope or source or None,
            "top_header": source or "<module>",
            "breadcrumb": breadcrumb(source, header),
            "language": "python",
            "kind": u.kind,
            "symbol": u.qualname.rsplit(".", 1)[-1],
            "qualname": u.qualname,
            "symbols": symbols,
            "signature": u.signature if len(symbols) <= 1 else "",
            "docstring": u.docstring if len(symbols) <= 1 else "",
            "decorators": u.decorators,
            "start_line": u.lo,
            "end_line": u.hi,
        }
        if u.part:
            meta["part"] = f"{u.part[0]}/{u.part[1]}"
        if source:
            meta["source"] = source
        return make_chunk(u.text, ContentType.CODE, **meta)


# =================================================================== generic fallback

_SYMBOL = re.compile(
    r"^\s*(?:export\s+|pub(?:\([\w:]+\))?\s+|public\s+|private\s+|protected\s+|static\s+|async\s+|default\s+|abstract\s+|final\s+)*"
    r"(?:function\*?|class|interface|struct|enum|trait|impl|type|def|fn|func|object|module|namespace)\s+"
    r"(?:<[^>]*>\s*)?([A-Za-z_$][\w$]*)"
)
_CLOSERS = ("}", ")", "]", "end", "else", "elif", "except", "finally", "catch", "case")


class LineCodeChunker:
    """Language-agnostic chunker: top-level blocks (separated by a blank line before an unindented
    line), packed up to the token budget, oversize blocks cut at blank lines."""

    def __init__(self, config: Optional[ChunkConfig] = None):
        self.config = config or ChunkConfig()

    def _blocks(self, lines: List[str]) -> List[Tuple[int, int]]:
        blocks: List[Tuple[int, int]] = []
        start = 0
        for i in range(1, len(lines)):
            line = lines[i]
            top_level = line.strip() and not line[0].isspace() and not line.lstrip().startswith(_CLOSERS)
            if top_level and not lines[i - 1].strip():
                blocks.append((start, i - 1))
                start = i
        blocks.append((start, len(lines) - 1))
        return [(a, b) for a, b in blocks if "\n".join(lines[a : b + 1]).strip()]

    def process(self, text: str, source: str = "", language: str = "") -> List[Chunk]:
        text = text.replace("\r\n", "\n")
        lines = text.split("\n")
        budget = self.config.max_chunk_tokens
        groups: List[Dict[str, Any]] = []
        for a, b in self._blocks(lines):
            block = "\n".join(lines[a : b + 1]).strip("\n")
            tokens = count_tokens(block)
            sym = next((m.group(1) for ln in lines[a : b + 1] if (m := _SYMBOL.match(ln))), "")
            if tokens > budget:
                pieces = pack_lines(block, budget)
                for i, piece in enumerate(pieces):
                    groups.append(
                        {
                            "text": piece,
                            "lo": a + 1,
                            "hi": b + 1,
                            "symbols": [sym] if sym else [],
                            "part": f"{i + 1}/{len(pieces)}",
                            "full": True,
                        }
                    )
                continue
            last = groups[-1] if groups else None
            if (
                last is not None
                and not last["full"]
                and self.config.merge_short_chunks
                and count_tokens(last["text"]) + tokens <= budget
            ):
                last["text"] += "\n\n" + block
                last["hi"] = b + 1
                last["symbols"] += [sym] if sym else []
            else:
                groups.append(
                    {
                        "text": block,
                        "lo": a + 1,
                        "hi": b + 1,
                        "symbols": [sym] if sym else [],
                        "part": None,
                        "full": False,
                    }
                )

        chunks = []
        for g in groups:
            header = ", ".join(g["symbols"][:3]) or (
                f"{source}:{g['lo']}-{g['hi']}" if source else f"lines {g['lo']}-{g['hi']}"
            )
            meta: Dict[str, Any] = {
                "section_header": header,
                "parent_section": source or None,
                "top_header": source or "<file>",
                "breadcrumb": breadcrumb(source, header),
                "language": language,
                "kind": "block",
                "symbols": g["symbols"],
                "start_line": g["lo"],
                "end_line": g["hi"],
            }
            if g["part"]:
                meta["part"] = g["part"]
            if source:
                meta["source"] = source
            chunks.append(make_chunk(g["text"], ContentType.CODE, **meta))
        return finalize_chunks(chunks)
