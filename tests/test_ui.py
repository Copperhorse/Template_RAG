"""The Streamlit app: pure display logic, then the real script driven headlessly with streamlit.testing.v1.AppTest."""

import json
from pathlib import Path

import pytest

from rag_template.retrieve import Answer, Hit, QuotedSource
from rag_template.ui import logic

APP = str(Path(__file__).resolve().parents[1] / "src" / "rag_template" / "ui" / "app.py")
CONTENT = "Intro line.\nA rollback redeploys the previous image tag. It <b>never</b> needs a rebuild & finishes fast.\nOutro."


def test_highlight_wraps_the_quote_and_escapes_everything_else():
    out = logic.highlight_html(CONTENT, ["A rollback redeploys the previous image tag."])
    assert "<mark>A rollback redeploys the previous image tag.</mark>" in out
    assert "&lt;b&gt;never&lt;/b&gt;" in out and "&amp; finishes" in out and "<b>" not in out  # document text can never inject markup
    assert out.count("<mark>") == 1


def test_highlight_handles_fuzzy_quotes_overlaps_and_missing_quotes():
    fuzzy = logic.highlight_html(CONTENT, ["a rollback redeploys the previous image tag"])  # the answer gate's normalised match
    assert "<mark>A rollback redeploys the previous image tag.</mark>" in fuzzy
    merged = logic.highlight_html("alpha beta gamma delta epsilon", ["alpha beta gamma", "gamma delta epsilon"])
    assert merged.count("<mark>") == 1 and "<mark>alpha beta gamma delta epsilon</mark>" in merged
    assert "<mark>" not in logic.highlight_html(CONTENT, ["a sentence that is nowhere in the text at all"])
    assert logic.quote_span(CONTENT, "") is None


def test_quote_lines_for_code():
    code = "def f(x):\n    y = x * 2\n    return y + 1\n"
    assert logic.quote_lines(code, "return y + 1", "code") == (3, 3)
    assert logic.quote_lines(code, "y = x * 2\n    return y + 1", "code") == (2, 3)
    assert logic.quote_lines(code, "not present anywhere here", "code") is None


def test_verdict_levels():
    hit = Hit("c", "d", "a.md", 1.0, CONTENT)
    grounded = Answer("x [S1]", [hit], quotes=[QuotedSource(1, hit, "q")], citations=[1])
    assert logic.verdict(grounded)[0] == "success" and "1 verified quote" in logic.verdict(grounded)[1]
    assert logic.verdict(Answer("idk", [hit], refused=True))[0] == "info"
    flagged = logic.verdict(Answer("x", [hit], grounded=False, reason="no verified quote from cited source(s) [S1]"))
    assert flagged[0] == "warning" and "no verified quote" in flagged[1]


def test_rows_for_tables():
    h = Hit("c", "d", "a.md", 0.5, "t", "a.md > S", "prose", rrf_score=0.0325, rerank_score=3.14159, dense_rank=2, lexical_rank=None)
    row = logic.hit_rows([h])[0]
    assert row["dense #"] == 2 and row["BM25 #"] is None and row["rerank"] == 3.14 and row["found by"] == "dense+rerank"
    rows = [{"chunk_id": "a", "chunk_index": 0, "should_use": 1, "content_type": "prose", "estimated_tokens": 10, "quality_score": 80.4, "section_header": "S", "reject_reason": None},
            {"chunk_id": "b", "chunk_index": 1, "should_use": 0, "content_type": "code", "estimated_tokens": 5, "quality_score": 0, "section_header": "T", "reject_reason": "Imports only"}]
    assert len(logic.chunk_rows(rows)) == 2
    only = logic.chunk_rows(rows, rejected_only=True)
    assert len(only) == 1 and only[0]["why rejected"] == "Imports only" and only[0]["usable"] is False


def test_result_files_and_recall_frame(tmp_path):
    assert logic.result_files(tmp_path / "missing") == []
    (tmp_path / "b.md").write_text("x"), (tmp_path / "a.md").write_text("y"), (tmp_path / "a.json").write_text("{}")
    assert [p.name for p in logic.result_files(tmp_path)] == ["a.md", "b.md"]
    js = tmp_path / "retrieval.json"
    js.write_text(json.dumps({"systems": {"s1": {"summary": {"recall@1": {"mean": 0.5}, "recall@5": {"mean": 0.75}, "recall@10": {"mean": 0.9}}}}}))
    assert logic.recall_frame(js) == [{"system": "s1", "recall@1": 50.0, "recall@5": 75.0, "recall@10": 90.0}]
    assert logic.recall_frame(tmp_path / "a.json") is None and logic.recall_frame(tmp_path / "nope.json") is None


# ----------------------------------------------------------------------------- the real app

