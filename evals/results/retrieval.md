# Retrieval evaluation

Gold: `evals/gold/handwritten.jsonl`: 70 answerable queries (35 documentation, 35 code). Values are percentages with a 95% bootstrap half-width (±). Relevance = the retrieved chunk is from the gold file and contains the gold snippet.

## Index

| chunker | files | chunks | usable | mean chars | gold reachable / gated out / split |
|---|---:|---:|---:|---:|---|
| ast | 40 | 488 | 477 | 810 | 70 / 0 / 0 |
| naive500 | 40 | 229 | 229 | 1770 | 70 / 0 / 0 |
| naive250 | 40 | 453 | 452 | 894 | 70 / 0 / 0 |

## All systems

| system | recall@1 | recall@3 | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 | map@10 | ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ast/bm25 | 34.3 ±10.7 | 60.0 ±11.4 | 70.0 ±11.4 | 77.1 ±10.0 | 84.3 ±8.6 | 48.0 ±9.5 | 55.1 ±8.9 | 48.0 ±9.5 | 2 |
| ast/gemma dense | 40.0 ±12.1 | 65.7 ±11.4 | 72.9 ±10.7 | 84.3 ±8.6 | 94.3 ±5.0 | 54.8 ±9.6 | 61.9 ±8.5 | 54.8 ±9.6 | 19 |
| ast/gemma RRF | 40.0 ±11.4 | 68.6 ±11.4 | 78.6 ±10.0 | 88.6 ±7.9 | 94.3 ±5.0 | 55.7 ±9.4 | 63.7 ±8.5 | 55.7 ±9.4 | 20 |
| ast/gemma RRF+rerank | 58.6 ±11.4 | 81.4 ±9.3 | 88.6 ±7.9 | 94.3 ±5.0 | 94.3 ±5.0 | 71.1 ±8.7 | 76.8 ±7.3 | 71.1 ±8.7 | 1003 |
| ast/bm25+rerank | 54.3 ±11.4 | 77.1 ±10.0 | 82.9 ±9.3 | 84.3 ±8.6 | 84.3 ±8.6 | 65.6 ±9.7 | 70.3 ±8.9 | 65.6 ±9.7 | 1118 |
| ast/gemma dense+rerank | 58.6 ±11.4 | 81.4 ±9.3 | 87.1 ±7.9 | 92.9 ±6.4 | 94.3 ±5.0 | 71.4 ±8.8 | 76.7 ±7.6 | 71.4 ±8.8 | 864 |
| ast/gemma(code task) dense | 38.6 ±12.1 | 64.3 ±11.4 | 75.7 ±10.0 | 84.3 ±8.6 | 97.1 ±3.6 | 54.0 ±9.3 | 61.3 ±8.5 | 54.0 ±9.3 | 19 |
| ast/gemma(code task) RRF+rerank | 57.1 ±11.4 | 78.6 ±9.3 | 91.4 ±6.4 | 92.9 ±6.4 | 92.9 ±6.4 | 70.0 ±8.9 | 75.7 ±7.7 | 70.0 ±8.9 | 997 |
| ast/gemma@256 dense | 35.7 ±10.7 | 64.3 ±11.4 | 70.0 ±10.0 | 81.4 ±8.6 | 92.9 ±6.4 | 51.4 ±9.3 | 58.7 ±8.5 | 51.4 ±9.3 | 20 |
| ast/gemma@256 RRF | 41.4 ±12.1 | 67.1 ±11.4 | 78.6 ±10.0 | 85.7 ±8.6 | 94.3 ±5.0 | 57.0 ±9.4 | 64.0 ±8.5 | 57.0 ±9.4 | 23 |
| ast/bge dense | 28.6 ±10.7 | 45.7 ±12.1 | 67.1 ±11.4 | 74.3 ±10.0 | 88.6 ±7.1 | 42.2 ±9.2 | 50.0 ±8.7 | 42.2 ±9.2 | 8 |
| ast/bge RRF | 30.0 ±10.7 | 61.4 ±11.4 | 78.6 ±9.3 | 85.7 ±7.9 | 91.4 ±6.4 | 48.3 ±8.9 | 57.4 ±8.1 | 48.3 ±8.9 | 7 |
| ast/bge RRF+rerank | 54.3 ±11.4 | 77.1 ±9.3 | 87.1 ±7.9 | 91.4 ±6.4 | 91.4 ±6.4 | 67.6 ±8.8 | 73.5 ±7.6 | 67.6 ±8.8 | 1114 |
| ast/hash dense (floor) | 12.9 ±7.9 | 21.4 ±9.3 | 24.3 ±10.0 | 34.3 ±10.7 | 50.0 ±11.4 | 18.8 ±7.9 | 22.4 ±8.2 | 18.8 ±7.9 | 2 |
| naive500/bm25 | 40.0 ±12.1 | 52.9 ±11.4 | 65.7 ±11.4 | 82.9 ±8.6 | 87.1 ±7.9 | 50.9 ±10.2 | 58.4 ±9.1 | 50.9 ±10.2 | 2 |
| naive500/gemma dense | 35.7 ±10.7 | 55.7 ±11.4 | 62.9 ±11.4 | 80.0 ±9.3 | 88.6 ±7.9 | 48.3 ±9.5 | 55.8 ±8.9 | 48.3 ±9.5 | 22 |
| naive500/gemma RRF | 38.6 ±11.4 | 65.7 ±11.4 | 75.7 ±10.0 | 87.1 ±7.9 | 94.3 ±5.0 | 54.2 ±9.3 | 62.1 ±8.1 | 54.2 ±9.3 | 22 |
| naive500/gemma RRF+rerank | 50.0 ±11.4 | 81.4 ±9.3 | 85.7 ±7.9 | 90.0 ±7.1 | 94.3 ±5.0 | 65.9 ±8.6 | 71.9 ±7.8 | 65.9 ±8.6 | 2388 |
| naive250/bm25 | 34.3 ±10.7 | 50.0 ±11.4 | 60.0 ±11.4 | 71.4 ±11.4 | 84.3 ±8.6 | 44.2 ±10.1 | 50.6 ±9.8 | 44.2 ±10.1 | 2 |
| naive250/gemma dense | 24.3 ±10.0 | 50.0 ±11.4 | 57.1 ±11.4 | 71.4 ±10.7 | 88.6 ±7.1 | 38.8 ±8.9 | 46.7 ±8.6 | 38.8 ±8.9 | 20 |
| naive250/gemma RRF | 25.7 ±10.7 | 55.7 ±11.4 | 70.0 ±10.7 | 84.3 ±8.6 | 90.0 ±6.4 | 44.4 ±8.8 | 54.0 ±8.0 | 44.4 ±8.8 | 22 |
| naive250/gemma RRF+rerank | 47.1 ±11.4 | 77.1 ±10.0 | 85.7 ±7.9 | 90.0 ±6.4 | 90.0 ±6.4 | 63.5 ±8.9 | 70.1 ±7.9 | 63.5 ±8.9 | 913 |

