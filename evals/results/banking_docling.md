# Retrieval evaluation

Gold: `evals/gold/banking.jsonl`: 32 answerable queries (32 documentation, 0 code). Values are percentages with a 95% bootstrap half-width (±). Relevance = the retrieved chunk is from the gold file and contains the gold snippet.

## Index

| chunker | files | chunks | usable | mean chars | gold reachable / gated out / split |
|---|---:|---:|---:|---:|---|
| ast | 1 | 284 | 270 | 1314 | 29 / 0 / 3 |

## All systems

| system | recall@1 | recall@3 | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 | map@10 | ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ast/bm25 | 59.4 ±17.2 | 68.8 ±17.2 | 68.8 ±17.2 | 78.1 ±14.1 | 84.4 ±14.1 | 65.3 ±14.8 | 68.4 ±14.1 | 65.3 ±14.8 | 2 |
| ast/gemma dense | 62.5 ±15.6 | 71.9 ±15.6 | 75.0 ±14.1 | 84.4 ±12.5 | 87.5 ±10.9 | 67.8 ±14.5 | 71.6 ±13.4 | 67.8 ±14.5 | 29 |
| ast/gemma RRF | 65.6 ±15.6 | 75.0 ±14.1 | 81.2 ±14.1 | 81.2 ±14.1 | 87.5 ±10.9 | 71.2 ±14.1 | 73.7 ±13.6 | 71.2 ±14.1 | 25 |
| ast/gemma RRF+rerank | 68.8 ±15.6 | 87.5 ±10.9 | 87.5 ±10.9 | 87.5 ±10.9 | 87.5 ±10.9 | 77.6 ±12.8 | 80.2 ±12.1 | 77.6 ±12.8 | 2121 |
| ast/bm25+rerank | 75.0 ±14.1 | 84.4 ±14.1 | 84.4 ±14.1 | 84.4 ±14.1 | 84.4 ±14.1 | 79.7 ±13.3 | 80.9 ±12.7 | 79.7 ±13.3 | 2015 |
| ast/gemma dense+rerank | 71.9 ±15.6 | 87.5 ±10.9 | 87.5 ±10.9 | 87.5 ±10.9 | 87.5 ±10.9 | 79.7 ±12.5 | 81.7 ±11.7 | 79.7 ±12.5 | 1925 |
| ast/gemma(code task) dense | 53.1 ±17.2 | 65.6 ±15.6 | 65.6 ±15.6 | 78.1 ±14.1 | 87.5 ±10.9 | 60.1 ±14.7 | 64.4 ±13.9 | 60.1 ±14.7 | 22 |
| ast/gemma(code task) RRF+rerank | 75.0 ±14.1 | 87.5 ±10.9 | 90.6 ±10.9 | 90.6 ±10.9 | 90.6 ±10.9 | 81.0 ±11.8 | 83.4 ±11.0 | 81.0 ±11.8 | 2025 |
| ast/gemma@256 dense | 53.1 ±15.6 | 68.8 ±15.6 | 78.1 ±14.1 | 84.4 ±12.5 | 87.5 ±10.9 | 63.3 ±14.2 | 68.4 ±12.8 | 63.3 ±14.2 | 24 |
| ast/gemma@256 RRF | 65.6 ±15.6 | 78.1 ±14.1 | 81.2 ±14.1 | 81.2 ±14.1 | 87.5 ±10.9 | 72.1 ±13.9 | 74.4 ±13.3 | 72.1 ±13.9 | 23 |
| ast/bge dense | 65.6 ±15.6 | 71.9 ±15.6 | 71.9 ±15.6 | 75.0 ±14.1 | 81.2 ±14.1 | 69.1 ±14.7 | 70.5 ±14.6 | 69.1 ±14.7 | 7 |
| ast/bge RRF | 68.8 ±15.6 | 75.0 ±14.1 | 75.0 ±14.1 | 81.2 ±14.1 | 84.4 ±14.1 | 72.3 ±14.5 | 74.4 ±14.0 | 72.3 ±14.5 | 7 |
| ast/bge RRF+rerank | 75.0 ±14.1 | 84.4 ±14.1 | 84.4 ±14.1 | 84.4 ±14.1 | 84.4 ±14.1 | 79.7 ±13.3 | 80.9 ±12.7 | 79.7 ±13.3 | 2071 |
| ast/hash dense (floor) | 15.6 ±12.5 | 25.0 ±14.1 | 37.5 ±17.2 | 59.4 ±17.2 | 71.9 ±15.6 | 24.8 ±12.2 | 32.7 ±12.1 | 24.8 ±12.2 | 2 |

## Documentation queries only

