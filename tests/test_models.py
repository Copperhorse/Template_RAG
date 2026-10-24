"""Tests that load real sentence-transformers models (the `local` extra). They download a few hundred MB on
first run and are skipped when the package or the network is missing. Deselect with -m 'not models'."""

import math

import pytest

pytest.importorskip("sentence_transformers")
pytestmark = pytest.mark.models

from rag_template import models  # noqa: E402
from rag_template.enrichment import verify  # noqa: E402
from rag_template.store.embedders import SentenceTransformerEmbedder  # noqa: E402


def need(loader, *args):
    try:
        return loader(*args)
    except Exception as e:  # offline, gated model, no disk
        pytest.skip(f"model unavailable: {type(e).__name__}: {str(e)[:120]}")


@pytest.fixture(scope="module")
def embedder():
    e = SentenceTransformerEmbedder()  # the default: google/embeddinggemma-2, text-only, bfloat16 on a GPU
    need(e._get)
    return e


def test_embedder_returns_unit_vectors_of_the_native_dimension(embedder):
    vecs = embedder.embed_documents(["retry sleeps with backoff", "cache entries expire"])
    assert len(vecs) == 2 and len(vecs[0]) == 768
    assert all(abs(math.sqrt(sum(x * x for x in v)) - 1) < 1e-6 for v in vecs)  # re-normalised in float32
    assert embedder.embed_documents([]) == []
    assert not any(math.isnan(x) for v in vecs for x in v)  # float16 would have produced NaN here


def test_the_formatted_inputs_equal_the_models_own_prompts(embedder):
    """store/formats.py writes the prefixes by hand; they must produce the same vectors as the model's
    built-in prompt_name mechanism, otherwise the format layer is wrong."""
    model = embedder._get()
    ours_q = embedder.embed_query("What causes the northern lights?")
    theirs_q = model.encode("What causes the northern lights?", prompt_name="SearchQuery", normalize_embeddings=True)
    ours_code = embedder.embed_query("sort a list", task="code retrieval")
    theirs_code = model.encode("sort a list", prompt_name="CodeRetrieval", normalize_embeddings=True)
    ours_d = embedder.embed_documents(["The northern lights are caused by charged particles."])[0]
    theirs_d = model.encode(
        "title: none | text: The northern lights are caused by charged particles.", normalize_embeddings=True
    )
    for a, b in ((ours_q, theirs_q), (ours_code, theirs_code), (ours_d, theirs_d)):
        assert (
            sum(x * float(y) for x, y in zip(a, b)) > 0.99
        )  # bfloat16: two code paths round differently, so not 0.9999
    wrong = model.encode("What causes the northern lights?", prompt_name="Classification", normalize_embeddings=True)
    assert (
        sum(x * float(y) for x, y in zip(ours_q, wrong)) < 0.97
    )  # control: a different task prefix is clearly distinguishable


def test_a_document_title_changes_the_vector_and_a_wrong_task_changes_the_query(embedder):
    plain = embedder.embed_documents(["def f(x): return x + 1"])[0]
    titled = embedder.embed_documents(["def f(x): return x + 1"], ["pkg/util.py > f"])[0]
    assert sum(a * b for a, b in zip(plain, titled)) < 0.999
    q1, q2 = embedder.embed_query("sort a list"), embedder.embed_query("sort a list", task="code retrieval")
    assert sum(a * b for a, b in zip(q1, q2)) < 0.999


def test_embedder_ranks_the_relevant_passage_first(embedder):
    docs = [
        "Cache entries expire after the time-to-live has passed.",
        "A rollback redeploys the previous image tag.",
        "retry sleeps with exponential backoff",
    ]
    d = embedder.embed_documents(docs)
    q = embedder.embed_query("how long do cached values stay valid?")
    sims = [sum(a * b for a, b in zip(q, v)) for v in d]
    assert sims.index(max(sims)) == 0


def test_float16_is_refused_for_embeddinggemma_because_it_returns_nan():
    with pytest.raises(ValueError, match="float16"):
        models.get_bi_encoder("google/embeddinggemma-2", dtype="float16")


def test_text_only_loading_leaves_out_the_vision_and_audio_encoders(embedder):
    params = sum(p.numel() for p in embedder._get()._model.parameters()) / 1e6
    assert 200 < params < 350, (
        f"{params:.0f}M parameters: the vision/audio encoders should not be loaded (full model is ~740M)"
    )


