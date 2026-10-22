# QuestionPrep — next phases (plan for Claude Code)

> **Status (2026-09-30):** Step 0 and Phase 2 (2.1–2.7) are complete on branch `phase-2`. Phases 3 and 4 are open. Decisions D1, D2 and D4 were taken at their defaults; D3 is still open. Off-plan work done on `phase-2` (prompt sets, `fewshot` default, `verify.py`, eval harness and gold set) is summarised in `evals/report.md`; its open follow-ups are task **3.6**.

Written after the Phase 1 patch (auth, GPU selection, llama lifecycle, enrichment-loop fix, file-scoped interviews).
Hand this file to Claude Code on the machine that has the repo, GPU and models.

**Kickoff prompt**
> Read NEXT-PHASES.md. Do "Step 0" first, then Phase 2 only, one task at a time, one commit per task on branch `phase-2`. After each task run its checks and give me the short report described under "Rules". Stop and ask at any ⚠ Decision that has no default answered in the file.

---

## Rules for every task

- Keep API paths and behaviour stable unless the task says otherwise. No drive-by refactors.
- Each task ends with: tests added or updated, `ruff check` clean on touched files, `node --check` on touched JS, and the manual check listed in the task.
- Report per task (5 lines max): what changed, tests added, commands run with results, anything **not** verified, anything surprising.
- Evidence tags used below: **[V]** = verified by reading the code, **[I]** = inferred, confirm before relying on it.
- The planner never saw: `templates/*.html`, `sw.js`, static assets, `pyproject.toml` / `uv.lock`, `MarkdownChunker.py` internals, real data. Read them before editing anything that touches them.
- Repo layout looks like a uv workspace (`parents[4]` in several modules) **[I]**. Discover the real layout first.

## Current state (Phase 1, already delivered as `phase1.zip`)

- New `qp_core/auth.py` (HS256 tokens, stdlib only) and `qp_core/device.py` (`get_device()`: cuda → mps → cpu, override `QP_DEVICE`).
- `main.py`: every route except `/api/status`, `/api/events`, pages requires `Authorization: Bearer`; user comes from the token; ownership checks on files and sessions; blocking work moved off the event loop; single-flight llama start; `llama serve … -ngl 99 --reasoning-budget 4096`.
- `DBManager.get_pending_files` no longer re-selects processed chunks; `Enricher.run()` terminates.
- Frontend: fetch shim adds the token (pasted into `app.js` and `interview.js`, also `auth-fetch.js`); toasts escaped; interviews scoped by `?file_id=`.

---

## Step 0 — Apply and verify Phase 1 on the real machine (no new features)

Phase 1 was tested only against stubbed models, a fake `llama`, and jsdom. Nothing has run on the real stack yet.

Apply the patch, run the existing tests, then check each line. Fix failures in a `phase1-fixes` commit.

| # | Check | Expected |
|---|---|---|
| 0.1 | `llama serve --help \| grep -iE "reasoning-budget\|ngl"` | both flags exist in **your** `llama` wrapper. If not, adjust `_build_llama_cmd()` and `enrichment.sh` |
| 0.2 | `uv run python -c "from qp_core.device import get_device; print(get_device())"` | `cuda` |
| 0.3 | Start the API, click Generate, look at `data/server_log.txt` | a line like `offloaded N/N layers to GPU` |
| 0.4 | `nvidia-smi` while answering one interview question | the Python process holds VRAM (bge + NLI on GPU) |
| 0.5 | Score a fixed set of ~20 (question, answer) pairs with `QP_DEVICE=cpu` and again on GPU | labels identical, `bi_score` within ~1e-3. If not, thresholds tuned on CPU need a look **[I]** |
| 0.6 | Browser devtools on **every** page (profile, interview, session, companion) | no 401s. A page that doesn't load `app.js`/`interview.js` needs `<script src="/static/js/auth-fetch.js">` in its template, before other scripts |
| 0.7 | Read `sw.js` | it must not cache `/api/*`, or responses would ignore auth and leak across logins |
| 0.8 | Enrich one fixed PDF with Sharp-MiniCPM5 and with LFM2.5 | compare accepted-question count, rejection reasons, time. Confirm `_extract_json` copes with MiniCPM output. The Enricher prompts say "keep each reasoning step to 5 words", which looks LFM-specific **[I]** |
| 0.9 | Browser that was logged in before the patch | one 401, then lands on `/login` |

