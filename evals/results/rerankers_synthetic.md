# Reranker comparison

149 answerable queries; relevance = the chunk holds the gold snippet; ± = 95% bootstrap half-width; every system is hybrid RRF (EmbeddingGemma 2 + BM25) plus the named reranker. `replace` orders candidates by the reranker alone, `fuse` makes it a third voter next to dense and BM25, `top N` is how many fused candidates it reads.

> Gold: `evals/gold/synthetic.jsonl`. Embedder loaded: 525 MB GPU memory before any reranker.

## Memory

| reranker | GPU memory to load (MB) |
|---|---:|
| jina-reranker-v3.5 | 1139 |
| ms-marco-MiniLM-L-6-v2 | 87 |

## All systems

| system | recall@1 | recall@3 | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 | map@10 | ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| RRF | 55.0 ±8.1 | 72.5 ±7.4 | 81.2 ±6.4 | 87.9 ±5.0 | 93.3 ±4.0 | 65.7 ±6.5 | 70.8 ±5.8 | 65.3 ±6.4 | 26 |
| RRF + jina-reranker-v3.5 (replace, top 20) | 80.5 ±6.4 | 91.3 ±4.4 | 92.6 ±4.4 | 92.6 ±4.4 | 93.3 ±4.0 | 85.9 ±4.9 | 87.5 ±4.5 | 85.7 ±4.8 | 1039 |
| RRF + jina-reranker-v3.5 (fuse, top 20) | 64.4 ±8.1 | 82.6 ±6.4 | 89.3 ±5.0 | 91.9 ±4.4 | 93.3 ±4.0 | 74.5 ±6.0 | 78.7 ±5.2 | 74.4 ±5.9 | 25 |
| RRF + ms-marco-MiniLM-L-6-v2 (replace, top 20) | 50.3 ±7.7 | 69.8 ±7.0 | 74.5 ±7.0 | 91.3 ±4.7 | 93.3 ±4.0 | 62.4 ±6.2 | 69.2 ±5.3 | 62.2 ±6.2 | 150 |
| RRF + ms-marco-MiniLM-L-6-v2 (fuse, top 20) | 55.7 ±8.1 | 75.8 ±7.0 | 83.2 ±5.7 | 89.9 ±4.7 | 93.3 ±4.0 | 66.9 ±6.4 | 72.3 ±5.6 | 66.5 ±6.4 | 24 |

**Reading the `ms/query` column:** scores were cached within the run, because `replace` and `fuse` read identical candidates, so the `fuse` rows show only retrieval plus fusion (~21 ms) and exclude the reranker. The cost of a reranker is the `replace` row's latency at the same `top N`.

Peak GPU memory per system (MB, includes the embedder and the LLM-free eval process): RRF + jina-reranker-v3.5 (replace, top 20): 2542, RRF + jina-reranker-v3.5 (fuse, top 20): 1754, RRF + ms-marco-MiniLM-L-6-v2 (replace, top 20): 1920, RRF + ms-marco-MiniLM-L-6-v2 (fuse, top 20): 1754

## Paired differences vs plain RRF, all queries (points; bold = 95% interval excludes 0)

| comparison (A − B) | Δ recall@1 | Δ recall@5 | Δ mrr@10 |
|---|---:|---:|---:|
| RRF + jina-reranker-v3.5 (replace, top 20) vs RRF | **+25.5** [+17.4, +33.6] p=0.000 | **+11.4** [+6.7, +16.8] p=0.000 | **+20.2** [+14.9, +25.7] p=0.000 |
| RRF + jina-reranker-v3.5 (fuse, top 20) vs RRF | **+9.4** [+4.7, +14.1] p=0.000 | **+8.1** [+4.0, +12.8] p=0.000 | **+8.9** [+6.1, +12.0] p=0.000 |
| RRF + ms-marco-MiniLM-L-6-v2 (replace, top 20) vs RRF | -4.7 [-13.4, +4.0] p=0.881 | **-6.7** [-12.8, -0.7] p=0.994 | -3.2 [-9.1, +2.6] p=0.873 |
| RRF + ms-marco-MiniLM-L-6-v2 (fuse, top 20) vs RRF | +0.7 [-6.0, +7.4] p=0.464 | +2.0 [-2.0, +6.0] p=0.200 | +1.2 [-2.8, +5.3] p=0.269 |