def test_matryoshka_truncation_renormalises():
    from rag_template.store.embedders import TruncatedEmbedder

    base = SentenceTransformerEmbedder()
    need(base._get)
    small = TruncatedEmbedder(base, 256)
    v = small.embed_query("how does retry back off")
    assert len(v) == 256 and abs(math.sqrt(sum(x * x for x in v)) - 1) < 1e-3


def test_embedding_helpers_flag_rare_words_and_score_similarity():
    h = need(verify.EmbeddingHelpers)
    assert h.is_rare("kinetochore") and not h.is_rare("cell")
    assert (
        h.similarity("Mitosis produces two daughter cells.", "The result is two genetically identical daughter cells.")
        > 0.7
    )
    assert (
        h.similarity(
            "The stock market closed higher on Tuesday.", "The result is two genetically identical daughter cells."
        )
        < 0.5
    )


def test_pair_verifier_with_embeddings_accepts_a_faithful_answer_and_ranks_the_rest():
    """Measured with bge-small: faithful 0.97, paraphrase 0.79, a different sentence of the same chunk 0.73,
    off-topic 0.46, against the 0.70 threshold. The similarity layer is therefore a coarse off-topic
    filter; it cannot tell a paraphrase from a wrong sentence of the same chunk (only a judge can)."""
    pv = verify.PairVerifier()
    h = need(pv._get_helpers)
    chunk = "Mitosis is cell division. The result is two genetically identical daughter cells. Meiosis produces four different gametes."
    quote = "The result is two genetically identical daughter cells."
    ok, why = pv.validate(
        "What does mitosis produce?", "It produces two genetically identical daughter cells.", chunk, quote
    )
    assert ok, why
    sims = [
        h.similarity(a, quote)
        for a in (
            "It produces two genetically identical daughter cells.",
            "Cells split into two copies.",
            "Meiosis produces four different gametes.",
            "The stock market closed higher on Tuesday.",
        )
    ]
    assert sims == sorted(sims, reverse=True) and sims[-1] < pv.cfg.min_quote_similarity < sims[1]


def test_nli_validator_for_maths():
    from rag_template.enrichment.validator import AnswerValidator

    val = need(AnswerValidator)
    chunk = "The loss is the mean squared error over the batch, defined as $L = \\frac{1}{N}\\sum_i (y_i - p_i)^2$."
    quote = "The loss is the mean squared error over the batch"
    ok, why = val.validate("What is the loss?", "The loss is the mean squared error over the batch.", chunk, quote)
    assert ok, why
    ok, why = val.validate("What is the loss?", "The loss is not the mean squared error over the batch.", chunk, quote)
    assert not ok, "a negated restatement must not pass the NLI gate"
    assert not val.validate("What is the loss?", "", chunk, quote)[0]
    assert not val.validate("What is the loss?", "Entirely unrelated discussion of federal tax policy.", chunk, quote)[
        0
    ]


def test_reranker_prefers_the_passage_that_answers_the_query():
    from rag_template.retrieve import CrossEncoderReranker

    rr = need(CrossEncoderReranker)
    scores = rr.rerank(
        "how long until cache entries expire",
        ["A rollback redeploys the previous image tag.", "Cache entries expire after the time-to-live has passed."],
    )
    assert scores[1] > scores[0]


def test_the_models_registry_loads_each_model_once():
    a = need(models.get_bi_encoder)
    assert models.get_bi_encoder() is a
    assert any(
        m["kind"] == "bi-encoder" and m["name"] == models.BI_ENCODER_NAME and m["device"] == models.get_device()
        for m in models.loaded_models()
    )


def test_real_embeddings_retrieve_the_right_chunk_in_the_full_pipeline(tmp_path, stub, sample_repo):
    from rag_template.config import Settings
    from rag_template.enrichment.enricher import Gates
    from rag_template.rag import RAG
    from rag_template.store.vector import InMemoryVectorStore
    from conftest import make_llm

    emb = SentenceTransformerEmbedder()
    need(emb._get)
    rag = RAG(
        Settings(data_dir=tmp_path / "d", max_chunk_tokens=200, min_chunk_tokens=30),
        store=InMemoryVectorStore(),
        embedder=emb,
        llm=make_llm(stub),
        gates=Gates(prose=verify.PairVerifier(), code=verify.CodeVerifier()),
    )
    rag.ingest_directory(sample_repo)
    assert not rag.enrich().server_down
    rag.index()
    assert rag.search("how do I undo a bad release?", k=1)[0].source == "docs/deploy.md"
    assert "Cache" in rag.search("when does a stored value stop being returned?", k=1)[0].label


