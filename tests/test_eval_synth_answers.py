import json

import pytest

from rag_template.evals import answers as A
from rag_template.evals import synth as S
from rag_template.evals.gold import GoldItem, Query
from rag_template.evals.metrics import wilson_interval

PASSAGE = "The release manifest stores the previous image tag. A rollback redeploys that tag, so it never needs a rebuild and completes quickly."
CHUNK = {"chunk_id": "c1", "source": "docs/deploy.md", "content": PASSAGE, "content_type": "prose", "should_use": 1}


SHORT = dict(CHUNK, content="Intro text goes here for the reader of this page. It is very fast. More text follows below it.")


def accept(raw, chunk=CHUNK, seen_q=None, seen_ev=None, **kw):
    stats = S.SynthStats()
    return S.accept(raw, chunk, seen_q if seen_q is not None else [], seen_ev if seen_ev is not None else set(), stats, **kw), stats


def test_a_good_pair_becomes_gold_with_the_exact_chunk_text_as_evidence():
    q, stats = accept({"question": "How can an earlier version be restored without compiling again?", "evidence": "a rollback redeploys that tag so it never needs a rebuild and completes quickly"})
    assert q and q.origin == "synthetic" and q.type == "doc" and stats.kept == 1
    assert q.gold[0] == GoldItem("docs/deploy.md", "A rollback redeploys that tag, so it never needs a rebuild and completes quickly.")


@pytest.mark.parametrize(
    "raw, reason",
    [
        ({"question": "", "evidence": "x"}, "missing"),
        ({"question": "How is an old version restored again?", "evidence": "This sentence was invented by the model and is not in the chunk at all."}, "not found"),
        ({"question": "How is an old version restored again?", "evidence": "It is very fast."}, "too short"),
        ({"question": "Restore?", "evidence": PASSAGE.split(". ")[1]}, "length"),
        ({"question": "What does deploy.md say about restoring an old version of the service?", "evidence": PASSAGE.split(". ")[1]}, "names the file"),
        ({"question": "Why does a rollback redeploys that tag so it never needs a rebuild?", "evidence": PASSAGE.split(". ")[1]}, "copies a 4-word phrase"),
    ],
)
def test_filters_reject_bad_pairs_for_the_stated_reason(raw, reason):
    q, stats = accept(raw, chunk=SHORT if reason == "too short" else CHUNK)
    assert q is None and any(reason in k for k in stats.rejected), stats.rejected


def test_duplicates_are_rejected():
    seen_q, seen_ev = [], set()
    ev = PASSAGE.split(". ")[1]
    assert accept({"question": "How can an earlier version be restored without compiling again?", "evidence": ev}, seen_q=seen_q, seen_ev=seen_ev)[0]
    q, stats = accept({"question": "How can an earlier version be restored without compiling it again?", "evidence": ev}, seen_q=seen_q, seen_ev=seen_ev)
    assert q is None and "near-duplicate question" in stats.rejected
    q, stats = accept({"question": "Which mechanism avoids producing new build artifacts on reverting?", "evidence": ev}, seen_q=seen_q, seen_ev=seen_ev)
    assert q is None and "duplicate evidence" in stats.rejected


def test_shared_run_finds_copied_phrases():
    assert S.shared_run("what does a rollback redeploys that tag", PASSAGE, 4) == "a rollback redeploys that"
    assert S.shared_run("how to restore the older release", PASSAGE, 4) is None


def test_sampling_is_balanced_seeded_and_size_bounded():
    code = "def f(x):\n    return x + 1  # " + "word " * 140
    chunks = [{"chunk_id": f"c{i}", "source": "a.py", "content": code + str(i), "content_type": "code", "should_use": 1} for i in range(10)]
    chunks += [{"chunk_id": f"d{i}", "source": "a.md", "content": ("Prose sentence number %d. " % i) * 20, "content_type": "prose", "should_use": 1} for i in range(10)]
    chunks.append({"chunk_id": "tiny", "source": "a.md", "content": "short", "content_type": "prose", "should_use": 1})
    chunks.append({"chunk_id": "gated", "source": "a.md", "content": ("Rejected sentence. " * 20), "content_type": "prose", "should_use": 0})
    a = S.sample_chunks(chunks, 8, seed=1)
    assert len(a) == 8 and sum(c["content_type"] == "code" for c in a) == 4
    assert {c["chunk_id"] for c in a}.isdisjoint({"tiny", "gated"})
    assert [c["chunk_id"] for c in a] == [c["chunk_id"] for c in S.sample_chunks(chunks, 8, seed=1)]


