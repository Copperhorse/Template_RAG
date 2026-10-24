"""
rerank_stability.py: does a reranker's verdict depend on the order the candidates are shown in?

A pairwise cross-encoder scores each (query, passage) alone, so shuffling the list cannot change anything. A listwise
model reads every candidate in one causal pass, so earlier documents are seen without the later ones: in principle the
same candidates can be scored differently in another order. We shuffle the list several times and compare each
shuffled ranking with the ranking of the original order.
"""

import random
from typing import Callable, Dict, List, Sequence


def kendall_tau(a: Sequence[float], b: Sequence[float]) -> float:
    """Kendall tau-b between two score lists over the same items: 1 = same order, -1 = reversed. Ties are handled (tau-b),
    so two identical score lists give 1.0 even when they contain ties. If one list is constant and the other is not, the
    correlation is undefined and 0.0 is returned; two constant lists agree (1.0)."""
    n = len(a)
    if n < 2:
        return 1.0
    concordant = discordant = ties_a = ties_b = 0
    for i in range(n):
        for j in range(i + 1, n):
            da, db = a[i] - a[j], b[i] - b[j]
            ties_a += da == 0
            ties_b += db == 0
            if da * db > 0:
                concordant += 1
            elif da * db < 0:
                discordant += 1
    pairs = n * (n - 1) // 2
    if ties_a == pairs and ties_b == pairs:
        return 1.0
    denom = ((pairs - ties_a) * (pairs - ties_b)) ** 0.5
    return (concordant - discordant) / denom if denom else 0.0


def order_sensitivity(
    rerank: Callable[[str, List[str]], List[float]],
    query: str,
    texts: Sequence[str],
    n_shuffles: int = 5,
    seed: int = 0,
) -> Dict[str, float]:
    """Scores of the original order are the reference. For each shuffle: tau against the reference, whether the top-1 item
    is the same, and the largest absolute change of any item's score."""
    base = rerank(query, list(texts))
    rng = random.Random(seed)
    taus, top1, deltas = [], [], []
    for _ in range(n_shuffles):
        perm = list(range(len(texts)))
        rng.shuffle(perm)
        shuffled = rerank(query, [texts[i] for i in perm])
        again = [0.0] * len(texts)
        for pos, orig in enumerate(perm):
            again[orig] = shuffled[pos]
        taus.append(kendall_tau(base, again))
        top1.append(max(range(len(texts)), key=base.__getitem__) == max(range(len(texts)), key=again.__getitem__))
        deltas.append(max(abs(x - y) for x, y in zip(base, again)))
    return {"tau": sum(taus) / len(taus), "top1_agree": sum(top1) / len(top1), "max_score_delta": max(deltas)}
