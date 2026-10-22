# Reranker comparison

70 answerable queries; relevance = the chunk holds the gold snippet; ± = 95% bootstrap half-width; every system is hybrid RRF (EmbeddingGemma 2 + BM25) plus the named reranker. `replace` orders candidates by the reranker alone, `fuse` makes it a third voter next to dense and BM25, `top N` is how many fused candidates it reads.

> Gold: `evals/gold/handwritten.jsonl`. Embedder loaded: 525 MB GPU memory before any reranker.

## Memory

| reranker | GPU memory to load (MB) |
|---|---:|
| jina-reranker-v3.5 | 1139 |
| ms-marco-MiniLM-L-6-v2 | 87 |

## All systems

| system | recall@1 | recall@3 | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 | map@10 | ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| RRF | 40.0 ±11.4 | 68.6 ±11.4 | 78.6 ±10.0 | 88.6 ±7.9 | 94.3 ±5.0 | 55.7 ±9.4 | 63.7 ±8.5 | 55.7 ±9.4 | 55 |
| RRF + jina-reranker-v3.5 (replace, top 10) | 60.0 ±11.4 | 78.6 ±10.0 | 84.3 ±8.6 | 88.6 ±7.9 | 94.3 ±5.0 | 70.1 ±9.3 | 74.6 ±8.5 | 70.1 ±9.3 | 518 |
| RRF + jina-reranker-v3.5 (replace, top 20) | 58.6 ±11.4 | 81.4 ±9.3 | 88.6 ±7.9 | 94.3 ±5.0 | 94.3 ±5.0 | 71.1 ±8.7 | 76.8 ±7.3 | 71.1 ±8.7 | 1195 |
| RRF + jina-reranker-v3.5 (replace, top 40) | 60.0 ±11.4 | 84.3 ±8.6 | 90.0 ±7.1 | 95.7 ±5.0 | 98.6 ±2.1 | 72.4 ±8.3 | 78.1 ±6.8 | 72.4 ±8.3 | 2824 |
| RRF + jina-reranker-v3.5 (replace, top 60) | 61.4 ±11.4 | 84.3 ±8.6 | 88.6 ±7.9 | 97.1 ±3.6 | 100.0 ±0.0 | 73.0 ±8.4 | 78.8 ±6.8 | 73.0 ±8.4 | 5415 |
| RRF + jina-reranker-v3.5 (fuse, top 10) | 45.7 ±12.1 | 74.3 ±10.0 | 80.0 ±9.3 | 88.6 ±7.9 | 94.3 ±5.0 | 61.3 ±9.2 | 68.0 ±8.3 | 61.3 ±9.2 | 23 |
| RRF + jina-reranker-v3.5 (fuse, top 20) | 45.7 ±12.1 | 75.7 ±10.0 | 81.4 ±9.3 | 92.9 ±6.4 | 94.3 ±5.0 | 62.7 ±8.7 | 70.0 ±7.5 | 62.7 ±8.7 | 21 |
| RRF + jina-reranker-v3.5 (fuse, top 40) | 45.7 ±12.1 | 75.7 ±10.0 | 82.9 ±9.3 | 94.3 ±5.0 | 98.6 ±2.1 | 62.8 ±8.7 | 70.5 ±7.3 | 62.8 ±8.7 | 21 |
| RRF + jina-reranker-v3.5 (fuse, top 60) | 45.7 ±12.1 | 75.7 ±10.0 | 82.9 ±9.3 | 94.3 ±5.0 | 100.0 ±0.0 | 63.1 ±8.6 | 70.7 ±7.2 | 63.1 ±8.6 | 21 |
| RRF + ms-marco-MiniLM-L-6-v2 (replace, top 10) | 35.7 ±10.7 | 64.3 ±11.4 | 77.1 ±10.0 | 88.6 ±7.9 | 94.3 ±5.0 | 51.3 ±9.1 | 60.2 ±8.1 | 51.3 ±9.1 | 85 |
| RRF + ms-marco-MiniLM-L-6-v2 (replace, top 20) | 35.7 ±10.7 | 62.9 ±11.4 | 74.3 ±10.0 | 84.3 ±8.6 | 94.3 ±5.0 | 50.3 ±9.4 | 58.5 ±8.5 | 50.3 ±9.4 | 146 |
| RRF + ms-marco-MiniLM-L-6-v2 (replace, top 40) | 35.7 ±10.7 | 61.4 ±11.4 | 75.7 ±10.0 | 84.3 ±8.6 | 88.6 ±7.9 | 50.2 ±9.3 | 58.4 ±8.4 | 50.2 ±9.3 | 233 |
| RRF + ms-marco-MiniLM-L-6-v2 (replace, top 60) | 35.7 ±10.7 | 61.4 ±11.4 | 74.3 ±10.0 | 82.9 ±9.3 | 88.6 ±7.9 | 50.0 ±9.4 | 57.9 ±8.5 | 50.0 ±9.4 | 313 |
| RRF + ms-marco-MiniLM-L-6-v2 (fuse, top 10) | 37.1 ±11.4 | 68.6 ±10.7 | 78.6 ±9.3 | 88.6 ±7.9 | 94.3 ±5.0 | 54.1 ±9.1 | 62.4 ±8.1 | 54.1 ±9.1 | 21 |
| RRF + ms-marco-MiniLM-L-6-v2 (fuse, top 20) | 37.1 ±11.4 | 65.7 ±11.4 | 77.1 ±10.0 | 84.3 ±8.6 | 94.3 ±5.0 | 53.1 ±9.4 | 60.8 ±8.7 | 53.1 ±9.4 | 21 |
| RRF + ms-marco-MiniLM-L-6-v2 (fuse, top 40) | 37.1 ±11.4 | 67.1 ±11.4 | 78.6 ±9.3 | 84.3 ±8.6 | 95.7 ±5.0 | 53.3 ±9.3 | 60.9 ±8.5 | 53.3 ±9.3 | 22 |
| RRF + ms-marco-MiniLM-L-6-v2 (fuse, top 60) | 37.1 ±11.4 | 67.1 ±11.4 | 78.6 ±9.3 | 84.3 ±8.6 | 94.3 ±5.0 | 53.3 ±9.3 | 60.9 ±8.5 | 53.3 ±9.3 | 21 |

