# Architecture

## Components

```
Browser ──HTTP/SSE──► apps/orchestrator (FastAPI)
  ├─ pages + JS + ONNX stress model                 │
  └─ Authorization: Bearer <token>                  ├─► qp_core        SQLite (DBManager), auth, models registry
                                                    ├─► qp_pipeline    ingest, chunk, enrich, index, score
                                                    ├─► qp_voice       speech-to-text, text-to-speech
                                                    ├─► ChromaDB       data/chroma_store (embeddings of Q/A pairs)
                                                    └─► llama serve    child process on localhost:8080 (OpenAI-compatible)
```

Python packages form a [uv workspace](../pyproject.toml): `qp-core`, `qp-pipeline`, `qp-voice`,
the app `orchestrator`, and `qp_notebooks`.

## 1. Ingestion (upload → chunks)

`POST /api/files/ingest` → `run_ingestion_task` → `qp_pipeline.ingester.ingest()`

1. **Validate**: `%PDF-` magic bytes, size ≤ `QP_MAX_UPLOAD_MB`, SHA-256 computed while streaming.
   The same user re-uploading identical bytes gets `409` before any conversion work.
2. **Convert**: Docling turns the PDF into Markdown (shared converter from `qp_core.models`).
3. **Near-duplicate check**: a SimHash of the Markdown is compared with the *same user's* files.
4. **Chunk**: `MarkdownChunker` splits by headers, keeps code / math / table blocks intact.
5. **Evaluate**: `ChunkEvaluator` marks chunks unusable (TOC, references, copyright, low text ratio…).
6. **Save**: file row, chunk rows, SHA-256 and SimHash; the file is assigned to the user.

`ingest()` returns an `IngestResult(status = ok | duplicate | failed, …)`; progress lines go to the
user's live status feed.

## 2. Enrichment (chunks → questions)

`POST /api/questions/generate` → `run_enrichment_task`, which starts `llama serve` if needed and then
runs `EnrichmentManager.enrich_single_file` (`qp_pipeline/Enricher.py`). Per usable chunk:

| Step | What happens |
|---|---|
| Metadata | LLM returns summary, tags and triplets; tags / triplets not found in the text are dropped |
| Pass 1 | LLM proposes questions (Easy / Medium / Hard) with a verbatim `source_quote` |
| Quote | the quote is located in the chunk (`verify.locate_quote`) and replaced by the exact chunk text, so the stored quote is always verbatim; a quote that cannot be found rejects the pair before any answer is written |
| Pass 2 | LLM writes a short reference answer from the quote (skipped by the `combined` prompt sets) |
| Filters | Pass-2 refusal (`NOT_ENOUGH_INFORMATION`) and deflection patterns |
| Verifier | prose chunks: `verify.py` checks the answer against the chunk (numbers must occur in it, no mostly-unfamiliar sentence, at most one unfamiliar technical term), then the question (an answer that only repeats it, a "how many" answer with no quantity, a "why"/"purpose" answer with no reason, an answer far from its quote). Math chunks keep the lexical → bge → NLI validator |
| Judge (optional) | `QP_VERIFY_JUDGE=d1`: pairs that passed the verifier go to Liquid AI's D1 decision model, which answers "is the answer supported by the chunk?" and "does it give what the question asks?" as probabilities; a pair below the threshold is rejected with the reason. Off by default; it sends chunk, question and answer text to an external API |

The verifier checks provenance and support. It cannot tell that a grounded answer does not really answer the
question (about 1 accepted pair in 50 on the gold set, more in the held-out runs); local judges were tried and did not
help; the optional D1 judge does, see [evals/report.md](../evals/report.md).

Accepted pairs go to `chunk_questions`, rejected ones (with a reason) to `chunk_rejections`.

**Failure handling** (`LLMClient`): timeouts (`LLM_TIMEOUT_S`), one retry, `max_tokens` = reasoning
budget + answer size. If the *server* fails (unreachable, timeout, 5xx) the file is aborted with
`LLMUnavailable`: no rejection rows are written and the chunks stay pending for a re-run. If the
*output* is unusable (garbage, empty, refused) it is recorded as a rejection.

Optionally (`QP_INDEX_EMBEDDINGS`, default on) `VectorIndexer` then embeds each Q/A pair into Chroma.
Nothing on the web path reads Chroma yet; it is kept for planned semantic features.

## 3. Interview (questions → results)

`POST /api/interview/start` creates an in-memory `InterviewSession` (`qp_pipeline/game_loop.py`),
optionally scoped to one file. Each `POST /api/interview/evaluate` runs `LogicEngine.analyze_response`:

1. **Lexical** score (bidirectional fuzzy match).
2. **Bi-encoder** cosine similarity (bge-small).
3. **NLI cross-encoder** (only when the bi-encoder score ≥ 0.35): contradiction caps the score,
   entailment slightly boosts it, neutral scales it.
4. **Lexical override** only for verbatim copies; **length guard** penalises answers under 85 % of the
   reference length.
5. **Difficulty**: exponential moving average (α = 0.3) of the score → Easy < 0.35 ≤ Medium ≤ 0.75 < Hard.

Results are written to `session_results` after every answer, so they survive restarts and the
30-minute session TTL. `GET /api/interview/{id}/summary` reads memory first, then the stored copy.

## 4. Voice and stress

* Server: `POST /api/analyze-speech` decodes Opus with ffmpeg, transcribes with Qwen3-ASR and counts
  disfluencies (repetitions, fillers); `POST /api/tts` synthesises questions with Pocket-TTS.
* Browser: `tcn-stress-detector.js` runs a TCN ONNX model in a Web Worker over the microphone
  stream and reports a stress level; `companion.html` is a standalone PWA version.

## 5. Cross-cutting

**Authentication.** `qp_core/auth.py` issues HS256 bearer tokens (secret from `QP_JWT_SECRET` or
`data/.jwt_secret`). Every API route except signup / login / minimal `/api/status` requires a token,
and file / session access is owner-checked (other users' ids look like 404s). Passwords are
PBKDF2-SHA256 (260 000 iterations).

**Live status (SSE).** `EventSource` cannot send headers, so the client trades its token for a
single-use, 30-second ticket (`POST /api/events/ticket`) and connects to `/api/events?ticket=…`.
Each stream belongs to a user; ingest / enrichment / session / voice lines go only to that user,
system lines (llama, model loading) to everyone signed in and contain no file names or ids.

**Models.** `qp_core/models.py` loads bge, the NLI model and Docling once per process (thread-safe,
device from `get_device()`: CUDA → MPS → CPU, override `QP_DEVICE`). `QP_PRELOAD=1` warms them at
start-up. `/api/status` (signed in) lists what is loaded.

**Deletion.** Chroma first, then SQLite. If Chroma fails the rows are kept and recorded in
`pending_deletions`, retried at start-up and after each delete; `scripts/reconcile_chroma.py`
audits drift. See [data-model.md](data-model.md).

**llama server lifecycle.** `main.py` starts `llama serve -m <model> -ngl <n> --reasoning-budget <n>`
as a child process (single-flight, health-checked on `/v1/models`) and stops it on shutdown.
`scripts/enrichment.sh` does the same for command-line runs and reuses a server that is already up.
