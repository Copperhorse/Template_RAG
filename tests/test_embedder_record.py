import pytest

from rag_template.index import EmbedderMismatch, Indexer, verify_embedder
from rag_template.retrieve import Retriever
from rag_template.store.db import Database
from rag_template.store.embedders import HashingEmbedder, embedder_id
from rag_template.store.vector import InMemoryVectorStore


def test_first_indexing_records_the_embedder_and_a_different_one_is_refused(tmp_path):
    db = Database(tmp_path / "r.db")
    Indexer(db, InMemoryVectorStore(), HashingEmbedder(64)).index_document("d")
    assert db.get_meta("embedder:default") == "hashing-64"
    with pytest.raises(EmbedderMismatch, match="hashing-64.*hashing-128"):
        Indexer(db, InMemoryVectorStore(), HashingEmbedder(128)).index_document("d")
    with pytest.raises(EmbedderMismatch):  # the query side too: a query embedded by another model finds nothing useful
        Retriever(db, InMemoryVectorStore(), HashingEmbedder(128))
    Retriever(db, InMemoryVectorStore(), HashingEmbedder(64))


def test_a_store_without_a_record_is_accepted_and_querying_never_writes_one(tmp_path):
    db = Database(tmp_path / "r.db")
    verify_embedder(db, HashingEmbedder(64))
    assert db.get_meta("embedder:default") is None


def test_scopes_keep_several_embedders_on_one_database_apart(tmp_path):
    db = Database(tmp_path / "r.db")
    Indexer(db, InMemoryVectorStore(), HashingEmbedder(64), scope="a").index_document("d")
    Indexer(db, InMemoryVectorStore(), HashingEmbedder(128), scope="b").index_document("d")


def test_matryoshka_dimension_is_part_of_the_identity():
    class E:
        name, truncate_dim = "m", 256

    class Same:
        name, truncate_dim = "m", None

    assert embedder_id(E()) == "m@256" and embedder_id(Same()) == "m"


def test_index_all_only_new_skips_documents_that_already_have_vectors(tmp_path):
    db = Database(tmp_path / "r.db")
    store = InMemoryVectorStore()
    seen = []

    class Spy(Indexer):
        def index_document(self, doc_id):
            seen.append(doc_id)
            return 0

    db.list_documents = lambda: [{"doc_id": "old"}, {"doc_id": "new"}]
    store.doc_ids = lambda: {"v1": "old"}
    Spy(db, store, HashingEmbedder(64)).index_all(only_new=True)
    assert seen == ["new"]
    Spy(db, store, HashingEmbedder(64)).index_all()
    assert seen == ["new", "old", "new"]


def test_a_gpu_out_of_memory_halves_the_batch_and_retries(monkeypatch):
    from rag_template.store import embedders as E

    class OutOfMemoryError(RuntimeError):
        pass

    calls = []

    class Model:
        def encode(self, texts, batch_size, **kw):
            calls.append(batch_size)
            if batch_size > 4:
                raise OutOfMemoryError("CUDA out of memory")
            import numpy as np

            return np.ones((len(texts), 3), dtype="float32")

    emb = E.SentenceTransformerEmbedder("m", batch_size=16)
    emb._model = Model()
    monkeypatch.setattr(E, "_free_gpu_cache", lambda: None)
    assert len(emb.embed_documents(["a", "b"])) == 2
    assert calls == [16, 8, 4] and emb.batch_size == 4


def test_an_error_that_is_not_out_of_memory_is_not_swallowed():
    from rag_template.store import embedders as E

    class Model:
        def encode(self, *a, **k):
            raise ValueError("bad input")

    emb = E.SentenceTransformerEmbedder("m", batch_size=16)
    emb._model = Model()
    with pytest.raises(ValueError):
        emb.embed_documents(["a"])
