"""The answer gate: citations must exist, every cited source needs a quote that is really in that chunk,
and the answer must be supported by those verified quotes."""

import json
import re

import pytest

from rag_template.enrichment.llm import LLMClient
from rag_template.retrieve import REFUSAL, Answerer, Hit

PROSE = Hit("c1", "d1", "deploy.md", 1.0, "A rollback redeploys the previous image tag. The tag is stored in the release manifest and completes in under two minutes.", "deploy.md > Rollbacks")
CODE = Hit("c2", "d1", "retry.py", 0.9, "def retry(fn, attempts=3):\n    for i in range(attempts):\n        try:\n            return fn()\n        except OSError:\n            time.sleep(2 ** i)", "retry.py > retry", "code", {"language": "python"})
Q1 = "A rollback redeploys the previous image tag."
Q2 = "The tag is stored in the release manifest and completes in under two minutes."


class StaticRetriever:
    def __init__(self, hits):
        self.hits = hits

    def span_scorer(self):
        """Word overlap with the query: a deterministic stand-in for the cross-encoder."""
        def score(query, texts):
            q = set(re.findall(r"\w+", query.lower()))
            return [float(len(q & set(re.findall(r"\w+", t.lower())))) for t in texts]
        return score

    def search(self, query, k=5, doc_id=None, **kw):
        return self.hits[:k]


class FakeLLM:
    def __init__(self, reply):
        self.reply, self.prompts = reply, []

    def chat(self, system, user, tokens, json_mode=False):
        self.prompts.append(user)
        return self.reply

    def chat_json(self, system, user, tokens, schema=None):
        return LLMClient.extract_json(self.chat(system, user, tokens))


def reply(answer, *quotes):
    return json.dumps({"answer": answer, "quotes": [{"source": n, "quote": q} for n, q in quotes]})


def ask(raw, hits=(PROSE,), **kw):
    llm = FakeLLM(raw)
    answerer_kw = {k: kw.pop(k) for k in ("support_against", "max_context_tokens", "policy") if k in kw}
    return Answerer(StaticRetriever(list(hits)), llm, **answerer_kw).ask("What happens on rollback?", **kw), llm


def test_supported_cited_and_quoted_answer_passes():
    a, llm = ask(reply("A rollback redeploys the previous image tag [S1].", (1, Q1)))
    assert a.grounded and a.reason == "" and a.citations == [1] and not a.unverified_quotes
    assert [(q.source, q.text) for q in a.quotes] == [(1, Q1)] and a.quotes[0].hit is PROSE
    assert "[S1] deploy.md > Rollbacks" in llm.prompts[0]


def test_the_stored_quote_is_the_exact_chunk_text_not_the_models_paraphrase():
    a, _ = ask(reply("A rollback redeploys the previous image tag [S1].", (1, "rollback redeploys the previous image tag")))
    assert a.grounded and a.quotes[0].text == Q1  # snapped to the whole sentence, punctuation restored


def test_an_invented_quote_is_dropped_and_leaves_the_citation_unsupported():
    a, _ = ask(reply("A rollback redeploys the previous image tag [S1].", (1, "Rollbacks are performed by the platform team overnight.")))
    assert not a.grounded and "no verified quote" in a.reason
    assert a.unverified_quotes and a.unverified_quotes[0][0] == 1 and not a.quotes


def test_one_good_quote_keeps_the_answer_while_a_bad_one_is_reported():
    a, _ = ask(reply("A rollback redeploys the previous image tag [S1].", (1, Q1), (1, "An invented sentence about something else entirely.")))
    assert a.grounded and len(a.quotes) == 1 and len(a.unverified_quotes) == 1


def test_every_cited_source_needs_its_own_quote():
    a, _ = ask(reply("A rollback redeploys the previous tag [S1], stored in the manifest [S2].", (1, Q1)), hits=(PROSE, CODE))
    assert not a.grounded and "[S2]" in a.reason


def test_refusal_is_recognised_and_empty_retrieval_never_calls_the_llm():
    a, _ = ask(reply(REFUSAL))
    assert a.refused and a.grounded and a.text == REFUSAL
    llm = FakeLLM("should not be called")
    a = Answerer(StaticRetriever([]), llm).ask("anything")
    assert a.refused and llm.prompts == [] and a.sources == []


