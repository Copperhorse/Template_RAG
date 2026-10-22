"""The LLM client fails fast, separates 'server down' from 'bad output', and never turns an outage
into a rejection. Runs against a real local HTTP server, see llm_stub.py."""

import socket

import pytest
from llm_stub import StubLLM

from rag_template.config import LLMSettings
from rag_template.enrichment.llm import LLMClient, LLMUnavailable, questions_per_level, strip_thinking
from conftest import make_llm


def test_defaults_are_tighter_than_the_openai_library():
    c = LLMClient(LLMSettings())
    assert c.client.max_retries == 1  # library default: 2
    assert c.client.timeout.read == 120  # library default: 600
    assert c.client.timeout.connect == 5.0


@pytest.mark.parametrize("budget, extra", [(4096, 4096), (0, 0), (-1, 8192)])
def test_every_request_allows_reasoning_budget_plus_the_answer(budget, extra):
    with StubLLM() as stub:
        LLMClient(LLMSettings(base_url=stub.url, reasoning_budget=budget)).chat("sys", "user", 500)
        assert stub.requests[-1]["max_tokens"] == extra + 500


def test_good_json_is_parsed_and_stats_are_counted():
    with StubLLM() as stub:
        llm = make_llm(stub)
        out = llm.generate_metadata("The retry function sleeps between attempts. " * 5, "ctx", estimated_tokens=100)
        assert out["summary"] and isinstance(out["tags"], list)
        assert llm.stats["calls"] == 1 and llm.stats["prompt_tokens"] == 100


def test_too_short_chunks_make_no_call():
    with StubLLM() as stub:
        assert make_llm(stub).generate_metadata("tiny", "ctx", estimated_tokens=5) == {}
        assert stub.requests == []


@pytest.mark.parametrize("mode", ["500", "503", "429"])
def test_server_errors_and_rate_limits_are_unavailable_not_bad_output(mode):
    with StubLLM(mode=mode) as stub:
        with pytest.raises(LLMUnavailable):
            make_llm(stub).chat("s", "u", 100)


def test_a_400_is_the_requests_problem_not_an_outage():
    with StubLLM(mode="400") as stub:
        assert make_llm(stub).chat("s", "u", 100) == ""


def test_timeout_is_unavailable_and_fast():
    with StubLLM(mode="hang", hang_seconds=3) as stub:
        import time

        t = time.monotonic()
        with pytest.raises(LLMUnavailable):
            make_llm(stub, timeout=0.5).chat("s", "u", 100)
        assert time.monotonic() - t < 2.5


def test_connection_refused_is_unavailable():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    llm = LLMClient(LLMSettings(base_url=f"http://127.0.0.1:{port}/v1", timeout_s=1, max_retries=0))
    with pytest.raises(LLMUnavailable):
        llm.chat("s", "u", 10)
    with pytest.raises(LLMUnavailable):
        llm.check_health()


def test_health_check_fails_while_the_model_is_loading():
    with StubLLM(models_mode="503") as stub:
        with pytest.raises(LLMUnavailable):
            make_llm(stub).check_health()
    with StubLLM() as stub:
        make_llm(stub).check_health()


@pytest.mark.parametrize("mode, expect_json", [("garbage", False), ("reasoning", False), ("inline_think", True), ("truncated_think", False), ("length", False)])
def test_odd_model_output_never_crashes(mode, expect_json):
    with StubLLM(mode=mode) as stub:
        out = make_llm(stub).generate_metadata("The retry function sleeps between attempts. " * 5, "ctx", estimated_tokens=100)
        assert bool(out) is expect_json


def test_reasoning_content_is_never_parsed():
    with StubLLM(mode="reasoning") as stub:
        assert make_llm(stub).chat("s", "u", 100) == ""


@pytest.mark.parametrize(
    "raw, expected",
    [
        ('{"a": 1}', {"a": 1}),
        ('Here you go:\n```json\n{"a": 1}\n```', {"a": 1}),
        ('{"a": 1,}', {"a": 1}),  # trailing comma
        ("{'a': 1}", {"a": 1}),  # single quotes
        ('[{"a": 1}]', {"a": 1}),  # single-element list unwrapped
        ("not json at all", {}),
        ("", {}),
    ],
)
def test_json_extraction_repairs_what_it_can(raw, expected):
    assert LLMClient.extract_json(raw) == expected


