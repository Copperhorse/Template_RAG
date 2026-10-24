import json

import pytest

from rag_template.evals import pooled as P


def test_pool_dir_keeps_each_corpus_relative_path_and_refuses_a_name_clash(tmp_path, monkeypatch):
    for corpus, name in (("a", "docs/x.md"), ("b", "y.pdf")):
        f = tmp_path / corpus / name
        f.parent.mkdir(parents=True)
        f.write_text(f"text of {corpus}")
    monkeypatch.setattr(P, "CORPORA", {"a": ("a", "", ""), "b": ("b", "", ""), "c": ("c", "", "")})
    (tmp_path / "c" / "docs").mkdir(parents=True)
    (tmp_path / "c" / "docs" / "x.md").write_text("different text")
    dest = tmp_path / "pool"
    dest.mkdir()
    _, alias, owner = P.build_pool_dir(["a", "b"], tmp_path, dest)
    assert alias == {} and owner == {"docs/x.md": "a", "y.pdf": "b"}
    assert (dest / "docs/x.md").read_text() == "text of a" and (dest / "y.pdf").exists()
    with pytest.raises(ValueError, match="also in another corpus"):
        P.build_pool_dir(["c"], tmp_path, dest)


def test_golden_format_questions_become_gold_items_only_when_a_usable_chunk_of_that_pdf_holds_the_quote(
    tmp_path, monkeypatch
):
    rows = [
        {
            "id": "q1",
            "question": "Who?",
            "answerable": "yes",
            "evidence": [{"quote": "Alexia Jolicoeur-Martineau"}, {"quote": "not anywhere"}],
        },
        {"id": "q2", "question": "Where?", "answerable": "yes", "evidence": [{"quote": "missing from the pdf"}]},
        {"id": "q3", "question": "Unknowable?", "answerable": "no", "evidence": []},
        {"id": "q4", "question": "Wrong file?", "answerable": "yes", "evidence": [{"quote": "only in other"}]},
    ]
    (tmp_path / "g.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    monkeypatch.setattr(P, "CORPORA", {"t": ("t", "g.jsonl", "paper.pdf")})
    chunks = [
        {"source": "paper.pdf", "content": "By Alexia Jolicoeur-Martineau, Samsung", "should_use": 1},
        {
            "source": "paper.pdf",
            "content": "not anywhere",
            "should_use": 0,
        },  # rejected by the quality gate: unreachable
        {"source": "other.pdf", "content": "only in other", "should_use": 1},
    ]
    pool = P.load_pool(["t"], tmp_path, chunks)
    assert [q.id for q in pool.queries] == ["t:q1"]
    assert [g.snippet for g in pool.queries[0].gold] == [
        "Alexia Jolicoeur-Martineau"
    ]  # the quote nothing holds is dropped, not scored as a miss
    assert pool.unreachable == {"t": 2} and pool.unanswerable == {"t": 1}


def test_wrong_document_means_no_top_k_hit_from_a_gold_file():
    ranked = [{"source": "b.pdf"}, {"source": "a.pdf"}]
    assert P.wrong_document(ranked, {"a.pdf"}, 1) and not P.wrong_document(ranked, {"a.pdf"}, 2)


def test_a_byte_identical_file_in_another_corpus_is_indexed_once_and_its_gold_follows_the_kept_copy(
    tmp_path, monkeypatch
):
    (tmp_path / "a").mkdir(), (tmp_path / "b").mkdir()
    (tmp_path / "a" / "one.pdf").write_text("same bytes")
    (tmp_path / "b" / "two.pdf").write_text("same bytes")
    (tmp_path / "g.jsonl").write_text(
        json.dumps({"id": "x", "query": "q", "gold": [{"file": "two.pdf", "snippet": "s"}]})
    )
    monkeypatch.setattr(P, "CORPORA", {"a": ("a", "", ""), "b": ("b", "g.jsonl", "")})
    dest = tmp_path / "pool"
    dest.mkdir()
    _, alias, owner = P.build_pool_dir(["a", "b"], tmp_path, dest)
    assert alias == {"two.pdf": "one.pdf"} and not (dest / "two.pdf").exists() and owner == {"one.pdf": "a"}
    assert P.load_pool(["b"], tmp_path, alias=alias).queries[0].gold[0].file == "one.pdf"
