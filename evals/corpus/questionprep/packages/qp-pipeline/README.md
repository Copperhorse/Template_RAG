# qp-pipeline

Turns documents into interview questions and scores answers. Import name: `qp_pipeline`.
The flow is described in [docs/architecture.md](../../docs/architecture.md).

| Module | Stage | Purpose |
|---|---|---|
| `docling_ocr.py` | ingest | `PDFDocumentConverter`: PDF → (metadata, Markdown) with Docling. Get the shared instance from `qp_core.models.get_docling_converter()`. |
| `MarkdownChunker.py` | ingest | Header-aware chunking; code, math and table blocks are never split. |
| `ChunkEvaluator.py` | ingest | Flags unusable chunks (TOC, references, copyright, links, low text ratio) and scores quality. |
| `ingester.py` | ingest | `ingest()` → `IngestResult(status, file_id, duplicate_of, message)`; also an interactive CLI (`python -m qp_pipeline.ingester`). |
| `Enricher.py` | enrich | `LLMClient` (timeouts, `LLMUnavailable`, token budgets), `AnswerValidator` (lexical / bge / NLI gates), `EnrichmentManager` (`enrich_single_file`, `run`). CLI: `uv run -m qp_pipeline.Enricher`. |
| `Embedder.py` | index | `QAVectorStore` (Chroma collection `qa_pairs`) and `VectorIndexer` (`index_file`, `delete_embeddings_for_file`, `search`). |
| `game_loop.py` | interview | `LogicEngine` (scoring), `InterviewSession` (used by the API), `TerminalInterview` (Rich CLI: `uv run python -m qp_pipeline.game_loop`). |

## Scoring in `LogicEngine`

Lexical + bge cosine + NLI (only if bge ≥ 0.35) → contradiction caps, entailment boosts, neutral
scales; verbatim copies use a lexical override; answers under 85 % of the reference length are
penalised. Thresholds are constants at the top of `game_loop.py`. Known weaknesses are listed in
[docs/development.md](../../docs/development.md#known-issues).

## Notes

* `game_loop.py` (~1400 lines) mixes the engine, the web session and the terminal UI; splitting it is
  planned (Phase 3.2).
* Several modules still locate the repo with `parents[4]` and `sys.path` edits (Phase 3.1).
* Prompts in `Enricher.py` contain model-specific wording ("reasoning steps of 5 words") that may not
  suit every model; evaluate before changing ([evals/](../../evals/README.md)).

Tests: `tests/test_chunk_evaluator.py`, `test_markdown_chunker.py` (golden files), `test_ingester.py`,
`test_logic_engine.py`, `test_llm_client.py`, `test_scoring_real_models.py` (`-m gpu`).
