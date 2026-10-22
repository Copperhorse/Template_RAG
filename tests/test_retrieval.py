"""Each retrieval stage on its own, then together: bi-encoder, BM25, RRF, cross-encoder, gates, evidence."""

import re

from rag_template.retrieve import RRF_K
from conftest import SAMPLE_MD, SAMPLE_PY


def build(make_rag, tmp_path, files):
    rag = make_rag()
    for name, text in files.items():
        p = tmp_path / name
        p.write_text(text)
        assert rag.ingest_path(p, source=name).ok
    rag.index()
    return rag


FILES = {
    "retry.py": SAMPLE_PY,
    "deploy.md": SAMPLE_MD,
    "errors.md": "# Errors\n\nThe error code ERR_QUOTA_7731 means the account has exhausted its monthly request allowance and must wait for the reset.\n",
    "misc.md": "# Misc\n\nOffice plants need indirect light and a little water every week during the growing season of the year.\n",
}


def test_bm25_finds_an_exact_token_that_embeddings_miss(make_rag, tmp_path):
    rag = build(make_rag, tmp_path, FILES)
    hits = rag.search("ERR_QUOTA_7731", k=3, dense=False)
    assert hits[0].source == "errors.md" and hits[0].lexical_rank == 1 and hits[0].dense_rank is None
    assert hits[0].via == ["lexical"]


def test_dense_only_and_lexical_only_can_be_switched_off(make_rag, tmp_path):
    rag = build(make_rag, tmp_path, FILES)
    d = rag.search("previous image tag rollback", k=3, lexical=False)
    assert d and all(h.lexical_rank is None and h.dense_rank for h in d)
    assert rag.search("anything", k=3, dense=False, lexical=False) == []


def test_rrf_scores_are_the_sum_of_reciprocal_ranks(make_rag, tmp_path):
    rag = build(make_rag, tmp_path, FILES)
    for h in rag.search("rollback previous image tag release manifest", k=5):
        expect = sum(1 / (RRF_K + r) for r in (h.dense_rank, h.lexical_rank) if r)
        assert abs(h.rrf_score - expect) < 1e-12 and h.score == h.rrf_score and h.rerank_score is None
    both = [h for h in rag.search("rollback previous image tag release manifest", k=5) if h.dense_rank and h.lexical_rank]
    assert both and both[0].rrf_score > 1 / (RRF_K + 1)  # a chunk both rankers found outranks any single-ranker rank 1


def test_rrf_weights_shift_the_balance(make_rag, tmp_path):
    rag = build(make_rag, tmp_path, FILES)
    q = "ERR_QUOTA_7731 plants water"
    lex_heavy = rag.search(q, k=1, weights=(0.0, 1.0))[0]
    dense_heavy = rag.search(q, k=1, weights=(1.0, 0.0))[0]
    assert lex_heavy.lexical_rank == 1 and dense_heavy.dense_rank == 1


class ReverseReranker:
    """Scores chunks by how many query words they contain: a cross-encoder stand-in that disagrees with RRF."""

    def __init__(self):
        self.calls = []

    def rerank(self, query, texts):
        self.calls.append((query, list(texts)))
        words = set(re.findall(r"\w+", query.lower()))
        return [float(len(words & set(re.findall(r"\w+", t.lower())))) for t in texts]


def test_the_cross_encoder_reorders_the_fused_candidates(make_rag, tmp_path):
    rr = ReverseReranker()
    rag = build(make_rag, tmp_path, FILES)
    rag._reranker, rag._reranker_set = rr, True
    q = "tag stored release manifest rollback"
    plain = rag.search(q, k=4, rerank=False)
    reranked = rag.search(q, k=4, rerank_mode="replace")
    assert rr.calls and rr.calls[0][0] == q
    scores = [h.rerank_score for h in reranked]
    assert scores == sorted(scores, reverse=True) and all(h.score == h.rerank_score for h in reranked)
    assert all(h.rerank_score is None for h in plain)
    assert {h.chunk_id for h in plain} >= {h.chunk_id for h in reranked[:1]}


def test_only_the_top_candidates_are_sent_to_the_cross_encoder(make_rag, tmp_path):
    rr = ReverseReranker()
    rag = build(make_rag, tmp_path, FILES)
    rag._reranker, rag._reranker_set = rr, True
    rag.search("rollback previous image tag", k=2, rerank_top=2)
    assert len(rr.calls[0][1]) == 2


