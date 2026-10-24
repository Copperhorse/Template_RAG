"""Whole pipeline on a tiny repository with an in-memory vector store, a hashing embedder and the stub LLM."""

import json

from rag_template.cli import main
from rag_template.config import Settings
from rag_template.enrichment.enricher import Gates
from rag_template.enrichment import verify
from rag_template.index import reconcile
from conftest import SAMPLE_PY


def gates():
    return Gates(prose=verify.PairVerifier(use_embeddings=False), code=verify.CodeVerifier())


def built(make_rag, stub, sample_repo):
    rag = make_rag(stub, gates=gates())
    results = rag.ingest_directory(sample_repo)
    assert all(r.ok for r in results.values()), results
    assert not rag.enrich().server_down
    rag.index()
    return rag, results


def test_ingest_directory_walks_supported_files_and_skips_junk(make_rag, sample_repo):
    rag = make_rag()
    results = rag.ingest_directory(sample_repo)
    assert sorted(results) == ["docs/deploy.md", "pkg/retry.py"]  # node_modules skipped, paths relative to the root
    assert all(r.ok and r.usable_chunks > 0 for r in results.values())
    assert {d["source"] for d in rag.db.list_documents()} == set(results)


def test_duplicates_are_caught_by_hash_and_by_simhash(make_rag, sample_repo, tmp_path):
    rag = make_rag()
    rag.ingest_directory(sample_repo)
    again = rag.ingest_directory(sample_repo)
    assert {r.status for r in again.values()} == {"duplicate"} and "Identical" in again["pkg/retry.py"].message
    near = tmp_path / "retry_copy.py"
    near.write_text(SAMPLE_PY + "\n# one trailing comment\n")
    r = rag.ingest_path(near)
    assert r.status == "duplicate" and "Near-duplicate" in r.message
    assert r.duplicate_of == rag.db.get_document_by_source("pkg/retry.py")["doc_id"]


def test_replace_swaps_a_changed_file_and_removes_the_old_vectors(make_rag, stub, sample_repo):
    rag, results = built(make_rag, stub, sample_repo)
    old = results["pkg/retry.py"].doc_id
    path = sample_repo / "pkg" / "retry.py"
    path.write_text(
        SAMPLE_PY.replace("DEFAULT_ATTEMPTS = 3", "DEFAULT_ATTEMPTS = 5").replace("tiny time-to-live", "small expiring")
    )
    new = rag.ingest_path(path, replace=True, source="pkg/retry.py")
    assert new.ok and new.doc_id != old
    assert rag.db.get_document(old) is None and old not in set(rag.store.doc_ids().values())


def test_search_finds_the_right_code_by_identifier_and_by_question(make_rag, stub, sample_repo):
    rag, _ = built(make_rag, stub, sample_repo)
    hits = rag.search("how does Cache.get decide a value has expired (ttl)?", k=3)
    assert hits and hits[0].metadata.get("symbols") and "Cache" in hits[0].label
    assert "ttl" in hits[0].content and hits[0].content_type == "code"
    assert "lexical" in hits[0].via or "dense" in hits[0].via

    hits = rag.search("rollback previous image tag", k=3)
    assert hits[0].source == "docs/deploy.md" and "Rollback" in hits[0].breadcrumb

    scoped = rag.search(
        "rollback previous image tag", k=3, doc_id=rag.db.get_document_by_source("pkg/retry.py")["doc_id"]
    )
    assert all(h.source == "pkg/retry.py" for h in scoped)


def test_qa_vectors_are_indexed_and_resolve_to_their_chunk(make_rag, stub, sample_repo):
    rag, _ = built(make_rag, stub, sample_repo)
    qa = rag.db.get_qa_for_document(rag.db.get_document_by_source("docs/deploy.md")["doc_id"])[0]
    kinds = {m["kind"] for _, _, m in rag.store._rows.values()}
    assert kinds == {"chunk", "qa"}
    hits = rag.search(qa["question_text"], k=3, lexical=False)
    top = next(h for h in hits if h.chunk_id == qa["chunk_id"])
    assert top.matched_question == qa["question_text"] and "qa" in top.via
    assert len({h.chunk_id for h in hits}) == len(hits)  # a chunk and its QA never appear twice


def test_rejected_chunks_are_never_retrievable(make_rag, tmp_path):
    rag = make_rag()
    (tmp_path / "toc.md").write_text(
        "# Contents\n\n1 Intro ........ 1\n2 Methods ........ 5\n3 Results ........ 9\n4 Discussion ........ 12\n5 Notes ........ 20\n"
    )
    r = rag.ingest_path(tmp_path / "toc.md")
    assert r.ok and r.usable_chunks == 0 and r.rejection_reasons
    rag.index()
    assert rag.store.count() == 0 and rag.search("contents intro methods") == []


def test_ask_returns_a_cited_grounded_answer(make_rag, stub, sample_repo):
    rag, _ = built(make_rag, stub, sample_repo)
    a = rag.ask("What does the retry function do between attempts?", k=3)
    assert a.grounded, a.reason
    assert a.citations == [1] and "[S1]" in a.text and not a.refused
    assert a.sources[0].label
    assert "SOURCES:" in stub.chat_requests("ask")[-1]["messages"][-1]["content"]