Done when every row passes or has a fix committed. Write the results as a table in `docs/phase1-verification.md`.

---

## Phase 2 — Safety net and data integrity

Order: **2.1 first** (tests protect everything after it). 2.2–2.7 are independent of each other. 2.5 must land before 3.2. Read D4 before starting 2.3 and 2.5.

### 2.1 Real test suite + CI — effort M
**Why** `test.py`, `test_pipeline_llm.py`, `test_game_loop.py` contain **0 test functions**, need a live LLM, and `test_game_loop.py` tests a copy (`FixedLogicEngine`), not the real `LogicEngine` **[V]**. Nothing guards refactors.
**Do**
- Unit tests, no network/GPU/LLM by default: `ChunkEvaluator`, `SimHashHandler`, `IDGenerator`, `MarkdownChunker` (golden files from 2–3 small markdown samples), `DBManager` on a temp SQLite (users, files, chunks, pending files, cascade delete, rejections), `auth.py` (tampered / expired / `alg:none` / wrong secret).
- API tests with FastAPI `TestClient`: a 401 matrix over every protected route, a two-user ownership matrix, file-scoped interview, login rate limit. Monkeypatch the model loaders (`LogicEngine._get_bi_encoder/_get_ce_model`, `EnrichmentManager.llm`, `VectorIndexer`) instead of faking imports.
- `LogicEngine` scoring test with fake encoders returning fixed vectors/logits; assert labels and thresholds.
- Move the three script-style files to `evals/` (rename `eval_*.py`), document that they need `llama serve`. Port `FixedLogicEngine`'s cases into unit tests against the real `LogicEngine`, then delete the copy.
- Markers `@pytest.mark.gpu` and `@pytest.mark.llm`, skipped by default.
- CI (GitHub Actions): `uv sync`, `ruff check`, `pytest -m "not gpu and not llm"`, `node --check` on `static/js/*.js`.
**Done when** `uv run pytest` is green in under 60 s with no GPU/LLM; CI green; **mutation check**: temporarily remove one ownership check in `main.py` and confirm a test fails.

### 2.2 Upload validation and duplicate handling — effort M — ⚠ D1
**Why** The web path calls `ingest(..., auto_confirm=True)`, which logs "Duplicate detected" and **continues**, so a re-upload creates a second file with duplicate questions **[V: ingester.py]**. `run_ingestion_task` then says "skipped (duplicate…)", which is misleading **[V]**. No type or size checks on upload **[V]**.
**Do**
- Reject before ingestion: `%PDF-` magic bytes → 400; size over `QP_MAX_UPLOAD_MB` (default 50) → 413; stream to the temp file with a running limit.
- Add `files.sha256` (ALTER migration in the existing style). Exact duplicate **for the same user** → 409 immediately, returning the existing file id and name.
- Near-duplicate (SimHash) is only known after Docling conversion, so make `ingest()` return a structured result (`status: ok | duplicate | failed`, `file_id`, `duplicate_of`) instead of `(bool, str)`. Update `main.py`, `ingester.batch_process`, and the CLI. Surface the outcome to the UI through the SSE message (2.7), and make the "already have this" case a toast.
- Add `DBManager.get_simhashes_for_user(user_id)` so near-duplicate checks are per user (D1 default).
**Done when** tests: non-PDF → 400; oversize → 413; same bytes twice → 409 and one DB row; a different user uploading the same bytes is unaffected.
**⚠ D1** Duplicate scope. **Default: per user** (no cross-account sharing of content or questions). Alternative: global dedup with shared embeddings, which leaks the existence of others' documents.

