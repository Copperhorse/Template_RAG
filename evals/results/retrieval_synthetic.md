# Retrieval evaluation

Gold: `evals/gold/synthetic.jsonl`: 149 answerable queries (38 documentation, 111 code). Values are percentages with a 95% bootstrap half-width (±). Relevance = the retrieved chunk is from the gold file and contains the gold snippet.

## Index

| chunker | files | chunks | usable | mean chars | gold reachable / gated out / split |
|---|---:|---:|---:|---:|---|
| ast | 40 | 488 | 477 | 810 | 149 / 0 / 0 |

## All systems

| system | recall@1 | recall@3 | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 | map@10 | ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ast/bm25 | 28.9 ±7.4 | 47.7 ±8.1 | 57.0 ±7.7 | 65.1 ±7.7 | 77.9 ±7.0 | 40.0 ±6.9 | 45.9 ±6.7 | 39.7 ±6.7 | 2 |
| ast/gemma dense | 58.4 ±8.1 | 78.5 ±6.4 | 83.9 ±5.7 | 89.9 ±4.7 | 95.3 ±3.4 | 69.4 ±6.3 | 74.3 ±5.4 | 69.2 ±6.2 | 20 |
| ast/gemma RRF | 55.0 ±8.1 | 72.5 ±7.4 | 81.2 ±6.4 | 87.9 ±5.0 | 93.3 ±4.0 | 65.7 ±6.5 | 70.8 ±5.8 | 65.3 ±6.4 | 23 |
| ast/gemma RRF+rerank | 80.5 ±6.4 | 91.3 ±4.4 | 92.6 ±4.4 | 92.6 ±4.4 | 93.3 ±4.0 | 85.9 ±4.9 | 87.5 ±4.5 | 85.7 ±4.8 | 1040 |
| ast/bm25+rerank | 67.1 ±7.4 | 75.8 ±7.0 | 77.2 ±7.0 | 77.9 ±7.0 | 77.9 ±7.0 | 71.5 ±7.0 | 72.9 ±6.8 | 71.2 ±6.9 | 1204 |
| ast/gemma dense+rerank | 81.2 ±6.4 | 93.3 ±3.7 | 94.6 ±3.7 | 94.6 ±3.7 | 95.3 ±3.4 | 86.9 ±4.6 | 88.7 ±4.1 | 86.7 ±4.5 | 830 |
| ast/gemma(code task) dense | 52.3 ±8.1 | 76.5 ±6.7 | 81.9 ±6.0 | 88.6 ±5.0 | 94.6 ±3.7 | 65.0 ±6.2 | 70.6 ±5.5 | 64.8 ±6.1 | 21 |
| ast/gemma(code task) RRF+rerank | 81.2 ±6.4 | 89.9 ±5.0 | 91.3 ±4.4 | 91.3 ±4.4 | 91.9 ±4.4 | 85.6 ±5.2 | 86.9 ±4.9 | 85.4 ±5.1 | 1018 |
| ast/gemma@256 dense | 49.7 ±8.1 | 76.5 ±6.4 | 82.6 ±6.0 | 86.6 ±5.4 | 94.6 ±3.7 | 64.3 ±6.1 | 69.6 ±5.5 | 64.0 ±6.1 | 22 |
| ast/gemma@256 RRF | 53.0 ±8.1 | 75.2 ±7.0 | 81.2 ±6.4 | 87.9 ±5.0 | 91.9 ±4.4 | 65.4 ±6.5 | 70.8 ±5.9 | 65.2 ±6.4 | 24 |
| ast/bge dense | 47.0 ±7.7 | 70.5 ±7.4 | 77.2 ±6.4 | 83.2 ±5.7 | 88.6 ±5.0 | 59.6 ±6.3 | 65.2 ±5.8 | 59.3 ±6.3 | 6 |
| ast/bge RRF | 44.3 ±7.7 | 66.4 ±7.7 | 78.5 ±7.0 | 83.9 ±5.7 | 91.3 ±4.4 | 57.3 ±6.5 | 63.6 ±6.1 | 57.0 ±6.5 | 8 |
| ast/bge RRF+rerank | 79.2 ±6.4 | 89.3 ±5.0 | 91.3 ±4.4 | 91.3 ±4.4 | 91.3 ±4.4 | 84.6 ±5.0 | 86.2 ±4.7 | 84.4 ±5.1 | 1089 |
| ast/hash dense (floor) | 6.0 ±3.7 | 10.7 ±4.7 | 16.1 ±6.0 | 22.8 ±6.7 | 32.9 ±7.4 | 10.1 ±4.0 | 12.9 ±4.3 | 10.0 ±4.0 | 2 |

