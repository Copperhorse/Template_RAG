"""env.flag, the golden-QA helpers (evals/golden.py) and the profile memoisation."""

import json
import os
import time

import pymupdf
import pytest

from rag_template import env
from rag_template.evals import golden as G
from rag_template.pdf_profile import profile_pdf


@pytest.mark.parametrize(
    "value,default,expected",
    [
        ("off", True, False),
        ("0", True, False),
        ("FALSE", True, False),
        ("no", True, False),
        ("on", False, True),
        ("1", False, True),
        ("Yes", False, True),
        ("", True, True),
        ("", False, False),
        ("maybe", True, True),
        ("maybe", False, False),
    ],
)
def test_env_flag(monkeypatch, value, default, expected):
    monkeypatch.setenv("RAG_TEST_FLAG", value)
    assert env.flag("RAG_TEST_FLAG", default) is expected


def test_env_flag_unset_uses_the_default(monkeypatch):
    monkeypatch.delenv("RAG_TEST_FLAG", raising=False)
    assert env.flag("RAG_TEST_FLAG") is True and env.flag("RAG_TEST_FLAG", False) is False


def rows(*specs):
    return [G.Row(f"q{i}", "question", "truth", True, list(quotes)) for i, quotes in enumerate(specs)]


def test_audit_evidence_classifies_each_quote():
    chunks = [
        {"content": "The Act came into force at once.", "should_use": 1, "reject_reason": None},
        {"content": "Published in the Gazette on Tuesday.", "should_use": 0, "reject_reason": "Header filter: x"},
        {"content": "A quote that continues", "should_use": 1, "reject_reason": None},
        {"content": "into the next chunk.", "should_use": 1, "reject_reason": None},
    ]
    audit = G.audit_evidence(
        chunks,
        rows(["came into force at once"], ["Gazette on Tuesday"], ["continues into the next"], ["never written"]),
    )
    assert [audit[f"q{i}"][0]["status"] for i in range(4)] == ["usable", "rejected", "split", "absent"]
    assert audit["q1"][0]["why"] == "Header filter: x"


def test_fact_score_alternatives_and_polarity():
    facts = [["23 july 1992", "23rd july, 1992"], ["assent"]]
    assert G.fact_score("assent was given on the 23rd July, 1992", facts) == 1.0
    assert G.fact_score("assent was given", facts) == 0.5
    assert G.fact_score("whatever", []) is None
    assert G.fact_score("No, it does not apply to exports", [["export"]], "no") == 1.0
    assert G.fact_score("Yes, it applies to exports", [["export"]], "no") == 0.5


def test_load_golden_prefers_verbatim_evidence(tmp_path):
    f = tmp_path / "g.jsonl"
    f.write_text(
        json.dumps(
            {
                "id": "a",
                "question": "q",
                "ground_truth": "t",
                "answerable": True,
                "evidence": [{"quote": "[Footnote 3: annotated]"}],
                "evidence_verbatim": ["Inserted vide Finance Act, 2018"],
                "question_type": "amendment",
            }
        )
        + "\n\n"
    )
    (row,) = G.load_golden(f)
    assert row.quotes == ["Inserted vide Finance Act, 2018"] and row.kind == "amendment"


def test_render_summarises_a_run():
    rec = lambda i, answerable, **kw: {
        "id": f"x-{i:03d}",
        "question": "q",
        "kind": "factual",
        "difficulty": "easy",
        "answerable": answerable,
        "ground_truth": "t",  # noqa: E731
        "evidence_status": ["usable"] if answerable else [],
        "rank": 1,
        "covered": 1,
        "n_quotes": 1,
        "answer": "a | b",
        "refused": False,
        "grounded": True,
        "reason": "",
        "citations": [1],
        "n_verified": 1,
        "verified_from_evidence": True,
        "cites_evidence": True,
        "fact_score": 1.0 if answerable else None,
        "sources": [],
        "seconds": 1.0,
        **kw,
    }
    records = [
        rec(1, True),
        rec(2, True, grounded=False, reason="no verified quote", fact_score=0.5),
        rec(3, False, refused=True),
    ]
    meta = {
        "label": "t",
        "golden": "g.jsonl",
        "store": "s",
        "chunks": 30,
        "usable": 25,
        "json_mode": "off",
        "policy": "balanced",
        "k": 5,
    }
    text = G.render(records, meta)
    assert "delivered (answered and passed the gates): 50% (1/2)" in text and "refused: 100% (1/1)" in text
    assert (
        "correct among flagged answers (false alarms): 0% (0/1)" in text
        and "a / b" in text
        and "by construction" not in text
    )
    assert "by construction" in G.render(records, {**meta, "usable": 4})


def _pdf(path, pages):
    doc = pymupdf.open()
    for _ in range(pages):
        doc.new_page().insert_text((50, 100), "Some ordinary text on the page. " * 3, fontname="helv", fontsize=11)
    doc.save(str(path))