## Paired differences vs plain RRF, code queries (points; bold = 95% interval excludes 0)

| comparison (A − B) | Δ recall@1 | Δ recall@5 | Δ mrr@10 |
|---|---:|---:|---:|
| RRF + jina-reranker-v3.5 (replace, top 20) vs RRF | **+27.0** [+18.0, +36.0] p=0.000 | **+8.1** [+3.6, +13.5] p=0.000 | **+19.4** [+13.5, +25.8] p=0.000 |
| RRF + jina-reranker-v3.5 (fuse, top 20) vs RRF | **+9.0** [+3.6, +14.4] p=0.000 | **+6.3** [+1.8, +10.8] p=0.001 | **+7.7** [+4.9, +10.9] p=0.000 |
| RRF + ms-marco-MiniLM-L-6-v2 (replace, top 20) vs RRF | -5.4 [-15.3, +4.5] p=0.873 | -4.5 [-11.7, +1.8] p=0.929 | -3.7 [-10.7, +3.1] p=0.855 |
| RRF + ms-marco-MiniLM-L-6-v2 (fuse, top 20) vs RRF | +0.9 [-7.2, +9.0] p=0.456 | +1.8 [-2.7, +6.3] p=0.268 | +1.6 [-3.6, +6.6] p=0.273 |

## Paired differences vs plain RRF, documentation queries (points; bold = 95% interval excludes 0)

| comparison (A − B) | Δ recall@1 | Δ recall@5 | Δ mrr@10 |
|---|---:|---:|---:|
| RRF + jina-reranker-v3.5 (replace, top 20) vs RRF | **+21.1** [+7.9, +36.8] p=0.002 | **+21.1** [+7.9, +34.2] p=0.000 | **+22.6** [+12.0, +33.5] p=0.000 |
| RRF + jina-reranker-v3.5 (fuse, top 20) vs RRF | **+10.5** [+2.6, +21.1] p=0.015 | **+13.2** [+2.6, +23.7] p=0.004 | **+12.2** [+5.8, +19.7] p=0.000 |
| RRF + ms-marco-MiniLM-L-6-v2 (replace, top 20) vs RRF | -2.6 [-18.4, +13.2] p=0.688 | **-13.2** [-23.7, -2.6] p=1.000 | -1.9 [-11.5, +7.6] p=0.647 |
| RRF + ms-marco-MiniLM-L-6-v2 (fuse, top 20) vs RRF | +0.0 [-7.9, +7.9] p=0.644 | +2.6 [-5.3, +10.5] p=0.399 | +0.3 [-4.5, +4.8] p=0.428 |

## jina-reranker-v3.5 vs ms-marco-MiniLM-L-6-v2, head to head (points)

| comparison (A − B) | Δ recall@1 | Δ recall@5 | Δ mrr@10 |
|---|---:|---:|---:|
| jina-reranker-v3.5 vs ms-marco-MiniLM-L-6-v2 (replace, top 20) | **+30.2** [+22.8, +38.3] p=0.000 | **+18.1** [+12.1, +24.8] p=0.000 | **+23.5** [+18.1, +29.0] p=0.000 |
| jina-reranker-v3.5 vs ms-marco-MiniLM-L-6-v2 (fuse, top 20) | **+8.7** [+2.7, +14.8] p=0.002 | **+6.0** [+2.0, +10.7] p=0.004 | **+7.6** [+3.9, +11.4] p=0.000 |