## Documentation queries only

| system | recall@1 | recall@3 | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 | map@10 | ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ast/bm25 | 28.9 ±14.5 | 44.7 ±15.8 | 60.5 ±15.8 | 68.4 ±14.5 | 78.9 ±13.2 | 39.6 ±12.9 | 46.5 ±12.5 | 39.6 ±12.9 | 2 |
| ast/gemma dense | 31.6 ±14.5 | 63.2 ±15.8 | 73.7 ±13.2 | 84.2 ±11.8 | 94.7 ±6.6 | 49.6 ±12.0 | 58.0 ±11.1 | 49.6 ±12.0 | 20 |
| ast/gemma RRF | 50.0 ±15.8 | 65.8 ±15.8 | 73.7 ±13.2 | 84.2 ±11.8 | 94.7 ±6.6 | 59.4 ±13.4 | 65.3 ±12.1 | 59.4 ±13.4 | 23 |
| ast/gemma RRF+rerank | 71.1 ±14.5 | 94.7 ±6.6 | 94.7 ±6.6 | 94.7 ±6.6 | 94.7 ±6.6 | 82.0 ±9.4 | 85.3 ±8.5 | 82.0 ±9.4 | 928 |
| ast/bm25+rerank | 57.9 ±15.8 | 78.9 ±13.2 | 78.9 ±13.2 | 78.9 ±13.2 | 78.9 ±13.2 | 68.0 ±13.4 | 70.8 ±12.8 | 68.0 ±13.4 | 1086 |
| ast/gemma dense+rerank | 63.2 ±15.8 | 92.1 ±7.9 | 94.7 ±6.6 | 94.7 ±6.6 | 94.7 ±6.6 | 77.0 ±10.3 | 81.5 ±8.8 | 77.0 ±10.3 | 769 |
| ast/gemma(code task) dense | 18.4 ±11.8 | 55.3 ±15.8 | 65.8 ±15.8 | 84.2 ±11.8 | 89.5 ±9.2 | 39.0 ±10.4 | 49.8 ±9.8 | 39.0 ±10.4 | 21 |
| ast/gemma(code task) RRF+rerank | 71.1 ±14.5 | 89.5 ±9.2 | 89.5 ±9.2 | 89.5 ±9.2 | 89.5 ±9.2 | 79.8 ±10.3 | 82.3 ±9.7 | 79.8 ±10.3 | 912 |
| ast/gemma@256 dense | 21.1 ±13.2 | 63.2 ±15.8 | 71.1 ±14.5 | 76.3 ±13.2 | 89.5 ±9.2 | 43.3 ±10.9 | 51.6 ±10.8 | 43.3 ±10.9 | 22 |
| ast/gemma@256 RRF | 52.6 ±15.8 | 65.8 ±14.5 | 73.7 ±13.2 | 84.2 ±11.8 | 89.5 ±9.2 | 60.9 ±13.3 | 66.5 ±11.9 | 60.9 ±13.3 | 23 |
| ast/bge dense | 31.6 ±15.8 | 52.6 ±15.8 | 55.3 ±15.8 | 65.8 ±15.8 | 76.3 ±13.2 | 42.3 ±13.6 | 47.9 ±13.3 | 42.3 ±13.6 | 6 |
| ast/bge RRF | 34.2 ±14.5 | 50.0 ±15.8 | 68.4 ±14.5 | 81.6 ±11.8 | 89.5 ±9.2 | 46.7 ±12.9 | 54.9 ±11.7 | 46.7 ±12.9 | 8 |
| ast/bge RRF+rerank | 65.8 ±14.5 | 89.5 ±9.2 | 89.5 ±9.2 | 89.5 ±9.2 | 89.5 ±9.2 | 77.6 ±11.2 | 80.7 ±10.2 | 77.6 ±11.2 | 951 |
| ast/hash dense (floor) | 7.9 ±9.2 | 10.5 ±9.2 | 15.8 ±11.8 | 23.7 ±13.2 | 44.7 ±15.8 | 11.5 ±8.8 | 14.3 ±9.2 | 11.5 ±8.8 | 1 |