def test_unparsable_replies_and_uncited_answers_are_flagged():
    a, _ = ask("Sure! A rollback redeploys the previous image tag.")
    assert not a.grounded and a.refused and "no parsable answer" in a.reason
    a, _ = ask(reply("A rollback redeploys the previous image tag.", (1, Q1)))
    assert not a.grounded and "cites no source" in a.reason
    a, _ = ask(reply("A rollback redeploys the previous image tag [S7].", (1, Q1)))
    assert not a.grounded and "do not exist" in a.reason


def test_answer_must_be_supported_by_the_quotes_not_merely_by_the_chunk():
    claim = "A rollback redeploys the previous image tag in under two minutes [S1]."
    a, _ = ask(reply(claim, (1, Q1)))
    assert not a.grounded and "number" in a.reason  # "two" is in the chunk, but not in the quote that was given
    a, _ = ask(reply(claim, (1, Q1)), support_against="sources")
    assert a.grounded, a.reason
    a, _ = ask(reply(claim, (1, Q1), (1, Q2)))
    assert a.grounded, a.reason


def test_invented_content_is_flagged_for_prose():
    a, _ = ask(reply("A rollback redeploys the previous image tag within 9 minutes [S1].", (1, Q1)))
    assert not a.grounded and "number" in a.reason
    a, _ = ask(reply("Rollbacks trigger kubernetes autoscaling controllers across multiple datacenters [S1].", (1, Q1)))
    assert not a.grounded and "Unsupported" in a.reason


def test_code_answers_are_checked_against_the_quoted_lines():
    quote = "time.sleep(2 ** i)"
    a, llm = ask(reply("It sleeps for `2 ** i` seconds [S1].", (1, quote)), hits=(CODE,))
    assert a.grounded, a.reason
    assert a.quotes[0].text == "            time.sleep(2 ** i)"  # whole line of code, indentation intact
    assert "[S1] retry.py > retry\n```python\ndef retry" in llm.prompts[0]
    a, _ = ask(reply("It uses `exponential_backoff` between attempts [S1].", (1, quote)), hits=(CODE,))
    assert not a.grounded and "identifier" in a.reason
    a, _ = ask(reply("It loops `attempts` times [S1].", (1, quote)), hits=(CODE,))
    assert not a.grounded and "`attempts`" in a.reason  # in the chunk, but not in the quoted line
    a, _ = ask(reply("It loops `attempts` times [S1].", (1, quote)), hits=(CODE,), support_against="sources")
    assert a.grounded


def test_strict_mode_replaces_an_ungrounded_answer_with_a_refusal():
    a, _ = ask(reply("A rollback redeploys the previous image tag within 9 minutes [S1].", (1, Q1)), strict=True)
    assert a.refused and a.text == REFUSAL and not a.grounded and a.sources and a.quotes


def test_context_budget_limits_how_many_sources_can_be_cited():
    big = Hit("c3", "d1", "big.md", 0.5, "filler words " * 600, "big.md")
    llm = FakeLLM(reply("A rollback redeploys the previous image tag [S2].", (2, "filler words filler words")))
    ans = Answerer(StaticRetriever([PROSE, big]), llm, max_context_tokens=300).ask("q")
    assert "[S2] big.md" not in llm.prompts[0] and len(ans.sources) == 1
    assert not ans.grounded and "do not exist" in ans.reason  # source 2 was never shown to the model


@pytest.mark.parametrize("source", [1, "1", [1], "[S1]", ["1"], "source 1", "Source [S1]", 1.0])
def test_models_write_the_source_number_in_many_ways_and_all_are_understood(source):
    """Regression: Gemma 4 E2B wrote "source": [S1]; the answer was correct but was flagged as having no quote."""
    raw = json.dumps({"answer": "A rollback redeploys the previous image tag [S1].", "quotes": [{"source": source, "quote": Q1}]})
    a, _ = ask(raw)
    assert a.grounded, a.reason
    assert [q.source for q in a.quotes] == [1]


@pytest.mark.parametrize("source", [None, "", "none", [], True, "the first source"])
def test_a_verbatim_quote_with_no_usable_id_is_attributed_by_its_text(source):
    raw = json.dumps({"answer": "A rollback redeploys the previous image tag [S1].", "quotes": [{"source": source, "quote": Q1}]})
    a, _ = ask(raw)
    assert a.grounded, a.reason
    assert [(q.source, q.text) for q in a.quotes] == [(1, Q1)] and not a.unverified_quotes