Peak GPU memory per system (MB, includes the embedder and the LLM-free eval process): RRF + jina-reranker-v3.5 (replace, top 10): 2074, RRF + jina-reranker-v3.5 (replace, top 20): 2470, RRF + jina-reranker-v3.5 (replace, top 40): 3484, RRF + jina-reranker-v3.5 (replace, top 60): 4514, RRF + jina-reranker-v3.5 (fuse, top 10): 1754, RRF + jina-reranker-v3.5 (fuse, top 20): 1754, RRF + jina-reranker-v3.5 (fuse, top 40): 1754, RRF + jina-reranker-v3.5 (fuse, top 60): 1754, RRF + ms-marco-MiniLM-L-6-v2 (replace, top 10): 1836, RRF + ms-marco-MiniLM-L-6-v2 (replace, top 20): 1921, RRF + ms-marco-MiniLM-L-6-v2 (replace, top 40): 2023, RRF + ms-marco-MiniLM-L-6-v2 (replace, top 60): 2023, RRF + ms-marco-MiniLM-L-6-v2 (fuse, top 10): 1754, RRF + ms-marco-MiniLM-L-6-v2 (fuse, top 20): 1754, RRF + ms-marco-MiniLM-L-6-v2 (fuse, top 40): 1754, RRF + ms-marco-MiniLM-L-6-v2 (fuse, top 60): 1754

## Paired differences vs plain RRF, all queries (points; bold = 95% interval excludes 0)