def test_strip_thinking_and_helpers():
    assert strip_thinking("<think>hmm</think> answer") == "answer"
    assert strip_thinking("<think>never ends") == ""
    assert [questions_per_level(t) for t in (10, 100, 500)] == [1, 2, 3]
    assert LLMClient.normalize_tags(["Weak Labels", "weak_labels", "GanTraining", "", 5]) == ["weak_labels", "gan_training"]
    assert LLMClient.verify_tags_grounded(["weak_labels", "invented_tag"], "We use weak labels.") == ["weak_labels"]
    trip = [{"subject": "Retry", "predicate": "calls", "object": "sleep"}, {"subject": "Retry", "predicate": "calls", "object": "kafka"}, "junk"]
    assert LLMClient.verify_triplets_grounded(trip, "retry calls sleep") == trip[:1]


def test_candidates_are_deduplicated_by_question_and_by_evidence():
    cands = [
        {"question": "What does retry do?", "source_quote": "retry calls fn until it works"},
        {"question": "What does retry do??", "source_quote": "something else entirely written here"},  # same question
        {"question": "How is the wait computed?", "source_quote": "retry calls fn until it works"},  # same evidence
        {"question": "What is the default delay?", "source_quote": "delay defaults to 0.5 seconds"},
        "junk",
        {"question": "", "source_quote": "x"},
    ]
    kept = LLMClient.deduplicate_candidates(cands)
    assert [c["question"] for c in kept] == ["What does retry do?", "What is the default delay?"]


# ------------------------------------------------------------------- constrained replies (response_format)

SCHEMA = {"type": "object", "properties": {"answer": {"type": "string"}}, "required": ["answer"]}


@pytest.mark.parametrize(
    "mode, with_schema, expected",
    [
        ("off", True, None), (False, True, None),
        ("json_object", True, {"type": "json_object"}), (True, False, {"type": "json_object"}),
        ("schema", False, {"type": "json_object"}),  # a caller without a schema still gets valid JSON
        ("schema", True, {"type": "json_schema", "json_schema": {"name": "reply", "strict": True, "schema": SCHEMA}}),
    ],
)
def test_response_format_follows_the_json_mode_setting(mode, with_schema, expected):
    llm = LLMClient(LLMSettings(json_mode=mode))
    assert llm.response_format_for(SCHEMA if with_schema else None) == expected


def test_the_schema_reaches_the_server_only_in_schema_mode():
    with StubLLM() as stub:
        LLMClient(LLMSettings(base_url=stub.url, reasoning_budget=0, json_mode="schema")).chat_json("s", "u", 50, schema=SCHEMA)
        assert stub.requests[-1]["response_format"]["json_schema"]["schema"] == SCHEMA
        LLMClient(LLMSettings(base_url=stub.url, reasoning_budget=0, json_mode="off")).chat_json("s", "u", 50, schema=SCHEMA)
        assert "response_format" not in stub.requests[-1]
        LLMClient(LLMSettings(base_url=stub.url, reasoning_budget=0, json_mode="json_object")).chat("plain text call", "u", 50)
        assert "response_format" not in stub.requests[-1]  # only structured calls are constrained; free text never is


def test_json_mode_defaults_to_schema_and_off_is_an_explicit_choice(monkeypatch):
    from rag_template.config import LLMSettings, Settings

    monkeypatch.delenv("LLM_JSON_MODE", raising=False)
    assert LLMSettings().json_mode == "schema" and Settings.from_env().llm.json_mode == "schema"
    monkeypatch.setenv("LLM_JSON_MODE", "off")
    assert Settings.from_env().llm.json_mode == "off"


def test_llm_json_mode_environment_values(monkeypatch):
    from rag_template.config import Settings

    for raw, want in (("schema", "schema"), ("1", "json_object"), ("true", "json_object"), ("json_object", "json_object"), ("0", "off"), ("", "off"), ("nonsense", "off")):
        monkeypatch.setenv("LLM_JSON_MODE", raw)
        assert Settings.from_env().llm.json_mode == want, raw