## Code queries only

| system | recall@1 | recall@3 | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 | map@10 | ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ast/bm25 | 28.8 ±8.6 | 48.6 ±9.5 | 55.9 ±9.5 | 64.0 ±9.5 | 77.5 ±8.1 | 40.1 ±7.8 | 45.7 ±7.7 | 39.8 ±7.7 | 2 |
| ast/gemma dense | 67.6 ±9.0 | 83.8 ±7.2 | 87.4 ±5.9 | 91.9 ±5.0 | 95.5 ±4.1 | 76.2 ±6.9 | 79.8 ±6.0 | 75.9 ±6.8 | 20 |
| ast/gemma RRF | 56.8 ±9.5 | 74.8 ±8.1 | 83.8 ±7.2 | 89.2 ±5.9 | 92.8 ±5.0 | 67.8 ±7.5 | 72.7 ±6.7 | 67.3 ±7.6 | 23 |
| ast/gemma RRF+rerank | 83.8 ±6.8 | 90.1 ±5.9 | 91.9 ±5.0 | 91.9 ±5.0 | 92.8 ±5.0 | 87.2 ±5.7 | 88.3 ±5.5 | 87.0 ±5.7 | 1078 |
| ast/bm25+rerank | 70.3 ±8.6 | 74.8 ±8.6 | 76.6 ±8.1 | 77.5 ±8.1 | 77.5 ±8.1 | 72.7 ±8.3 | 73.7 ±8.0 | 72.3 ±8.2 | 1245 |
| ast/gemma dense+rerank | 87.4 ±6.3 | 93.7 ±5.0 | 94.6 ±4.1 | 94.6 ±4.1 | 95.5 ±4.1 | 90.3 ±5.1 | 91.2 ±4.6 | 90.0 ±5.1 | 850 |
| ast/gemma(code task) dense | 64.0 ±9.0 | 83.8 ±6.8 | 87.4 ±5.9 | 90.1 ±5.9 | 96.4 ±3.2 | 74.0 ±6.9 | 77.8 ±6.2 | 73.6 ±6.9 | 21 |
| ast/gemma(code task) RRF+rerank | 84.7 ±6.8 | 90.1 ±5.9 | 91.9 ±5.0 | 91.9 ±5.0 | 92.8 ±5.0 | 87.5 ±5.7 | 88.5 ±5.4 | 87.3 ±5.7 | 1055 |
| ast/gemma@256 dense | 59.5 ±9.0 | 81.1 ±7.2 | 86.5 ±6.3 | 90.1 ±5.4 | 96.4 ±3.2 | 71.4 ±6.8 | 75.7 ±6.0 | 71.0 ±6.8 | 22 |
| ast/gemma@256 RRF | 53.2 ±9.5 | 78.4 ±7.7 | 83.8 ±6.8 | 89.2 ±5.9 | 92.8 ±5.0 | 66.9 ±7.3 | 72.2 ±6.5 | 66.6 ±7.1 | 24 |
| ast/bge dense | 52.3 ±9.5 | 76.6 ±7.7 | 84.7 ±6.8 | 89.2 ±5.9 | 92.8 ±5.0 | 65.5 ±7.3 | 71.1 ±6.5 | 65.1 ±7.2 | 6 |
| ast/bge RRF | 47.7 ±9.5 | 72.1 ±8.6 | 82.0 ±7.7 | 84.7 ±6.8 | 91.9 ±5.0 | 60.9 ±7.8 | 66.5 ±7.2 | 60.5 ±7.7 | 8 |
| ast/bge RRF+rerank | 83.8 ±6.8 | 89.2 ±5.9 | 91.9 ±5.0 | 91.9 ±5.0 | 91.9 ±5.0 | 87.0 ±5.9 | 88.1 ±5.4 | 86.8 ±5.8 | 1137 |
| ast/hash dense (floor) | 5.4 ±4.1 | 10.8 ±5.9 | 16.2 ±7.2 | 22.5 ±7.7 | 28.8 ±8.1 | 9.6 ±4.5 | 12.5 ±4.9 | 9.5 ±4.4 | 2 |