## Documentation queries only

| system | recall@1 | recall@3 | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 | map@10 | ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ast/bm25 | 31.4 ±15.7 | 57.1 ±17.1 | 68.6 ±14.3 | 77.1 ±14.3 | 85.7 ±11.4 | 45.6 ±13.2 | 53.2 ±12.4 | 45.6 ±13.2 | 2 |
| ast/gemma dense | 25.7 ±14.3 | 60.0 ±17.1 | 65.7 ±15.7 | 80.0 ±12.9 | 91.4 ±10.0 | 44.6 ±12.4 | 53.2 ±11.6 | 44.6 ±12.4 | 20 |
| ast/gemma RRF | 34.3 ±15.7 | 60.0 ±17.1 | 74.3 ±14.3 | 85.7 ±11.4 | 94.3 ±7.1 | 49.3 ±12.9 | 58.1 ±11.7 | 49.3 ±12.9 | 20 |
| ast/gemma RRF+rerank | 48.6 ±17.1 | 74.3 ±15.7 | 85.7 ±11.4 | 94.3 ±7.1 | 94.3 ±7.1 | 64.1 ±12.7 | 71.5 ±10.4 | 64.1 ±12.7 | 945 |
| ast/bm25+rerank | 48.6 ±17.1 | 77.1 ±12.9 | 85.7 ±11.4 | 85.7 ±11.4 | 85.7 ±11.4 | 63.6 ±12.9 | 69.2 ±11.8 | 63.6 ±12.9 | 1070 |
| ast/gemma dense+rerank | 45.7 ±17.1 | 74.3 ±14.3 | 80.0 ±12.9 | 88.6 ±10.0 | 91.4 ±10.0 | 61.5 ±13.1 | 68.1 ±11.7 | 61.5 ±13.1 | 853 |
| ast/gemma(code task) dense | 22.9 ±12.9 | 54.3 ±17.1 | 65.7 ±14.3 | 80.0 ±12.9 | 94.3 ±7.1 | 42.2 ±11.5 | 51.3 ±11.0 | 42.2 ±11.5 | 19 |
| ast/gemma(code task) RRF+rerank | 45.7 ±17.1 | 71.4 ±15.7 | 88.6 ±10.0 | 91.4 ±10.0 | 91.4 ±10.0 | 61.6 ±12.8 | 68.9 ±11.3 | 61.6 ±12.8 | 939 |
| ast/gemma@256 dense | 20.0 ±14.3 | 57.1 ±17.1 | 62.9 ±15.7 | 74.3 ±14.3 | 94.3 ±7.1 | 38.9 ±11.6 | 47.5 ±11.6 | 38.9 ±11.6 | 20 |
| ast/gemma@256 RRF | 37.1 ±17.1 | 60.0 ±17.1 | 74.3 ±14.3 | 85.7 ±11.4 | 94.3 ±7.1 | 52.1 ±13.3 | 60.2 ±11.8 | 52.1 ±13.3 | 23 |
| ast/bge dense | 14.3 ±11.4 | 28.6 ±15.7 | 62.9 ±17.1 | 71.4 ±15.7 | 88.6 ±10.0 | 29.9 ±10.8 | 39.8 ±11.1 | 29.9 ±10.8 | 9 |
| ast/bge RRF | 20.0 ±12.9 | 60.0 ±17.1 | 80.0 ±12.9 | 85.7 ±11.4 | 94.3 ±7.1 | 42.8 ±11.2 | 53.3 ±10.4 | 42.8 ±11.2 | 7 |
| ast/bge RRF+rerank | 48.6 ±17.1 | 77.1 ±12.9 | 88.6 ±10.0 | 94.3 ±7.1 | 94.3 ±7.1 | 64.5 ±12.4 | 71.8 ±10.2 | 64.5 ±12.4 | 1037 |
| ast/hash dense (floor) | 14.3 ±12.9 | 22.9 ±15.7 | 22.9 ±15.7 | 37.1 ±15.7 | 57.1 ±17.1 | 20.1 ±11.8 | 24.1 ±12.0 | 20.1 ±11.8 | 2 |

