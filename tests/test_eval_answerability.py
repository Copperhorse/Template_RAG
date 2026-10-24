import pytest

from rag_template.evals import answerability as A


def test_auc_known_values():
    assert A.auc([2, 3], [0, 1]) == 1.0 and A.auc([0, 1], [2, 3]) == 0.0
    assert A.auc([1, 2], [1, 2]) == 0.5  # (0 + .5 + 1 + .5) / 4 ... pairs: 1v1 tie, 1v2 loss, 2v1 win, 2v2 tie
    assert A.auc([1, 1, 1], [1, 1]) == 0.5 and A.auc([], [1]) == 0.5
    assert A.auc([1, 3], [2]) == 0.5  # one win, one loss


def test_bootstrap_interval_brackets_the_estimate_and_is_degenerate_when_perfect():
    a, lo, hi = A.bootstrap_auc([5, 6, 7, 8, 9] * 4, [1, 2, 3] * 4)
    assert a == 1.0 and lo == hi == 1.0
    a, lo, hi = A.bootstrap_auc([1, 2, 3, 4, 5, 6], [3, 4, 5, 6, 7, 8], seed=1)
    assert lo <= a <= hi and hi - lo > 0.05


def test_keep_threshold_keeps_at_least_the_target_share():
    pos = list(range(1, 101))  # 1..100
    for keep in (0.99, 0.95, 0.90, 0.80):
        t = A.keep_threshold(pos, keep)
        assert sum(x >= t for x in pos) / len(pos) >= keep
        assert sum(x >= t + 1 for x in pos) / len(pos) < keep + 0.02  # and it is not wastefully low
    assert A.keep_threshold([], 0.9) == 0.0


def test_operating_points_use_the_tuning_set_for_the_threshold_only():
    tune = list(range(10, 110))  # the threshold must come from these
    heldout = [20, 25, 200]  # must not influence it
    neg = [0, 5, 15, 60]
    pts = A.operating_points(tune, heldout, neg, keeps=(0.9,))
    t = A.keep_threshold(tune, 0.9)
    assert pts[0]["threshold"] == t == A.keep_threshold(tune, 0.9)
    assert pts[0]["heldout_refused"]["k"] == sum(x < t for x in heldout) and pts[0]["unanswerable_refused"]["k"] == sum(
        x < t for x in neg
    )
    other = A.operating_points(tune, [1, 2, 3], neg, keeps=(0.9,))
    assert other[0]["threshold"] == t  # changing the held-out data cannot move the threshold


def test_signal_report_and_markdown():
    tune, held = [8, 9, 10, 9, 8], [7, 9, 10]
    negs = {"far": [1, 2], "near": [6, 9]}
    r = A.signal_report("rerank top-1", tune, held, negs)
    assert r["auc_by_kind"]["far"] == 1.0 and r["auc_by_kind"]["near"] < r["auc_by_kind"]["far"]
    md = A.markdown([r], {"tune": 5, "heldout": 3, "neg": 4, "by_kind": {"far": 2, "near": 2}})
    assert "rerank top-1" in md and "AUC vs near" in md and "good refused (held-out)" in md


def test_decision_stability_counts_queries_whose_decision_depends_on_candidate_order():
    scores = [
        [0.50, 0.48, 0.52],  # always above 0.2: stable
        [0.05, 0.04, 0.06],  # always below: stable
        [0.25, 0.15, 0.26],  # natural order says answer, one shuffle says refuse: unstable
        [0.18, 0.30, 0.19],  # natural says refuse, one shuffle says answer: unstable
    ]
    r = A.decision_stability(scores, 0.2)
    assert r["queries"] == 4 and r["unstable_k"] == 2 and r["unstable"] == 0.5
    assert r["max_spread"] == pytest.approx(0.12) and r["mean_spread"] == pytest.approx((0.04 + 0.02 + 0.11 + 0.12) / 4)
    assert A.decision_stability([], 0.2)["unstable"] == 0.0
    assert A.decision_stability([[0.5, 0.5]], 0.2)["unstable_k"] == 0
