import uuid

from rag_template.chunking import ChunkConfig, chunk_file
from rag_template.evaluator import ChunkEvaluator
from rag_template.store.dedupe import SimHashIndex, hamming, simhash
from conftest import SAMPLE_MD, SAMPLE_PY


def seed(db, text=SAMPLE_PY, name="a.py", budget=400):
    chunks = ChunkEvaluator().evaluate_chunks(chunk_file(name, text, ChunkConfig(max_chunk_tokens=budget, min_chunk_tokens=1), source=name))["evaluated_chunks"]
    doc_id = str(uuid.uuid4())
    db.save_document(doc_id, name, simhash(text), len(text), "sha-" + doc_id)
    db.save_chunks(doc_id, chunks)
    return doc_id, chunks


def test_chunks_round_trip_with_metadata(db):
    doc_id, chunks = seed(db)
    rows = db.get_indexable_chunks(doc_id)
    assert [r["chunk_id"] for r in rows] == [c["chunk_id"] for c in chunks if c["evaluation"]["should_use"]]
    retry = next(r for r in rows if r["metadata"].get("qualname") == "retry")
    assert retry["metadata"]["signature"].startswith("def retry(")
    assert retry["breadcrumb"] == "a.py > retry" and retry["content_type"] == "code"
    assert db.get_document(doc_id)["name"] == "a.py"
    assert db.list_documents()[0]["usable_chunks"] == len(rows)


def test_rejected_chunks_are_stored_with_their_reason_but_not_indexable(db):
    doc_id, _ = seed(db, "# Licence\n# Copyright 2024 Example\n# All rights reserved\n\n\ndef compute_value(a, b):\n    return a + b + 1\n", budget=400)
    rejected = db.get_rejected_chunks(doc_id)
    assert rejected and "Comment-only" in rejected[0]["reject_reason"]
    assert all(r["should_use"] == 1 for r in db.get_indexable_chunks(doc_id))


def test_pending_work_is_derived_from_attempts(db):
    doc_id, _ = seed(db)
    assert db.get_pending_documents() == [doc_id]
    assert db.get_pending_documents(exclude=[doc_id]) == []
    ids = db.get_chunk_ids_for_document(doc_id, usable_only=True)
    for i, cid in enumerate(ids):
        assert doc_id in db.get_pending_documents()
        if i % 3 == 0:
            db.save_qa(cid, [{"question": "What?", "answer": "That.", "source_quote": "q", "difficulty": "Easy", "type": "fact"}])
        elif i % 3 == 1:
            db.save_rejections(cid, [{"reason": "Weak quote"}])
        else:
            db.save_enrichment(cid, {"summary": "s", "tags": ["a"], "triplets": []})
    assert db.get_pending_documents() == []
    db.delete_enrichment(ids[2])  # an LLM outage forgets the enrichment: the chunk is pending again
    assert db.get_pending_documents() == [doc_id]
    assert [c["chunk_id"] for c in db.get_chunks_to_enrich(doc_id)] == [ids[2]]


def test_qa_enrichment_and_rejections(db):
    doc_id, _ = seed(db)
    cid = db.get_chunk_ids_for_document(doc_id)[0]
    db.save_enrichment(cid, {"summary": "Sum.", "tags": ["t1"], "triplets": [{"subject": "a", "predicate": "p", "object": "b"}]})
    assert db.get_enrichment(cid)["tags"] == ["t1"]
    db.save_qa(cid, [{"question": " Q1? ", "answer": " A1 ", "source_quote": "src", "difficulty": "Hard", "type": "critical"}])
    qa = db.get_qa_for_chunk(cid)[0]
    assert (qa["question_text"], qa["answer_text"], qa["difficulty"], qa["question_type"]) == ("Q1?", "A1", "Hard", "Critical")
    db.save_rejections(cid, [{"reason": "Deflection", "question": "q", "answer": "a"}, {"reason": "Deflection"}, {"reason": "Weak quote"}])
    db.save_rejections(cid, [{"reason": "Deflection"}])  # a re-run replaces, not appends
    assert db.rejection_summary() == {"Deflection": 1}
    assert db.get_rejections_for_document(doc_id)[0]["chunk_id"] == cid
    assert db.stats()["qa_pairs"] == 1


def test_lexical_search_finds_identifiers_and_respects_document_scope(db):
    a, _ = seed(db, SAMPLE_PY, "a.py", budget=120)
    b, _ = seed(db, "def unrelated_function(value):\n    return value * 2  # nothing to do with caching at all\n", "b.py")
    if not db.has_fts:
        return
    hits = db.search_lexical("how does Cache.get expire values with ttl")
    top = db.get_chunk(hits[0]["chunk_id"])
    assert top["doc_id"] == a and "ttl" in top["content"]
    assert db.search_lexical("unrelated_function", doc_id=b)
    assert db.search_lexical("unrelated_function", doc_id=a) == []
    assert db.search_lexical("!!! ???") == []  # no usable token, no SQL error
    assert db.search_lexical('"; DROP TABLE chunks; --')  is not None


def test_delete_removes_everything_under_the_document(db):
    doc_id, _ = seed(db)
    cid = db.get_chunk_ids_for_document(doc_id)[0]
    db.save_qa(cid, [{"question": "Q?", "answer": "A.", "difficulty": "Easy"}])
    db.save_rejections(cid, [{"reason": "x"}])
    assert db.delete_document(doc_id) is True
    assert db.stats() == {k: 0 for k in db.stats()}
    if db.has_fts:
        assert db.search_lexical("retry") == []
    assert db.delete_document(doc_id) is False


def test_sha256_and_source_lookups(db):
    db.save_document("d1", "docs/a.md", "0" * 16, 10, "abc")
    assert db.get_document_by_sha256("abc")["doc_id"] == "d1"
    assert db.get_document_by_sha256("zzz") is None
    assert db.get_document_by_source("docs/a.md")["doc_id"] == "d1"


# ------------------------------------------------------------------------------ dedupe

def test_simhash_flags_near_duplicates_not_different_documents():
    idx = SimHashIndex(k=3)
    idx.add("orig", simhash(SAMPLE_MD * 4))
    tweaked = (SAMPLE_MD * 4).replace("registry", "registry server", 1) + "\nOne extra closing line."
    assert idx.check(tweaked).is_duplicate and idx.check(tweaked).duplicate_ids == ["orig"]
    assert not idx.check(SAMPLE_PY * 3).is_duplicate
    assert idx.check("").is_duplicate is False
    idx.remove("orig")
    assert not idx.check(SAMPLE_MD * 4).is_duplicate


def test_simhash_is_stable_and_loadable():
    h = simhash("The quick brown fox jumps over the lazy dog " * 5)
    assert h == simhash("The quick brown fox jumps over the lazy dog " * 5) and len(h) == 16
    assert hamming(h, h) == 0
    idx = SimHashIndex()
    idx.load({"x": h})
    assert len(idx) == 1 and idx.check("The quick brown fox jumps over the lazy dog " * 5).duplicate_ids == ["x"]