def test_generate_queries_end_to_end_with_a_fake_llm():
    class LLM:
        def __init__(self):
            self.n = 0

        def chat_json(self, system, user, tokens, schema=None):
            self.n += 1
            return {"question": "How can an earlier version be restored without compiling again?", "evidence": PASSAGE.split(". ")[1]} if self.n == 1 else {}

    big = dict(CHUNK, content=(PASSAGE + " ") * 4)
    qs, stats = S.generate_queries([big, dict(big, chunk_id="c2", content=(PASSAGE + " ") * 5)], LLM(), n=5)
    assert len(qs) == 1 and qs[0].id == "s001" and stats.attempted == 2 and stats.rejected == {"no parsable JSON": 1}


# ---------------------------------------------------------------------------- answers

def rec(i, answerable=True, refused=False, grounded=True, correct=None, cites=True, ctx=True):
    return A.AnswerRecord(i, "q", answerable, "doc", refused, grounded, "" if grounded else "no verified quote", "t", [1], 1, 0, ctx if answerable else None,
                          cites if answerable else None, None if (refused or not answerable) else correct, 1.0)


def test_summary_rates_and_gate_discrimination():
    records = [rec("a1", correct=True), rec("a2", correct=True), rec("a3", correct=False), rec("a4", grounded=False, correct=False), rec("a5", grounded=False, correct=True),
               rec("a6", refused=True, ctx=False, cites=False),
               rec("u1", answerable=False, refused=True), rec("u2", answerable=False, grounded=False), rec("u3", answerable=False)]
    s = A.summarize(records)
    a, u, st = s["answerable"], s["unanswerable"], s["strict_mode"]
    assert a["n"] == 6 and a["answered"]["k"] == 5 and a["refused"]["k"] == 1 and a["context_recall"]["k"] == 5
    assert a["correct_given_gates_passed"] == pytest.approx({"n": 3, "k": 2, "rate": 2 / 3, "lo": a["correct_given_gates_passed"]["lo"], "hi": a["correct_given_gates_passed"]["hi"]})
    assert (a["correct_given_gates_flagged"]["k"], a["correct_given_gates_flagged"]["n"]) == (1, 2)
    assert (u["refused"]["k"], u["answered_and_flagged"]["k"], u["answered_and_passed_gates"]["k"]) == (1, 1, 1)
    assert (st["unanswerable_refused"]["k"], st["answerable_answered"]["k"], st["answerable_correct"]["k"]) == (2, 3, 2)
    assert s["flag_reasons"] == {"no verified quote": 3}
    assert "dangerous case" in A.markdown(s, records)


def test_is_correct_normalises_and_handles_missing_keys():
    assert A.is_correct("The ticket lasts 30 seconds.", ["30-second"]) is True  # comparison ignores case, spacing and punctuation
    assert A.is_correct("The ticket lasts 60 seconds.", ["30-second"]) is False
    assert A.is_correct("A PBKDF2-SHA256 hash is used", ["pbkdf2"]) is True
    assert A.is_correct("anything", []) is None


def test_wilson_interval_is_sane_at_the_edges():
    p, lo, hi = wilson_interval(0, 10)
    assert p == 0 and lo == 0 and 0.2 < hi < 0.35
    p, lo, hi = wilson_interval(10, 10)
    assert p == 1 and hi == 1 and 0.65 < lo < 0.8
    assert wilson_interval(0, 0) == (0, 0, 0)
    assert wilson_interval(50, 100)[1] < 0.5 < wilson_interval(50, 100)[2]


def test_run_answer_eval_wires_retrieval_llm_and_gold():
    from rag_template.retrieve import Hit

    hit = Hit("c1", "d", "docs/deploy.md", 1.0, PASSAGE, "docs/deploy.md > Rollbacks")

    class R:
        def search(self, q, k=5, doc_id=None, **kw):
            return [hit]

    class LLM:
        def chat_json(self, system, user, tokens, schema=None):
            return {"answer": "A rollback redeploys that tag, so it never needs a rebuild [S1].", "quotes": [{"source": 1, "quote": "A rollback redeploys that tag, so it never needs a rebuild"}]} if "QUESTION: what does rollback use" in user else {"answer": "I don't know based on the provided sources.", "quotes": []}

    gold = Query("g1", "what does rollback use? tag", gold=[GoldItem("docs/deploy.md", "A rollback redeploys that tag")], answer_contains=["rebuild"])
    none = Query("n1", "kubernetes", answerable=False)
    recs = A.run_answer_eval(R(), LLM(), [gold, none])
    assert recs[0].grounded and recs[0].correct and recs[0].cites_gold and recs[0].context_has_gold and recs[0].n_quotes == 1
    assert recs[1].refused and recs[1].correct is None


# ------------------------------------------------------------------ replaying one recorded reply under every policy

TABLE = "| Variable | Default | Effect |\n|---|---|---|\n| `QP_TOKEN_TTL_SECONDS` | `604800` (7 days) | Token lifetime. |\n| `QP_MAX_UPLOAD_MB` | `50` | Upload size limit. |"


