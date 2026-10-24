import math

import pytest

from rag_template.chunking import ChunkConfig
from rag_template.chunking.naive import naive_chunk_file
from rag_template.evals import metrics as M
from rag_template.evals.gold import GoldItem, Query, check_reachability, covered_items, load_gold, norm, save_gold


def test_ranking_metrics_match_hand_computed_values():
    rel = [False, True, False, True]
    assert M.hit_at_k(rel, 1) == 0 and M.hit_at_k(rel, 2) == 1
    assert M.mrr_at_k(rel, 10) == 0.5 and M.mrr_at_k(rel, 1) == 0
    dcg = 1 / math.log2(3) + 1 / math.log2(5)
    ideal = 1 + 1 / math.log2(3)
    assert M.ndcg_at_k(rel, 10, n_relevant=2) == pytest.approx(dcg / ideal)
    assert M.ndcg_at_k([True], 10, 1) == 1.0 and M.ndcg_at_k([False] * 3, 10, 1) == 0.0
    assert M.average_precision_at_k(rel, 10, 2) == pytest.approx((1 / 2 + 2 / 4) / 2)
    assert M.average_precision_at_k(rel, 3, 2) == pytest.approx((1 / 2) / 2)  # only rank 2 counts within k=3


def test_ideal_ndcg_is_capped_by_k_and_by_the_relevant_chunks_that_exist():
    assert M.ndcg_at_k([True, True], 10, n_relevant=2) == 1.0
    assert M.ndcg_at_k([True], 10, n_relevant=5) < 1.0  # four relevant chunks were missed
    assert M.ndcg_at_k([True, True], 2, n_relevant=50) == 1.0  # at k=2 nothing better than two hits exists


def test_recall_counts_distinct_gold_items_covered():
    covered = [{0}, set(), {1}, {0}]
    assert M.recall_at_k(covered, 2, 1) == 0.5
    assert M.recall_at_k(covered, 2, 2) == 0.5
    assert M.recall_at_k(covered, 2, 3) == 1.0
    assert M.recall_at_k([], 1, 5) == 0 and M.recall_at_k(covered, 0, 5) == 0


def test_query_metrics_bundle():
    m = M.query_metrics([False, True], [set(), {0}], n_gold=1, n_relevant=1)
    assert m["recall@1"] == 0 and m["recall@3"] == 1 and m["recall@20"] == 1 and m["mrr@10"] == 0.5
    assert set(m) >= {"recall@1", "recall@5", "recall@10", "mrr@10", "ndcg@10", "map@10"}


def test_bootstrap_interval_brackets_the_mean_and_shrinks_with_more_data():
    small = M.bootstrap_ci([1, 0, 1, 1, 0, 1, 0, 1], seed=1)
    assert small[1] <= small[0] <= small[2]
    big = M.bootstrap_ci([1, 0, 1, 1, 0, 1, 0, 1] * 25, seed=1)
    assert (big[2] - big[1]) < (small[2] - small[1])
    assert M.bootstrap_ci([0.5] * 10) == (0.5, 0.5, 0.5) and M.bootstrap_ci([]) == (0, 0, 0)


def test_paired_bootstrap_detects_a_real_difference_and_not_a_tie():
    a = [1.0] * 40 + [0.0] * 10
    b = [1.0] * 25 + [0.0] * 25
    d = M.paired_bootstrap(a, b)
    assert d["diff"] == pytest.approx(0.3) and d["lo"] > 0 and d["p"] < 0.01
    tie = M.paired_bootstrap(a, list(a))
    assert tie["diff"] == 0 and tie["p"] == 1.0 and tie["lo"] == tie["hi"] == 0
    flipped = M.paired_bootstrap(b, a)
    assert flipped["hi"] < 0 and flipped["p"] > 0.99
    with pytest.raises(AssertionError):
        M.paired_bootstrap([1.0], [1.0, 0.0])


def test_percentile():
    assert M.percentile([1, 2, 3, 4, 100], 0.95) == 100 and M.percentile([], 0.5) == 0 and M.percentile([5], 0.9) == 5


# ----------------------------------------------------------------------------------- gold


def test_snippet_matching_ignores_case_whitespace_and_punctuation():
    q = Query("q", "x", gold=[GoldItem("a.py", "def  Foo(x):\n    return x+1")])
    assert covered_items(q, "a.py", "class A:\n    def foo(x):\n        return x + 1\n") == {0}
    assert covered_items(q, "b.py", "def foo(x): return x+1") == set()  # right text, wrong file
    assert covered_items(q, "a.py", "def foo(x): return x+2") == set()
    assert norm("A_b-C 1!") == "abc1"


