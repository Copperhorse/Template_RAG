# Data model

Runtime state lives in `data/` (git-ignored, see [data/README.md](../data/README.md)).

## SQLite: `data/rag_staging.db`

Created and migrated by `qp_core.DBManager` on start (`CREATE IF NOT EXISTS` + additive `ALTER`s).
WAL mode, foreign keys on.

| Table | Purpose | Key columns |
|---|---|---|
| `users` | accounts | `user_id`, unique `username` (display name) and `email` (the login; stored lower-case, compared with `LOWER()` so legacy mixed-case rows still work), `password_hash` (`salt:pbkdf2`) |
| `files` | one row per ingested document | `file_id`, `file_name`, `simhash`, `sha256`, `content_length` |
| `user_files` | which user owns which file | unique (`user_id`, `file_id`) |
| `chunks` | Markdown chunks | `chunk_id`, `file_id`, `chunk_index`, `content`, `content_type`, `should_use`, `quality_score`, prev/next ids |
| `chunk_enrichments` | LLM metadata per chunk | `tags`, `triplets`, `summary` |
| `chunk_questions` | accepted Q/A pairs | `question_id` (`<chunk>_qN`), `question_text`, `answer_text`, `source_quote`, `difficulty` (Easy/Medium/Hard), `question_type` |
| `chunk_rejections` | rejected candidates and why | `reason`, `question_text`, `answer_text` |
| `session_results` | finished or in-progress interviews | `session_id`, `user_id`, `start_time`, `end_time`, `questions_attempted`, `average_score`, `final_difficulty`, `history_json` |
| `pending_deletions` | files whose Chroma cleanup failed | `file_id`, `attempts`, `last_error` |

`session_results.history_json` is `{"v": 1, "file_id": …, "questions": [{question_id, question_text,
user_answer, reference_answer, similarity, confidence, feedback, timestamp}]}`.

### "Pending" chunks

A chunk counts as *attempted* once it has a question, an enrichment row or a rejection row.
`get_pending_files()` returns files with usable, unattempted chunks. LLM outages deliberately write
none of those rows, so the chunk stays pending.

### Duplicates

* Exact: same user + same `sha256` → rejected at upload (`409`).
* Near: SimHash (k = 3) against that user's own files, checked after conversion; the file is skipped
  and the user is told through the status feed.
* Content is **not** shared between accounts.

## Chroma: `data/chroma_store`

One collection, `qa_pairs` (cosine). Document id = `question_id`; text = `Question: …\nAnswer: …`;
metadata = `file_id`, `chunk_id`, `difficulty`, `type`; embeddings from bge-small.
Only written when `QP_INDEX_EMBEDDINGS` is on.

### Consistency between the two stores

Delete order is Chroma → SQLite. On a Chroma failure the file's rows stay and a `pending_deletions`
row is written; the API retries at start-up and after any delete. To audit or repair:

```bash
uv run python scripts/reconcile_chroma.py          # report orphans / unindexed files
uv run python scripts/reconcile_chroma.py --fix    # delete orphan embeddings (stop the API first)
```

## Other files in `data/`

| File | Purpose |
|---|---|
| `.jwt_secret` | generated token secret (0600) unless `QP_JWT_SECRET` is set |
| `server_log.txt` | stdout / stderr of the `llama serve` process the API started (truncated on each start) |
| `<uuid>_<name>.pdf` | temporary upload, removed after ingestion |
