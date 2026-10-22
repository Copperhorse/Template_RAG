# Answer-level evaluation

70 answerable and 15 unanswerable queries. Rates are Wilson 95% intervals. "Correct" = the answer contains a hand-written key phrase, so it is a lower bound.

## Answerable queries

- gold chunk was in the context the model saw: 79% (55/70; 95% CI 68-87)
- answered (did not refuse): 100% (70/70; 95% CI 95-100)
- answered and cites a chunk that holds the gold snippet: 59% (41/70; 95% CI 47-69)
- answered and contains the expected fact: 81% (57/70; 95% CI 71-89)
- answered and passed every gate: 50% (35/70; 95% CI 39-61)

## Do the gates discriminate?

- correct, among answers that **passed** the gates: 89% (31/35; 95% CI 74-95)
- correct, among answers the gates **flagged**: 74% (26/35; 95% CI 58-86)

## Unanswerable queries (the right behaviour is to refuse)

- refused: 73% (11/15; 95% CI 48-89)
- answered but flagged by the gates: 7% (1/15; 95% CI 1-30)
- answered and passed the gates (the dangerous case): 20% (3/15; 95% CI 7-45)

## If `strict=True` were used (flagged answers become refusals)

- answerable queries answered: 50% (35/70; 95% CI 39-61)
- answerable queries answered correctly: 44% (31/70; 95% CI 33-56)
- unanswerable queries refused: 80% (12/15; 95% CI 55-93)

Mean latency 2.5s per question. Why answers were flagged: {'Unsupported number in answer': 10, 'no verified quote from cited source(s) [1]': 4, 'Unsupported identifier in answer': 15, 'no verified quote from cited source(s) [3]': 1, 'no verified quote from cited source(s) [2]': 3, 'the answer cites no source': 2, 'no verified quote from cited source(s) [5]': 1}

## Per-query record

