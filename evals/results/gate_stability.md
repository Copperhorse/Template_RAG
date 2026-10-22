# Does candidate order change the relevance gate's decision?

jinaai/jina-reranker-v3.5, 20 candidates, 70 answerable and 59 unanswerable questions. The best score is re-computed under 5 random candidate orders; the first is the natural fused order the system uses. A query is *unstable* when some order lands on the other side of the threshold.

| threshold | group | queries | unstable | largest score spread | mean spread |
|---:|---|---:|---:|---:|---:|
| 0.183 | answerable | 70 | 0% (0) | 0.234 | 0.127 |
| 0.183 | unanswerable | 59 | 32% (19) | 0.277 | 0.091 |
| 0.211 | answerable | 70 | 6% (4) | 0.234 | 0.127 |
| 0.211 | unanswerable | 59 | 24% (14) | 0.277 | 0.091 |
| 0.304 | answerable | 70 | 11% (8) | 0.234 | 0.127 |
| 0.304 | unanswerable | 59 | 8% (5) | 0.277 | 0.091 |

## Does averaging over candidate orders help?

ROC-AUC for separating answerable from unanswerable questions, 95% bootstrap interval. More passes cost proportionally more latency.

| signal | AUC (95% CI) |
|---|---:|
| natural order (one pass) | 0.984 (0.966-0.997) |
| mean over 2 orders (2 passes) | 0.986 (0.970-0.997) |
| mean over 3 orders (3 passes) | 0.987 (0.972-0.998) |
| mean over 6 orders (6 passes) | 0.989 (0.976-0.998) |
| dense cosine top-1 (order-free, no reranker) | 0.919 (0.863-0.963) |