@pytest.fixture
def app(tmp_path, monkeypatch, stub, sample_repo):
    import streamlit as st
    from streamlit.testing.v1 import AppTest

    for k, v in {"RAG_DATA_DIR": str(tmp_path / "data"), "RAG_VECTOR_STORE": "memory", "RAG_EMBEDDER": "hash", "RAG_RERANK": "off",
                 "LLM_BASE_URL": stub.url, "LLM_REASONING_BUDGET": "0", "RAG_MAX_CHUNK_TOKENS": "200", "RAG_RESULTS_DIR": str(tmp_path / "results")}.items():
        monkeypatch.setenv(k, v)
    (tmp_path / "results").mkdir()
    (tmp_path / "results" / "demo.md").write_text("# Demo report\n\nSome numbers.")
    st.cache_resource.clear()
    at = AppTest.from_file(APP, default_timeout=60)
    at.sample_repo = sample_repo
    yield at
    st.cache_resource.clear()


def button(at, label):
    return next(b for b in at.button if b.label == label)


def test_app_starts_with_an_empty_library(app):
    app.run()
    assert not app.exception
    assert [t.label for t in app.tabs] == ["Ask", "Search", "Library", "Evals", "Status"]
    assert any("library is empty" in i.value for i in app.info)
    assert any("Demo" in m.value for m in app.markdown) or any("demo" in str(s.options) for s in app.selectbox)


def test_ingest_index_search_and_ask_through_the_app(app):
    app.run()
    next(t for t in app.text_input if t.label == "File or folder path").set_value(str(app.sample_repo))
    app.run()
    button(app, "Ingest path").click()
    app.run()
    assert not app.exception
    ingested = next(df for df in app.dataframe if "status" in df.value.columns)
    assert set(ingested.value["status"]) == {"ok"} and len(ingested.value) == 2

    button(app, "Index new documents").click()
    app.run()
    assert any("new vectors" in s.value for s in app.success)

    next(t for t in app.text_input if t.label == "Query").set_value("rollback previous image tag")
    app.run()
    hits = next(df for df in app.dataframe if "BM25 #" in df.value.columns)
    top = hits.value.iloc[0]
    assert len(hits.value) >= 1 and "Rollbacks" in top["chunk"]  # Markdown breadcrumbs are heading paths
    assert top["BM25 #"] == 1 and top["dense #"] >= 1 and "lexical" in top["found by"]  # the stages' ranks are visible per hit

    next(t for t in app.text_input if t.label == "Question").set_value("What does a rollback redeploy?")
    app.run()
    button(app, "Ask").click()
    app.run()
    assert not app.exception
    assert any("Passed every gate" in s.value for s in app.success), [w.value for w in app.warning]
    assert any("Verified quotes" in s.value for s in app.subheader)


def test_flagged_answers_are_shown_as_warnings_and_dropped_quotes_as_errors(app, stub):
    stub.answer_override = None
    app.run()
    next(t for t in app.text_input if t.label == "File or folder path").set_value(str(app.sample_repo))
    app.run(), button(app, "Ingest path").click(), app.run(), button(app, "Index new documents").click(), app.run()

    import llm_stub

    original = llm_stub.StubLLM._good

    def fabricated(self, kind, body):
        if kind == "ask":
            return json.dumps({"answer": "A rollback redeploys the tag [S1].", "quotes": [{"source": 1, "quote": "Rollbacks are handled by the platform team every night."}]})
        return original(self, kind, body)

    llm_stub.StubLLM._good = fabricated
    try:
        next(t for t in app.text_input if t.label == "Question").set_value("What does a rollback redeploy?")
        app.run(), button(app, "Ask").click(), app.run()
    finally:
        llm_stub.StubLLM._good = original
    assert any("Flagged" in w.value for w in app.warning)
    assert any("Dropped quote" in e.value for e in app.error)


def test_status_and_evals_tabs_render(app):
    app.run()
    assert not app.exception
    assert any("Vectors in the store" == m.label for m in app.metric)
    assert any(j for j in app.json)


def test_table_rows_are_detected_so_they_are_not_rendered_as_a_blockquote():
    assert logic.looks_tabular("| a | b |\n|---|---|\n| 1 | 2 |")
    assert logic.looks_tabular("| `QP_TOKEN_TTL_SECONDS` | `604800` (7 days) | Token lifetime. |")
    assert not logic.looks_tabular("A sentence with a | pipe in it.") and not logic.looks_tabular("") and not logic.looks_tabular("| half a row")


def test_a_refusal_before_the_model_was_called_says_so():
    hit = Hit("c", "d", "a.md", 1.0, CONTENT)
    level, text = logic.verdict(Answer("I don't know.", [hit], refused=True, reason="no retrieved source looks relevant (best reranker score 0.120 < 0.183)"))
    assert level == "info" and "No answer was generated" in text and "0.120" in text
