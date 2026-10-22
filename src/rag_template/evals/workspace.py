"""
workspace.py: an isolated index of a corpus for evaluation.

    ws = Workspace(corpus_dir, chunker="ast")        # or "naive" (fixed windows, the baseline)
    ws.ingest()                                       # chunk + quality gate -> SQLite, nothing deduplicated
    ws.add_embedder("gemma", embedder)                # embed every usable chunk -> an in-memory vector store
    hits = ws.retriever("gemma", reranker).search(...)

Several embedders can share one ingest (same chunks, separate vector stores), which is what a fair
embedder comparison needs. Nothing touches your real data directory.
"""

import logging
import tempfile
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional

from rag_template.chunking import ChunkConfig, chunk_file, supported_extensions
from rag_template.chunking.naive import naive_chunk_file
from rag_template.evaluator import ChunkEvaluator
from rag_template.index import Indexer
from rag_template.ingest import IngestResult, ingest
from rag_template.retrieve import Reranker, Retriever
from rag_template.store.db import Database
from rag_template.store.dedupe import SimHashIndex
from rag_template.store.embedders import Embedder
from rag_template.store.vector import InMemoryVectorStore

logger = logging.getLogger("rag_template.evals")

CHUNKERS: Dict[str, Optional[Callable]] = {"ast": None, "naive": naive_chunk_file}  # None = the default router


class Workspace:
    def __init__(self, corpus_dir: str | Path, chunker: str = "ast", max_tokens: int = 500, min_tokens: int = 50, work_dir: Optional[str | Path] = None, breadcrumb: bool = True):
        """`breadcrumb=False` blanks every chunk's breadcrumb (so neither the embedder's document title nor the
        BM25 text carries the symbol path): the control that separates what chunk *boundaries* buy from
        what *metadata* buys."""
        if chunker not in CHUNKERS:
            raise ValueError(f"unknown chunker '{chunker}'; choose from {sorted(CHUNKERS)}")
        self.corpus_dir, self.chunker_name, self.use_breadcrumb = Path(corpus_dir), chunker, breadcrumb
        self.config = ChunkConfig(max_chunk_tokens=max_tokens, min_chunk_tokens=min_tokens)
        self._tmp = None if work_dir else tempfile.TemporaryDirectory(prefix="rag-eval-")
        self.work_dir = Path(work_dir or self._tmp.name)  # type: ignore[union-attr]
        self.db = Database(self.work_dir / f"{chunker}.db")
        self.stores: Dict[str, InMemoryVectorStore] = {}
        self.embedders: Dict[str, Embedder] = {}
        self.ingest_seconds = 0.0
        self.results: Dict[str, IngestResult] = {}

    def files(self) -> List[Path]:
        exts = set(supported_extensions()) | {".pdf"}
        return sorted(p for p in self.corpus_dir.rglob("*") if p.is_file() and p.suffix.lower() in exts)

    def ingest(self) -> Dict[str, IngestResult]:
        started = time.monotonic()
        dedupe = SimHashIndex(k=-1)  # an eval corpus is evaluated whole: never skip a near-duplicate file
        evaluator = ChunkEvaluator()
        for p in self.files():
            rel = str(p.relative_to(self.corpus_dir))
            self.results[rel] = ingest(p, self.db, dedupe, self.config, evaluator, source=rel, chunk_fn=self._chunk_fn())
        self.ingest_seconds = time.monotonic() - started
        return self.results

    def _chunk_fn(self) -> Optional[Callable]:
        base = CHUNKERS[self.chunker_name]
        if self.use_breadcrumb:
            return base

        def without_breadcrumb(path, text, config, source=None):
            chunks = (base or chunk_file)(path, text, config, source=source)
            for c in chunks:
                c["metadata"]["breadcrumb"] = ""
            return chunks

        return without_breadcrumb

    def add_embedder(self, key: str, embedder: Embedder, batch_size: int = 64) -> float:
        """Embed all usable chunks with `embedder`. Returns seconds taken."""
        started = time.monotonic()
        store = InMemoryVectorStore()
        Indexer(self.db, store, embedder, batch_size=batch_size, scope=key).index_all()
        self.stores[key], self.embedders[key] = store, embedder
        return time.monotonic() - started

    def retriever(self, key: str, reranker: Optional[Reranker] = None, query_task: Optional[str] = None) -> Retriever:
        return Retriever(self.db, self.stores[key], self.embedders[key], reranker, query_task, scope=key)

    def chunk_stats(self) -> Dict[str, float]:
        chunks = self.db.iter_chunks()
        usable = [c for c in chunks if c["should_use"]]
        return {
            "files": len(self.results), "chunks": len(chunks), "usable": len(usable),
            "mean_chars": sum(len(c["content"]) for c in usable) / max(1, len(usable)),
        }