def test_min_rerank_score_drops_weak_candidates(make_rag, tmp_path):
    rr = ReverseReranker()
    rag = build(make_rag, tmp_path, FILES)
    rag._reranker, rag._reranker_set = rr, True
    q = "rollback previous image tag"
    everything = rag.search(q, k=10, rerank_mode="replace")
    strong = rag.search(q, k=10, min_rerank_score=3, rerank_mode="replace")
    assert len(strong) < len(everything) and all(h.rerank_score >= 3 for h in strong)
    assert rag.search("zzz qqq", k=10, min_rerank_score=1) == []


def test_min_dense_score_keeps_chunks_that_bm25_also_found(make_rag, tmp_path):
    rag = build(make_rag, tmp_path, FILES)
    hits = rag.search("ERR_QUOTA_7731", k=5, min_dense_score=0.99)
    assert [h.source for h in hits] == ["errors.md"]  # dense score is far below 0.99, but BM25 found it


def test_extractive_evidence_is_a_verbatim_span_of_the_hit(make_rag, tmp_path):
    rag = build(make_rag, tmp_path, FILES)
    hits = rag.search("release manifest rebuild", k=3, quotes=True)  # no cross-encoder: bi-encoder scores the spans
    top = next(h for h in hits if h.source == "deploy.md")
    assert top.quote and top.quote.text in top.content
    assert top.content[top.quote.start : top.quote.end].strip() == top.quote.text
    assert "rebuild" in top.quote.text and "A rollback redeploys" not in top.quote.text

    code = next(h for h in rag.search("when does Cache.get return None because the ttl passed", k=3, quotes=True) if h.content_type == "code")
    assert code.quote.text in code.content and "ttl" in code.quote.text


def test_the_cross_encoder_also_picks_the_evidence_span(make_rag, tmp_path):
    rr = ReverseReranker()
    rag = build(make_rag, tmp_path, FILES)
    rag._reranker, rag._reranker_set = rr, True
    top = rag.search("rollback completes in under two minutes", k=1, quotes=True, rerank_mode="replace")[0]
    assert top.quote.text.endswith("under two minutes.")
    assert len(rr.calls) == 2  # one call ranks the chunks, one ranks the sentences of the hit
    assert all(t in top.content for t in rr.calls[1][1])


def test_filter_by_document(make_rag, tmp_path):
    rag = build(make_rag, tmp_path, FILES)
    doc = rag.db.get_document_by_source("errors.md")["doc_id"]
    hits = rag.search("rollback previous image tag ERR_QUOTA_7731", k=5, doc_id=doc)
    assert hits and all(h.source == "errors.md" for h in hits)


def test_fuse_mode_makes_the_cross_encoder_a_third_voter_not_the_only_one(make_rag, tmp_path):
    rr = ReverseReranker()
    rag = build(make_rag, tmp_path, FILES)
    rag._reranker, rag._reranker_set = rr, True
    q = "tag stored release manifest rollback previous image"
    replaced = rag.search(q, k=6, rerank_mode="replace")
    fused = rag.search(q, k=6, rerank_mode="fuse")
    plain = rag.search(q, k=6, rerank=False)
    head = [h.chunk_id for h in plain]  # all candidates were read by the reranker
    first = {c: i + 1 for i, c in enumerate(head)}
    second = {h.chunk_id: i + 1 for i, h in enumerate(sorted(plain, key=lambda h: next(x.rerank_score for x in replaced if x.chunk_id == h.chunk_id), reverse=True))}
    for h in fused:
        assert abs(h.score - (1 / (RRF_K + first[h.chunk_id]) + 1 / (RRF_K + second[h.chunk_id]))) < 1e-12
        assert h.rerank_score is not None  # the raw cross-encoder score is still reported
    assert [h.score for h in fused] == sorted((h.score for h in fused), reverse=True)
    import pytest

    with pytest.raises(ValueError):
        rag.search(q, rerank_mode="nonsense")


