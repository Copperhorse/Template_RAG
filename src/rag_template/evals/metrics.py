"""
metrics.py: retrieval metrics and the statistics to compare systems honestly. Pure functions, no models.

Relevance is binary and judged per retrieved chunk (see gold.py). For a query with `n_gold` gold items:

    hit@k          1 if any of the top k chunks is relevant
    recall@k       share of the gold items covered by the top k chunks (equals hit@k when n_gold == 1)
    MRR@k          1 / rank of the first relevant chunk, 0 if none in the top k
    nDCG@k         binary gains, log2 discount; the ideal ranking puts min(R, k) relevant chunks first,
                   where R is the number of relevant chunks that exist in the index
    AP@k           average precision: sum of precision at each relevant rank, divided by min(R, k)

With a few dozen queries a difference of a few points is noise. `bootstrap_ci` gives a percentile interval
for a mean and `paired_bootstrap` the interval and one-sided p-value for "system A beats system B" on the
same queries (resampling queries, not chunks).
"""

import math
import random
from typing import Dict, Sequence, Set, Tuple


def hit_at_k(rel: Sequence[bool], k: int) -> float:
    return 1.0 if any(rel[:k]) else 0.0


def recall_at_k(covered: Sequence[Set[int]], n_gold: int, k: int) -> float:
    """`covered[i]` = indices of the gold items that the chunk at rank i+1 contains."""
    if n_gold == 0:
        return 0.0
    return len(set().union(*covered[:k])) / n_gold if covered[:k] else 0.0


def mrr_at_k(rel: Sequence[bool], k: int) -> float:
    for i, r in enumerate(rel[:k], 1):
        if r:
            return 1.0 / i
    return 0.0


def ndcg_at_k(rel: Sequence[bool], k: int, n_relevant: int) -> float:
    dcg = sum(1.0 / math.log2(i + 1) for i, r in enumerate(rel[:k], 1) if r)
    ideal = sum(1.0 / math.log2(i + 1) for i in range(1, min(n_relevant, k) + 1))
    return dcg / ideal if ideal else 0.0


def average_precision_at_k(rel: Sequence[bool], k: int, n_relevant: int) -> float:
    hits, total = 0, 0.0
    for i, r in enumerate(rel[:k], 1):
        if r:
            hits += 1
            total += hits / i
    denom = min(n_relevant, k)
    return total / denom if denom else 0.0


def query_metrics(
    rel: Sequence[bool],
    covered: Sequence[Set[int]],
    n_gold: int,
    n_relevant: int,
    ks: Sequence[int] = (1, 3, 5, 10, 20),
) -> Dict[str, float]:
    m = {f"recall@{k}": recall_at_k(covered, n_gold, k) for k in ks}
    m["mrr@10"] = mrr_at_k(rel, 10)
    m["ndcg@10"] = ndcg_at_k(rel, 10, n_relevant)
    m["map@10"] = average_precision_at_k(rel, 10, n_relevant)
    return m


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def bootstrap_ci(
    values: Sequence[float], n_resamples: int = 2000, alpha: float = 0.05, seed: int = 0
) -> Tuple[float, float, float]:
    """(mean, lower, upper) percentile bootstrap interval of the mean."""
    if not values:
        return 0.0, 0.0, 0.0
    rng = random.Random(seed)
    n = len(values)
    means = sorted(mean([values[rng.randrange(n)] for _ in range(n)]) for _ in range(n_resamples))
    return (
        mean(values),
        means[int(n_resamples * alpha / 2)],
        means[min(n_resamples - 1, int(n_resamples * (1 - alpha / 2)))],
    )


def paired_bootstrap(
    a: Sequence[float], b: Sequence[float], n_resamples: int = 5000, alpha: float = 0.05, seed: int = 0
) -> Dict[str, float]:
    """Compare two systems on the same queries. Returns the mean difference a - b, its percentile interval
    and `p`, the share of resamples in which a is not better than b (a small p supports "a beats b")."""
    assert len(a) == len(b), "paired comparison needs one value per query for both systems"
    if not a:
        return {"diff": 0.0, "lo": 0.0, "hi": 0.0, "p": 1.0}
    diffs = [x - y for x, y in zip(a, b)]
    rng = random.Random(seed)
    n = len(diffs)
    resampled = sorted(mean([diffs[rng.randrange(n)] for _ in range(n)]) for _ in range(n_resamples))
    return {
        "diff": mean(diffs),
        "lo": resampled[int(n_resamples * alpha / 2)],
        "hi": resampled[min(n_resamples - 1, int(n_resamples * (1 - alpha / 2)))],
        "p": sum(1 for d in resampled if d <= 0) / n_resamples,
    }


def percentile(values: Sequence[float], q: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    return s[min(len(s) - 1, int(round(q * (len(s) - 1))))]


def wilson_interval(successes: int, n: int, z: float = 1.96) -> Tuple[float, float, float]:
    """(rate, lower, upper) Wilson score interval for a proportion; sane for small n and rates near 0 or 1."""
    if n == 0:
        return 0.0, 0.0, 0.0
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return p, max(0.0, centre - half), min(1.0, centre + half)
