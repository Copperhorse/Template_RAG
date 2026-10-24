"""
rag.py: the facade that wires every stage together.

    rag = RAG()                               # settings from the environment / .env
    rag.ingest_directory("path/to/repo")      # chunk (AST for .py), gate, store
    rag.enrich()                              # LLM metadata + gated Q&A pairs
    rag.index()                               # embeddings -> vector store
    rag.ask("How does retry back off?")       # hybrid retrieval + cited, gated answer

Heavy parts (LLM client, embedder, vector store, gates) are built on first use, so a script that
only ingests needs no model and no server. Every collaborator can be injected for tests or to swap
a component:  RAG(settings, store=InMemoryVectorStore(), embedder=HashingEmbedder(), llm=my_llm).
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from rag_template import env
from rag_template.chunking import ChunkConfig, supported_extensions
from rag_template.config import Settings
from rag_template.enrichment.enricher import EnrichConfig, EnrichmentManager, EnrichReport, Gates
from rag_template.enrichment.judge import make_judge
from rag_template.enrichment.llm import LLMClient
from rag_template.enrichment.prompts import get_prompt_set
from rag_template.evaluator import ChunkEvaluator
from rag_template.index import Indexer, reconcile
from rag_template.ingest import IngestResult, ingest
from rag_template.rerankers import (
    FALLBACK_RERANK_MODEL,
    CrossEncoderReranker,
    Reranker,
    default_rerank_mode,
    make_reranker,
)
from rag_template.retrieve import Answer, Answerer, Hit, Retriever
from rag_template.store.db import Database
from rag_template.store.dedupe import SimHashIndex
from rag_template.store.embedders import Embedder, make_embedder
from rag_template.store.vector import VectorStore, make_vector_store

logger = logging.getLogger("rag_template")

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    "dist",
    "build",
    ".idea",
    ".vscode",
    "site-packages",
}
MAX_FILE_BYTES = 1_000_000


class RAG:
    def __init__(
        self,
        settings: Optional[Settings] = None,
        *,
        db: Optional[Database] = None,
        store: Optional[VectorStore] = None,
        embedder: Optional[Embedder] = None,
        llm: Optional[LLMClient] = None,
        gates: Optional[Gates] = None,
        judge: Any = None,
        reranker: Optional[Reranker] = None,
        enrich_config: Optional[EnrichConfig] = None,
    ):
        if settings is None:
            env.load_dotenv()
            settings = Settings.from_env()
        self.settings = settings
        self.chunk_config = ChunkConfig(
            max_chunk_tokens=settings.max_chunk_tokens, min_chunk_tokens=settings.min_chunk_tokens
        )
        self.evaluator = ChunkEvaluator()
        self.enrich_config = enrich_config

        settings.ensure_dirs()
        self.db = db or Database(settings.db_path)
        self._store, self._embedder, self._llm, self._gates = store, embedder, llm, gates
        self._judge, self._judge_set = judge, judge is not None
        self._reranker, self._reranker_set = reranker, reranker is not None
        self.dedupe = SimHashIndex()
        self.dedupe.load(self.db.get_all_simhashes())

    # ------------------------------------------------------------------ lazy collaborators

    @property
    def store(self) -> VectorStore:
        if self._store is None:
            self._store = make_vector_store(self.settings.vector_store, str(self.settings.vector_dir))
        return self._store

    @property
    def embedder(self) -> Embedder:
        if self._embedder is None:
            s = self.settings
            self._embedder = make_embedder(
                s.embedder, s.embed_model, s.llm.base_url, s.llm.api_key, s.embed_dtype, s.embed_dim
            )
        return self._embedder

    @property
    def llm(self) -> LLMClient:
        if self._llm is None:
            self._llm = LLMClient(self.settings.llm, prompts=get_prompt_set(self.settings.prompt_set))
        return self._llm

    @property
    def gates(self) -> Gates:
        if self._gates is None:
            self._gates = Gates()
        return self._gates

    @property
    def judge(self):
        if not self._judge_set:
            self._judge, self._judge_set = make_judge(self.settings.judge, self.llm), True
        return self._judge

    @property
    def reranker(self) -> Optional[Reranker]:
        """The reranker named by Settings.rerank_model, per RAG_RERANK: "auto" falls back to a small cross-encoder, loudly,
        when the configured one cannot be loaded; "on" raises instead; "off" disables reranking."""
        if self._reranker_set:
            return self._reranker
        s = self.settings
        if s.rerank == "off":
            self._reranker_set = True
            return None
        if s.rerank not in ("auto", "on", "cross-encoder"):
            raise ValueError(f"unknown rerank mode '{s.rerank}'; choose auto, on or off")
        try:
            self._reranker = make_reranker(s.rerank_model, s.rerank_revision, s.rerank_trust_remote_code)
        except Exception as e:  # noqa: BLE001 - import, download, trust or memory problems all end up here
            if s.rerank != "auto":
                raise
            logger.warning(
                f"Could not load the reranker '{s.rerank_model}' ({type(e).__name__}: {str(e)[:160]}); "
                f"falling back to '{FALLBACK_RERANK_MODEL}'. Set RAG_RERANK=on to make this an error."
            )
            try:
                self._reranker = CrossEncoderReranker(FALLBACK_RERANK_MODEL)
                self._rerank_model_in_use = FALLBACK_RERANK_MODEL
            except Exception as e2:  # noqa: BLE001
                logger.warning(
                    f"The fallback reranker could not be loaded either ({type(e2).__name__}); retrieval runs without a rerank stage."
                )
        self._reranker_set = True  # a failure that raised above leaves it unset, so the next access fails again instead of returning None
        return self._reranker

    # ------------------------------------------------------------------ ingest

    def ingest_path(self, path: str | Path, replace: bool = False, source: Optional[str] = None) -> IngestResult:
        """Ingest one file. `replace=True` first removes a stored document with the same source."""
        source = source or str(path)
        if replace:
            old = self.db.get_document_by_source(source)
            if old:
                self.delete(old["doc_id"])
        return ingest(
            path, self.db, self.dedupe, self.chunk_config, self.evaluator, source=source, pdf=self.settings.pdf
        )

    def iter_files(self, root: str | Path, extensions: Optional[Iterable[str]] = None) -> List[Path]:
        root = Path(root)
        wanted = {e.lower() for e in (extensions or [*supported_extensions(), ".pdf"])}
        files: List[Path] = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.endswith(".egg-info"))
            for name in sorted(filenames):
                p = Path(dirpath) / name
                if p.suffix.lower() in wanted and p.stat().st_size <= MAX_FILE_BYTES:
                    files.append(p)
        return files

    def ingest_directory(
        self, root: str | Path, extensions: Optional[Iterable[str]] = None, replace: bool = False
    ) -> Dict[str, IngestResult]:
        """Ingest every supported file under `root`; chunks cite paths relative to `root`."""
        root = Path(root)
        results: Dict[str, IngestResult] = {}
        for p in self.iter_files(root, extensions):
            rel = str(p.relative_to(root))
            results[rel] = self.ingest_path(p, replace=replace, source=rel)
        return results

    # ------------------------------------------------------------------ enrich + index

    def enrich(self) -> EnrichReport:
        """Optional stage: LLM summaries/tags and gated Q&A pairs per chunk (see enrichment/)."""
        manager = EnrichmentManager(self.db, self.llm, self.gates, self.judge, self.enrich_config)
        return manager.run()

    def index(self, doc_id: Optional[str] = None, everything: bool = False) -> int:
        """Embed one document, or the documents that have no vectors yet; `everything=True` re-embeds all of them."""
        indexer = Indexer(self.db, self.store, self.embedder)
        return indexer.index_document(doc_id) if doc_id else indexer.index_all(only_new=not everything)

    def delete(self, doc_id: str) -> bool:
        """Vectors first, then rows: if the vector delete fails the document stays fully intact."""
        self.store.delete_document(doc_id)
        self.dedupe.remove(doc_id)
        return self.db.delete_document(doc_id)

    # ------------------------------------------------------------------ query

    @property
    def retriever(self) -> Retriever:
        reranker = self.reranker  # resolves a fallback first, so the mode below matches the model actually in use
        model_in_use = getattr(
            self, "_rerank_model_in_use", self.settings.rerank_model
        )  # the fallback model has its own (safe) mode
        mode = default_rerank_mode(model_in_use) if self.settings.rerank_mode == "auto" else self.settings.rerank_mode
        return Retriever(
            self.db,
            self.store,
            self.embedder,
            reranker,
            self.settings.query_task,
            mode,
            self.settings.rerank_top,
            route_margin=self.settings.route_margin,
        )

    def search(self, query: str, k: int = 5, **kwargs) -> List[Hit]:
        return self.retriever.search(query, k=k, **kwargs)

    def answerer(self, policy: Optional[str] = None) -> Answerer:
        return Answerer(
            self.retriever,
            self.llm,
            policy=policy or self.settings.answer_policy,
            quotes_first=self.settings.answer_quotes_first,
            min_relevance=self.settings.answer_min_relevance,
        )

    def ask(self, question: str, k: int = 5, strict: bool = False, policy: Optional[str] = None, **kwargs) -> Answer:
        """`policy`: strict | tolerant | balanced | lenient (default Settings.answer_policy); `strict=True` turns a flagged answer into a refusal."""
        return self.answerer(policy).ask(question, k=k, strict=strict, **kwargs)

    # ------------------------------------------------------------------ housekeeping

    def status(self) -> Dict[str, Any]:
        out: Dict[str, Any] = dict(self.db.stats())
        out["rejection_reasons"] = self.db.rejection_summary()
        return out

    def reconcile(self) -> Dict[str, List[str]]:
        return reconcile(self.db, self.store)