## Paired comparisons (percentage points; bold = 95% interval excludes 0)

| comparison (A − B) | Δ recall@5 | Δ mrr@10 |
|---|---:|---:|
| hybrid RRF vs dense only (gemma) | -2.7 [-8.7, +3.4] p=0.829 | -3.7 [-10.3, +2.8] p=0.868 |
| hybrid RRF vs BM25 only | **+24.2** [+17.4, +31.5] p=0.000 | **+25.6** [+20.2, +31.3] p=0.000 |
| dense only vs BM25 only (gemma) | **+26.8** [+18.8, +34.9] p=0.000 | **+29.4** [+20.9, +37.8] p=0.000 |
| + cross-encoder rerank vs RRF | **+11.4** [+6.7, +16.8] p=0.000 | **+20.2** [+14.9, +25.7] p=0.000 |
| + cross-encoder rerank on BM25 vs BM25 | **+20.1** [+14.1, +26.8] p=0.000 | **+31.5** [+25.4, +37.6] p=0.000 |
| EmbeddingGemma 2 vs bge-small (dense) | **+6.7** [+0.7, +12.8] p=0.023 | **+9.8** [+3.9, +15.8] p=0.001 |
| EmbeddingGemma 2 vs bge-small (RRF+rerank) | +1.3 [-1.3, +4.0] p=0.224 | +1.3 [-1.4, +4.2] p=0.181 |
| gemma 768d vs 256d (dense) | +1.3 [-1.3, +4.0] p=0.226 | **+5.1** [+2.5, +8.1] p=0.000 |
| code task prefix vs search prefix (dense) | -2.0 [-6.0, +2.0] p=0.885 | **-4.4** [-7.6, -1.1] p=0.996 |

### Same comparisons, code queries only

| comparison (A − B) | Δ recall@5 | Δ mrr@10 |
|---|---:|---:|
| + cross-encoder rerank vs RRF | **+8.1** [+3.6, +13.5] p=0.000 | **+19.4** [+13.5, +25.8] p=0.000 |
| + cross-encoder rerank on BM25 vs BM25 | **+20.7** [+13.5, +28.8] p=0.000 | **+32.5** [+25.5, +40.1] p=0.000 |
| EmbeddingGemma 2 vs bge-small (RRF+rerank) | +0.0 [-2.7, +2.7] p=0.646 | +0.2 [-2.8, +3.5] p=0.457 |
| code task prefix vs search prefix (dense) | +0.0 [-3.6, +3.6] p=0.603 | -2.2 [-5.9, +1.4] p=0.878 |

### Same comparisons, documentation queries only

| comparison (A − B) | Δ recall@5 | Δ mrr@10 |
|---|---:|---:|
| + cross-encoder rerank vs RRF | **+21.1** [+7.9, +34.2] p=0.000 | **+22.6** [+12.0, +33.5] p=0.000 |
| + cross-encoder rerank on BM25 vs BM25 | **+18.4** [+7.9, +31.6] p=0.000 | **+28.3** [+17.9, +39.2] p=0.000 |
| EmbeddingGemma 2 vs bge-small (RRF+rerank) | +5.3 [+0.0, +13.2] p=0.119 | +4.4 [-0.9, +11.4] p=0.083 |
| code task prefix vs search prefix (dense) | -7.9 [-18.4, +2.6] p=0.954 | **-10.7** [-17.0, -4.8] p=1.000 |

## Error analysis: `ast/gemma RRF+rerank`

11 queries without a relevant chunk in the top 10:

