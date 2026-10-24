"""
vector.py: the vector store interface and two implementations.

    InMemoryVectorStore   no dependencies; for tests, notebooks and small corpora
    ChromaVectorStore     persistent (needs the `chroma` extra)

Every vector carries metadata {doc_id, chunk_id, kind} where kind is "chunk" (the chunk text) or "qa"
(a verified question/answer generated from the chunk). Searching QA vectors lets a user question match
the *question* the chunk answers, which usually beats matching the raw passage; a hit on a QA vector
resolves to its chunk (see retrieve.py).
"""

import logging
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Sequence

logger = logging.getLogger("rag_template.vector")


@dataclass
class VectorHit:
    id: str
    score: float  # cosine similarity, higher is better
    document: str
    metadata: Dict[str, Any]


class VectorStore(Protocol):
    def upsert(
        self,
        ids: Sequence[str],
        embeddings: Sequence[Sequence[float]],
        documents: Sequence[str],
        metadatas: Sequence[Dict[str, Any]],
    ) -> None: ...

    def query(
        self, embedding: Sequence[float], n_results: int = 5, where: Optional[Dict[str, Any]] = None
    ) -> List[VectorHit]: ...

    def delete(self, ids: Sequence[str]) -> None: ...

    def delete_document(self, doc_id: str) -> int:
        """Remove every vector of a document. Must raise on failure (callers keep the DB rows then)."""
        ...

    def doc_ids(self) -> Dict[str, str]:
        """{vector id: doc_id ('' if the metadata has none)} for every vector (used by reconcile)."""
        ...

    def count(self) -> int: ...


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class InMemoryVectorStore:
    """Exact cosine search. Uses numpy for the scan when it is installed (it is, with the `local` extra)."""

    def __init__(self) -> None:
        self._rows: Dict[str, tuple] = {}  # id -> (embedding, document, metadata)
        self._matrix = None  # (ids, normalised matrix), rebuilt lazily after a change

    def upsert(self, ids, embeddings, documents, metadatas) -> None:
        for i, e, d, m in zip(ids, embeddings, documents, metadatas):
            self._rows[i] = (list(e), d, dict(m))
        self._matrix = None

    def _scan(self, embedding) -> List[tuple]:
        """[(id, cosine)] for every row."""
        try:
            import numpy as np
        except ImportError:
            return [(i, _cosine(embedding, e)) for i, (e, _, _) in self._rows.items()]
        if self._matrix is None:
            ids = list(self._rows)
            mat = np.array([self._rows[i][0] for i in ids], dtype="float32").reshape(len(ids), -1)
            norms = np.linalg.norm(mat, axis=1, keepdims=True)
            self._matrix = (ids, mat / np.where(norms == 0, 1, norms))
        ids, mat = self._matrix
        q = np.asarray(embedding, dtype="float32")
        qn = np.linalg.norm(q)
        sims = mat @ (q / qn) if qn else np.zeros(len(ids), dtype="float32")
        return list(zip(ids, sims.tolist()))

    def query(self, embedding, n_results=5, where=None) -> List[VectorHit]:
        if not self._rows:
            return []
        hits = []
        for i, score in self._scan(embedding):
            e, d, m = self._rows[i]
            if not where or all(m.get(k) == v for k, v in where.items()):
                hits.append(VectorHit(i, score, d, m))
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:n_results]

    def delete(self, ids) -> None:
        for i in ids:
            self._rows.pop(i, None)
        self._matrix = None

    def delete_document(self, doc_id: str) -> int:
        doomed = [i for i, (_, _, m) in self._rows.items() if m.get("doc_id") == doc_id]
        self.delete(doomed)
        return len(doomed)

    def doc_ids(self) -> Dict[str, str]:
        return {i: str(m.get("doc_id") or "") for i, (_, _, m) in self._rows.items()}

    def count(self) -> int:
        return len(self._rows)


class ChromaVectorStore:
    PAGE = 1000

    def __init__(self, persist_directory: str, collection: str = "rag_chunks"):
        try:
            import chromadb
        except ImportError as e:
            raise ImportError("ChromaVectorStore needs the `chroma` extra: pip install 'rag-template[chroma]'") from e
        self._client = chromadb.PersistentClient(path=str(persist_directory))
        self._collection = self._client.get_or_create_collection(collection, metadata={"hnsw:space": "cosine"})
        logger.info(f"ChromaVectorStore ready: {self._collection.count()} vector(s) in '{collection}'")

    def upsert(self, ids, embeddings, documents, metadatas) -> None:
        if ids:
            self._collection.upsert(
                ids=list(ids),
                embeddings=[list(e) for e in embeddings],
                documents=list(documents),
                metadatas=list(metadatas),
            )

    def query(self, embedding, n_results=5, where=None) -> List[VectorHit]:
        total = self._collection.count()
        if total == 0:
            return []
        kwargs: Dict[str, Any] = {
            "query_embeddings": [list(embedding)],
            "n_results": min(n_results, total),
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where if len(where) == 1 else {"$and": [{k: v} for k, v in where.items()]}
        raw = self._collection.query(**kwargs)
        return [
            VectorHit(i, round(1 - dist, 4), doc, meta or {})
            for i, doc, meta, dist in zip(raw["ids"][0], raw["documents"][0], raw["metadatas"][0], raw["distances"][0])
        ]

    def delete(self, ids) -> None:
        if ids:
            self._collection.delete(ids=list(ids))

    def delete_document(self, doc_id: str) -> int:
        found = self._collection.get(where={"doc_id": doc_id}, include=[]).get("ids", [])
        for i in range(0, len(found), self.PAGE):
            self._collection.delete(ids=found[i : i + self.PAGE])
        return len(found)

    def doc_ids(self) -> Dict[str, str]:
        out: Dict[str, str] = {}
        offset = 0
        while True:
            page = self._collection.get(include=["metadatas"], limit=self.PAGE, offset=offset)
            ids = page.get("ids") or []
            if not ids:
                return out
            for vid, meta in zip(ids, page.get("metadatas") or [{}] * len(ids)):
                out[vid] = str((meta or {}).get("doc_id") or "")
            offset += len(ids)

    def count(self) -> int:
        return self._collection.count()


def make_vector_store(kind: str, directory: str) -> VectorStore:
    if kind == "memory":
        return InMemoryVectorStore()
    if kind == "chroma":
        return ChromaVectorStore(directory)
    raise ValueError(f"unknown vector store '{kind}'; choose chroma or memory")