## Code queries only

| system | recall@1 | recall@3 | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 | map@10 | ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ast/bm25 | 37.1 ±15.7 | 62.9 ±17.1 | 71.4 ±14.3 | 77.1 ±12.9 | 82.9 ±12.9 | 50.3 ±13.8 | 56.9 ±12.9 | 50.3 ±13.8 | 2 |
| ast/gemma dense | 54.3 ±17.1 | 71.4 ±15.7 | 80.0 ±12.9 | 88.6 ±10.0 | 97.1 ±4.3 | 65.0 ±13.6 | 70.7 ±12.2 | 65.0 ±13.6 | 19 |
| ast/gemma RRF | 45.7 ±15.7 | 77.1 ±12.9 | 82.9 ±12.9 | 91.4 ±10.0 | 94.3 ±7.1 | 62.2 ±12.5 | 69.3 ±10.8 | 62.2 ±12.5 | 20 |
| ast/gemma RRF+rerank | 68.6 ±14.3 | 88.6 ±10.0 | 91.4 ±8.6 | 94.3 ±7.1 | 94.3 ±7.1 | 78.2 ±11.4 | 82.2 ±9.7 | 78.2 ±11.4 | 1060 |
| ast/bm25+rerank | 60.0 ±17.1 | 77.1 ±12.9 | 80.0 ±12.9 | 82.9 ±12.9 | 82.9 ±12.9 | 67.7 ±14.0 | 71.4 ±13.0 | 67.7 ±14.0 | 1166 |
| ast/gemma dense+rerank | 71.4 ±14.3 | 88.6 ±10.0 | 94.3 ±7.1 | 97.1 ±4.3 | 97.1 ±4.3 | 81.3 ±10.4 | 85.2 ±8.5 | 81.3 ±10.4 | 876 |
| ast/gemma(code task) dense | 54.3 ±17.1 | 74.3 ±14.3 | 85.7 ±12.9 | 88.6 ±10.0 | 100.0 ±0.0 | 65.8 ±13.2 | 71.4 ±11.9 | 65.8 ±13.2 | 19 |
| ast/gemma(code task) RRF+rerank | 68.6 ±14.3 | 85.7 ±11.4 | 94.3 ±7.1 | 94.3 ±7.1 | 94.3 ±7.1 | 78.5 ±11.1 | 82.5 ±9.5 | 78.5 ±11.1 | 1055 |
| ast/gemma@256 dense | 51.4 ±17.1 | 71.4 ±14.3 | 77.1 ±14.3 | 88.6 ±10.0 | 91.4 ±10.0 | 64.0 ±13.0 | 69.9 ±12.0 | 64.0 ±13.0 | 20 |
| ast/gemma@256 RRF | 45.7 ±15.7 | 74.3 ±14.3 | 82.9 ±12.9 | 85.7 ±11.4 | 94.3 ±7.1 | 61.9 ±12.8 | 67.8 ±11.9 | 61.9 ±12.8 | 23 |
| ast/bge dense | 42.9 ±15.7 | 62.9 ±17.1 | 71.4 ±14.3 | 77.1 ±12.9 | 88.6 ±10.0 | 54.6 ±14.1 | 60.1 ±13.1 | 54.6 ±14.1 | 7 |
| ast/bge RRF | 40.0 ±15.7 | 62.9 ±15.7 | 77.1 ±12.9 | 85.7 ±11.4 | 88.6 ±10.0 | 53.9 ±13.3 | 61.5 ±12.2 | 53.9 ±13.3 | 8 |
| ast/bge RRF+rerank | 60.0 ±15.7 | 77.1 ±14.3 | 85.7 ±11.4 | 88.6 ±10.0 | 88.6 ±10.0 | 70.7 ±12.6 | 75.2 ±11.4 | 70.7 ±12.6 | 1190 |
| ast/hash dense (floor) | 11.4 ±10.0 | 20.0 ±12.9 | 25.7 ±14.3 | 31.4 ±15.7 | 42.9 ±17.1 | 17.5 ±10.4 | 20.8 ±11.0 | 17.5 ±10.4 | 2 |