@pytest.mark.parametrize("source", [None, "", "the first source"])
def test_a_quote_with_no_usable_id_that_is_not_in_any_source_is_dropped_and_reported(source):
    invented = "Rollbacks are performed by the platform team overnight."
    a, _ = ask(json.dumps({"answer": "A rollback redeploys the previous image tag [S1].", "quotes": [{"source": source, "quote": invented}]}))
    assert not a.grounded and "no verified quote" in a.reason
    assert a.unverified_quotes == [(0, invented)]  # visible to the user, with source 0 meaning "no id given"


def test_a_quote_given_as_a_bare_string_is_located_by_its_text():
    a, _ = ask(json.dumps({"answer": "A rollback redeploys the previous image tag [S2].", "quotes": [Q1]}), hits=(CODE, PROSE))
    assert a.grounded, a.reason
    assert [(q.source, q.hit) for q in a.quotes] == [(2, PROSE)]


def test_a_quote_found_in_two_sources_is_not_guessed_when_it_has_no_id():
    twin = Hit("c3", "d1", "copy.md", 0.8, PROSE.content, "copy.md > Rollbacks")
    a, _ = ask(json.dumps({"answer": "A rollback redeploys the previous image tag [S1].", "quotes": [Q1]}), hits=(PROSE, twin))
    assert not a.grounded and a.unverified_quotes == [(0, Q1)]


def test_quotes_that_are_not_a_list_of_objects_do_not_crash():
    for quotes in ("a string", {"source": 1, "quote": Q1}, None):
        a, _ = ask(json.dumps({"answer": "A rollback redeploys the previous image tag [S1].", "quotes": quotes}))
        assert not a.grounded and a.unverified_quotes == []
    a, _ = ask(json.dumps({"answer": "A rollback redeploys the previous image tag [S1].", "quotes": [1, "x", None]}))
    assert not a.grounded and a.unverified_quotes == [(0, "x")]  # a string is a quote without an id; numbers and null are ignored


TABLE = ("| Variable | Default | Effect |\n|---|---|---|\n| `QP_TOKEN_TTL_SECONDS` | `604800` (7 days) | Token lifetime. |\n"
         "| `QP_MAX_UPLOAD_MB` | `50` | Upload size limit. |")
TABLE_HIT = Hit("c9", "d", "docs/configuration.md", 1.0, TABLE, "Configuration > Security")
# What Gemma 4 E2B really wrote for this question: right answer, right chunk, but the quote has a column header spliced in.
GEMMA_REPLY = json.dumps({"answer": "The default token lifetime is 7 days [S1].", "quotes": [{"source": [1], "quote": "QP_TOKEN_TTL_SECONDS | Default | 604800 (7 days)"}]})


def test_the_real_gemma_reply_is_dropped_by_the_strict_policy_and_accepted_by_the_tolerant_one():
    strict, _ = ask(GEMMA_REPLY, hits=(TABLE_HIT,), policy="strict")
    assert not strict.grounded and strict.unverified_quotes and "no verified quote" in strict.reason
    tolerant, _ = ask(GEMMA_REPLY, hits=(TABLE_HIT,), policy="tolerant")
    assert tolerant.grounded, tolerant.reason
    q = tolerant.quotes[0]
    assert q.how == "loose"
    assert q.text in TABLE and "| `QP_TOKEN_TTL_SECONDS` | `604800` (7 days) | Token lifetime. |" in q.text  # real, contiguous table text containing the row
    assert "QP_MAX_UPLOAD_MB" not in q.text and "Default | 604800" not in q.text  # not the model's wording, not the unrelated rows
    assert not tolerant.unverified_quotes


def test_the_tolerant_policy_still_rejects_invented_and_foreign_quotes():
    for quote in ("Rollbacks are handled by the platform team every night of the week.",
                  "QP_REFRESH_TOKEN_LIFETIME | Default | 90 days | Refresh lifetime",  # plausible, invented
                  "def retry(fn, attempts=3):  time.sleep(2 ** i)"):  # real text, from another chunk
        a, _ = ask(reply("The default token lifetime is 7 days [S1].", (1, quote)), hits=(TABLE_HIT,), policy="tolerant")
        assert not a.grounded and a.unverified_quotes, quote


def test_how_a_quote_matched_is_recorded():
    a, _ = ask(reply("A rollback redeploys the previous image tag [S1].", (1, Q1)), policy="tolerant")
    assert a.quotes[0].how == "exact"
    a, _ = ask(reply("A rollback redeploys the previous image tag [S1].", (1, "a rollback redeploys the previous image tag")), policy="tolerant")
    assert a.quotes[0].how in ("exact", "fuzzy") and a.quotes[0].text == Q1