# ------------------------------------------------------------------------------------ jina-reranker-v3.5 (listwise)


@pytest.fixture(scope="module")
def jina():
    from rag_template.rerankers import JinaListwiseReranker

    return need(JinaListwiseReranker)


DOCS = [
    "Green tea contains antioxidants called catechins that may help reduce inflammation and protect cells from damage.",
    "El precio del café ha aumentado un 20% este año debido a problemas en la cadena de suministro.",
    "Studies show that drinking green tea regularly can improve brain function and boost metabolism.",
    "Basketball is one of the most popular sports in the United States.",
    "绿茶富含儿茶素等抗氧化剂，可以降低心脏病风险，还有助于控制体重。",
]


def test_jina_is_loaded_from_the_pinned_audited_commit(jina):
    from rag_template.rerankers import JINA_ID, JINA_SHA

    assert (jina.name, jina.revision) == (JINA_ID, JINA_SHA)
    assert JINA_SHA in str(jina._model.name_or_path), (
        jina._model.name_or_path
    )  # a local snapshot of exactly that commit


def test_jina_ranks_the_relevant_documents_first_across_languages(jina):
    scores = jina.rerank("What are the health benefits of green tea?", DOCS)
    assert len(scores) == len(DOCS) and not any(math.isnan(x) for x in scores)
    order = sorted(range(len(DOCS)), key=lambda i: -scores[i])
    assert set(order[:3]) == {0, 2, 4}  # the three green-tea documents, English and Chinese
    assert set(order[3:]) == {1, 3}


def test_jina_is_deterministic_and_scores_are_returned_in_input_order(jina):
    a = jina.rerank("green tea benefits", DOCS)
    assert a == jina.rerank("green tea benefits", DOCS)  # same input, same order: identical scores
    reversed_scores = jina.rerank("green tea benefits", DOCS[::-1])[::-1]  # mapped back to the original positions
    top3 = lambda sc: set(sorted(range(len(sc)), key=lambda i: -sc[i])[:3])  # noqa: E731
    assert top3(a) == top3(reversed_scores) == {0, 2, 4}  # the relevant set survives a reordering of the candidates ...
    # ... but NOT necessarily the exact order within it, nor the exact scores: a listwise model reads the candidates in one
    # causal pass, so a document's score depends a little on what came before it. Measured in evals/results/rerankers.md.
    assert max(abs(x - y) for x, y in zip(a, reversed_scores)) < 0.15


def test_jina_ranks_code_and_prose_sensibly_for_a_developer_question(jina):
    code = "def retry(fn, attempts=3, delay=0.5):\n    for i in range(attempts):\n        try:\n            return fn()\n        except OSError:\n            time.sleep(delay * 2 ** i)\n    raise RuntimeError('gave up')"
    docs = [
        code,
        "A rollback redeploys the previous image tag stored in the release manifest.",
        "Tokens expire after 24 hours.",
        "The nightly cleanup job removes uploaded files after thirty days.",
    ]
    scores = jina.rerank("how does the retry function back off between attempts?", docs)
    assert max(range(len(docs)), key=scores.__getitem__) == 0


def test_jina_handles_sentence_sized_candidates_for_evidence_spans(jina):
    sentences = [
        "The default token lifetime is seven days.",
        "Uploads larger than fifty megabytes are rejected.",
        "Passwords are hashed with PBKDF2.",
    ]
    scores = jina.rerank("How long do tokens last?", sentences)
    assert max(range(3), key=scores.__getitem__) == 0


def test_jina_order_stability_is_measured_and_reported(jina):
    from rag_template.evals.rerank_stability import order_sensitivity

    r = order_sensitivity(jina.rerank, "What are the health benefits of green tea?", DOCS, n_shuffles=4)
    print("jina order sensitivity:", r)  # visible with -s; the full measurement is in evals/results/rerankers.md
    assert r["top1_agree"] >= 0.75 and r["tau"] > 0.5  # a loose floor: the model must not be dominated by position
