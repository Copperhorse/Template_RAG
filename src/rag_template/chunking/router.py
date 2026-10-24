"""
router.py: pick a chunker from the file extension.

    chunk_file("pkg/service.py", text)   -> AST chunks
    chunk_file("notes.md", text)         -> header-aware Markdown chunks
    chunk_file("app.ts", text)           -> LineCodeChunker (language-agnostic)

`register_chunker(".ts", my_tree_sitter_chunker)` plugs in a better chunker for a language. A chunker
is any callable `(text: str, source: str, config: ChunkConfig) -> List[chunk dict]` (see base.py).
"""

from pathlib import PurePath
from typing import Callable, Dict, List, Optional

from rag_template.chunking.base import Chunk, ChunkConfig
from rag_template.chunking.code import LineCodeChunker, PythonASTChunker
from rag_template.chunking.markdown import MarkdownChunker

ChunkerFn = Callable[[str, str, ChunkConfig], List[Chunk]]

PROSE_EXTENSIONS = {".md", ".markdown", ".mdx", ".txt", ".rst", ".text"}
CODE_LANGUAGES = {
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
    ".scala": "scala",
    ".c": "c",
    ".h": "c",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".lua": "lua",
    ".sh": "shell",
    ".bash": "shell",
    ".sql": "sql",
    ".r": "r",
    ".jl": "julia",
}

_registry: Dict[str, ChunkerFn] = {}


def register_chunker(extension: str, fn: ChunkerFn) -> None:
    _registry[extension.lower()] = fn


def _python(text: str, source: str, config: ChunkConfig) -> List[Chunk]:
    return PythonASTChunker(config).process(text, source)


def _markdown(text: str, source: str, config: ChunkConfig) -> List[Chunk]:
    return MarkdownChunker(config).process(text, source)


def _line_code(language: str) -> ChunkerFn:
    return lambda text, source, config: LineCodeChunker(config).process(text, source, language=language)


register_chunker(".py", _python)
register_chunker(".pyi", _python)
for _ext, _lang in CODE_LANGUAGES.items():
    register_chunker(_ext, _line_code(_lang))
for _ext in PROSE_EXTENSIONS:
    register_chunker(_ext, _markdown)


def supported_extensions() -> List[str]:
    return sorted(_registry)


def is_code_file(path: str) -> bool:
    ext = PurePath(path).suffix.lower()
    return ext in (".py", ".pyi") or ext in CODE_LANGUAGES


def chunk_file(path: str, text: str, config: Optional[ChunkConfig] = None, source: Optional[str] = None) -> List[Chunk]:
    """Chunk `text` the way its extension suggests. `source` is what chunks cite (default: the path)."""
    config = config or ChunkConfig()
    fn = _registry.get(PurePath(path).suffix.lower(), _markdown)
    return fn(text, source if source is not None else str(path), config)
