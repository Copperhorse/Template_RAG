# Configuration

Everything is configured through environment variables; all are optional. A git-ignored `.env` file at the repository
root is loaded at start-up by `qp_core.env.load_dotenv` (the app, the Enricher and the eval scripts call it): copy
[`.env.example`](../.env.example) to `.env` and fill it in. Rules: one `KEY=VALUE` per line, `#` comments, optional
`export ` and quotes; a variable already set in the real environment always wins; `QP_ENV_FILE` points at another file and
`QP_NO_DOTENV=1` turns loading off (the test suite sets it so a real key never reaches a test). `.env` can hold secrets, so it
is ignored by git; keep its permissions at `600`. A central config object is still planned (Phase 3.1).

## Paths and process

| Variable | Default | Effect |
|---|---|---|
| `QP_DATA_DIR` | `<repo>/data` | Where the API keeps the SQLite DB, uploads, llama log and JWT secret. Used by the API and `scripts/reconcile_chroma.py`. **Not yet honoured** by `Enricher` / `Embedder` (they use `RAG_PROJECT_ROOT` / the repo path). |
| `RAG_PROJECT_ROOT` | repo root | Root used by `qp_pipeline.Enricher` to find `data/rag_staging.db`. |
| `QP_HOST`, `QP_PORT` | `127.0.0.1`, `8000` | Only for `python apps/orchestrator/main.py`. |
| `ALLOWED_ORIGINS` | `http://localhost:8000,http://127.0.0.1:8000` | CORS origins, comma-separated. |

## Security

| Variable | Default | Effect |
|---|---|---|
| `QP_JWT_SECRET` | generated into `data/.jwt_secret` (mode 0600) | Token signing secret. Set it for any shared deployment. |
| `QP_TOKEN_TTL_SECONDS` | `604800` (7 days) | Token lifetime. |
| `QP_MAX_UPLOAD_MB` | `50` | Upload size limit. |

## LLM server (`llama serve`)

| Variable | Default | Effect |
|---|---|---|
| `LLAMA_CMD` | `llama serve` | Command used to start the server. |
| `LLAMA_MODEL` | `/home/copper/models/Sharp-MiniCPM5-2B-Q8_K_M.gguf` | GGUF model path (**machine-specific default, set it**). |
| `LLAMA_HOST`, `LLAMA_PORT` | `localhost`, `8080` | Where the server listens and where clients connect. |
| `LLAMA_NGL` | `99` | GPU layers (`-ngl`). Ignored without a GPU. |
| `LLAMA_REASONING_BUDGET` | `4096` | Thinking-token budget; also sizes `max_tokens` for every request. `-1` = unlimited, `0` = no thinking. |
| `LLAMA_EXTRA_ARGS` | empty | Extra arguments appended to the command, e.g. `--ctx-size 8192`. |
| `LLAMA_API_URL` | `http://$LLAMA_HOST:$LLAMA_PORT/v1` | Base URL used by the Enricher client. |
| `LLAMA_MODEL_NAME` | `lfm-2.5-1.2b` | Model name sent in requests (llama-server ignores it). |
| `LLM_TIMEOUT_S` | `120` | Per-request read timeout. Raise it on CPU-only machines. |
| `QP_PROMPT_SET` | `fewshot` | Enrichment prompt set: `baseline` (the original prompts), `nohint`, `grounded`, `fewshot`, `bloom_fewshot`, `combined`, `combined_fewshot`. Defined in `qp_pipeline/prompts.py`; compared in [evals/report.md](../evals/report.md). |
| `QP_VERIFY_JUDGE` | unset (off) | Optional second opinion on generated pairs that passed `verify.py`: `d1` uses Liquid AI's decision model. **Sends the text of each chunk, question and answer to `api.liquid.ai`** (the app is otherwise fully local); needs `LIQUID_API_KEY`. About 2 s per pair; a bad key, rate limiting or a network failure aborts the file and leaves it pending for a re-run. See [evals/report.md](../evals/report.md). |
| `LIQUID_API_KEY` | unset | API key for `QP_VERIFY_JUDGE=d1` (keys start with `liquid_`). Read from the environment only; never put it in a file in the repo. |
| `QP_D1_THRESHOLD` | `0.867` | A pair passes the D1 judge when the lower of its two yes/no probabilities is at least this. The default keeps 97% of the good pairs of the gold set. |

## Models and scoring

| Variable | Default | Effect |
|---|---|---|
| `QP_DEVICE` | auto (`cuda` → `mps` → `cpu`) | Force the torch device, e.g. `cpu`, `cuda:1`. |
| `QP_PRELOAD` | off | `1` loads bge / NLI / Docling in the background at start-up. |
| `QP_ASR_MODEL` | unset | Speech-recognition model: a folder, or a Hugging Face id such as `Qwen/Qwen3-ASR-0.6B`. Unset: a `Qwen3-ASR-0.6B/` folder in the working directory or repository root, else `Qwen/Qwen3-ASR-0.6B` from the Hugging Face cache (downloaded on first use). |
| `QP_INDEX_EMBEDDINGS` | on | `0` skips writing embeddings to Chroma after enrichment. |
| `SCORING_NEUTRAL_FLOOR` | `0.35` | Minimum multiplier applied to a neutral-NLI answer's score. |

## `scripts/enrichment.sh`

Reads `LLAMA_MODEL`, `LLAMA_HOST`, `LLAMA_PORT`, `LLAMA_NGL`, `LLAMA_REASONING_BUDGET`; reuses an
already-running server and only stops one it started itself.

## Constants that are still in code

Session TTL (30 min), upload chunk size, rate limits (signup 5/min, login 10/min, ingest 5/min,
generate 10/min, ticket 60/min), SSE ticket lifetime (30 s), scoring thresholds in
`qp_pipeline/game_loop.py` and validator thresholds in `qp_pipeline/Enricher.py`.
