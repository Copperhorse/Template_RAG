"""
index.py: embed chunks (and their verified QA pairs) into the vector store.

Two vectors per useful chunk:
    kind="chunk"  the chunk text with its breadcrumb ("pkg/mod.py > Class.method") as the document title,
                  written in the format the embedding model was trained on (store/formats.py)
    kind="qa"     "Question: ...\nAnswer: ..." for each verified pair

Only chunks the evaluator accepted are indexed. Vector ids are deterministic (the chunk id, the QA
id), so re-indexing a document is an idempotent upsert.
"""

import logging
from typing import Dict, List, Optional

from rag_template.store.db import Database
from rag_template.store.embedders import Embedder, embedder_id
from rag_template.store.vector import VectorStore

logger = logging.getLogger("rag_template.index")


class EmbedderMismatch(RuntimeError):
    pass


def verify_embedder(db: Database, embedder: Embedder, scope: str = "default", register: bool = False) -> None:
    """The vectors in a store only mean something to the embedder that made them: a query embedded by another model finds nothing
    useful and nothing says so. The first indexing records the embedder (`register=True`); after that a different one raises.
    A store indexed before this record existed has none and is accepted (its embedder is unknown)."""
    key, now = f"embedder:{scope}", embedder_id(embedder)
    recorded = db.get_meta(key)
    if recorded is None:
        if register:
            db.set_meta(key, now)
    elif recorded != now:
        raise EmbedderMismatch(
            f"This store was indexed with '{recorded}' but the embedder in use is '{now}'. Set EMBED_MODEL back, or re-index into an empty "
            "vector store (delete data/chroma and run `rag index`) and clear the record with `rag index --reset-embedder`."
        )


class Indexer:
    def __init__(self, db: Database, store: VectorStore, embedder: Embedder, batch_size: int = 64, scope: str = "default"):
        self.db, self.store, self.embedder, self.batch_size, self.scope = db, store, embedder, batch_size, scope

    def index_document(self, doc_id: str) -> int:
        """Embed and upsert every usable chunk and QA pair of a document. Returns the vector count."""
        verify_embedder(self.db, self.embedder, self.scope, register=True)
        chunks = self.db.get_indexable_chunks(doc_id)
        ids: List[str] = []
        texts: List[str] = []
        titles: List[Optional[str]] = []  # the breadcrumb is the document title, formatted by the embedder
        metas: List[Dict] = []
        for c in chunks:
            ids.append(c["chunk_id"])
            texts.append(c["content"])
            titles.append(c.get("breadcrumb") or None)
            metas.append({"doc_id": doc_id, "chunk_id": c["chunk_id"], "kind": "chunk"})
            for qa in self.db.get_qa_for_chunk(c["chunk_id"]):
                ids.append(qa["qa_id"])
                texts.append(f"Question: {qa['question_text']}\nAnswer: {qa['answer_text']}")
                titles.append(None)
                metas.append({"doc_id": doc_id, "chunk_id": c["chunk_id"], "kind": "qa", "difficulty": qa["difficulty"] or ""})

        for i in range(0, len(ids), self.batch_size):
            sl = slice(i, i + self.batch_size)
            self.store.upsert(ids[sl], self.embedder.embed_documents(texts[sl], titles[sl]), texts[sl], metas[sl])
        logger.info(f"Indexed {len(ids)} vector(s) for document {doc_id[:8]} ({len(chunks)} chunk(s))")
        return len(ids)

    def index_all(self, only_new: bool = False) -> int:
        """Embed every document, or with `only_new` just those that have no vectors yet (what "index new documents" means)."""
        have = set(self.store.doc_ids().values()) if only_new else set()
        return sum(self.index_document(d["doc_id"]) for d in self.db.list_documents() if d["doc_id"] not in have)

    def delete_document(self, doc_id: str) -> int:
        """Remove a document's vectors. Raises on failure: do not delete the database rows then."""
        return self.store.delete_document(doc_id)


def reconcile(db: Database, store: VectorStore) -> Dict[str, List[str]]:
    """Compare the database with the vector store.

    orphan_vectors    vector ids whose document is not in the database (a failed delete left them;
                      they still hold the deleted text)
    unindexed_docs    documents with usable chunks but no vectors (indexing failed or was skipped)
    Fix orphans with `store.delete(ids)`; fix unindexed documents with `Indexer.index_document`.
    """
    docs = {d["doc_id"]: d for d in db.list_documents()}
    vec = store.doc_ids()
    orphans = sorted(v for v, doc in vec.items() if doc not in docs)
    indexed = {doc for doc in vec.values() if doc}
    unindexed = sorted(d for d, row in docs.items() if row["usable_chunks"] and d not in indexed)
    return {"orphan_vectors": orphans, "unindexed_docs": unindexed}
