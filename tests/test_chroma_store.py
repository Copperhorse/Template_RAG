"""The persistent store: same contract as the in-memory one, plus persistence across processes."""

import pytest

pytest.importorskip("chromadb")

from rag_template.store.embedders import HashingEmbedder  # noqa: E402
from rag_template.store.vector import ChromaVectorStore  # noqa: E402

E = HashingEmbedder()


def fill(store):
    texts = ["retry sleeps with exponential backoff", "cache entries expire after the ttl", "rollbacks redeploy the previous tag"]
    docs = ["d1", "d1", "d2"]
    store.upsert(
        [f"v{i}" for i in range(3)], E.embed_documents(texts), texts,
        [{"doc_id": d, "chunk_id": f"c{i}", "kind": "chunk"} for i, d in enumerate(docs)],
    )


def test_query_filter_delete_and_listing(tmp_path):
    store = ChromaVectorStore(str(tmp_path / "chroma"))
    assert store.query(E.embed_query("anything")) == []  # empty collection is fine
    fill(store)
    assert store.count() == 3

    hits = store.query(E.embed_query("how long until cache entries expire"), n_results=10)  # more than exist
    assert len(hits) == 3 and hits[0].id == "v1" and hits[0].metadata["chunk_id"] == "c1"
    assert 0.0 < hits[0].score <= 1.0 and hits[0].score >= hits[1].score

    scoped = store.query(E.embed_query("rollback"), n_results=5, where={"doc_id": "d1"})
    assert {h.id for h in scoped} == {"v0", "v1"}
    both = store.query(E.embed_query("rollback"), n_results=5, where={"doc_id": "d1", "kind": "chunk"})
    assert len(both) == 2

    assert store.doc_ids() == {"v0": "d1", "v1": "d1", "v2": "d2"}
    assert store.delete_document("d1") == 2 and store.count() == 1
    assert store.delete_document("d1") == 0
    store.delete(["v2"])
    assert store.count() == 0


def test_upsert_is_idempotent_and_survives_reopening(tmp_path):
    path = str(tmp_path / "chroma")
    store = ChromaVectorStore(path)
    fill(store)
    fill(store)
    assert store.count() == 3
    assert ChromaVectorStore(path).count() == 3


def test_listing_pages_through_more_than_one_page(tmp_path):
    store = ChromaVectorStore(str(tmp_path / "chroma"))
    store.PAGE = 7
    n = 20
    store.upsert([f"v{i}" for i in range(n)], E.embed_documents(["text"] * n), ["text"] * n, [{"doc_id": "d"}] * n)
    assert len(store.doc_ids()) == n
    assert store.delete_document("d") == n and store.count() == 0