| system | recall@1 | recall@3 | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 | map@10 | ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ast/bm25 | 59.4 ±17.2 | 68.8 ±17.2 | 68.8 ±17.2 | 78.1 ±14.1 | 84.4 ±14.1 | 65.3 ±14.8 | 68.4 ±14.1 | 65.3 ±14.8 | 2 |
| ast/gemma dense | 62.5 ±15.6 | 71.9 ±15.6 | 75.0 ±14.1 | 84.4 ±12.5 | 87.5 ±10.9 | 67.8 ±14.5 | 71.6 ±13.4 | 67.8 ±14.5 | 29 |
| ast/gemma RRF | 65.6 ±15.6 | 75.0 ±14.1 | 81.2 ±14.1 | 81.2 ±14.1 | 87.5 ±10.9 | 71.2 ±14.1 | 73.7 ±13.6 | 71.2 ±14.1 | 25 |
| ast/gemma RRF+rerank | 68.8 ±15.6 | 87.5 ±10.9 | 87.5 ±10.9 | 87.5 ±10.9 | 87.5 ±10.9 | 77.6 ±12.8 | 80.2 ±12.1 | 77.6 ±12.8 | 2121 |
| ast/bm25+rerank | 75.0 ±14.1 | 84.4 ±14.1 | 84.4 ±14.1 | 84.4 ±14.1 | 84.4 ±14.1 | 79.7 ±13.3 | 80.9 ±12.7 | 79.7 ±13.3 | 2015 |
| ast/gemma dense+rerank | 71.9 ±15.6 | 87.5 ±10.9 | 87.5 ±10.9 | 87.5 ±10.9 | 87.5 ±10.9 | 79.7 ±12.5 | 81.7 ±11.7 | 79.7 ±12.5 | 1925 |
| ast/gemma(code task) dense | 53.1 ±17.2 | 65.6 ±15.6 | 65.6 ±15.6 | 78.1 ±14.1 | 87.5 ±10.9 | 60.1 ±14.7 | 64.4 ±13.9 | 60.1 ±14.7 | 22 |
| ast/gemma(code task) RRF+rerank | 75.0 ±14.1 | 87.5 ±10.9 | 90.6 ±10.9 | 90.6 ±10.9 | 90.6 ±10.9 | 81.0 ±11.8 | 83.4 ±11.0 | 81.0 ±11.8 | 2025 |
| ast/gemma@256 dense | 53.1 ±15.6 | 68.8 ±15.6 | 78.1 ±14.1 | 84.4 ±12.5 | 87.5 ±10.9 | 63.3 ±14.2 | 68.4 ±12.8 | 63.3 ±14.2 | 24 |
| ast/gemma@256 RRF | 65.6 ±15.6 | 78.1 ±14.1 | 81.2 ±14.1 | 81.2 ±14.1 | 87.5 ±10.9 | 72.1 ±13.9 | 74.4 ±13.3 | 72.1 ±13.9 | 23 |
| ast/bge dense | 65.6 ±15.6 | 71.9 ±15.6 | 71.9 ±15.6 | 75.0 ±14.1 | 81.2 ±14.1 | 69.1 ±14.7 | 70.5 ±14.6 | 69.1 ±14.7 | 7 |
| ast/bge RRF | 68.8 ±15.6 | 75.0 ±14.1 | 75.0 ±14.1 | 81.2 ±14.1 | 84.4 ±14.1 | 72.3 ±14.5 | 74.4 ±14.0 | 72.3 ±14.5 | 7 |
| ast/bge RRF+rerank | 75.0 ±14.1 | 84.4 ±14.1 | 84.4 ±14.1 | 84.4 ±14.1 | 84.4 ±14.1 | 79.7 ±13.3 | 80.9 ±12.7 | 79.7 ±13.3 | 2071 |
| ast/hash dense (floor) | 15.6 ±12.5 | 25.0 ±14.1 | 37.5 ±17.2 | 59.4 ±17.2 | 71.9 ±15.6 | 24.8 ±12.2 | 32.7 ±12.1 | 24.8 ±12.2 | 2 |

## Code queries only

| system | recall@1 | recall@3 | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 | map@10 | ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ast/bm25 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0 |
| ast/gemma dense | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0 |
| ast/gemma RRF | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0 |
| ast/gemma RRF+rerank | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0 |
| ast/bm25+rerank | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0 |
| ast/gemma dense+rerank | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0 |
| ast/gemma(code task) dense | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0 |
| ast/gemma(code task) RRF+rerank | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0 |
| ast/gemma@256 dense | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0 |
| ast/gemma@256 RRF | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0 |
| ast/bge dense | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0 |
| ast/bge RRF | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0 |
| ast/bge RRF+rerank | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0 |
| ast/hash dense (floor) | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0.0 ±0.0 | 0 |

## Paired comparisons (percentage points; bold = 95% interval excludes 0)

