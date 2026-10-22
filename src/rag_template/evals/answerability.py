"""
answerability.py: can retrieval scores tell that a question has no answer in the corpus?

Before the LLM is called, every query already has numbers attached to it: how well the best chunk scored with the
reranker, how close the nearest vector was, whether BM25 found anything. If those numbers separate answerable from
unanswerable questions, a cheap pre-LLM gate could refuse them (and save the call). This module measures how well each
signal separates the two groups, without ever fitting on the groups it reports:

  1. A signal is a number where HIGHER means "more likely answerable".
  2. ROC-AUC (probability that a random answerable query scores above a random unanswerable one; ties count half), with a
     bootstrap interval that resamples both groups.
  3. Operating points. The threshold is chosen from the answerable queries alone, as the value that keeps a given share
     (99/95/90/80%) of the *hand-written* answerable queries. It is then applied to answerable queries it was NOT chosen
     on (the synthetic set) to estimate how many good questions it would wrongly refuse, and to the unanswerable queries
     to estimate how many it would correctly refuse. Wilson 95% intervals; no number here is tuned on its own test data.
"""

import random
from typing import Dict, List, Sequence, Tuple

from rag_template.evals.metrics import wilson_interval


def auc(pos: Sequence[float], neg: Sequence[float]) -> float:
    """P(pos > neg) + 0.5 P(pos == neg). 1.0 = perfect separation, 0.5 = chance."""
    if not pos or not neg:
        return 0.5
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def bootstrap_auc(pos: Sequence[float], neg: Sequence[float], n_resamples: int = 1000, alpha: float = 0.05, seed: int = 0) -> Tuple[float, float, float]:
    rng = random.Random(seed)
    stats = sorted(auc([rng.choice(pos) for _ in pos], [rng.choice(neg) for _ in neg]) for _ in range(n_resamples)) if pos and neg else [0.5]
    return auc(pos, neg), stats[int(len(stats) * alpha / 2)], stats[min(len(stats) - 1, int(len(stats) * (1 - alpha / 2)))]


def keep_threshold(pos: Sequence[float], keep: float) -> float:
    """The largest threshold t such that at least `keep` of `pos` scores are >= t."""
    s = sorted(pos)
    return s[min(len(s) - 1, max(0, int((1 - keep) * len(s))))] if s else 0.0


def rate(k: int, n: int) -> Dict[str, float]:
    p, lo, hi = wilson_interval(k, n)
    return {"k": k, "n": n, "rate": p, "lo": lo, "hi": hi}


def operating_points(tune_pos: Sequence[float], heldout_pos: Sequence[float], neg: Sequence[float], keeps: Sequence[float] = (0.99, 0.95, 0.90, 0.80)) -> List[Dict]:
    out = []
    for keep in keeps:
        t = keep_threshold(tune_pos, keep)
        out.append({
            "keep_target": keep, "threshold": t,
            "tune_refused": rate(sum(x < t for x in tune_pos), len(tune_pos)),  # good questions refused, on the set t was chosen from
            "heldout_refused": rate(sum(x < t for x in heldout_pos), len(heldout_pos)),  # good questions refused, on data t never saw
            "unanswerable_refused": rate(sum(x < t for x in neg), len(neg)),  # the point of the gate
        })
    return out


def signal_report(name: str, tune_pos: Sequence[float], heldout_pos: Sequence[float], negs_by_kind: Dict[str, Sequence[float]]) -> Dict:
    all_neg = [x for v in negs_by_kind.values() for x in v]
    everything_pos = list(tune_pos) + list(heldout_pos)
    a, lo, hi = bootstrap_auc(everything_pos, all_neg)
    return {
        "signal": name, "auc": a, "auc_lo": lo, "auc_hi": hi,
        "auc_by_kind": {k: auc(everything_pos, v) for k, v in negs_by_kind.items() if v},
        "points": operating_points(tune_pos, heldout_pos, all_neg),
        "pos_median": sorted(everything_pos)[len(everything_pos) // 2] if everything_pos else 0.0,
        "neg_median": sorted(all_neg)[len(all_neg) // 2] if all_neg else 0.0,
    }


def markdown(reports: Sequence[Dict], counts: Dict[str, int]) -> str:
    def c(d):
        return f"{100 * d['rate']:.0f}% ({d['k']}/{d['n']})"

    lines = [
        "# Can retrieval scores detect unanswerable questions?", "",
        f"Answerable: {counts['tune']} hand-written (thresholds are chosen from these) + {counts['heldout']} synthetic (never used to choose anything). "
        f"Unanswerable: {counts['neg']} ({', '.join(f'{k} {v}' for k, v in counts['by_kind'].items())}). AUC 0.5 = chance, 1.0 = perfect.", "",
        "| signal | AUC (95% CI) | " + " | ".join(f"AUC vs {k}" for k in counts["by_kind"]) + " | median answerable | median unanswerable |",
        "|---|---:|" + "---:|" * len(counts["by_kind"]) + "---:|---:|",
    ]
    for r in reports:
        lines.append(f"| {r['signal']} | {r['auc']:.2f} ({r['auc_lo']:.2f}-{r['auc_hi']:.2f}) | " + " | ".join(f"{r['auc_by_kind'].get(k, float('nan')):.2f}" for k in counts["by_kind"]) + f" | {r['pos_median']:.3g} | {r['neg_median']:.3g} |")
    lines += ["", "## Operating points", "", "A threshold keeps (does not refuse) the target share of the hand-written answerable queries. "
              "*Held-out refused* is the share of synthetic answerable queries it would wrongly refuse; *unanswerable refused* is the benefit.", ""]
    for r in reports:
        lines += [f"### {r['signal']}", "", "| keep target | threshold | good refused (tuning set) | good refused (held-out) | unanswerable refused |", "|---:|---:|---:|---:|---:|"]
        lines += [f"| {100 * p['keep_target']:.0f}% | {p['threshold']:.3g} | {c(p['tune_refused'])} | {c(p['heldout_refused'])} | {c(p['unanswerable_refused'])} |" for p in r["points"]]
        lines.append("")
    return "\n".join(lines)


def decision_stability(top1_by_order: Sequence[Sequence[float]], threshold: float) -> Dict[str, float]:
    """How often does reordering the candidates change the refuse/answer decision at `threshold`?

    `top1_by_order[i]` holds one query's best score under several candidate orders (the first is the natural, fused order the
    system actually uses). A query is *unstable* when some order lands on the other side of the threshold than the natural
    one. Returns the share of unstable queries, the largest spread of one query's scores, and the mean spread."""
    n = len(top1_by_order)
    unstable = sum(1 for scores in top1_by_order if any((x >= threshold) != (scores[0] >= threshold) for x in scores[1:]))
    spreads = [max(scores) - min(scores) for scores in top1_by_order]
    return {"queries": n, "unstable": unstable / n if n else 0.0, "unstable_k": unstable, "max_spread": max(spreads, default=0.0), "mean_spread": sum(spreads) / n if n else 0.0}
