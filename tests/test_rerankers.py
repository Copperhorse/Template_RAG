"""The reranker adapters, with a fake model so no download is needed. The real Jina model is tested in test_models.py."""

import dataclasses
import logging

import pytest

from rag_template.config import Settings
from rag_template.evals.rerank_stability import kendall_tau, order_sensitivity
from rag_template.rerankers import (
    FALLBACK_RERANK_MODEL,
    JINA_ID,
    JINA_SHA,
    TRUSTED_REMOTE_CODE,
    CrossEncoderReranker,
    JinaListwiseReranker,
    make_reranker,
)


class FakeListwise:
    """Mimics jinaai's `rerank`: returns results SORTED by score, each carrying the index of its input."""

    def __init__(self, scorer=None, fail_over=None):
        self.scorer = scorer or (lambda q, d: float(len(set(q.split()) & set(d.split()))))
        self.fail_over, self.calls = fail_over, []

    def rerank(self, query, documents, top_n=None, return_embeddings=False):
        self.calls.append(len(documents))
        if self.fail_over is not None and len(documents) > self.fail_over:
            raise RuntimeError("CUDA out of memory. Tried to allocate 2.00 GiB")
        scored = [
            {"document": d, "relevance_score": self.scorer(query, d), "index": i, "embedding": None}
            for i, d in enumerate(documents)
        ]
        return sorted(scored, key=lambda r: r["relevance_score"], reverse=True)


def jina(model, **kw):
    return JinaListwiseReranker(model=model, **kw)


def test_scores_come_back_in_input_order_although_the_model_returns_them_sorted():
    docs = ["unrelated words here", "cache expiry after ttl", "the cache ttl", "nothing"]
    scores = jina(FakeListwise()).rerank("cache ttl", docs)
    assert scores == [0.0, 2.0, 2.0, 0.0] or scores == [0.0, 2.0, 2.0, 0.0]
    assert [scores[i] for i in (1, 2)] == [2.0, 2.0] and scores[0] == scores[3] == 0.0
    best = max(range(len(docs)), key=scores.__getitem__)
    assert best in (1, 2)


def test_an_empty_list_costs_nothing_and_a_single_document_works():
    model = FakeListwise()
    r = jina(model)
    assert r.rerank("q", []) == [] and model.calls == []
    assert r.rerank("cache", ["cache"]) == [1.0]


def test_an_out_of_memory_error_splits_the_list_and_keeps_every_score_in_place(caplog):
    docs = [f"doc{i} cache" for i in range(8)]
    model = FakeListwise(scorer=lambda q, d: float(int(d[3])), fail_over=3)
    with caplog.at_level(logging.WARNING, logger="rag_template.rerankers"):
        scores = jina(model).rerank("cache", docs)
    assert scores == [float(i) for i in range(8)]  # input order preserved across the sub-passes
    assert (
        model.calls[0] == 8
        and max(model.calls[1:]) <= 4
        and any("not strictly comparable" in r.message for r in caplog.records)
    )


def test_other_errors_are_not_swallowed_and_a_single_doc_oom_is_raised():
    class Broken(FakeListwise):
        def rerank(self, *a, **k):
            raise ValueError("bad input")

    with pytest.raises(ValueError, match="bad input"):
        jina(Broken()).rerank("q", ["a", "b"])
    with pytest.raises(RuntimeError, match="out of memory"):
        jina(FakeListwise(fail_over=0)).rerank("q", ["only one"])


def test_the_audited_model_and_commit_are_pinned_and_trusted():
    assert JINA_ID == "jinaai/jina-reranker-v3.5" and len(JINA_SHA) == 40 and (JINA_ID, JINA_SHA) in TRUSTED_REMOTE_CODE
    assert jina(FakeListwise()).revision == JINA_SHA  # the default revision is the audited commit, never "main"