| comparison (A − B) | Δ recall@5 | Δ mrr@10 |
|---|---:|---:|
| hybrid RRF vs dense only (gemma) | +6.2 [+0.0, +15.6] p=0.126 | +3.4 [-2.8, +9.9] p=0.148 |
| hybrid RRF vs BM25 only | **+12.5** [+3.1, +25.0] p=0.012 | **+5.9** [+0.2, +13.4] p=0.023 |
| dense only vs BM25 only (gemma) | +6.2 [-6.2, +18.8] p=0.220 | +2.5 [-4.8, +10.8] p=0.262 |
| + cross-encoder rerank vs RRF | +6.2 [+0.0, +15.6] p=0.124 | **+6.4** [+1.9, +12.1] p=0.002 |
| + cross-encoder rerank on BM25 vs BM25 | **+15.6** [+3.1, +28.1] p=0.003 | **+14.3** [+4.7, +25.9] p=0.000 |
| EmbeddingGemma 2 vs bge-small (dense) | +3.1 [-6.2, +12.5] p=0.399 | -1.3 [-7.1, +3.4] p=0.672 |
| EmbeddingGemma 2 vs bge-small (RRF+rerank) | +3.1 [+0.0, +9.4] p=0.359 | -2.1 [-7.3, +3.1] p=0.824 |
| gemma 768d vs 256d (dense) | -3.1 [-12.5, +6.2] p=0.815 | +4.5 [-1.9, +11.8] p=0.088 |
| code task prefix vs search prefix (dense) | -9.4 [-21.9, +0.0] p=1.000 | **-7.7** [-16.3, -0.2] p=0.978 |

### Same comparisons, code queries only

| comparison (A − B) | Δ recall@5 | Δ mrr@10 |
|---|---:|---:|
| + cross-encoder rerank vs RRF | +0.0 [+0.0, +0.0] p=1.000 | +0.0 [+0.0, +0.0] p=1.000 |
| + cross-encoder rerank on BM25 vs BM25 | +0.0 [+0.0, +0.0] p=1.000 | +0.0 [+0.0, +0.0] p=1.000 |
| EmbeddingGemma 2 vs bge-small (RRF+rerank) | +0.0 [+0.0, +0.0] p=1.000 | +0.0 [+0.0, +0.0] p=1.000 |
| code task prefix vs search prefix (dense) | +0.0 [+0.0, +0.0] p=1.000 | +0.0 [+0.0, +0.0] p=1.000 |

### Same comparisons, documentation queries only

| comparison (A − B) | Δ recall@5 | Δ mrr@10 |
|---|---:|---:|
| + cross-encoder rerank vs RRF | +6.2 [+0.0, +15.6] p=0.124 | **+6.4** [+1.9, +12.1] p=0.002 |
| + cross-encoder rerank on BM25 vs BM25 | **+15.6** [+3.1, +28.1] p=0.003 | **+14.3** [+4.7, +25.9] p=0.000 |
| EmbeddingGemma 2 vs bge-small (RRF+rerank) | +3.1 [+0.0, +9.4] p=0.359 | -2.1 [-7.3, +3.1] p=0.824 |
| code task prefix vs search prefix (dense) | -9.4 [-21.9, +0.0] p=1.000 | **-7.7** [-16.3, -0.2] p=0.978 |

## Error analysis: `ast/gemma RRF+rerank`

4 queries without a relevant chunk in the top 10:

- `b07` (doc, natural) **How long does the Banking Mohtasib hold office, and can the term be extended?**  
  gold: `Banking-Companies-Ordinance-1962.pdf`; found at rank >20; top-3: PART IVA BANKING MOHTASIB; PART IVA BANKING MOHTASIB; Part-IVA Banking Mohtasib
- `b15` (doc, natural) **How does the Ordinance define banking?**  
  gold: `Banking-Companies-Ordinance-1962.pdf`; found at rank >20; top-3: 2. Interpretation.-In these rules,; BUSINESS OF BANKING COMPANIES; PRELIMINARY
- `b16` (doc, natural) **Does a manufacturer that takes deposits only to finance its own business count as a banking company?**  
  gold: `Banking-Companies-Ordinance-1962.pdf`; found at rank >20; top-3: PRELIMINARY; 26. 4 Power of State Bank to prohibit acceptance o; 26. 4 Power of State Bank to prohibit acceptance o
- `b26` (doc, paraphrase) **Does the Ordinance replace the Companies Ordinance, 1984?**  
  gold: `Banking-Companies-Ordinance-1962.pdf`; found at rank >20; top-3: PART V MISCELLANEOUS; SUSPENSION OF BUSINESS AND WINDING UP OF BANKING C; PART V MISCELLANEOUS