def test_delete_removes_vectors_rows_and_fts_in_the_safe_order(make_rag, stub, sample_repo):
    rag, results = built(make_rag, stub, sample_repo)
    doc = results["docs/deploy.md"].doc_id
    before = rag.store.count()
    assert rag.delete(doc) is True
    assert doc not in set(rag.store.doc_ids().values()) and rag.store.count() < before
    assert rag.db.get_document(doc) is None
    assert all(h.doc_id != doc for h in rag.search("rollback previous image tag", k=5))
    assert reconcile(rag.db, rag.store) == {"orphan_vectors": [], "unindexed_docs": []}


def test_a_failed_vector_delete_keeps_the_document_intact(make_rag, stub, sample_repo):
    import pytest

    rag, results = built(make_rag, stub, sample_repo)
    doc = results["docs/deploy.md"].doc_id

    def boom(_):
        raise RuntimeError("chroma is down")

    rag.store.delete_document = boom
    with pytest.raises(RuntimeError):
        rag.delete(doc)
    assert rag.db.get_document(doc) is not None and rag.db.get_indexable_chunks(doc)


def test_reconcile_reports_orphans_and_unindexed_documents(make_rag, stub, sample_repo):
    rag, results = built(make_rag, stub, sample_repo)
    rag.store.upsert(
        ["ghost"], [[0.1] * 512], ["text of a deleted file"], [{"doc_id": "gone", "chunk_id": "x", "kind": "chunk"}]
    )
    rag.store.delete_document(results["pkg/retry.py"].doc_id)
    rep = reconcile(rag.db, rag.store)
    assert rep["orphan_vectors"] == ["ghost"] and rep["unindexed_docs"] == [results["pkg/retry.py"].doc_id]
    rag.store.delete(rep["orphan_vectors"])
    rag.index(results["pkg/retry.py"].doc_id)
    assert reconcile(rag.db, rag.store) == {"orphan_vectors": [], "unindexed_docs": []}


def test_status_summarises_the_run(make_rag, stub, sample_repo):
    rag, _ = built(make_rag, stub, sample_repo)
    s = rag.status()
    assert s["documents"] == 2 and s["qa_pairs"] > 0 and s["enriched_chunks"] > 0 and s["usable_chunks"] <= s["chunks"]


# ----------------------------------------------------------------------------- settings + cli


def test_settings_read_the_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("RAG_DATA_DIR", str(tmp_path / "d"))
    monkeypatch.setenv("LLM_BASE_URL", "http://example:1/v1")
    monkeypatch.setenv("LLM_REASONING_BUDGET", "0")
    monkeypatch.setenv("RAG_MAX_CHUNK_TOKENS", "321")
    monkeypatch.setenv("RAG_EMBEDDER", "HASH")
    s = Settings.from_env()
    assert s.llm.base_url == "http://example:1/v1" and s.llm.reasoning_budget == 0
    assert s.max_chunk_tokens == 321 and s.embedder == "hash"
    assert s.db_path == tmp_path / "d" / "rag.db" and s.vector_dir == tmp_path / "d" / "vectors"


def test_dotenv_never_overrides_the_real_environment(monkeypatch, tmp_path):
    from rag_template import env

    f = tmp_path / ".env"
    f.write_text("# c\nexport A_VAR='quoted value'\nB_VAR=plain # trailing\nC_VAR=from_file\nbad line\n")
    monkeypatch.delenv("RAG_NO_DOTENV")
    monkeypatch.setenv("C_VAR", "from_env")
    assert sorted(env.load_dotenv(f)) == ["A_VAR", "B_VAR"]
    import os

    assert (os.environ["A_VAR"], os.environ["B_VAR"], os.environ["C_VAR"]) == ("quoted value", "plain", "from_env")
    for k in ("A_VAR", "B_VAR"):
        monkeypatch.delenv(k)


def test_cli_chunks_preview_and_full_run(monkeypatch, tmp_path, sample_repo, capsys):
    monkeypatch.setenv("RAG_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("RAG_VECTOR_STORE", "memory")
    monkeypatch.setenv("RAG_EMBEDDER", "hash")
    assert main(["chunks", str(sample_repo / "pkg" / "retry.py")]) == 0
    out = capsys.readouterr().out
    assert "retry" in out and "Cache" in out and "usable" in out
    assert main(["chunks", str(sample_repo / "pkg" / "retry.py"), "--json"]) == 0
    assert isinstance(json.loads(capsys.readouterr().out)[0]["evaluation"]["should_use"], bool)

    assert main(["ingest", str(sample_repo)]) == 0
    assert "ok" in capsys.readouterr().out
    assert main(["docs"]) == 0
    assert "pkg/retry.py" in capsys.readouterr().out
    assert main(["status"]) == 0 and json.loads(capsys.readouterr().out)["documents"] == 2