@pytest.mark.parametrize(
    "model, revision, trust, allowed",
    [
        (JINA_ID, "", False, True),  # the audited pair needs no flag
        (JINA_ID, JINA_SHA, False, True),
        (JINA_ID, "0123456789abcdef", False, False),  # same model, different commit: not audited
        ("jinaai/jina-reranker-v3", "", False, False),  # a sibling model: not audited
        ("jinaai/jina-reranker-v3", "", True, True),  # explicit opt-in
    ],
)
def test_remote_code_is_only_trusted_for_the_audited_pair_unless_the_user_opts_in(
    monkeypatch, model, revision, trust, allowed
):
    loaded = []
    monkeypatch.setattr(
        JinaListwiseReranker, "_load", lambda self, dtype: loaded.append((self.name, self.revision)) or FakeListwise()
    )
    if allowed:
        JinaListwiseReranker(model, revision, trust)
        assert loaded == [(model, revision or (JINA_SHA if model == JINA_ID else "main"))]
    else:
        with pytest.raises(ValueError, match="RAG_TRUST_REMOTE_CODE=1"):
            JinaListwiseReranker(model, revision, trust)
        assert loaded == []  # nothing was downloaded or executed


def test_the_factory_picks_the_adapter_by_model_id(monkeypatch):
    monkeypatch.setattr(JinaListwiseReranker, "_load", lambda self, dtype: FakeListwise())
    monkeypatch.setattr(
        "rag_template.rerankers.CrossEncoderReranker.__init__", lambda self, name=None: setattr(self, "name", name)
    )
    assert isinstance(make_reranker(JINA_ID), JinaListwiseReranker)
    assert isinstance(make_reranker("cross-encoder/ms-marco-MiniLM-L-6-v2"), CrossEncoderReranker)
    assert make_reranker("BAAI/some-other-ranker").name == "BAAI/some-other-ranker"