## Paired comparisons (percentage points; bold = 95% interval excludes 0)

| comparison (A − B) | Δ recall@5 | Δ mrr@10 |
|---|---:|---:|
| hybrid RRF vs dense only (gemma) | +5.7 [-2.9, +15.7] p=0.155 | +0.9 [-5.5, +7.3] p=0.375 |
| hybrid RRF vs BM25 only | **+8.6** [+1.4, +15.7] p=0.017 | **+7.7** [+0.8, +14.8] p=0.013 |
| dense only vs BM25 only (gemma) | +2.9 [-10.0, +14.3] p=0.370 | +6.8 [-4.2, +17.4] p=0.109 |
| + cross-encoder rerank vs RRF | **+10.0** [+1.4, +18.6] p=0.010 | **+15.4** [+8.6, +22.6] p=0.000 |
| + cross-encoder rerank on BM25 vs BM25 | **+12.9** [+5.7, +21.4] p=0.000 | **+17.7** [+9.7, +25.7] p=0.000 |
| EmbeddingGemma 2 vs bge-small (dense) | +5.7 [-4.3, +15.7] p=0.152 | **+12.6** [+5.3, +20.0] p=0.000 |
| EmbeddingGemma 2 vs bge-small (RRF+rerank) | +1.4 [-5.7, +8.6] p=0.436 | +3.5 [-1.0, +8.6] p=0.074 |
| gemma 768d vs 256d (dense) | +2.9 [-2.9, +8.6] p=0.228 | +3.4 [-1.1, +7.8] p=0.069 |
| code task prefix vs search prefix (dense) | +2.9 [-4.3, +10.0] p=0.272 | -0.8 [-4.4, +2.7] p=0.669 |
| AST chunks vs fixed 500-token windows (RRF+rerank) | +2.9 [-5.7, +11.4] p=0.324 | +5.2 [-2.7, +13.1] p=0.103 |
| AST chunks vs fixed 250-token windows (RRF+rerank) | +2.9 [-5.7, +11.4] p=0.321 | +7.6 [-0.4, +15.8] p=0.032 |
| AST chunks vs fixed 250-token windows (dense) | **+15.7** [+2.9, +27.1] p=0.009 | **+16.0** [+5.0, +26.3] p=0.001 |