| comparison (A − B) | Δ recall@1 | Δ recall@5 | Δ mrr@10 |
|---|---:|---:|---:|
| RRF + jina-reranker-v3.5 (replace, top 10) vs RRF | **+20.0** [+10.0, +30.0] p=0.000 | +5.7 [-1.4, +12.9] p=0.072 | **+14.4** [+7.7, +21.6] p=0.000 |
| RRF + jina-reranker-v3.5 (replace, top 20) vs RRF | **+18.6** [+8.6, +28.6] p=0.000 | **+10.0** [+1.4, +18.6] p=0.010 | **+15.4** [+8.6, +22.6] p=0.000 |
| RRF + jina-reranker-v3.5 (replace, top 40) vs RRF | **+20.0** [+10.0, +30.0] p=0.000 | **+11.4** [+2.9, +21.4] p=0.011 | **+16.7** [+9.3, +24.3] p=0.000 |
| RRF + jina-reranker-v3.5 (replace, top 60) vs RRF | **+21.4** [+11.4, +32.9] p=0.000 | **+10.0** [+1.4, +18.6] p=0.021 | **+17.3** [+9.7, +25.1] p=0.000 |
| RRF + jina-reranker-v3.5 (fuse, top 10) vs RRF | **+5.7** [+1.4, +11.4] p=0.017 | +1.4 [-2.9, +5.7] p=0.385 | **+5.6** [+2.3, +9.5] p=0.000 |
| RRF + jina-reranker-v3.5 (fuse, top 20) vs RRF | **+5.7** [+1.4, +11.4] p=0.017 | +2.9 [-2.9, +8.6] p=0.216 | **+6.9** [+3.6, +10.9] p=0.000 |
| RRF + jina-reranker-v3.5 (fuse, top 40) vs RRF | **+5.7** [+1.4, +11.4] p=0.017 | +4.3 [+0.0, +10.0] p=0.044 | **+7.1** [+3.7, +11.1] p=0.000 |
| RRF + jina-reranker-v3.5 (fuse, top 60) vs RRF | **+5.7** [+1.4, +11.4] p=0.017 | +4.3 [+0.0, +10.0] p=0.044 | **+7.3** [+3.9, +11.4] p=0.000 |
| RRF + ms-marco-MiniLM-L-6-v2 (replace, top 10) vs RRF | -4.3 [-14.3, +4.3] p=0.854 | -1.4 [-7.1, +4.3] p=0.740 | -4.5 [-11.0, +2.3] p=0.903 |
| RRF + ms-marco-MiniLM-L-6-v2 (replace, top 20) vs RRF | -4.3 [-14.3, +4.3] p=0.854 | -4.3 [-11.4, +2.9] p=0.909 | -5.4 [-12.1, +1.4] p=0.942 |
| RRF + ms-marco-MiniLM-L-6-v2 (replace, top 40) vs RRF | -4.3 [-14.3, +4.3] p=0.854 | -2.9 [-11.4, +4.3] p=0.806 | -5.5 [-12.3, +1.5] p=0.940 |
| RRF + ms-marco-MiniLM-L-6-v2 (replace, top 60) vs RRF | -4.3 [-14.3, +4.3] p=0.854 | -4.3 [-11.4, +2.9] p=0.906 | -5.7 [-12.6, +1.3] p=0.945 |
| RRF + ms-marco-MiniLM-L-6-v2 (fuse, top 10) vs RRF | -2.9 [-10.0, +4.3] p=0.848 | +0.0 [-4.3, +4.3] p=0.645 | -1.6 [-6.3, +2.6] p=0.768 |
| RRF + ms-marco-MiniLM-L-6-v2 (fuse, top 20) vs RRF | -2.9 [-10.0, +4.3] p=0.848 | -1.4 [-5.7, +2.9] p=0.809 | -2.6 [-7.4, +1.8] p=0.867 |
| RRF + ms-marco-MiniLM-L-6-v2 (fuse, top 40) vs RRF | -2.9 [-10.0, +4.3] p=0.848 | +0.0 [-5.7, +5.7] p=0.587 | -2.4 [-7.2, +2.0] p=0.852 |
| RRF + ms-marco-MiniLM-L-6-v2 (fuse, top 60) vs RRF | -2.9 [-10.0, +4.3] p=0.848 | +0.0 [-5.7, +5.7] p=0.587 | -2.4 [-7.2, +2.0] p=0.852 |

