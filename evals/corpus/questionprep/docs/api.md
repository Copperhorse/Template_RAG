# HTTP API

Auth: send `Authorization: Bearer <token>` (token from `/api/auth/login`). Errors are JSON
`{"detail": "..."}`. Unknown or foreign ids return `404` (never `403`) so existence does not leak.
The live OpenAPI schema is at `/docs` when the server runs.

## Pages (HTML, public)

`/` landing · `/login` · `/profile` · `/interview[?file_id=…]` · `/session?sid=…` · `/companion` ·
`/sw.js` (service worker).

## Auth and account

| Method & path | Auth | Notes |
|---|---|---|
| `POST /api/auth/signup` | – | `{username, email, password}`; `username` is a unique display name, `email` is validated and stored lower-case and unique (case-insensitive); `400` if either exists, `422` if the email is malformed; 5/min per IP |
| `POST /api/auth/login` | – | **`{email, password}`** (case- and whitespace-insensitive email) → `{token, user}`; `401 Invalid email or password` for both unknown email and wrong password; 10/min per IP |
| `GET /api/auth/profile` | ✓ | current user |
| `PUT /api/users/{user_id}/email` | ✓ self | `{new_email}`; this is the login address; `422` if malformed, `409` if taken |
| `DELETE /api/users/{user_id}` | ✓ self | deletes files, embeddings, results; `207` (account kept) if some embeddings could not be removed |

## Files and question generation

| Method & path | Notes |
|---|---|
| `POST /api/files/ingest` | multipart `file`; `400` not a PDF, `413` too large, `409` same bytes already uploaded (`{detail, file_id, file_name}`); `200 {status:"processing"}`, work continues in the background; 5/min |
| `GET /api/files` | the user's files |
| `POST /api/questions/generate` | `{file_id}`; starts LLM enrichment; returns `{skipped:true}` if the file already has questions or is running; 10/min |
| `GET /api/files/{file_id}/audit` | metadata, accepted questions (no answers), rejections with reasons |
| `DELETE /api/files/{file_id}` | `502 {failed:[id]}` if embeddings could not be removed (file kept, retried later) |
| `DELETE /api/files/all/{user_id}` | self only; `207 {deleted, failed}` on partial failure |

## Interview

| Method & path | Notes |
|---|---|
| `POST /api/interview/start` | `{file_id?}` → `{session_id, first_question}`; `404` if no questions |
| `POST /api/interview/evaluate` | `{session_id, user_answer ≤ 5000 chars}` → `{evaluation, next_question, is_terminal}` |
| `GET /api/interview/{sid}/status` | live session only |
| `GET /api/interview/{sid}/summary` | live or stored; includes per-question text, answer, reference, score, feedback |
| `GET /api/interview/history` | the user's stored sessions, newest first |
| `DELETE /api/interview/{sid}` | ends the session (results are saved first) |

## Voice

| Method & path | Notes |
|---|---|
| `POST /api/analyze-speech` | multipart `audio` (Opus) → `{transcript, stutter_flag, disfluency_rate, details}` |
| `POST /api/tts` | `{text ≤ 2000 chars}` → `audio/wav` |

## Live status

| Method & path | Notes |
|---|---|
| `POST /api/events/ticket` | ✓ → `{ticket, expires_in: 30}`; single use; 60/min |
| `GET /api/events?ticket=…` | Server-Sent Events. Lines are plain text such as `[INFO] ingest: ✓ notes.pdf ingested`. `401` without a valid ticket (a bearer token also works for non-browser clients) |
| `GET /api/status` | anonymous → `{llm_server_running}`; signed in → adds `active_enrichments`, `sessions_with_asr`, `active_sessions`, `models` |
