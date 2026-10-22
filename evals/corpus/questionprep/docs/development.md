# Development guide

## Setup

```bash
uv sync                         # all workspace packages + pytest, httpx, ruff
uv run uvicorn apps.orchestrator.main:app --reload
```

You also need `llama serve` (llama.cpp) and a GGUF model for question generation, `ffmpeg` for
audio, and the Qwen3-ASR weights if you use voice input (a `Qwen3-ASR-0.6B/` folder in the repository root, or let the first use download `Qwen/Qwen3-ASR-0.6B`; see `QP_ASR_MODEL`). Set
`LLAMA_MODEL` first ([configuration.md](configuration.md)).

## Testing

| Command | What runs | Needs |
|---|---|---|
| `uv run pytest` | ~360 tests in ~40 s: auth, DB, chunking, scoring with fake encoders, API (401 matrix, ownership matrix), uploads, deletion, results, model registry, LLM client against a local HTTP stub, SSE, Node tests | nothing |
| `uv run pytest -m gpu` | the 34 labelled scoring cases through the real bge + NLI models | cached / downloadable models |
| `uv run pytest -m llm` | one chat completion against a running server | `llama serve` on :8080 |
| `node --test tests/js` | front-end logic (also run by pytest) | Node ≥ 20 |

Tests never touch `data/`: `tests/conftest.py` points `QP_DATA_DIR` at a temp directory and swaps in
fake models and a fake Chroma. Details in [tests/README.md](../tests/README.md).

After a change to security-relevant code, do a **mutation check**: break the check on purpose (for
example remove an ownership test in `main.py`) and confirm a test fails.

## Lint and CI

`uv run ruff check .` (rules: syntax errors, undefined names, unused imports/variables; see
`ruff.toml`). `.github/workflows/ci.yml` runs `uv sync --frozen`, ruff, `node --check` on the JS, and
`pytest -m "not gpu and not llm"`.

## Evaluations

`evals/` holds scripts for judging model or prompt quality; they are not run by CI. See
[evals/README.md](../evals/README.md). `evals/results/` is git-ignored.

## Code conventions

* Package code lives in `packages/*/src/<package>/`; the app in `apps/orchestrator/`.
* Heavy models are obtained only through `qp_core.models` (never `SentenceTransformer(...)` directly).
* Status lines: `emit(msg, user_id)` for anything containing file names or ids, `emit(msg)` only for
  system lines free of private data.
* Every new `/api/` route is automatically covered by the 401 test; add it to `PUBLIC_API` in
  `tests/test_api_auth.py` only if it is intentionally public.
* Schema changes: add an `ALTER TABLE` to the migration list in `DBManager._init_db` and a test in
  `tests/test_db_manager.py`.

## Known issues

* **Scoring**: answers that are cut off mid-sentence still score 0.8–1.0, and correct answers in
  different terminology score about 0.28 (pinned as strict xfails in
  `tests/test_scoring_real_models.py`).
* **Hardcoded paths**: `Enricher`, `Embedder`, `game_loop` and `ingester` compute the repo root with
  `parents[4]` / `sys.path` edits and ignore `QP_DATA_DIR`; `LLAMA_MODEL` and `scripts/enrichment.sh`
  default to a machine-specific path (Phase 3.1).
* **SimHash** (k = 3) misses lightly edited documents (about 10 % changed text).
* **Legacy modules** with no importers: `qp_core.CSVManager` and `qp_core.VectorStore` (the vector
  store in use is `Embedder.QAVectorStore`). One-off scripts were moved to `scripts/legacy/`.
* `docling_ocr.py` runs Docling with `AcceleratorDevice.AUTO` regardless of `QP_DEVICE`.
* Access log lines contain SSE tickets (single-use, 30 s).

## Roadmap

[NEXT-PHASES.md](NEXT-PHASES.md): Phase 3 (config + packaging, split `game_loop.py`, front-end
consolidation, stress-detector fixes, auth hardening) and Phase 4 (operations, docs, model evals).