| id | type | refused | gates | correct | cites gold | answer |
|---|---|---|---|---|---|---|
| d01 | doc | no | pass | True | False | The single-use ticket for the live status stream is valid for approxim |
| d02 | doc | no | flag: Unsupported number in answer: [260000] | True | False | The application uses PBKDF2 with SHA256 for password hashing, employin |
| d03 | doc | no | flag: Unsupported number in answer: [409] | True | False | If the same user uploads the exact same PDF twice, the system checks f |
| d04 | doc | no | pass | True | True | The environment variable for the maximum upload size in megabytes is ` |
| d05 | doc | no | flag: no verified quote from cited source(s) [ | True | True | The default token lifetime is 7 days [1]. |
| d06 | doc | no | pass | True | False | You can check for drift between SQLite and Chroma by running `scripts/ |
| d07 | doc | no | pass | True | True | The delete order is Chroma → SQLite [1], as Chroma is deleted first so |
| d08 | doc | no | pass | True | False | A chunk counts as attempted once it has a question, an enrichment row, |
| d09 | doc | no | pass | True | True | Difficulty adaptation uses hand-set constants: EMA `alpha = 0.3`, Hard |
| d10 | doc | no | pass | False | False | The NLI cross-encoder is consulted when the bi-encoder score is greate |
| d11 | doc | no | pass | True | True | EventSource cannot send an Authorization header, so the client trades  |
| d12 | doc | no | pass | True | True | `sw.js` must never cache `/api/*` (responses are per user) [2], and it |
| d13 | doc | no | pass | True | True | The browser storage keys are `qp_token`, `qp_user_id`, `qp_session_id` |
| d14 | doc | no | pass | True | True | When an account is deleted but some embeddings could not be removed, t |
| d15 | doc | no | pass | True | False | If an upload is too large, the API returns a status code of 413 with t |
| d16 | doc | no | pass | True | True | Unknown or foreign ids return a 404 status code, which means existence |
| d17 | doc | no | pass | True | True | The rate limits are 5/min for signup and 10/min for login [1]. |
| d18 | doc | no | flag: Unsupported identifier in answer: `REASO | True | False | The `REASONING_BUDGET` variable controls the reasoning budget, which i |
| d19 | doc | no | pass | True | False | The ingest function can report one of the following statuses: ok, dupl |
| d20 | doc | no | flag: no verified quote from cited source(s) [ | True | True | The torch device is chosen based on the following order of preference: |
| d21 | doc | no | flag: no verified quote from cited source(s) [ | True | True | The external decision model, Liquid AI's decision model D1, is optiona |
| d22 | doc | no | pass | False | False | Known weaknesses of near-duplicate detection are listed in [docs/devel |
| d23 | doc | no | flag: no verified quote from cited source(s) [ | True | False | The legacy modules with no importers are `qp_core.CSVManager` and `qp_ |
| d24 | doc | no | pass | True | True | You can run the tests that use the real bge + NLI models by executing  |
| d25 | doc | no | pass | True | True | After a change to security-relevant code, you should perform a mutatio |
| d26 | doc | no | pass | True | True | Interview history is stored in `session_results.history_json`, which h |
| d27 | doc | no | flag: no verified quote from cited source(s) [ | True | False | The application starts the LLM server by executing the command specifi |
| d28 | doc | no | pass | True | False | Spoken audio is turned into a transcript by using the `SpeechToText` c |
| d29 | doc | no | flag: the answer cites no source | True | False | The `POST /api/tts` endpoint accepts text with a maximum length of 200 |
| d30 | doc | no | pass | True | True | The `auth-fetch.js` script wraps `fetch` to add `Authorization: Bearer |
| d31 | doc | no | pass | True | False | Rules for the .env file include: one `KEY=VALUE` per line, blank lines |
| d32 | doc | no | flag: Unsupported number in answer: [2] | True | True | When an LLM server is unavailable, the system is designed to abort the |
| d33 | doc | no | pass | True | False | The Chroma collection is called "qa_pairs" [1, 2], and it uses cosine  |
| d34 | doc | no | pass | True | False | An answer that only repeats the question adds nothing, and a "how many |
| d35 | doc | no | pass | False | False | The audit endpoint returns an object containing the file's metadata, t |
| c01 | code | no | flag: Unsupported identifier in answer: `verif | True | True | The function that finds the exact chunk text a generated quote refers  |
| c02 | code | no | pass | True | True | The check_support function verifies that every number in the answer mu |
| c03 | code | no | flag: the answer cites no source | False | False | the\s+text\s+does\s+not\s+(specify/mention/state/provide/include/addre |
| c04 | code | no | flag: Unsupported identifier in answer: `per_d | False | False | The number of questions requested per difficulty depends on the `per_d |
| c05 | code | no | flag: Unsupported identifier in answer: `LLMUn | False | True | The client verifies that the LLM server is reachable by attempting to  |
| c06 | code | no | flag: no verified quote from cited source(s) [ | False | True | Inline /$)` with an empty string and then strips whitespace from the r |
| c07 | code | no | flag: no verified quote from cited source(s) [ | False | False | Code blocks, math, and table blocks are never split during markdown ch |
| c08 | code | no | flag: Unsupported number in answer: [400] | False | True | A table of contents is recognized if the text contains more than 3 lin |
| c09 | code | no | pass | False | True | Character n-gram features are generated by taking substrings of a spec |
| c10 | code | no | pass | True | True | The function `get_device()` picks the device in the order: CUDA -> App |
| c11 | code | no | flag: no verified quote from cited source(s) [ | True | True | The regular expression used to match lines starting with 'export' and  |
| c12 | code | no | pass | True | False | Orphan embeddings, which are Chroma documents whose `file_id` metadata |
| c13 | code | no | flag: Unsupported identifier in answer: `gener | True | True | The `generate_file_id` method in the `IDGenerator` class generates a u |
| c14 | code | no | flag: Unsupported number in answer: [1] | False | False | Heavy models are loaded once per process, and the loading mechanism is |
| c15 | code | no | flag: Unsupported identifier in answer: `Seria | True | True | The `SerializedConverter` shares one Docling converter between threads |
| c16 | code | no | flag: Unsupported identifier in answer: `PDFDo | True | True | Formula enrichment is controlled by the `enable_formula_enrichment` ar |
| c17 | code | no | flag: Unsupported identifier in answer: `delet | True | True | To remove all Chroma embeddings belonging to a specific file, you shou |
| c18 | code | no | pass | True | True | The near-duplicate check is performed after conversion, where the PDF  |
| c19 | code | no | flag: Unsupported identifier in answer: `DBMan | True | True | Files that still have usable chunks nobody has attempted are retrieved |
| c20 | code | no | flag: Unsupported number in answer: [260000] | True | True | A password is hashed with salt and pbkdf2 by first generating a salt u |
| c21 | code | no | pass | True | True | The NLI check rejects an answer if the probability of contradiction is |
| c22 | code | no | flag: no verified quote from cited source(s) [ | False | False | For how/why questions, the answer must state the mechanism in the pass |
| c23 | code | no | flag: Unsupported identifier in answer: `_norm | True | True | The `_normalize_tags` method in `LLMClient` converts tags to snake cas |
| c24 | code | no | flag: Unsupported number in answer: [2] | False | False | Near-duplicate questions are handled by making the `ingest()` function |
| c25 | code | no | flag: Unsupported identifier in answer: `_chat | True | False | The `max_tokens` is computed using the method `self._max_tokens(answer |
| c26 | code | no | pass | True | True | The D1_URL is "https://api.liquid.ai/decisions/v1/systemone" [1]. |
| c27 | code | no | flag: Unsupported number in answer: [5] | True | False | Rule 5 in the GROUNDED_ANSWER_RULES states: "No hedging (never "likely |
| c28 | code | no | pass | True | True | The default prompt set used is `fewshot` [4]. |
| c29 | code | no | flag: Unsupported identifier in answer: `Share | True | True | The `SharedModel` class wraps a sentence-transformers model to allow c |
| c30 | code | no | flag: Unsupported identifier in answer: `_add_ | True | True | Chunk IDs are linked to the previous and next chunk by setting the `pr |
| c31 | code | no | pass | True | False | A table is considered useful if its alpha ratio is less than 0.30 and  |
| c32 | code | no | flag: Unsupported number in answer: [2] | True | True | The reference answer is checked for the refusal sentinel when the answ |
| c33 | code | no | pass | True | False | When the NLI result is neutral, the adjusted score is calculated by sc |
| c34 | code | no | flag: Unsupported number in answer: [429] | True | True | If the D1 judge encounters a rate limiting error (HTTP 429), it will r |
| c35 | code | no | flag: Unsupported identifier in answer: `chunk | True | True | Rejected pairs are saved with their reason in the `chunk_rejections` t |
| u01 | none | yes | pass | None | None | The provided sources do not contain information on how to configure Ku |
| u02 | none | yes | pass | None | None | The provided sources do not contain information about the Postgres con |
| u03 | none | yes | pass | None | None | I don't know based on the provided sources. |
| u04 | none | no | flag: Unsupported identifier in answer: `LLMUn | None | None | The application sends notifications to the user when an enrichment tas |
| u05 | none | yes | pass | None | None | The provided sources do not specify the amount of GPU memory the speec |
| u06 | none | yes | pass | None | None | The provided sources do not contain information on how to enable OAuth |
| u07 | none | no | pass | None | None | Results live only in `active_sessions`, and they vanish after a 30-min |
| u08 | none | yes | pass | None | None | The provided sources do not specify which Kafka topic receives enrichm |
| u09 | none | yes | pass | None | None | I don't know based on the provided sources. |
| u10 | none | yes | pass | None | None | The provided sources do not specify the maximum number of concurrent i |
| u11 | none | yes | pass | None | None | The provided sources do not contain information about who the on-call  |
| u12 | none | no | pass | None | None | The text-to-speech voice supports the 'alba' voice [2]. |
| u13 | none | yes | pass | None | None | The provided sources do not state the cost per request for the externa |
| u14 | none | yes | pass | None | None | The provided sources do not contain information on how to reset a forg |
| u15 | none | no | pass | None | None | The profile page (`profile.html`) has scripts loaded, including `statu |

## Gate policies, same replies re-judged

| policy | answered | flagged | false alarms (correct answers flagged) | errors missed (wrong answers passed) | usable (correct and accepted) | passed answers citing the gold chunk | unanswerable that passed |
|---|---:|---:|---:|---:|---:|---:|---:|
| strict | 70 | 50% (35/70) | 46% (26/57) | 31% (4/13) | 44% (31/70) | 57% (20/35) | 20% (3/15) |
| tolerant | 70 | 47% (33/70) | 44% (25/57) | 38% (5/13) | 46% (32/70) | 59% (22/37) | 20% (3/15) |
| lenient | 70 | 16% (11/70) | 16% (9/57) | 85% (11/13) | 69% (48/70) | 58% (34/59) | 27% (4/15) |