def test_missing_quotes_are_extracted_only_under_the_lenient_policy_and_labelled():
    no_quotes = json.dumps({"answer": "A rollback redeploys the previous image tag [S1]."})
    for name in ("strict", "tolerant"):
        a, _ = ask(no_quotes, policy=name)
        assert not a.grounded and "no verified quote" in a.reason
    a, _ = ask(no_quotes, policy="lenient")
    assert a.grounded, a.reason
    assert [(q.source, q.how) for q in a.quotes] == [(1, "extracted")] and a.quotes[0].text in PROSE.content
    assert "rollback" in a.quotes[0].text.lower()  # the span that best matches the answer, not an arbitrary one


def test_extraction_does_not_rescue_an_unsupported_answer():
    a, _ = ask(json.dumps({"answer": "A rollback redeploys the previous image tag within 9 minutes [S1]."}), policy="lenient")
    assert not a.grounded and "number" in a.reason
    a, _ = ask(json.dumps({"answer": "Rollbacks trigger kubernetes autoscaling controllers across multiple datacenters [S1]."}), policy="lenient")
    assert not a.grounded and "Unsupported" in a.reason
    a, _ = ask(json.dumps({"answer": "A rollback redeploys the previous image tag [S9]."}), policy="lenient")
    assert not a.grounded and "do not exist" in a.reason
    a, _ = ask(json.dumps({"answer": "A rollback redeploys the previous image tag."}), policy="lenient")
    assert not a.grounded and "cites no source" in a.reason


def test_a_fabricated_quote_is_still_reported_even_when_extraction_lets_a_supported_answer_through():
    a, _ = ask(reply("A rollback redeploys the previous image tag [S1].", (1, "Rollbacks are performed by the platform team overnight.")), policy="lenient")
    assert a.grounded and a.unverified_quotes and a.quotes[0].how == "extracted"  # visible to the reader, who sees it was not the model's quote


def test_the_lenient_policy_checks_support_against_the_cited_chunk_not_the_quotes():
    claim = "A rollback redeploys the previous image tag in under two minutes [S1]."
    assert not ask(reply(claim, (1, Q1)), policy="strict")[0].grounded
    assert not ask(reply(claim, (1, Q1)), policy="tolerant")[0].grounded
    assert ask(reply(claim, (1, Q1)), policy="lenient")[0].grounded


def test_judge_is_pure_so_a_recorded_reply_can_be_regated_under_every_policy():
    from rag_template.retrieve import POLICIES

    answerer = Answerer(StaticRetriever([TABLE_HIT]), llm=None)
    parsed = LLMClient.extract_json(GEMMA_REPLY)
    verdicts = {name: answerer.judge(parsed, [TABLE_HIT], "default token lifetime", policy=p).grounded for name, p in POLICIES.items()}
    assert verdicts == {"strict": False, "tolerant": True, "balanced": True, "lenient": True}
    assert parsed == LLMClient.extract_json(GEMMA_REPLY)  # judging never mutates the recorded reply


# ------------------------------------------------------------------ answer format and natural-wording refusals

@pytest.mark.parametrize(
    "text, refusal",
    [
        (REFUSAL, True),
        ("I don't know based on the provided sources.", True),
        ("The provided sources do not contain information on how to configure Kubernetes autoscaling.", True),
        ("The sources do not state how much GPU memory the model needs.", True),
        ("The document does not mention a Postgres connection string.", True),
        ("There is no information about Slack notifications in the context.", True),
        ("Not enough information to answer.", True),
        ("The sources do not say, but a rollback redeploys the previous tag [S1].", False),  # it cites: an answer, judged as one
        ("A rollback redeploys the previous image tag [S1].", False),
        ("The context window of the model is large.", False),
        ("Documents are stored in SQLite.", False),
        ("The default is 50 and the sources do not limit it further.", False),
    ],
)
def test_refusals_in_the_models_own_words_are_refusals_not_uncited_answers(text, refusal):
    from rag_template.retrieve import is_refusal

    assert is_refusal(text) is refusal
    a, _ = ask(json.dumps({"answer": text, "quotes": []}))
    assert a.refused is refusal
    if refusal:
        assert a.grounded and a.reason == ""  # declining is correct behaviour, not a gate failure


