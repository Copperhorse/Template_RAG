"""
formats.py: how each embedding model family wants its inputs written.

Many retrieval embedders are trained with a task prefix and give measurably worse results without it:

    EmbeddingGemma   query     "task: search result | query: {text}"       (task: search result,
                                code retrieval, question answering, fact checking)
                     document  "title: {title or none} | text: {text}"
    BGE (English)    query     "Represent this sentence for searching relevant passages: {text}"
    E5               query     "query: {text}"        document  "passage: {text}"
    anything else    no prefix; a document title (the chunk's breadcrumb) is put on its own line above the text

`format_for(model_name)` picks the format by model name. Add a family by appending to `_FORMATS`.
"""

import re
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

DEFAULT_TASK = "search result"
CODE_TASK = "code retrieval"


@dataclass(frozen=True)
class EmbedFormat:
    query: Callable[[str, Optional[str]], str]  # (text, task) -> model input
    document: Callable[[str, Optional[str]], str]  # (text, title) -> model input


def _plain_document(text: str, title: Optional[str]) -> str:
    return f"{title}\n{text}" if title else text


PLAIN = EmbedFormat(lambda text, task: text, _plain_document)

EMBEDDING_GEMMA = EmbedFormat(
    query=lambda text, task: f"task: {task or DEFAULT_TASK} | query: {text}",
    document=lambda text, title: f"title: {title or 'none'} | text: {text}",
)
BGE = EmbedFormat(
    query=lambda text, task: f"Represent this sentence for searching relevant passages: {text}",
    document=_plain_document,
)
E5 = EmbedFormat(
    query=lambda text, task: f"query: {text}", document=lambda text, title: f"passage: {_plain_document(text, title)}"
)

_FORMATS: List[Tuple[re.Pattern, EmbedFormat]] = [
    (re.compile(r"embeddinggemma", re.I), EMBEDDING_GEMMA),
    (re.compile(r"bge-(?!m3)", re.I), BGE),
    (re.compile(r"e5-|multilingual-e5", re.I), E5),
]


def format_for(model_name: str) -> EmbedFormat:
    return next((f for pattern, f in _FORMATS if pattern.search(model_name)), PLAIN)
