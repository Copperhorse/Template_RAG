"""The enrichment gates and failure model. Gate order and reasons are the contract: they are what
ends up in chunk_rejections and what you read when tuning."""

import pytest
from llm_stub import StubLLM

from rag_template.chunking import ChunkConfig
from rag_template.enrichment import verify
from rag_template.enrichment.enricher import DEFLECTION_PATTERN, EnrichmentManager, Gates
from rag_template.enrichment.judge import JudgeUnavailable
from rag_template.enrichment.llm import LLMUnavailable
from rag_template.enrichment.prompts import get_prompt_set
from rag_template.ingest import ingest
from rag_template.store.dedupe import SimHashIndex
from conftest import AcceptAll, SAMPLE_MD, SAMPLE_PY, make_llm

CFG = ChunkConfig(max_chunk_tokens=200, min_chunk_tokens=30)


def real_gates():
    return Gates(prose=verify.PairVerifier(use_embeddings=False), code=verify.CodeVerifier())


def load(db, tmp_path, name, text, cfg=CFG):
    p = tmp_path / name
    p.write_text(text)
    r = ingest(p, db, SimHashIndex(), cfg, source=name)
    assert r.ok, r.message
    return r.doc_id


def counts(db, doc_id):
    return {
        "qa": len(db.get_qa_for_document(doc_id)),
        "rejections": len(db.get_rejections_for_document(doc_id)),
        "enrichments": sum(1 for c in db.get_chunk_ids_for_document(doc_id) if db.get_enrichment(c)),
        "pending": doc_id in db.get_pending_documents(),
    }


# ---------------------------------------------------------------------------- end to end

def test_code_and_prose_documents_are_enriched_and_gated(db, tmp_path, stub):
    code = load(db, tmp_path, "retry.py", SAMPLE_PY)
    prose = load(db, tmp_path, "deploy.md", SAMPLE_MD)
    report = EnrichmentManager(db, make_llm(stub), real_gates()).run()
    assert report.documents == 2 and not report.server_down

    for doc in (code, prose):
        qa = db.get_qa_for_document(doc)
        assert qa, f"no QA for {doc}"
        for row in qa:
            chunk = db.get_chunk(row["chunk_id"])
            assert row["source_quote"] in chunk["content"]  # the stored quote is verbatim chunk text
            assert row["answer_text"] and row["difficulty"] in ("Easy", "Medium", "Hard")
        assert not counts(db, doc)["pending"]

    enrichment = db.get_enrichment(db.get_qa_for_document(code)[0]["chunk_id"])
    chunk_text = db.get_chunk(db.get_qa_for_document(code)[0]["chunk_id"])["content"]
    assert enrichment["tags"] and all(t in chunk_text.lower() for t in enrichment["tags"])  # tags are grounded
    # code questions were asked with the code prompts
    asked = " ".join(r["messages"][-1]["content"] for r in stub.chat_requests("questions"))
    assert 'Never write "this function"' in asked and "Signature: class Cache" in asked
    assert "Location: retry.py > " in asked


def test_a_second_run_does_nothing(db, tmp_path, stub):
    load(db, tmp_path, "retry.py", SAMPLE_PY)
    mgr = EnrichmentManager(db, make_llm(stub), real_gates())
    mgr.run()
    calls = len(stub.requests)
    mgr.run()
    assert len(stub.requests) == calls


def test_combined_prompt_set_asks_for_answers_in_one_call(db, tmp_path, stub):
    doc = load(db, tmp_path, "deploy.md", SAMPLE_MD)
    llm = make_llm(stub)
    llm.prompts = get_prompt_set("combined_fewshot")
    EnrichmentManager(db, llm, real_gates()).run()
    assert db.get_qa_for_document(doc)
    assert any("Write up to" in r["messages"][-1]["content"] and "EACH level" in r["messages"][-1]["content"] for r in stub.chat_requests("questions"))


# ------------------------------------------------------------------------- failure model

def test_unparsable_metadata_is_a_rejection_not_a_crash(db, tmp_path):
    with StubLLM(chat_modes={"metadata": "garbage"}) as stub:
        doc = load(db, tmp_path, "deploy.md", SAMPLE_MD)
        EnrichmentManager(db, make_llm(stub), AcceptAll_gates()).run()
    assert db.rejection_summary() == {"Metadata generation failed": len(db.get_chunk_ids_for_document(doc, usable_only=True))}
    assert counts(db, doc)["qa"] == 0 and not counts(db, doc)["pending"]


def AcceptAll_gates():
    return Gates.uniform(AcceptAll())