def test_settings_defaults_and_environment(monkeypatch):
    s = Settings()
    assert (
        s.rerank_model == JINA_ID
        and s.rerank_revision == ""
        and s.rerank_top == 20
        and s.rerank_trust_remote_code is False
    )
    monkeypatch.setenv("RAG_RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    monkeypatch.setenv("RAG_RERANK_REVISION", "abc123")
    monkeypatch.setenv("RAG_TRUST_REMOTE_CODE", "1")
    monkeypatch.setenv("RAG_RERANK_TOP", "40")
    s = Settings.from_env()
    assert (s.rerank_model, s.rerank_revision, s.rerank_trust_remote_code, s.rerank_top) == (
        "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "abc123",
        True,
        40,
    )


# ------------------------------------------------------- the facade: fallback must be loud and "on" must be strict


def make_rag(tmp_path, **settings_kw):
    from rag_template.rag import RAG
    from rag_template.store.embedders import HashingEmbedder
    from rag_template.store.vector import InMemoryVectorStore

    st = Settings(data_dir=tmp_path / "d", vector_store="memory", embedder="hash", **settings_kw)
    return RAG(st, store=InMemoryVectorStore(), embedder=HashingEmbedder())


def test_auto_falls_back_to_the_small_cross_encoder_with_a_warning(tmp_path, monkeypatch, caplog):
    import rag_template.rag as rag_mod

    def fake_make(name, revision="", trust=False, dtype="auto"):
        if name == JINA_ID:
            raise OSError("no network")
        raise AssertionError("fallback must go through CrossEncoderReranker")

    class FakeCE:
        def __init__(self, name):
            self.name = name

    monkeypatch.setattr(rag_mod, "make_reranker", fake_make)
    monkeypatch.setattr(rag_mod, "CrossEncoderReranker", FakeCE)
    with caplog.at_level(logging.WARNING, logger="rag_template"):
        r = make_rag(tmp_path, rerank="auto").reranker
    assert isinstance(r, FakeCE) and r.name == FALLBACK_RERANK_MODEL
    assert any(
        "falling back" in m.message and JINA_ID in m.message and "RAG_RERANK=on" in m.message for m in caplog.records
    )


def test_on_mode_raises_instead_of_falling_back_and_off_disables(tmp_path, monkeypatch):
    import rag_template.rag as rag_mod

    monkeypatch.setattr(rag_mod, "make_reranker", lambda *a, **k: (_ for _ in ()).throw(OSError("no network")))
    with pytest.raises(OSError):
        make_rag(tmp_path, rerank="on").reranker
    assert make_rag(tmp_path, rerank="off").reranker is None
    with pytest.raises(ValueError, match="unknown rerank mode"):
        make_rag(tmp_path, rerank="maybe").reranker


def test_if_even_the_fallback_fails_retrieval_runs_without_a_reranker(tmp_path, monkeypatch, caplog):
    import rag_template.rag as rag_mod

    def boom(*a, **k):
        raise ImportError("no sentence-transformers")

    monkeypatch.setattr(rag_mod, "make_reranker", boom)
    monkeypatch.setattr(rag_mod, "CrossEncoderReranker", boom)
    with caplog.at_level(logging.WARNING, logger="rag_template"):
        assert make_rag(tmp_path, rerank="auto").reranker is None
    assert any("without a rerank stage" in m.message for m in caplog.records)


def test_the_configured_candidate_count_reaches_the_retriever(tmp_path):
    rag = make_rag(tmp_path, rerank="off", rerank_top=7)
    assert rag.retriever.rerank_top == 7


# -------------------------------------------------------------------------------- order stability metrics


def test_kendall_tau_known_values():
    assert kendall_tau([1, 2, 3], [10, 20, 30]) == 1.0
    assert kendall_tau([1, 2, 3], [3, 2, 1]) == -1.0
    assert kendall_tau([1, 2, 3, 4], [1, 3, 2, 4]) == pytest.approx((5 - 1) / 6)
    assert (
        kendall_tau([1, 1, 1], [1, 2, 3]) == 0.0 and kendall_tau([1], [1]) == 1.0
    )  # one list constant: undefined, reported as 0
    assert (
        kendall_tau([1, 1, 2], [1, 1, 2]) == 1.0 and kendall_tau([5, 5, 5], [7, 7, 7]) == 1.0
    )  # identical lists with ties agree
    assert kendall_tau([1, 2, 2, 3], [1, 2, 3, 3]) == pytest.approx(0.8)  # hand-computed tau-b: (4 - 0) / sqrt(5 * 5)


def test_a_pairwise_scorer_is_perfectly_order_stable_and_a_position_biased_one_is_not():
    texts = [f"doc {i} about topic {i % 3}" for i in range(8)]
    pairwise = lambda q, ds: [float(len(set(q.split()) & set(d.split()))) for d in ds]  # noqa: E731
    stable = order_sensitivity(pairwise, "topic 1 doc", texts, n_shuffles=6)
    assert stable == {"tau": 1.0, "top1_agree": 1.0, "max_score_delta": 0.0}
    biased = lambda q, ds: [pairwise(q, ds)[i] + 3.0 / (i + 1) for i in range(len(ds))]  # noqa: E731  an earlier slot scores higher
    unstable = order_sensitivity(biased, "topic 1 doc", texts, n_shuffles=6)
    assert unstable["tau"] < 1.0 and unstable["max_score_delta"] > 0


def test_a_failed_load_in_on_mode_fails_again_instead_of_returning_no_reranker(tmp_path, monkeypatch):
    import rag_template.rag as rag_mod

    monkeypatch.setattr(rag_mod, "make_reranker", lambda *a, **k: (_ for _ in ()).throw(OSError("no network")))
    rag = make_rag(tmp_path, rerank="on")
    for _ in range(2):  # the second access used to return None silently
        with pytest.raises(OSError):
            rag.reranker


def test_document_routing_is_on_by_default_and_can_be_switched_off_or_tuned(monkeypatch, tmp_path):
    from rag_template.config import Settings

    monkeypatch.delenv("RAG_ROUTE_MARGIN", raising=False)
    assert Settings.from_env().route_margin == 0.10
    for off in ("off", "OFF", "none", ""):
        monkeypatch.setenv("RAG_ROUTE_MARGIN", off)
        assert Settings.from_env().route_margin is None
    monkeypatch.setenv("RAG_ROUTE_MARGIN", "0.25")
    assert Settings.from_env().route_margin == 0.25
    monkeypatch.delenv("RAG_ROUTE_MARGIN")
    rag = make_rag(tmp_path)
    rag.settings = dataclasses.replace(rag.settings, route_margin=0.10)
    assert rag.retriever.route_margin == 0.10  # the facade hands the setting to the Retriever