def test_the_schema_and_prompt_follow_the_requested_order():
    from rag_template.retrieve import answer_schema, system_prompt

    first, quotes_first = answer_schema(), answer_schema(quotes_first=True)
    assert list(first["properties"]) == ["answer", "quotes"] and list(quotes_first["properties"]) == ["quotes", "answer"]
    assert first["required"] == ["answer", "quotes"] and quotes_first["additionalProperties"] is False
    assert first["properties"]["quotes"]["items"]["properties"]["source"] == {"type": "string", "pattern": "^S[0-9]+$"}
    assert system_prompt().index('"answer"') < system_prompt().index('"quotes"') < system_prompt(True).index('"answer"')
    assert system_prompt(True).index('"quotes"') < system_prompt(True).index('"answer"')


def test_the_schema_for_a_request_only_allows_the_ids_that_were_shown():
    from rag_template.retrieve import answer_schema

    source = answer_schema(True, 3)["properties"]["quotes"]["items"]["properties"]["source"]
    assert source == {"type": "string", "enum": ["S1", "S2", "S3"]}


def test_sources_are_labelled_with_ids_and_a_bare_number_is_not_a_citation():
    llm = FakeLLM(reply("Section 22 says so [22].", ("S1", Q1)))
    a = Answerer(StaticRetriever([PROSE]), llm).ask("What happens on rollback?")
    assert "[S1] deploy.md" in llm.prompts[0] and "[1] deploy.md" not in llm.prompts[0]
    assert a.citations == [] and a.reason == "the answer cites no source"


def test_the_answerer_sends_its_schema_to_the_client():
    seen = {}

    class Spy:
        def chat_json(self, system, user, tokens, schema=None):
            seen.update(system=system, schema=schema)
            return {"answer": REFUSAL, "quotes": []}

    Answerer(StaticRetriever([PROSE]), Spy(), quotes_first=True).ask("q")
    assert list(seen["schema"]["properties"]) == ["quotes", "answer"] and seen["system"].index('"quotes"') < seen["system"].index('"answer"')


def test_the_answer_lists_question_words_that_no_source_contains():
    a, _ = ask(reply("A rollback redeploys the previous image tag [S1].", (1, Q1)))
    assert a.missing_terms == []
    llm = FakeLLM(reply("A rollback redeploys the previous image tag [S1].", (1, Q1)))
    off_topic = Answerer(StaticRetriever([PROSE]), llm).ask("How does the app send Slack notifications?")
    assert "slack" in off_topic.missing_terms and "notifications" in off_topic.missing_terms
    assert off_topic.grounded  # a hint only: the answer is still judged on provenance and support


# ------------------------------------------------------------------ the optional pre-LLM relevance gate

def scored(hit, score):
    from dataclasses import replace

    return replace(hit, rerank_score=score)


def test_a_weak_best_score_refuses_without_calling_the_llm():
    llm = FakeLLM(reply("A rollback redeploys the previous image tag [S1].", (1, Q1)))
    a = Answerer(StaticRetriever([scored(PROSE, 0.05), scored(CODE, 0.10)]), llm, min_relevance=0.2).ask("What is the Slack webhook?")
    assert a.refused and a.grounded and a.text == REFUSAL and "no retrieved source looks relevant" in a.reason and "0.1" in a.reason
    assert llm.prompts == []  # the whole point: no model call


def test_one_good_source_is_enough_and_the_gate_does_not_touch_the_answer_checks():
    llm = FakeLLM(reply("A rollback redeploys the previous image tag [S1].", (1, Q1)))
    a = Answerer(StaticRetriever([scored(PROSE, 0.40), scored(CODE, 0.01)]), llm, min_relevance=0.2).ask("What happens on rollback?")
    assert not a.refused and a.grounded and llm.prompts
    bad = Answerer(StaticRetriever([scored(PROSE, 0.40)]), FakeLLM(reply("A rollback redeploys the previous image tag within 9 minutes [S1].", (1, Q1))), min_relevance=0.2).ask("q")
    assert not bad.grounded and "number" in bad.reason  # the content checks still run after the gate


def test_the_gate_is_off_by_default_and_inactive_without_reranker_scores(caplog):
    import logging

    llm = FakeLLM(reply("A rollback redeploys the previous image tag [S1].", (1, Q1)))
    assert not Answerer(StaticRetriever([scored(PROSE, -5.0)]), llm).ask("q").refused  # default: off, even for a terrible score
    with caplog.at_level(logging.WARNING, logger="rag_template.retrieve"):
        a = Answerer(StaticRetriever([PROSE]), llm, min_relevance=0.2).ask("q")  # PROSE has rerank_score None
    assert not a.refused and any("relevance gate is inactive" in r.message for r in caplog.records)