@pytest.mark.parametrize("mode", ["500", "503", "429", "hang"])
def test_an_outage_mid_run_records_nothing_and_leaves_the_document_pending(db, tmp_path, mode):
    with StubLLM(chat_modes={"questions": mode}, hang_seconds=2) as stub:
        doc = load(db, tmp_path, "retry.py", SAMPLE_PY)
        mgr = EnrichmentManager(db, make_llm(stub, timeout=0.5), AcceptAll_gates())
        report = mgr.run()
    assert report.server_down and report.documents == 0
    assert counts(db, doc) == {"qa": 0, "rejections": 0, "enrichments": 0, "pending": True}


def test_server_down_before_start_touches_nothing(db, tmp_path):
    with StubLLM(models_mode="503") as stub:
        doc = load(db, tmp_path, "retry.py", SAMPLE_PY)
        report = EnrichmentManager(db, make_llm(stub), AcceptAll_gates()).run()
        assert report.server_down and stub.chat_requests() == []
    assert counts(db, doc)["pending"] and counts(db, doc)["enrichments"] == 0


def test_a_run_that_dies_halfway_resumes_without_redoing_finished_chunks(db, tmp_path):
    doc = load(db, tmp_path, "retry.py", SAMPLE_PY, ChunkConfig(max_chunk_tokens=70, min_chunk_tokens=5))
    n_chunks = len(db.get_chunk_ids_for_document(doc, usable_only=True))
    assert n_chunks >= 5
    with StubLLM() as stub:
        llm = make_llm(stub)
        real_chat = llm.chat
        state = {"calls": 0}

        def flaky(system, user, tokens, json_mode=False, response_format=None):
            state["calls"] += 1
            if state["calls"] == 8:
                raise LLMUnavailable("server fell over")
            return real_chat(system, user, tokens, json_mode, response_format)

        llm.chat = flaky
        assert EnrichmentManager(db, llm, real_gates()).run().server_down
        done_first = {q["chunk_id"] for q in db.get_qa_for_document(doc)}
        assert 0 < len(done_first) < n_chunks and counts(db, doc)["pending"]

        llm.chat = real_chat
        stub.requests.clear()
        assert not EnrichmentManager(db, llm, real_gates()).run().server_down
        redone = {q["chunk_id"] for q in db.get_qa_for_document(doc)}
    assert done_first <= redone and not counts(db, doc)["pending"]
    assert all(db.get_chunk(c)["content"] not in str(stub.requests) or c not in done_first for c in done_first)


# ------------------------------------------------------------------------------- the gates

class FakeLLM:
    def __init__(self, answer="", prompts=None):
        self.answer, self.asked = answer, []
        self.prompts = prompts

    def generate_reference_answer(self, question, content, quote="", content_type="prose"):
        self.asked.append((question, quote, content_type))
        return self.answer


PROSE_CHUNK = "Rollbacks redeploy the previous image tag. The tag is stored in the release manifest, so a rollback never needs a rebuild. It completes in under two minutes."
QUOTE = "The tag is stored in the release manifest, so a rollback never needs a rebuild."


def gate(db, answer, cand, content=PROSE_CHUNK, ctype="prose", gates=None):
    mgr = EnrichmentManager(db, FakeLLM(answer), gates or real_gates())
    return mgr._gate_candidate(cand, content, ctype)


def cand(question="Where is the previous tag stored?", quote=QUOTE, **kw):
    return {"question": question, "source_quote": quote, "difficulty": "Easy", **kw}


def test_gate_order_and_reasons(db):
    good = "The previous tag is stored in the release manifest."
    ok, _ = gate(db, good, cand())
    assert ok
    cases = [
        (good, cand(question=""), "Invalid Pass 1"),
        (good, cand(quote="too short"), "Invalid Pass 1"),
        (good, cand(quote="A quote that was invented by the model and is not in the chunk."), "Weak quote: not found in chunk"),
        ("NOT_ENOUGH_INFORMATION", cand(), "Pass 2 refused"),
        ("", cand(), "Pass 2 refused"),
        ("The text does not specify where the tag is stored.", cand(), "Deflection"),
        ("The tag is stored in the registry within 9 minutes.", cand(), "Unsupported number"),
        ("Where is the previous tag stored?", cand(), "Answer only restates the question"),
    ]
    for answer, c, reason in cases:
        ok, rej = gate(db, answer, c)
        assert not ok and reason in rej["reason"], (answer, reason, rej)
        assert rej["level"] == "Easy"


def test_a_passing_candidate_carries_the_exact_chunk_quote_and_answer_type(db):
    c = cand(quote="the tag is stored in the release manifest so a rollback never needs a rebuild")
    ok, _ = gate(db, "The previous tag is stored in the release manifest.", c)
    assert ok and c["source_quote"] == QUOTE  # paraphrase replaced by the verbatim, sentence-snapped chunk text
    assert c["type"] == "Fact" and c["answer"].startswith("The previous tag")