class _Retriever:
    def __init__(self, hit):
        self.hit = hit

    def search(self, q, k=5, doc_id=None, **kw):
        return [self.hit]

    def span_scorer(self):
        import re

        return lambda query, texts: [float(len(set(re.findall(r"\w+", query.lower())) & set(re.findall(r"\w+", t.lower())))) for t in texts]


def _records_for(replies):
    from rag_template.retrieve import Hit

    hit = Hit("c", "d", "docs/configuration.md", 1.0, TABLE, "Configuration > Security", "table")
    queries = [Query(f"q{i}", "What is the default token lifetime?", gold=[GoldItem("docs/configuration.md", "`QP_TOKEN_TTL_SECONDS` | `604800` (7 days)")], answer_contains=["7 days"]) for i in range(len(replies))]
    it = iter(replies)

    class LLM:
        def chat_json(self, system, user, tokens, schema=None):
            return next(it)

    return queries, _Retriever(hit), A.run_answer_eval(_Retriever(hit), LLM(), queries, k=1, policy="strict")


def test_records_keep_the_reply_and_sources_so_other_policies_can_be_replayed():
    exact = {"answer": "The default token lifetime is 7 days [S1].", "quotes": [{"source": 1, "quote": "| `QP_TOKEN_TTL_SECONDS` | `604800` (7 days) | Token lifetime. |"}]}
    sloppy = {"answer": "The default token lifetime is 7 days [S1].", "quotes": [{"source": [1], "quote": "QP_TOKEN_TTL_SECONDS | Default | 604800 (7 days)"}]}
    forgot = {"answer": "The default token lifetime is 7 days [S1]."}
    wrong = {"answer": "The default token lifetime is 30 days [S1].", "quotes": [{"source": 1, "quote": "| `QP_TOKEN_TTL_SECONDS` | `604800` (7 days) | Token lifetime. |"}]}
    queries, retriever, recs = _records_for([exact, sloppy, forgot, wrong])
    assert [r.grounded for r in recs] == [True, False, False, False]  # under the strict policy that recorded them
    assert recs[1].reply == sloppy and recs[1].context[0]["content"] == TABLE and recs[1].dropped[0]["best_match_score"] >= 75

    from rag_template.retrieve import POLICIES

    runs = {name: A.regate(recs, queries, retriever, p) for name, p in POLICIES.items()}
    verdicts = {name: [r.grounded for r in rs] for name, rs in runs.items()}
    assert verdicts == {"strict": [True, False, False, False], "tolerant": [True, True, False, False], "balanced": [True, True, False, False], "lenient": [True, True, True, False]}
    assert runs["lenient"][2].how == ["extracted"] and runs["tolerant"][1].how == ["loose"]
    assert [r.correct for r in runs["strict"]] == [True, True, True, False]  # correctness is a property of the answer, not of the policy

    rows = {r["policy"]: r for r in A.policy_table(runs)}
    assert (rows["strict"]["false_alarm"]["k"], rows["tolerant"]["false_alarm"]["k"], rows["lenient"]["false_alarm"]["k"]) == (2, 1, 0)
    assert all(r["missed_error"]["k"] == 0 for r in rows.values())  # the wrong answer (30 days) is caught by every policy
    assert rows["lenient"]["usable"]["k"] == 3 and rows["strict"]["usable"]["k"] == 1
    assert "false alarms" in A.policy_markdown(list(rows.values()))


def test_the_relevance_gate_can_be_replayed_on_recorded_replies_without_the_llm():
    from rag_template.retrieve import POLICIES, Hit

    reply = {"answer": "A rollback redeploys that tag, so it never needs a rebuild [S1].", "quotes": [{"source": 1, "quote": "A rollback redeploys that tag, so it never needs a rebuild"}]}
    hit = Hit("c", "d", "docs/deploy.md", 1.0, "A rollback redeploys that tag, so it never needs a rebuild and completes quickly.", "deploy.md > Rollbacks", rerank_score=0.15)

    class R:
        def search(self, q, k=5, doc_id=None, **kw):
            return [hit]

    class LLM:
        def chat_json(self, system, user, tokens, schema=None):
            return reply

    q = Query("g1", "what does rollback need?", gold=[GoldItem("docs/deploy.md", "A rollback redeploys that tag")], answer_contains=["rebuild"])
    rec = A.run_answer_eval(R(), LLM(), [q], k=1, policy="balanced")
    assert rec[0].grounded and rec[0].context[0]["rerank_score"] == 0.15
    ungated = A.regate(rec, [q], R(), POLICIES["balanced"])
    gated = A.regate(rec, [q], R(), POLICIES["balanced"], min_relevance=0.2)
    low = A.regate(rec, [q], R(), POLICIES["balanced"], min_relevance=0.1)
    assert ungated[0].grounded and not ungated[0].refused
    assert gated[0].refused and gated[0].correct is None and "no retrieved source looks relevant" in gated[0].reason  # the recorded reply is ignored
    assert not low[0].refused and low[0].correct is True
