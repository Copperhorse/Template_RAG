# Can retrieval scores detect unanswerable questions?

Answerable: 70 hand-written (thresholds are chosen from these) + 149 synthetic (never used to choose anything). Unanswerable: 59 (far 15, legacy 15, near 14, premise 15). AUC 0.5 = chance, 1.0 = perfect.

| signal | AUC (95% CI) | AUC vs far | AUC vs legacy | AUC vs near | AUC vs premise | median answerable | median unanswerable |
|---|---:|---:|---:|---:|---:|---:|---:|
| rerank top-1 (jina-reranker-v3.5) | 0.96 (0.94-0.98) | 0.99 | 0.95 | 0.97 | 0.94 | 0.443 | 0.0785 |
| rerank mean top-3 (jina-reranker-v3.5) | 0.96 (0.93-0.98) | 1.00 | 0.95 | 0.97 | 0.92 | 0.241 | 0.0284 |
| dense cosine top-1 | 0.92 (0.87-0.96) | 1.00 | 0.93 | 0.95 | 0.79 | 0.77 | 0.695 |
| RRF top score | 0.73 (0.65-0.81) | 0.89 | 0.78 | 0.69 | 0.56 | 0.0323 | 0.0308 |
| question-term coverage (top 5) | 0.69 (0.62-0.77) | 0.92 | 0.66 | 0.64 | 0.55 | 0.667 | 0.5 |
| rerank top-1 (ms-marco-MiniLM-L-6-v2) | 0.86 (0.81-0.92) | 1.00 | 0.85 | 0.91 | 0.70 | -0.33 | -7.16 |
| rerank mean top-3 (ms-marco-MiniLM-L-6-v2) | 0.84 (0.78-0.90) | 1.00 | 0.82 | 0.91 | 0.64 | -2.27 | -8.08 |

## Operating points

A threshold keeps (does not refuse) the target share of the hand-written answerable queries. *Held-out refused* is the share of synthetic answerable queries it would wrongly refuse; *unanswerable refused* is the benefit.

### rerank top-1 (jina-reranker-v3.5)

| keep target | threshold | good refused (tuning set) | good refused (held-out) | unanswerable refused |
|---:|---:|---:|---:|---:|
| 99% | 0.183 | 0% (0/70) | 8% (12/149) | 75% (44/59) |
| 95% | 0.211 | 4% (3/70) | 9% (14/149) | 83% (49/59) |
| 90% | 0.304 | 9% (6/70) | 20% (30/149) | 97% (57/59) |
| 80% | 0.333 | 19% (13/70) | 24% (36/149) | 98% (58/59) |

### rerank mean top-3 (jina-reranker-v3.5)

| keep target | threshold | good refused (tuning set) | good refused (held-out) | unanswerable refused |
|---:|---:|---:|---:|---:|
| 99% | 0.142 | 0% (0/70) | 12% (18/149) | 88% (52/59) |
| 95% | 0.156 | 4% (3/70) | 16% (24/149) | 95% (56/59) |
| 90% | 0.163 | 9% (6/70) | 20% (30/149) | 95% (56/59) |
| 80% | 0.202 | 19% (13/70) | 38% (57/149) | 97% (57/59) |

### dense cosine top-1

| keep target | threshold | good refused (tuning set) | good refused (held-out) | unanswerable refused |
|---:|---:|---:|---:|---:|
| 99% | 0.696 | 0% (0/70) | 0% (0/149) | 51% (30/59) |
| 95% | 0.718 | 4% (3/70) | 4% (6/149) | 71% (42/59) |
| 90% | 0.725 | 9% (6/70) | 7% (11/149) | 78% (46/59) |
| 80% | 0.739 | 19% (13/70) | 21% (31/149) | 85% (50/59) |

### RRF top score

| keep target | threshold | good refused (tuning set) | good refused (held-out) | unanswerable refused |
|---:|---:|---:|---:|---:|
| 99% | 0.0304 | 0% (0/70) | 17% (26/149) | 41% (24/59) |
| 95% | 0.0313 | 3% (2/70) | 24% (36/149) | 56% (33/59) |
| 90% | 0.0318 | 7% (5/70) | 33% (49/149) | 61% (36/59) |
| 80% | 0.032 | 14% (10/70) | 43% (64/149) | 68% (40/59) |

### question-term coverage (top 5)

| keep target | threshold | good refused (tuning set) | good refused (held-out) | unanswerable refused |
|---:|---:|---:|---:|---:|
| 99% | 0.25 | 0% (0/70) | 6% (9/149) | 14% (8/59) |
| 95% | 0.5 | 4% (3/70) | 26% (38/149) | 44% (26/59) |
| 90% | 0.5 | 4% (3/70) | 26% (38/149) | 44% (26/59) |
| 80% | 0.667 | 17% (12/70) | 60% (90/149) | 73% (43/59) |

### rerank top-1 (ms-marco-MiniLM-L-6-v2)

| keep target | threshold | good refused (tuning set) | good refused (held-out) | unanswerable refused |
|---:|---:|---:|---:|---:|
| 99% | -6.15 | 0% (0/70) | 9% (13/149) | 54% (32/59) |
| 95% | -2.85 | 4% (3/70) | 30% (44/149) | 80% (47/59) |
| 90% | -2.64 | 9% (6/70) | 30% (45/149) | 83% (49/59) |
| 80% | -1.58 | 19% (13/70) | 50% (74/149) | 83% (49/59) |

### rerank mean top-3 (ms-marco-MiniLM-L-6-v2)

| keep target | threshold | good refused (tuning set) | good refused (held-out) | unanswerable refused |
|---:|---:|---:|---:|---:|
| 99% | -7.39 | 0% (0/70) | 7% (10/149) | 54% (32/59) |
| 95% | -5.32 | 4% (3/70) | 20% (30/149) | 68% (40/59) |
| 90% | -4.29 | 9% (6/70) | 30% (45/149) | 76% (45/59) |
| 80% | -3.6 | 19% (13/70) | 36% (53/149) | 83% (49/59) |