def test_combined_answers_skip_pass_2(db):
    mgr = EnrichmentManager(db, FakeLLM("SHOULD NOT BE USED"), real_gates())
    c = cand(answer="The previous tag is stored in the release manifest.")
    ok, _ = mgr._gate_candidate(c, PROSE_CHUNK, "prose")
    assert ok and mgr.llm.asked == []


def test_maths_quotes_must_be_verbatim_and_use_the_math_checker(db):
    chunk = "The loss is defined as $L = \\frac{1}{N} \\sum_i (y_i - \\hat{y}_i)^2$ over the batch of size N."
    quote = "$L = \\frac{1}{N} \\sum_i (y_i - \\hat{y}_i)^2$ over the batch"
    seen = []

    class Math:
        def validate(self, q, a, c, s):
            seen.append(s)
            return False, "NLI Contradiction (0.9 > 0.6)"

    gates = Gates(prose=AcceptAll(), math=Math())
    ok, rej = gate(db, "It is the mean squared error over the batch.", cand("What is the loss?", quote), chunk, "math", gates)
    assert not ok and rej["reason"].startswith("NLI") and seen == [quote]
    ok, rej = gate(db, "x", cand("What is the loss?", quote.replace("frac", "dfrac")), chunk, "math", gates)
    assert not ok and rej["reason"] == "Math quote not verbatim"


def test_code_candidates_use_the_code_checker_and_line_snapped_quotes(db):
    chunk = "def retry(fn, attempts=3):\n    for i in range(attempts):\n        try:\n            return fn()\n        except OSError:\n            time.sleep(2 ** i)\n    raise RuntimeError('gave up')"
    c = cand("What does retry raise when every attempt fails?", "raise RuntimeError('gave up')")
    ok, _ = gate(db, "It raises `RuntimeError`.", c, chunk, "code")
    assert ok and c["source_quote"] == "    raise RuntimeError('gave up')"
    ok, rej = gate(db, "It raises `GiveUpError`.", cand("What does retry raise when every attempt fails?", "raise RuntimeError('gave up')"), chunk, "code")
    assert not ok and "Unsupported identifier" in rej["reason"]


def test_deflection_pattern():
    for s in ("The text does not specify the value.", "The code does not show a default.", "This is not mentioned in the text.", "It cannot be determined from the passage."):
        assert DEFLECTION_PATTERN.search(s), s
    assert not DEFLECTION_PATTERN.search("The manifest stores the previous tag.")


# ------------------------------------------------------------------------------- judge

class Judge:
    name = "test-judge"

    def __init__(self, verdicts=None, error=None):
        self.verdicts, self.error, self.seen = verdicts, error, []

    def check_many(self, items):
        self.seen.append(items)
        if self.error:
            raise self.error
        return [self.verdicts(i) for i in items]


def test_judge_can_veto_pairs_that_passed_every_gate(db, tmp_path, stub):
    doc = load(db, tmp_path, "deploy.md", SAMPLE_MD)
    judge = Judge(lambda item: (False, "LLM judge: answer does not give what the question asks"))
    EnrichmentManager(db, make_llm(stub), real_gates(), judge=judge).run()
    assert judge.seen and counts(db, doc)["qa"] == 0
    assert "LLM judge: answer does not give what the question asks" in db.rejection_summary()


def test_a_judge_outage_is_an_outage_not_a_rejection(db, tmp_path, stub):
    doc = load(db, tmp_path, "deploy.md", SAMPLE_MD)
    report = EnrichmentManager(db, make_llm(stub), real_gates(), judge=Judge(error=JudgeUnavailable("bad key"))).run()
    assert report.server_down and counts(db, doc) == {"qa": 0, "rejections": 0, "enrichments": 0, "pending": True}


def test_judge_is_skipped_for_maths(db):
    judge = Judge(lambda item: (False, "veto"))
    mgr = EnrichmentManager(db, FakeLLM(), Gates.uniform(AcceptAll()), judge=judge)
    chunk = {"chunk_id": "c1", "content": "The loss is $L = (y - p)^2$ summed over the whole batch of examples.", "estimated_tokens": 100, "content_type": "math"}
    db.save_document("d", "d.md", None, 1)
    db.save_chunks("d", [{"chunk_id": "c1", "chunk_index": 0, "content": chunk["content"], "metadata": {"content_type": "math"}, "estimated_tokens": 100}])
    with StubLLM() as stub:
        mgr.llm = make_llm(stub)
        mgr.process_chunk(chunk, "ctx")
    assert judge.seen == []