## Paired differences vs plain RRF, code queries (points; bold = 95% interval excludes 0)

| comparison (A − B) | Δ recall@1 | Δ recall@5 | Δ mrr@10 |
|---|---:|---:|---:|
| RRF + jina-reranker-v3.5 (replace, top 10) vs RRF | **+25.7** [+11.4, +40.0] p=0.000 | +5.7 [+0.0, +14.3] p=0.123 | **+16.5** [+6.9, +27.1] p=0.000 |
| RRF + jina-reranker-v3.5 (replace, top 20) vs RRF | **+22.9** [+8.6, +37.1] p=0.000 | +8.6 [+0.0, +20.0] p=0.043 | **+16.0** [+6.4, +26.4] p=0.000 |
| RRF + jina-reranker-v3.5 (replace, top 40) vs RRF | **+25.7** [+11.4, +40.0] p=0.000 | **+11.4** [+2.9, +22.9] p=0.013 | **+18.9** [+8.4, +30.2] p=0.000 |
| RRF + jina-reranker-v3.5 (replace, top 60) vs RRF | **+25.7** [+11.4, +40.0] p=0.000 | **+11.4** [+2.9, +22.9] p=0.013 | **+19.1** [+8.6, +30.5] p=0.000 |
| RRF + jina-reranker-v3.5 (fuse, top 10) vs RRF | +8.6 [+0.0, +20.0] p=0.042 | +0.0 [+0.0, +0.0] p=1.000 | **+5.9** [+0.7, +12.3] p=0.008 |
| RRF + jina-reranker-v3.5 (fuse, top 20) vs RRF | +8.6 [+0.0, +20.0] p=0.042 | +2.9 [+0.0, +8.6] p=0.365 | **+6.8** [+1.7, +13.3] p=0.002 |
| RRF + jina-reranker-v3.5 (fuse, top 40) vs RRF | +8.6 [+0.0, +20.0] p=0.042 | +2.9 [+0.0, +8.6] p=0.365 | **+7.1** [+1.9, +13.7] p=0.001 |
| RRF + jina-reranker-v3.5 (fuse, top 60) vs RRF | +8.6 [+0.0, +20.0] p=0.042 | +2.9 [+0.0, +8.6] p=0.365 | **+7.1** [+1.9, +13.7] p=0.001 |
| RRF + ms-marco-MiniLM-L-6-v2 (replace, top 10) vs RRF | -8.6 [-20.0, +0.0] p=1.000 | -5.7 [-17.1, +5.7] p=0.905 | **-11.5** [-19.8, -4.4] p=1.000 |
| RRF + ms-marco-MiniLM-L-6-v2 (replace, top 20) vs RRF | -8.6 [-20.0, +0.0] p=1.000 | -11.4 [-25.7, +0.0] p=0.977 | **-13.0** [-21.3, -6.0] p=1.000 |
| RRF + ms-marco-MiniLM-L-6-v2 (replace, top 40) vs RRF | -8.6 [-20.0, +0.0] p=1.000 | -11.4 [-25.7, +0.0] p=0.977 | **-13.8** [-22.2, -6.6] p=1.000 |
| RRF + ms-marco-MiniLM-L-6-v2 (replace, top 60) vs RRF | -8.6 [-20.0, +0.0] p=1.000 | **-14.3** [-25.7, -2.9] p=1.000 | **-14.1** [-22.6, -6.8] p=1.000 |
| RRF + ms-marco-MiniLM-L-6-v2 (fuse, top 10) vs RRF | -2.9 [-17.1, +8.6] p=0.748 | -2.9 [-8.6, +0.0] p=1.000 | -4.4 [-12.6, +3.1] p=0.870 |
| RRF + ms-marco-MiniLM-L-6-v2 (fuse, top 20) vs RRF | -2.9 [-17.1, +8.6] p=0.748 | -5.7 [-14.3, +0.0] p=1.000 | -6.0 [-14.3, +1.7] p=0.936 |
| RRF + ms-marco-MiniLM-L-6-v2 (fuse, top 40) vs RRF | -2.9 [-17.1, +8.6] p=0.748 | -2.9 [-11.4, +5.7] p=0.815 | -5.7 [-14.0, +1.9] p=0.924 |
| RRF + ms-marco-MiniLM-L-6-v2 (fuse, top 60) vs RRF | -2.9 [-17.1, +8.6] p=0.748 | -2.9 [-11.4, +5.7] p=0.815 | -5.7 [-14.0, +1.9] p=0.924 |