def test_the_breadcrumb_control_blanks_titles_everywhere(tmp_path):
    from rag_template.evals.workspace import Workspace

    root = tmp_path / "c"
    root.mkdir()
    (root / "m.py").write_text(SAMPLE_PY)
    with_crumb, without = Workspace(root, min_tokens=5), Workspace(root, min_tokens=5, breadcrumb=False)
    with_crumb.ingest(), without.ingest()
    assert all(c["breadcrumb"] for c in with_crumb.db.get_indexable_chunks(with_crumb.db.list_documents()[0]["doc_id"]))
    assert all(c["breadcrumb"] == "" for c in without.db.get_indexable_chunks(without.db.list_documents()[0]["doc_id"]))
    assert [c["content"] for c in with_crumb.db.iter_chunks()] == [c["content"] for c in without.db.iter_chunks()]  # same chunks, only the metadata differs


def test_the_default_rerank_mode_depends_on_the_reranker_and_can_be_overridden(make_rag, tmp_path):
    from rag_template.config import Settings
    from rag_template.rerankers import default_rerank_mode

    assert default_rerank_mode("jinaai/jina-reranker-v3.5") == "replace"
    assert default_rerank_mode("cross-encoder/ms-marco-MiniLM-L-6-v2") == "fuse" and default_rerank_mode("anything/else") == "fuse"
    assert Settings().rerank_mode == "auto"
    rr = ReverseReranker()
    rag = build(make_rag, tmp_path, FILES)
    rag._reranker, rag._reranker_set = rr, True
    q = "tag stored release manifest rollback previous image"
    rag.settings.rerank_model = "cross-encoder/ms-marco-MiniLM-L-6-v2"  # not Jina: the safe mode
    assert rag.retriever.rerank_mode == "fuse"
    rag.settings.rerank_model = "jinaai/jina-reranker-v3.5"
    assert rag.retriever.rerank_mode == "replace"
    assert [h.score for h in rag.search(q, k=5)] == [h.rerank_score for h in rag.search(q, k=5)]  # replace: the score is the reranker's
    rag.settings.rerank_mode = "fuse"  # an explicit setting always wins
    assert rag.retriever.rerank_mode == "fuse"
    assert [h.chunk_id for h in rag.search(q, k=5)] == [h.chunk_id for h in rag.search(q, k=5, rerank_mode="fuse")]


def test_a_score_threshold_also_drops_candidates_the_reranker_never_scored(make_rag, tmp_path):
    rr = ReverseReranker()
    rag = build(make_rag, tmp_path, FILES)
    rag._reranker, rag._reranker_set = rr, True
    q = "rollback previous image tag"
    hits = rag.search(q, k=10, rerank_top=1, min_rerank_score=1e9, rerank_mode="replace")  # one scored candidate, below the threshold
    assert hits == []  # the unscored tail used to survive and become the answer


ROUTING = {
    "deploy.md": "# Rollbacks\n\nA rollback redeploys the previous image tag. The rollback takes under two minutes for every service.\n",
    "notes.md": "# Release notes\n\nThe image registry keeps a tag for each release. Old images are deleted after ninety days.\n",
}


def test_routing_keeps_only_the_leading_document_when_it_leads_by_the_margin(make_rag, tmp_path):
    rag = build(make_rag, tmp_path, ROUTING)
    rag._reranker, rag._reranker_set = ReverseReranker(), True
    r = rag.retriever
    q = "rollback previous image tag"
    assert {h.source for h in r.search(q, k=5, rerank_mode="replace")} == {"deploy.md", "notes.md"}  # off by default: a mix
    r.route_margin = 1.0
    routed = r.search(q, k=5, rerank_mode="replace")
    assert routed and {h.source for h in routed} == {"deploy.md"}


def test_routing_keeps_the_mix_on_a_close_call_or_without_a_reranker(make_rag, tmp_path):
    rag = build(make_rag, tmp_path, ROUTING)
    rag._reranker, rag._reranker_set = ReverseReranker(), True
    r = rag.retriever
    r.route_margin = 100.0  # the leader never leads by this much
    assert {h.source for h in r.search("rollback previous image tag", k=5, rerank_mode="replace")} == {"deploy.md", "notes.md"}
    r.route_margin = 1.0
    assert {h.source for h in r.search("rollback previous image tag", k=5, rerank=False)} == {"deploy.md", "notes.md"}  # no reranker scores: nothing to route on