### 2.3 Consistent deletion (SQLite ↔ Chroma) — effort S–M
**Why** On Chroma failure the delete routes log a warning and delete the SQLite rows anyway, leaving orphan embeddings **[V: `delete_file`, `delete_all_user_files`, account deletion]**. Current impact is small because nothing on the web path reads Chroma (see D4), but orphans would appear in the terminal debug panel and in any future semantic search, and they hold a deleted user's text. Priority depends on D4.
**Do**
- Order: Chroma first. On failure keep the DB rows, record the file in a new `pending_deletions(file_id, attempts, last_error)` table, and return 207 or 502 naming the failed ids.
- Retry pending deletions on startup and on the next delete call.
- `scripts/reconcile_chroma.py`: report (and with `--fix` delete) embeddings whose `file_id` is not in SQLite, and enriched files with no embeddings.
**Done when** a Chroma stub that raises → DB row remains and the response names it; retry clears it; reconcile finds a seeded orphan.

### 2.4 Persist interview results — effort M
**Why** `DBManager.save_session_result` and `get_session_results_for_user` exist but **nothing calls them** **[V: grep across all uploaded `.py`/`.js`]**. Results live only in `active_sessions`, so they vanish after the 30-minute TTL or a restart. The templates weren't seen, so check whether `/session` expects anything else.
**Do**
- Save on terminal state, on `DELETE /api/interview/{sid}`, and in the pruner before it drops a session. Record `start_time` on `InterviewSession`. `history_json` carries a `{"v":1, ...}` header and per-question: id, text, similarity, confidence, feedback, timestamp.
- `GET /api/interview/{sid}/summary` falls back to the DB when the session is not in memory (owner-checked).
- New `GET /api/interview/history` (current user's past sessions, newest first).
**Done when** restart the server → the summary page still loads; another user gets 404; tests for save, fallback and history.

### 2.5 Model registry (speed and VRAM) — effort M
**Why** The same two models (`BAAI/bge-small-en-v1.5`, `cross-encoder/nli-deberta-v3-xsmall`) are loaded separately by `Enricher.AnswerValidator` (once per `EnrichmentManager()`, i.e. per Generate click), `game_loop.LogicEngine` (class-level), `ChromaVerifier` (per instance, terminal debug mode only **[V]**) and `VectorIndexer` (per instance). A new Docling converter is built per upload **[V]**. On a GPU that duplicates VRAM and costs seconds per action.
**Do**
- `qp_core/models.py`: `get_bi_encoder()`, `get_cross_encoder()`, `get_docling_converter()`: lazy, cached, thread-safe, device from `get_device()`. Port `game_loop`'s "local files first, then download" and "CE is optional" behaviour. Guard the Docling converter with a lock **[I: thread-safety unknown]**.
- Replace every constructor site. Expose loaded models and device in `/api/status`. Optional `QP_PRELOAD=1` warms them in a background thread at startup.
**Done when** a test asserts each model class is constructed once across Enricher + game_loop + Embedder; two Generate clicks don't reload (log check); `nvidia-smi` VRAM roughly flat between them.

### 2.6 LLM client hardening — effort S–M
**Why** `OpenAI(base_url, api_key)` uses library defaults, likely a 10-minute timeout and 2 retries **[I: verify in the installed openai-python]**. `_call_model` has no `max_tokens`. Any error returns `{}`, which `_process_chunk` records as a "Metadata generation failed" rejection, and since Phase 1 those chunks are **not retried** by `run()` **[V]**. A dead or hung server therefore silently marks a whole file as rejected.
**Do**
- `timeout` (env `LLM_TIMEOUT_S`, default 120), `max_retries=1`, `max_tokens` on every call (≥ reasoning budget + answer).
- Split failures: transport error or server down → abort the file, write **no** rejection rows, leave chunks pending; unparseable output → rejection row as now.
- Health-check the server before each file. Log latency and token usage per chunk.
- Make sure only `message.content` is parsed; ignore `reasoning_content` **[I: llama-server `--reasoning-format` default `auto`]**.
**Done when** a stub server that hangs → enrichment aborts with a clear error, zero rejection rows, file still pending; a stub returning garbage → rejection recorded.

### 2.7 SSE scoping and auth — effort M — ⚠ D2
**Why** `/api/events` is open. Any client receives every log line, including uploaded file names and session ids **[V]** (Phase 1 only removed user ids). `EventSource` cannot send an `Authorization` header.
**Do (default)**
- `POST /api/events/ticket` (authenticated) returns a single-use ticket valid ~30 s. The client connects with `EventSource('/api/events?ticket=…')`.
- Each SSE queue is tagged with its user. `emit(msg, user_id=None)`: user-scoped lines go only to that user; system lines (llm/asr/tts status) contain no file names or ids.
- Pass `user_id` from `run_ingestion_task` / `run_enrichment_task`. Update `status-panel.js` to fetch a ticket, and to fetch a fresh one on every reconnect.
- Trim `/api/status` to non-sensitive fields.
**Done when** anonymous connection → 401; user A never receives user B's ingest lines (two-client test); reconnect after ticket expiry works.
**⚠ D2** Token storage. **Default: keep bearer in `localStorage` + SSE ticket.** Alternative in 3.5: HttpOnly cookie, which also makes SSE work natively.

---

## Phase 3 — Structure, hardening, frontend

Order: **3.1 → 3.2**. 3.2 needs 2.1 and 2.5 done. 3.3–3.6 independent (3.6 can start first).

### 3.1 Packaging and central config — effort M
**Why** `current_file.parents[4]` plus `sys.path.append` in `Embedder`, `Enricher`, `game_loop`, `ingester`, and `PROJECT_ROOT = BASE_DIR.parents[1]` in `main.py` **[V]**. Hardcoded `/home/copper/...` defaults in `main.py` and `enrichment.sh` **[V]**. `Enricher.py` used to swallow its own import error, so imports are fragile.
**Do**
- `qp_core/config.py` (pydantic-settings or a frozen dataclass): data dir, DB path, Chroma dir, llama settings, JWT settings, limits. One source, env / `.env` driven.
- Delete every `parents[n]` and `sys.path` hack; make the packages importable via the workspace `pyproject`. Remove machine paths from code; model path comes from config and fails with a clear message if unset. `.env.example` and a minimal stdlib `.env` loader (`qp_core/env.py`) already exist; fold them into the config object. Make sure `data/` (contains `.jwt_secret` and the DB) is git-ignored.
**Done when** a fresh clone with only a `.env` runs `uvicorn …` and `uv run -m qp_pipeline.Enricher`; `grep -rn "parents\[\|/home/copper\|sys.path"` finds nothing outside `.env.example` and docs.

### 3.2 Split `game_loop.py` (1,436 lines) — effort M–L
**Why** It mixes the scoring engine, web session and the Rich terminal UI. `_quote_is_grounded` is duplicated in `Enricher.py` **[V]** (note: the Enricher copy is now only the pre-`verify.py` baseline for `evals/eval_verifier.py`; prose chunks use `verify.locate_quote`, so decide whether the `game_loop.py` copy should move to `qp_core/text.py` or be replaced by it).
**Do** Pure move, no behaviour change: `scoring/` (LogicEngine, NLI helpers), `session.py` (InterviewSession, InterviewContext), `terminal_ui.py` (TerminalInterview, `main`). Shared `_quote_is_grounded` → `qp_core/text.py`. Delete `qp_pipeline/VectorStore.py`: only `Embedder.QAVectorStore` is used and the two have different schemas **[V: no importers of VectorStore.py]**.
**Done when** the 2.1 suite passes unchanged; `git diff -M` shows moves and import edits only.

### 3.3 Frontend consolidation — effort S
- Include `auth-fetch.js` in the base template; delete the pasted shim from `app.js` and `interview.js`.
- One `apiFetch` helper and one place for the `qp_*` storage keys.
- `DEBUG = true` in `audio-worklet.js`, `tcn-stress-detector.js`, `tcn-worker.js` **[V]**: default off; enable via `?debug=1`. The worklet currently logs every 256 ms chunk.
**Done when** the console is quiet by default; jsdom/Node smoke tests still pass.

### 3.4 Stress-detector fixes — effort M — ⚠ D3
- **First clip contains ~3 s of zeros.** The clip is sent when `_samplesSinceLastClip >= hop` (2 s) but the ring buffer is 5 s and is not required to be full **[V]**. Require `_ringWritePos >= _clipSamples` before the first clip.
- **`THRESHOLD_HIGH` (0.65) and `THRESHOLD_STRESSED` (0.47) both return `"stressed"`** **[V: tcn-worker.js]**, so the 0.65 tier does nothing. **⚠ D3** Default: remove `THRESHOLD_HIGH`. Alternative: add a distinct level.
- Worker ignores the `wasmDir` it receives and hardcodes the path **[V]**. Use the parameter.
- `analyseClip` transfers `pcm.buffer`, detaching the caller's array **[V]**. Transfer a copy.
- **The stutter flag fires on fluent speech** **[V: 2026-09-30, Qwen3-ASR on 14 generated clips]**. `analyze_disfluencies` counts "like" as a filler (`DISFLUENCY_MARKERS`) and counts a repeated function word inside a window as a repetition (`count_windowed_repetitions`, "by **the** window and watch **the** rain"), so a clean 12-word sentence ("Would you like to sit by the window and watch the rain?") scores 2/12 and is flagged `stutter=True`; 4 of 14 clips were flagged, none of them stuttered. Short transcripts make the rate jump. Fix: drop "like" and require a repeated *content* word (or a minimum transcript length) before flagging, then re-check on these clips.
- Feature parity with training **[I: cannot check from here]**: add a golden test, one fixed WAV → expected 8 probabilities from the Python training/export code, within tolerance.
**Done when** a Node test shows the first clip has no zero padding; the golden test passes; thresholds behave per D3.

### 3.5 Auth hardening — effort M — depends on D2
- Password hashing: versioned format (`pbkdf2_sha256$<iters>$salt$hash`, ≥ 600k iterations per OWASP guidance **[I: confirm current figure]**, or argon2id via `argon2-cffi`). Keep verifying the legacy `salt:hash` (260k) form and **re-hash on successful login**.
- Password policy: min 8, max 256 characters.
- Revocation: `users.token_version`, carried as a claim; logout and "log out everywhere" bump it. Shorter default TTL (12 h) with sliding refresh, or keep 7 days now that it is revocable.
- Throttling per username, not just per IP; trust `X-Forwarded-For` only if configured.
- Security headers middleware (CSP, `X-Content-Type-Options`, `Referrer-Policy`). CSP needs an audit of inline scripts in the templates **[I]**.
- **⚠ D2 (revisit)**: only if the app will be reachable beyond localhost, move the token to an HttpOnly `SameSite=Strict` cookie plus a CSRF header check. That removes the token from JS (XSS) and lets `EventSource` authenticate natively.
**Done when** a legacy-hash user logs in and their hash is upgraded; a token issued before logout → 401; tests for each.

### 3.6 Verifier follow-ups: paraphrase, one-word errors and NLI — effort M
**Why** `qp_pipeline/verify.py` (prose chunks, since `6a8fbae`; measured in `evals/report.md`) checks provenance and lexical support of short extractive answers. Two measured limits **[V]**:
- On the 34 game-loop cases (`evals/scoring_cases.py`, run by `evals/eval_verifier_cases.py`) it accepts 2 of the 7 answers that should pass (old lexical → bge → NLI chain: 4) and 1 of the 12 that should fail (old: 0). It rejects true paraphrases (a number such as "two hosts" that the source only implies; the rare-term check firing on inflected verbs such as "calculates"), and it passes a one-word meaning change ("added to" instead of "multiplied by" the Value matrix).
- The gold set (`evals/corpus/gold_qa.json`) has no verb or operator swaps, so it never measured that. Only one such case exists (the game-loop critical error), so any claim about it rests on n = 1.
Ad-hoc runs on 2026-09-30 (not committed, re-create them): on the game-loop cases NLI entailment (`cross-encoder/nli-deberta-v3-xsmall`, whole reference as premise) separates should-pass from should-fail with AUROC 0.95 and catches the swap (entailment 0.05, contradiction 0.85); HHEM-2.1-Open misses it (0.84) and scores paraphrases low. On the gold set (short answers against a chunk or quote) the same NLI model is at chance for real bad pairs (AUROC 0.54–0.55) because short answers come out "neutral". So NLI seems right for long, paraphrased answers and wrong for short extractive ones, but that has not been tested on one-word errors in realistic data.
**Do**
- **Test data first.** Add verb / operator / comparative swap negatives to `build_gold_set.py` `synthesize()` (seeded, `synthetic=true`; e.g. multiplied↔added, increases↔decreases, before↔after; avoid swaps that stay true, such as encoder↔decoder for a shared fact), regenerate `gold_qa.json`, and re-run `evals/eval_verifier.py`. Expect the verifier's false-accept to rise; record it, do not tune yet.
- **Commit the evidence.** Extend `eval_verifier_cases.py` with NLI (entailment and contradiction) and HHEM columns, whole source as premise, so the numbers above are reproducible.
- **Test NLI only where it works.** Apply it to answers of at least N content words (choose N before looking at results; the game-loop answers run about 49–132 words), premise = the chunk, also trying the question + answer as one declarative claim. Write the decision rule first, for example: adopt only if it removes at least half of the swap negatives among long answers while rejecting at most 3% of the long good pairs; otherwise record the result and add no NLI gate. Do not touch `verify.py` thresholds in the same step.
- **Known rough edges, fix only against a fresh held-out set** (thresholds so far were tuned on the gold set): the number rule on implied counts, and the rare-term check on inflected forms (strip common suffixes before asking the tokenizer). A held-out set means a new PDF with at least one code or table chunk, generated and read pair by pair as in `evals/report.md` ("Held-out run").
- **Variance and quality.** Repeat the `s5` held-out runs 2–3 times before trusting differences of one or two questions. Two questions stay open and unmeasured: whether practising these questions improves interview performance, and why Hard questions are still rare (2–3B generators conflate two facts; the verifier cannot see that).
**Done when** the swap negatives are in the gold set with old/new numbers in `evals/report.md`; a committed script reproduces the NLI/HHEM numbers on the game-loop cases; the NLI decision is recorded with its pre-declared rule; `uv run pytest` passes.

---

## Phase 4 — Operations, docs, model quality

### 4.1 Dependency hygiene — effort S
`uv lock --check` in CI, `pip-audit` (or `uv pip audit`), Renovate/Dependabot, pin and record the llama.cpp build the flags were tested against.

### 4.2 Documentation — effort M
README (setup, GPU, env-var table), architecture doc (ingest → chunk → evaluate → two-pass enrich → validate → index → interview scoring), runbook (`server_log.txt`, llama failure modes, reconcile script), API reference from the OpenAPI schema.

### 4.3 Observability and backups — effort M
- Structured JSON logs with a request id.
- `/api/health`: DB, Chroma, llama, device. Separate from `/api/status`.
- Backup script: `sqlite3 .backup` plus a copy of `chroma_store/` taken while quiet.
- `data/server_log.txt` is truncated on every start (`open(LLAMA_LOG, "w")`) **[V]**: rotate instead.

### 4.4 Model and prompt evaluation — effort M–L
> **Status:** a first pass is done and written up in `evals/report.md` (four models, seven prompt sets, two reasoning budgets, five chunks of one paper; default is now the `fewshot` prompt set). Still open: the 3–5 PDF corpus, human rating of 30 sampled questions and repeat runs (see 3.6).
On a fixed corpus of 3–5 PDFs, compare LFM2.5-1.2B, Sharp-MiniCPM5-2B, Gemma-4-E2B at reasoning budgets 0 / 1024 / 4096. Metrics: accepted-question rate, rejection-reason mix, latency, VRAM, and human rating of 30 sampled questions. Output `evals/report.md`, pick the default, adapt the Enricher prompts (drop the LFM-specific "5 words per reasoning step" line if the winner doesn't need it **[I]**). Reuse your existing benchmarking harness where it fits.

### 4.5 Scoring calibration (optional) — effort M
> **Status (2026-09-30): first pass done** — see `evals/scoring_report.md`. The length guard and cut-off detection were recalibrated for the 16–19-word references the default prompts generate (correct answers flagged 31/42 → 0/42; 34-case suite 28 → 33 in band). Not done: real (human) labelled answers, a key-fact check for partial answers, terminology.
Difficulty adaptation uses hand-set constants: EMA `alpha = 0.3`, Hard above 0.75, Easy below 0.35 **[V]**. Collect ~100 human-labelled answers and check the labels, verdicts and difficulty transitions against them.

### 4.6 Deployment option (optional) — effort S–M
`compose.yaml` or systemd units for the API and `llama serve`, with GPU passthrough notes.

---

## Impact on quality (assessment, 2026-09-30)

Most of Phases 3–4 is engineering hygiene, security and operations. That matters for shipping and for not losing data, but it
does not change the questions, answers or scores a user sees. By likely effect on output quality **[I]**:

| Task | Effect on question / answer / score quality |
|---|---|
| 3.1 config, 3.2 split `game_loop.py`, 3.3 frontend, 3.5 auth, 4.1 deps, 4.2 docs, 4.3 observability, 4.6 deployment | None (reliability, maintainability, security) |
| 3.4 stress-detector fixes | The stress signal only |
| 3.6 verifier follow-ups | Small, except that D1 (below) changes what is worth doing |
| 4.4 model/prompt evaluation (human rating of 30 questions, more PDFs) | Measurement: the only way to learn whether the questions help interview practice, which nothing has measured |
| 4.5 scoring calibration | Done first pass; it was the most valuable item (the scorer and the question generator had drifted apart) |

**Decision D5 (taken 2026-09-30): D1 is an optional judge, off by default.** Liquid AI's decision model `d1:free`
(`evals/eval_judges.py`, `evals/report.md`) is the only judge that helped: with the deterministic checks first it accepts 0 of
15 real bad and 0 of 99 synthetic bad pairs (they accept 5 and 4), removes all 3 wrong or weak pairs among 29 held-out
ones without touching the other 26, and handles the paraphrase, terminology and one-word-error cases that `verify.py`
cannot. It is an external API, so document text leaves the machine (the app is otherwise fully local). It is implemented as
`verify.D1Judge`, enabled with `QP_VERIFY_JUDGE=d1` and `LIQUID_API_KEY`, and run only on pairs that already passed
`verify.py`. Not yet measured end to end: its effect on accepted-question counts and on run time on a real generation run
(`eval_enrichment.py run ... --verifier new+d1`), and the free tier's rate limits.

## Decisions for you

| ID | Question | Default if you don't answer |
|---|---|---|
| D1 | Duplicate uploads: per-user only, or shared across accounts? | Per user |
| D2 | Token in `localStorage` + SSE ticket, or HttpOnly cookie? | `localStorage` + ticket now; revisit in 3.5 if exposed beyond localhost |
| D3 | Stress tier 0.65: remove it, or make it a distinct level? | Remove |
| D4 | **Chroma has no reader on the web path.** Every Generate embeds all Q/A pairs, but the only code that queries Chroma is the terminal debug panel (`game_loop.py`, `chroma.query`) **[V: grep of all uploaded files; `VectorIndexer.search` has no caller]**. Keep indexing for planned features (semantic search, retrieval-grounded feedback), or make it optional/off? | Keep indexing, behind `QP_INDEX_EMBEDDINGS` (default on). 2.3 becomes low priority if you choose "off" |
| D5 | Use Liquid AI's D1 decision model as a judge of generated pairs? It helps (see "Impact on quality") but sends document text to an external API. | **Decided:** optional, off by default (`QP_VERIFY_JUDGE=d1`) |

## Out of scope / not planned
Larger (8B) generator or judge experiments (declined 2026-09-30); MiniCheck and a judge-by-generator table (considered, not run); `MarkdownChunker` internals (not reviewed); Docling tuning; sharing generated questions between users; the browser TCN model's training pipeline.

## Dependency order
`0 → 2.1 → {2.2, 2.3, 2.4, 2.6, 2.7} and 2.5 → 3.1 → 3.2`; `3.3`, `3.4`, `3.5`, `3.6` any time after 2.1; Phase 4 after Phase 3 (4.4 can run any time after Step 0).