def test_profile_is_memoised_per_file_version(tmp_path):
    f = tmp_path / "a.pdf"
    _pdf(f, 2)
    first = profile_pdf(str(f))
    assert profile_pdf(str(f)) is first
    time.sleep(0.01)
    _pdf(f, 5)
    os.utime(f, ns=(time.time_ns(), time.time_ns()))
    assert profile_pdf(str(f)).pages == 5


def test_render_copes_with_answerable_questions_that_list_no_facts_and_with_partial_ones():
    base = {
        "question": "q",
        "kind": "factual",
        "difficulty": "easy",
        "ground_truth": "t",
        "evidence_status": ["usable"],
        "rank": 1,
        "covered": 1,
        "n_quotes": 1,
        "answer": "a",
        "refused": False,
        "grounded": True,
        "reason": "",
        "citations": [1],
        "n_verified": 1,
        "verified_from_evidence": True,
        "cites_evidence": True,
        "sources": [],
        "seconds": 1.0,
        "item_recall": None,
    }
    records = [
        {**base, "id": "s-001", "answerable": True, "status": "yes", "fact_score": None},
        {**base, "id": "s-002", "answerable": True, "status": "yes", "fact_score": 0.5, "item_recall": 0.75},
        {**base, "id": "s-003", "answerable": False, "status": "partial", "fact_score": None},
        {
            **base,
            "id": "s-004",
            "answerable": False,
            "status": "no",
            "fact_score": None,
            "refused": True,
            "evidence_status": [],
        },
    ]
    meta = {
        "label": "t",
        "golden": "g.jsonl",
        "store": "s",
        "chunks": 30,
        "usable": 25,
        "json_mode": "schema",
        "policy": "balanced",
        "k": 5,
    }
    text = G.render(records, meta)
    assert "2 answerable, 1 unanswerable, 1 partially answerable" in text
    assert (
        "mean share of required facts present: 0.50 (over the 1 questions" in text
        and "item recall over the 1 list questions that name their items: 0.75" in text
    )
    assert "## 4b. Partially answerable" in text and "refused: 100% (1/1)" in text


def test_load_golden_reads_yes_partial_no_and_answer_items(tmp_path):
    f = tmp_path / "g.jsonl"
    f.write_text(
        "\n".join(
            json.dumps(d)
            for d in [
                {
                    "id": "a",
                    "question": "q",
                    "answerable": "yes",
                    "answer_items": [{"item": "x"}, {"item": "y"}],
                    "evidence": [{"quote": "e"}],
                },
                {
                    "id": "b",
                    "question": "q",
                    "answerable": "partial",
                    "expected_behavior": "cite and say what is missing",
                    "evidence": [{"quote": "e"}],
                },
                {"id": "c", "question": "q", "answerable": "no", "expected_behavior": "abstain"},
                {"id": "d", "question": "q", "answerable": True},
            ]
        )
    )
    a, b, c, d = G.load_golden(f)
    assert [r.status for r in (a, b, c, d)] == ["yes", "partial", "no", "yes"] and [
        r.answerable for r in (a, b, c, d)
    ] == [True, True, False, True]
    assert a.items == ["x", "y"] and b.expected.startswith("cite") and c.quotes == []


def test_item_recall_needs_every_number_and_long_word_of_an_item():
    items = ["Llama-3.1-8B +3.5", "no human-labeled solutions", "teacher model"]
    assert G.item_recall(
        "Llama-3.1-8B improves by +3.5pp; there are no human-labeled solutions.", items
    ) == pytest.approx(2 / 3)
    assert G.item_recall("Llama-3.1-8B improves by +3.9pp", items) == 0.0
    assert G.item_recall("anything", []) is None


def test_holds_exact_by_default_and_fuzzy_on_request():
    chunk = "| Qwen3-30B-Thinking | 66.1 | 99.8 | 73.0 | 41.5 | and some other cells"
    rendering = "Qwen3-30B-Thinking base: v6 pass@1 [66.1, 99.8, 73.0, 41.5]"
    assert not G.holds(rendering, chunk) and G.holds(rendering, chunk, fuzzy=True)
    assert G.holds("66.1 99.8", chunk)  # exact matching ignores punctuation as everywhere else
    assert not G.holds(
        "Qwen3-30B-Thinking base: v6 pass@1 [12.0, 13.0, 14.0, 15.0]", chunk, fuzzy=True
    )  # different numbers: not held
    assert G.holds("two words", "two words", fuzzy=False)  # exact still works for short quotes
    assert G.holds("a b c", "a b c d", fuzzy=True) and not G.holds(
        "a b c", "a b x d", fuzzy=True
    )  # fewer than 4 tokens: only the exact rule applies


def test_audit_labels_fuzzy_finds_separately():
    chunks = [
        {"content": "| Llama-3.1-8B-Instruct | 12.7 | 46.8 | 5.4 | 0.0 |", "should_use": 1, "reject_reason": None}
    ]
    row = G.Row("q", "q", "t", True, ["Llama-3.1-8B-Instruct base: v6 pass@1 [12.7, 46.8, 5.4, 0.0]"])
    assert G.audit_evidence(chunks, [row])["q"][0]["status"] == "absent"
    assert G.audit_evidence(chunks, [row], fuzzy=True)["q"][0]["status"] == "fuzzy-usable"