## Paired differences vs plain RRF, documentation queries (points; bold = 95% interval excludes 0)

| comparison (A − B) | Δ recall@1 | Δ recall@5 | Δ mrr@10 |
|---|---:|---:|---:|
| RRF + jina-reranker-v3.5 (replace, top 10) vs RRF | +14.3 [+0.0, +28.6] p=0.032 | +5.7 [-5.7, +17.1] p=0.232 | **+12.2** [+3.4, +21.9] p=0.003 |
| RRF + jina-reranker-v3.5 (replace, top 20) vs RRF | +14.3 [+0.0, +28.6] p=0.032 | +11.4 [+0.0, +25.7] p=0.065 | **+14.8** [+5.6, +24.6] p=0.001 |
| RRF + jina-reranker-v3.5 (replace, top 40) vs RRF | +14.3 [+0.0, +28.6] p=0.032 | +11.4 [-2.9, +25.7] p=0.103 | **+14.5** [+4.7, +24.9] p=0.001 |
| RRF + jina-reranker-v3.5 (replace, top 60) vs RRF | **+17.1** [+2.9, +31.4] p=0.015 | +8.6 [-5.7, +22.9] p=0.175 | **+15.5** [+5.2, +26.5] p=0.001 |
| RRF + jina-reranker-v3.5 (fuse, top 10) vs RRF | +2.9 [+0.0, +8.6] p=0.369 | +2.9 [-5.7, +11.4] p=0.405 | **+5.3** [+1.7, +10.1] p=0.000 |
| RRF + jina-reranker-v3.5 (fuse, top 20) vs RRF | +2.9 [+0.0, +8.6] p=0.369 | +2.9 [-5.7, +11.4] p=0.405 | **+7.0** [+3.3, +11.8] p=0.000 |
| RRF + jina-reranker-v3.5 (fuse, top 40) vs RRF | +2.9 [+0.0, +8.6] p=0.369 | +5.7 [+0.0, +14.3] p=0.130 | **+7.1** [+3.3, +11.8] p=0.000 |
| RRF + jina-reranker-v3.5 (fuse, top 60) vs RRF | +2.9 [+0.0, +8.6] p=0.369 | +5.7 [+0.0, +14.3] p=0.130 | **+7.6** [+3.7, +12.5] p=0.000 |
| RRF + ms-marco-MiniLM-L-6-v2 (replace, top 10) vs RRF | +0.0 [-17.1, +17.1] p=0.564 | +2.9 [+0.0, +8.6] p=0.373 | +2.6 [-7.5, +13.1] p=0.322 |
| RRF + ms-marco-MiniLM-L-6-v2 (replace, top 20) vs RRF | +0.0 [-17.1, +17.1] p=0.564 | +2.9 [+0.0, +8.6] p=0.373 | +2.1 [-8.0, +13.0] p=0.348 |
| RRF + ms-marco-MiniLM-L-6-v2 (replace, top 40) vs RRF | +0.0 [-17.1, +17.1] p=0.564 | +5.7 [+0.0, +14.3] p=0.131 | +2.7 [-7.6, +13.5] p=0.315 |
| RRF + ms-marco-MiniLM-L-6-v2 (replace, top 60) vs RRF | +0.0 [-17.1, +17.1] p=0.564 | +5.7 [+0.0, +14.3] p=0.131 | +2.7 [-7.6, +13.5] p=0.315 |
| RRF + ms-marco-MiniLM-L-6-v2 (fuse, top 10) vs RRF | -2.9 [-8.6, +0.0] p=1.000 | +2.9 [+0.0, +8.6] p=0.373 | +1.1 [-3.1, +4.8] p=0.276 |
| RRF + ms-marco-MiniLM-L-6-v2 (fuse, top 20) vs RRF | -2.9 [-8.6, +0.0] p=1.000 | +2.9 [+0.0, +8.6] p=0.373 | +0.8 [-3.6, +4.7] p=0.335 |
| RRF + ms-marco-MiniLM-L-6-v2 (fuse, top 40) vs RRF | -2.9 [-8.6, +0.0] p=1.000 | +2.9 [+0.0, +8.6] p=0.373 | +0.9 [-3.5, +4.8] p=0.325 |
| RRF + ms-marco-MiniLM-L-6-v2 (fuse, top 60) vs RRF | -2.9 [-8.6, +0.0] p=1.000 | +2.9 [+0.0, +8.6] p=0.373 | +0.9 [-3.5, +4.8] p=0.325 |

