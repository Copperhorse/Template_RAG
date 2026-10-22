# QuestionPrep

Interview practice built from your own documents. Upload a PDF, let a local LLM turn it into
interview questions with reference answers, then answer them by typing or speaking. Each answer is
scored against the reference (lexical + embedding + NLI), the difficulty adapts to how you are
doing, and a browser-side model watches your voice for stress signals.

Everything runs locally: FastAPI backend, SQLite + ChromaDB storage, a `llama serve` process for
question generation, and sentence-transformers / Docling / Qwen3-ASR for the rest.

## How it works

```
PDF ──► ingest ──► chunks ──► Generate (LLM, two passes) ──► questions ──► interview ──► results
        Docling    SQLite      metadata → questions →          SQLite      bge + NLI      SQLite
        + SimHash              answers → validation                        scoring
```

See [docs/architecture.md](docs/architecture.md) for the full picture.

## Repository layout

| Path | What it is | Docs |
|---|---|---|
| [`apps/orchestrator/`](apps/orchestrator) | FastAPI app: API, HTML pages, static JS/CSS, service worker | [README](apps/orchestrator/README.md), [frontend](docs/frontend.md), [API](docs/api.md) |
| [`packages/qp-core/`](packages/qp-core) | SQLite access, auth tokens, device selection, model registry, reconcile | [README](packages/qp-core/README.md) |
| [`packages/qp-pipeline/`](packages/qp-pipeline) | Ingestion, chunking, LLM enrichment, embeddings, interview scoring | [README](packages/qp-pipeline/README.md) |
| [`packages/qp-voice/`](packages/qp-voice) | Speech-to-text, disfluency detection, text-to-speech | [README](packages/qp-voice/README.md) |
| [`tests/`](tests) | pytest suite (no GPU / LLM needed) and Node tests for the front end | [README](tests/README.md) |
| [`evals/`](evals) | Scripts that measure model / prompt quality (not run by CI) | [README](evals/README.md) |
| [`scripts/`](scripts) | Operational scripts: enrichment runner, Chroma reconcile, legacy one-offs | [README](scripts/README.md) |
| [`data/`](data) | Runtime state: SQLite DB, Chroma store, logs, JWT secret (git-ignored) | [README](data/README.md), [data model](docs/data-model.md) |
| [`docs/`](docs) | Architecture, configuration, API, development notes, roadmap | [index](docs/README.md) |
| [`tools/`](tools) | Standalone dev helpers | [tcn-dev-server](tools/tcn-dev-server/README.md) |
| [`qp_notebooks/`](qp_notebooks) | Marimo notebook for exploration | [README](qp_notebooks/README.md) |

## Quick start

Requirements: Python 3.13, [uv](https://docs.astral.sh/uv/), a `llama serve` binary on `PATH`
(llama.cpp), a GGUF model file, `ffmpeg` for audio decoding, and preferably an NVIDIA GPU.

```bash
uv sync                                   # installs every workspace package + dev tools

# Point the app at your model (see docs/configuration.md for everything else)
export LLAMA_MODEL=~/models/your-model.gguf
# ...or put settings in a git-ignored .env (cp .env.example .env); see docs/configuration.md

uv run uvicorn apps.orchestrator.main:app --reload
# open http://localhost:8000, sign up, upload a PDF, press Generate, start an interview
```

The app starts `llama serve` itself the first time you press Generate. To run enrichment without
the web app: `bash scripts/enrichment.sh`.

## Common tasks

```bash
uv run pytest                    # unit + API tests, ~40 s, no GPU or LLM
uv run pytest -m gpu             # scoring cases against the real bge / NLI models
uv run pytest -m llm             # smoke test against a running llama server
uv run ruff check .              # lint
uv run python scripts/reconcile_chroma.py          # check SQLite ↔ Chroma consistency
uv run python evals/eval_game_loop.py              # scoring report on labelled answers
```

More in [docs/development.md](docs/development.md).

## Status

Phase 1 (auth, device selection, llama lifecycle) and Phase 2 (tests + CI, upload validation,
consistent deletion, persisted results, model registry, LLM hardening, authenticated SSE) are
done. What is planned next is in [docs/NEXT-PHASES.md](docs/NEXT-PHASES.md); known scoring
weaknesses are listed in [docs/development.md](docs/development.md#known-issues).
