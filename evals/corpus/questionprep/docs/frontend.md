# Front end

Server-rendered HTML (Jinja2) plus plain JavaScript, no build step. Everything lives in
`apps/orchestrator/` (`templates/`, `static/`, `sw.js`).

## Pages (`templates/`)

| Template | Route | Scripts | Purpose |
|---|---|---|---|
| `index.html` | `/` | inline | landing page |
| `auth.html` | `/login` | `app.js` | sign in / sign up, stores the token |
| `profile.html` | `/profile` | `app.js`, `status-panel.js` | upload PDFs, Generate, audit modal, delete, account actions, live status panel |
| `interview.html` | `/interview` | `interview.js`, ONNX runtime, stress detector | chat-style interview with voice input and stress indicator |
| `session.html` | `/session?sid=` | `auth-fetch.js` | results of a finished session |
| `companion.html` | `/companion` | stress detector | standalone stress-monitor PWA (registers `sw.js`) |

## JavaScript (`static/js/`)

| File | Role |
|---|---|
| `app.js` | auth forms, file list, upload, Generate, audit modal, toasts, account actions |
| `interview.js` | starts / resumes sessions (per-file), sends answers, TTS playback, voice recording |
| `auth-fetch.js` | wraps `fetch` to add `Authorization: Bearer <qp_token>` to same-origin calls and redirect to `/login` on `401`. `app.js` and `interview.js` still carry a pasted copy; consolidation is planned (Phase 3.3) |
| `status-panel.js` | floating log / status panel; gets a fresh SSE ticket on every (re)connect |
| `tcn-stress-detector.js`, `tcn-worker.js`, `audio-worklet.js` | microphone → 16 kHz clips → TCN model in a worker → stress level |
| `ort*.js/.mjs/.wasm` | vendored ONNX Runtime Web (see `scripts/install-onnx-local.sh`) |

Other assets: `static/css/styles.css`, `static/models/tcn_audio_model.onnx`, `static/manifest.json`,
`static/icons/lucide/*.svg` (fetch with `scripts/download_icons.sh`).

## Conventions

* Browser storage keys: `qp_token`, `qp_user_id`, `qp_session_id`, `qp_session_file`, `qp_draft_answer`.
* Any user-supplied text put into `innerHTML` must go through the page's `escapeHtml` helper.
* API calls that can return `207` or `409` must handle them explicitly (`res.ok` is true for 207).
* `sw.js` must never cache `/api/*` (responses are per user).
* Tests for front-end logic are Node tests in `tests/js/` (run by `pytest` too).

## Stress model

The TCN model's confusion matrix is in [images/tcn-confusion-matrix.png](images/tcn-confusion-matrix.png).
Known detector issues (first clip padded with zeros, duplicate thresholds) are tracked in Phase 3.4 of
[NEXT-PHASES.md](NEXT-PHASES.md).

## Service worker

`sw.js` pre-caches the companion page, stress-detector scripts, ONNX model and WASM for offline use. App code (`/static/**/*.js|css|json`) is fetched network-first so releases are never masked by a stale copy; the ONNX runtime and model stay cache-first. Templates append `?v={{ asset_v }}` (newest static-file mtime, computed at start-up) to local scripts and styles, so a changed file always gets a new URL. Bump `CACHE_NAME` when caching rules change (old caches are deleted on activate).
`/api/*` and `.mjs` requests are passed straight to the network.