def test_the_gate_threshold_comes_from_the_settings(monkeypatch):
    from rag_template.config import Settings

    assert Settings().answer_min_relevance is None
    monkeypatch.setenv("RAG_MIN_RELEVANCE", "0.211")
    assert Settings.from_env().answer_min_relevance == 0.211
    monkeypatch.setenv("RAG_MIN_RELEVANCE", "")
    assert Settings.from_env().answer_min_relevance is None


# ---- a model that cites the document's own numbering ("[22]" for section 22) instead of the source number ----

def test_an_out_of_range_source_number_is_resolved_from_the_verbatim_quote():
    a, _ = ask(reply("A rollback redeploys the previous image tag [S22].", (22, Q1)), hits=(CODE, PROSE))
    assert a.grounded and a.citations == [2] and a.text.endswith("[S2].")
    assert [(q.source, q.hit) for q in a.quotes] == [(2, PROSE)] and not a.unverified_quotes


def test_an_out_of_range_number_with_an_invented_quote_is_still_flagged():
    a, _ = ask(reply("A rollback redeploys the previous image tag [S22].", (22, "Rollbacks are performed overnight by the platform team.")), hits=(CODE, PROSE))
    assert not a.grounded and "do not exist" in a.reason


def test_a_quote_found_in_two_chunks_is_not_guessed():
    twin = Hit("c3", "d1", "copy.md", 0.8, PROSE.content, "copy.md > Rollbacks")
    a, _ = ask(reply("A rollback redeploys the previous image tag [S22].", (22, Q1)), hits=(PROSE, twin))
    assert not a.grounded and "do not exist" in a.reason


def test_an_in_range_but_wrong_source_is_not_corrected():
    # the quote is real, but in source 2; the model cited source 1: this is the wrong-source fabrication
    a, _ = ask(reply("A rollback redeploys the previous image tag [S1].", (1, Q1)), hits=(CODE, PROSE))
    assert not a.grounded and "no verified quote" in a.reason


def test_ask_with_hits_does_not_search_again():
    class Counting(StaticRetriever):
        searches = 0

        def search(self, query, k=5, doc_id=None, **kw):
            Counting.searches += 1
            return super().search(query, k=k)

    llm = FakeLLM(reply("A rollback redeploys the previous image tag [S1].", (1, Q1)))
    answerer = Answerer(Counting([PROSE]), llm)
    a = answerer.ask("What happens on rollback?", hits=[PROSE])
    assert a.grounded and Counting.searches == 0
    answerer.ask("What happens on rollback?")
    assert Counting.searches == 1


# ---- a number from the wrong cell of a table ----------------------------------------------------------------------

RESULTS = ("Table 2 Per-model results.\n\n| Model | V6 pass@1 HARD | V6 pass@5 HARD |\n|---|---|---|\n| Qwen3-30B-Thinking | 41.5 | 59.7 |\n| + SSD | 46.7 +5.2 | 65.8 +6.1 |\n")
TABLE_SRC = Hit("t1", "d1", "paper.pdf", 1.0, RESULTS, "Results", "table")
CELL_Q = "What is Qwen3-30B-Thinking's V6 hard pass@1 before and after SSD?"


def ask_table(answer, quote="| Qwen3-30B-Thinking | 41.5 | 59.7 |", policy="balanced"):
    llm = FakeLLM(json.dumps({"answer": answer, "quotes": [{"source": "S1", "quote": quote}]}))
    return Answerer(StaticRetriever([TABLE_SRC]), llm, policy=policy).ask(CELL_Q)


def test_a_number_from_the_wrong_column_of_a_table_is_flagged_although_it_occurs_in_the_table():
    a = ask_table("Qwen3-30B-Thinking's V6 hard pass@1 was 41.5 before SSD and 59.7 after [S1].")
    assert not a.grounded and "59.7" in a.reason and "fits this answer" in a.reason


def test_the_right_cells_pass_the_gate():
    a = ask_table("Qwen3-30B-Thinking's V6 hard pass@1 was 41.5 before SSD and 46.7 after [S1].", quote="| + SSD | 46.7 +5.2 | 65.8 +6.1 |")
    assert a.grounded, a.reason


def test_the_table_cell_check_is_a_policy_switch_off_only_for_lenient():
    wrong = "Qwen3-30B-Thinking's V6 hard pass@1 was 41.5 before SSD and 59.7 after [S1]."
    verdicts = {name: ask_table(wrong, policy=name).grounded for name in ("strict", "tolerant", "balanced", "lenient")}
    assert verdicts == {"strict": False, "tolerant": False, "balanced": False, "lenient": True}