## jina-reranker-v3.5 vs ms-marco-MiniLM-L-6-v2, head to head (points)

| comparison (A − B) | Δ recall@1 | Δ recall@5 | Δ mrr@10 |
|---|---:|---:|---:|
| jina-reranker-v3.5 vs ms-marco-MiniLM-L-6-v2 (replace, top 10) | **+24.3** [+14.3, +35.7] p=0.000 | +7.1 [+0.0, +14.3] p=0.042 | **+18.8** [+11.2, +26.7] p=0.000 |
| jina-reranker-v3.5 vs ms-marco-MiniLM-L-6-v2 (replace, top 20) | **+22.9** [+12.9, +32.9] p=0.000 | **+14.3** [+5.7, +22.9] p=0.002 | **+20.8** [+13.1, +28.7] p=0.000 |
| jina-reranker-v3.5 vs ms-marco-MiniLM-L-6-v2 (replace, top 40) | **+24.3** [+14.3, +35.7] p=0.000 | **+14.3** [+4.3, +24.3] p=0.003 | **+22.2** [+14.2, +30.5] p=0.000 |
| jina-reranker-v3.5 vs ms-marco-MiniLM-L-6-v2 (replace, top 60) | **+25.7** [+14.3, +37.1] p=0.000 | **+14.3** [+4.3, +24.3] p=0.003 | **+23.0** [+14.6, +31.5] p=0.000 |
| jina-reranker-v3.5 vs ms-marco-MiniLM-L-6-v2 (fuse, top 10) | **+8.6** [+1.4, +17.1] p=0.015 | +1.4 [-2.9, +5.7] p=0.398 | **+7.2** [+2.3, +12.7] p=0.001 |
| jina-reranker-v3.5 vs ms-marco-MiniLM-L-6-v2 (fuse, top 20) | **+8.6** [+1.4, +17.1] p=0.015 | +4.3 [-1.4, +11.4] p=0.137 | **+9.5** [+4.2, +15.3] p=0.000 |
| jina-reranker-v3.5 vs ms-marco-MiniLM-L-6-v2 (fuse, top 40) | **+8.6** [+1.4, +17.1] p=0.015 | +4.3 [+0.0, +10.0] p=0.051 | **+9.5** [+4.3, +15.3] p=0.000 |
| jina-reranker-v3.5 vs ms-marco-MiniLM-L-6-v2 (fuse, top 60) | **+8.6** [+1.4, +17.1] p=0.015 | +4.3 [+0.0, +10.0] p=0.051 | **+9.8** [+4.4, +15.6] p=0.000 |

## Candidate-order stability

The same candidates scored again in shuffled order. tau = Kendall rank correlation with the original order (1.0 = identical ranking), top-1 = share of shuffles with the same best candidate.

| reranker | queries | mean tau | top-1 unchanged | largest score change |
|---|---:|---:|---:|---:|
| jina-reranker-v3.5 | 30 | 0.606 | 69% | 0.389 |
| ms-marco-MiniLM-L-6-v2 | 30 | 1.000 | 100% | 0 |