def test_gold_round_trips_and_reachability_separates_split_from_gated(tmp_path):
    qs = [
        Query("a", "one", gold=[GoldItem("f.md", "alpha beta gamma delta")]),
        Query("b", "two", gold=[GoldItem("f.md", "epsilon zeta eta theta")]),
        Query("c", "three", gold=[GoldItem("f.md", "iota kappa lambda mu")]),
        Query("n", "none", answerable=False),
    ]
    save_gold(qs, tmp_path / "g.jsonl")
    back = load_gold(tmp_path / "g.jsonl")
    assert (
        [q.id for q in back] == ["a", "b", "c", "n"]
        and back[0].gold[0].snippet == "alpha beta gamma delta"
        and not back[3].answerable
    )
    chunks = [
        {"source": "f.md", "content": "intro alpha beta gamma delta outro", "should_use": 1},
        {"source": "f.md", "content": "epsilon zeta eta theta", "should_use": 0, "reject_reason": "Low alpha"},
        {"source": "f.md", "content": "iota kappa", "should_use": 1},
        {"source": "f.md", "content": "lambda mu", "should_use": 1},
    ]
    r = check_reachability(qs, chunks)
    assert (r.reachable, r.gated_out, r.split) == (1, 1, 1)
    assert "Low alpha" in r.details["b#0"] and "single chunk" in r.details["c#0"]


# ---------------------------------------------------------------------- naive baseline chunker


def test_naive_chunker_is_structure_blind_but_bounded_and_lossless():
    src = "\n".join(f"def func_{i}(x):\n    return x + {i}\n" for i in range(60))
    cs = naive_chunk_file("m.py", src, ChunkConfig(max_chunk_tokens=100), source="m.py")
    assert len(cs) > 5 and max(c["estimated_tokens"] for c in cs) <= 105
    assert "\n".join(c["content"] for c in cs).count("def func_") == 60
    assert any(not c["content"].lstrip().startswith("def ") for c in cs)  # windows start mid-function
    assert cs[0]["metadata"]["breadcrumb"] == "m.py" and cs[0]["metadata"]["content_type"] == "code"
    assert (
        naive_chunk_file("notes.md", "a b c\n" * 50, ChunkConfig(max_chunk_tokens=30))[0]["metadata"]["content_type"]
        == "prose"
    )
    assert cs[1]["prev_chunk_id"] == cs[0]["chunk_id"]


# ------------------------------------------------------------------------- quote tolerance experiment


def test_quote_tolerance_experiment_separates_slips_from_fabrications():
    from rag_template.evals import quotes as Q

    para = (
        "The deployment pipeline builds a container image and pushes it to the registry after every merge to the main branch. "
        "A rollback redeploys the previous image tag stored in the release manifest, so no rebuild is ever needed afterwards. "
        "Access tokens expire after twenty four hours and must be refreshed by the client library before the next request is made. "
        "The nightly cleanup job removes every uploaded file older than thirty days from the bucket and from the search index."
    )
    other = "Completely different material about gardening, soil acidity, composting methods and seasonal planting schedules for vegetables."
    chunks = [
        {"source": "a.md", "content": para, "content_type": "prose", "should_use": 1},
        {"source": "b.md", "content": other * 3, "content_type": "prose", "should_use": 1},
    ]
    queries = [
        Query(f"q{i}", "x", gold=[GoldItem("a.md", s)])
        for i, s in enumerate(
            [
                "A rollback redeploys the previous image tag stored in the release manifest, so no rebuild is ever needed afterwards.",
                "Access tokens expire after twenty four hours and must be refreshed by the client library before the next request is made.",
                "The nightly cleanup job removes every uploaded file older than thirty days from the bucket and from the search index.",
                "The deployment pipeline builds a container image and pushes it to the registry after every merge to the main branch.",
            ]
        )
    ]
    rows = {r["damage"]: r for r in Q.run_quote_tolerance(queries, chunks, seed=3)}
    assert rows["text of another chunk"]["loose_accepts"] == 0 and rows["text of another chunk"]["strict_accepts"] == 0
    for slip in ("one word inserted", "two words swapped", "last 25% cut off"):
        assert rows[slip]["loose_accepts"] >= rows[slip]["strict_accepts"] and rows[slip]["loose_accepts"] >= 0.75, (
            slip,
            rows[slip],
        )
    assert rows["50% of words replaced"]["loose_accepts"] <= 0.5
    assert all(r["loose_accepts"] >= r["strict_accepts"] for r in rows.values())  # loosening only ever accepts more
    assert "| damage |" in Q.markdown(list(rows.values()))


def test_every_evals_subcommand_can_be_imported_and_parsed():
    """Regression: a syntax error in evals/cli.py went unnoticed because no test imported it."""
    import pytest as _pytest

    from rag_template.evals import cli

    for cmd in (
        "retrieval",
        "ablations",
        "rerankers",
        "answerability",
        "gates",
        "quotes",
        "synth",
        "answers",
        "summarize",
    ):
        assert callable(getattr(cli, f"cmd_{cmd}"))
    with _pytest.raises(SystemExit) as e:
        cli.main(["--help"])
    assert e.value.code == 0
    with _pytest.raises(SystemExit):
        cli.main(["no-such-command"])