- `s002` (code, synthetic) **What data structures are used to store questions and their difficulty levels?**  
  gold: `packages/qp-pipeline/src/qp_pipeline/game_loop.py`; found at rank >20; top-3: packages/qp-pipeline/src/qp_pipeline/game_loop.py ; Data model > Chroma: `data/chroma_store`; packages/qp-pipeline/src/qp_pipeline/game_loop.py 
- `s006` (code, synthetic) **What external libraries or modules does this code rely on for text processing and tokenization?**  
  gold: `packages/qp-pipeline/src/qp_pipeline/MarkdownChunker.py`; found at rank >20; top-3: packages/qp-pipeline/src/qp_pipeline/MarkdownChunk; packages/qp-pipeline/src/qp_pipeline/MarkdownChunk; qp-pipeline
- `s022` (code, synthetic) **What models are initialized in this class constructor?**  
  gold: `packages/qp-pipeline/src/qp_pipeline/Enricher.py`; found at rank >20; top-3: packages/qp-pipeline/src/qp_pipeline/game_loop.py ; QuestionPrep — next phases (plan for Claude Code) ; packages/qp-pipeline/src/qp_pipeline/game_loop.py 
- `s042` (doc, synthetic) **How can I retrieve real-time updates about the system's operational state?**  
  gold: `docs/api.md`; found at rank >20; top-3: apps/orchestrator/main.py > get_system_status; QuestionPrep — next phases (plan for Claude Code) ; QuestionPrep — next phases (plan for Claude Code) 
- `s050` (code, synthetic) **What is the purpose of the function described in this code snippet?**  
  gold: `packages/qp-pipeline/src/qp_pipeline/verify.py`; found at rank >20; top-3: qp-pipeline; packages/qp-pipeline/src/qp_pipeline/game_loop.py ; packages/qp-pipeline/src/qp_pipeline/ChunkEvaluato
- `s060` (code, synthetic) **How does the system handle errors when an external language model service becomes unavailable during file processing?**  
  gold: `packages/qp-pipeline/src/qp_pipeline/Enricher.py`; found at rank >20; top-3: apps/orchestrator/main.py > run_enrichment_task; QuestionPrep — next phases (plan for Claude Code) ; packages/qp-pipeline/src/qp_pipeline/Enricher.py >
- `s107` (code, synthetic) **How is the audio file converted into a NumPy array?**  
  gold: `packages/qp-voice/src/qp_voice/speech_to_text.py`; found at rank >20; top-3: packages/qp-voice/src/qp_voice/speech_to_text.py >; packages/qp-voice/src/qp_voice/text_to_speech.py >; packages/qp-voice/src/qp_voice/speech_to_text.py >
- `s116` (code, synthetic) **What is the purpose of the function when processing a specific file identifier?**  
  gold: `packages/qp-pipeline/src/qp_pipeline/Embedder.py`; found at rank >20; top-3: Data model > Other files in `data/`; packages/qp-core/src/qp_core/CSVManager.py > CSVMa; HTTP API > Files and question generation
- `s122` (doc, synthetic) **What is the current status of the project and what tasks remain unfinished?**  
  gold: `docs/NEXT-PHASES.md`; found at rank >20; top-3: QuestionPrep — next phases (plan for Claude Code); QuestionPrep > Status; QuestionPrep — next phases (plan for Claude Code) 
- `s124` (code, synthetic) **What is the function of this code snippet?**  
  gold: `packages/qp-voice/src/qp_voice/asr_model.py`; found at rank >20; top-3: packages/qp-pipeline/src/qp_pipeline/verify.py > <; packages/qp-core/src/qp_core/device.py > <module>; packages/qp-pipeline/src/qp_pipeline/prompts.py > 
- `s147` (code, synthetic) **What is the primary characteristic of the prompts managed by this class?**  
  gold: `packages/qp-pipeline/src/qp_pipeline/prompts.py`; found at rank 13; top-3: packages/qp-pipeline/src/qp_pipeline/prompts.py > ; packages/qp-pipeline/src/qp_pipeline/prompts.py > ; packages/qp-pipeline/src/qp_pipeline/prompts.py > 
