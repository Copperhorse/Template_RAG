# Phase 1 verification (Step 0)

Run on 2026-09-29 against the real stack: RTX A2000 8 GB, `llama serve` wrapper, Sharp-MiniCPM5-2B-Q8_K_M.
Test data: a 3-paragraph biology PDF (one chunk) and a throwaway user, deleted afterwards. DB and Chroma were restored.

| # | Check | Result | Notes |
|---|---|---|---|
| 0.1 | `llama serve --help` has `--reasoning-budget` and `-ngl` | PASS | both present |
| 0.2 | `get_device()` | PASS | `cuda` |
| 0.3 | GPU offload line in `data/server_log.txt` | PASS with fix | this llama build never logs an "offloaded" line. `nvidia-smi` shows `llama` holding 4760 MiB and generation runs at ~55 tok/s. `enrichment.sh` grepped for that line and would have wrongly warned "running on CPU"; it now asks `nvidia-smi` |
| 0.4 | VRAM held by the Python process | PASS | 2116 MiB during enrichment, 2218 MiB while answering an interview question |
| 0.5 | CPU vs GPU scoring parity | PASS | 21 (question, answer) pairs: verbatim, half, scrambled, negated, off-topic, short, vague. 0 label or grader differences; max `bi_score` difference 2.4e-7 (NLI probabilities and final similarity also within 1e-3) |
| 0.6 | No 401s on any page | PASS with fix | `session.html` calls `fetch()` but loads neither `app.js` nor `interview.js`, so it sent no token. Added `auth-fetch.js`. Checked by reading every template's scripts and fetch calls, **not** in a browser |
| 0.7 | `sw.js` must not cache `/api/*` | PASS with hardening | it only ever `put`s `/static/` and `/companion`, but its cache-first `match` covered API requests. Added an explicit `/api/` bypass |
| 0.8 | MiniCPM vs LFM2.5 | PARTIAL | see below |
| 0.9 | Pre-patch browser lands on `/login` | PASS (API level) | `Bearer mock-jwt-token` gets 401; the shim then redirects to `/login`. Not clicked through in a browser |

## 0.8 detail

The LFM2.5-1.2B file from the plan is not on this machine; I used `LiquidAI_LFM2.5-2.6B-Q6_K.gguf`. One chunk only, so treat as a smoke test, not a comparison.

| Model | Accepted | Rejected | Wall time (incl. server start) |
|---|---|---|---|
| Sharp-MiniCPM5-2B | 3 | 2 (`Pass 2 refused`, `Why/How-question lacks causal/mechanism phrase`) | ~2.3 min |
| LFM2.5-2.6B | 0 | 4 (3× `Pass 2 refused`, 1× causal-phrase) | ~2.5 min |

`_extract_json` parsed MiniCPM output fine (questions were produced). The "5 words per reasoning step" prompt line was not tested; it stays **[I]**. A proper comparison is task 4.4.

## Other findings

- `data/.jwt_secret` was untracked but **not git-ignored** (`data/` is otherwise tracked, including the DB and Chroma store). Added to `.gitignore`.
- Re-uploading the same PDF created a second file with its own questions (confirms the 2.2 problem).
- `/static/theme.js` (referenced by `session.html`) returns 404. Not fixed here.