### Same comparisons, code queries only

| comparison (A − B) | Δ recall@5 | Δ mrr@10 |
|---|---:|---:|
| + cross-encoder rerank vs RRF | +8.6 [+0.0, +20.0] p=0.043 | **+16.0** [+6.4, +26.4] p=0.000 |
| + cross-encoder rerank on BM25 vs BM25 | +8.6 [+0.0, +17.1] p=0.043 | **+17.4** [+6.4, +28.8] p=0.001 |
| EmbeddingGemma 2 vs bge-small (RRF+rerank) | +5.7 [-5.7, +17.1] p=0.221 | **+7.5** [+0.4, +17.0] p=0.009 |
| code task prefix vs search prefix (dense) | +5.7 [-5.7, +17.1] p=0.225 | +0.8 [-4.0, +5.4] p=0.350 |
| AST chunks vs fixed 500-token windows (RRF+rerank) | +5.7 [-5.7, +17.1] p=0.226 | +5.8 [-5.6, +18.1] p=0.176 |
| AST chunks vs fixed 250-token windows (RRF+rerank) | +2.9 [-5.7, +14.3] p=0.395 | **+11.4** [+0.6, +23.2] p=0.017 |
| AST chunks vs fixed 250-token windows (dense) | +17.1 [-2.9, +37.1] p=0.065 | **+21.0** [+3.1, +37.7] p=0.010 |

### Same comparisons, documentation queries only

| comparison (A − B) | Δ recall@5 | Δ mrr@10 |
|---|---:|---:|
| + cross-encoder rerank vs RRF | +11.4 [+0.0, +25.7] p=0.065 | **+14.8** [+5.6, +24.6] p=0.001 |
| + cross-encoder rerank on BM25 vs BM25 | **+17.1** [+5.7, +31.4] p=0.001 | **+17.9** [+6.7, +29.7] p=0.001 |
| EmbeddingGemma 2 vs bge-small (RRF+rerank) | -2.9 [-11.4, +5.7] p=0.811 | -0.4 [-5.5, +5.2] p=0.564 |
| code task prefix vs search prefix (dense) | +0.0 [-8.6, +8.6] p=0.656 | -2.4 [-8.1, +3.0] p=0.810 |
| AST chunks vs fixed 500-token windows (RRF+rerank) | +0.0 [-14.3, +14.3] p=0.595 | +4.7 [-6.1, +14.8] p=0.199 |
| AST chunks vs fixed 250-token windows (RRF+rerank) | +2.9 [-11.4, +17.1] p=0.431 | +3.8 [-7.4, +14.9] p=0.251 |
| AST chunks vs fixed 250-token windows (dense) | +14.3 [+0.0, +28.6] p=0.035 | +11.0 [-0.5, +22.6] p=0.030 |

## Error analysis: `ast/gemma RRF+rerank`

4 queries without a relevant chunk in the top 10:

- `d02` (doc, natural) **What password hashing does the app use and how many iterations?**  
  gold: `docs/architecture.md`; found at rank >20; top-3: QuestionPrep — next phases (plan for Claude Code) ; packages/qp-core/src/qp_core/DBManager.py > DBMana; packages/qp-core/src/qp_core/DBManager.py > DBMana
- `d28` (doc, natural) **How is spoken audio turned into a transcript?**  
  gold: `docs/architecture.md`; found at rank >20; top-3: packages/qp-voice/src/qp_voice/speech_to_text.py >; HTTP API > Voice; apps/orchestrator/main.py > analyze_speech
- `c07` (code, natural) **how are code blocks math and tables protected from being split in markdown chunking**  
  gold: `packages/qp-pipeline/src/qp_pipeline/MarkdownChunker.py`; found at rank >20; top-3: packages/qp-pipeline/src/qp_pipeline/MarkdownChunk; Architecture > 1. Ingestion (upload → chunks); packages/qp-pipeline/src/qp_pipeline/Enricher.py >
- `c24` (code, natural) **how are near-identical generated questions removed**  
  gold: `packages/qp-pipeline/src/qp_pipeline/Enricher.py`; found at rank >20; top-3: packages/qp-pipeline/src/qp_pipeline/Enricher.py >; packages/qp-pipeline/src/qp_pipeline/verify.py > <; QuestionPrep — next phases (plan for Claude Code) 
