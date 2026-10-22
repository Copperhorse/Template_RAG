# Answer-level evaluation

70 answerable and 15 unanswerable queries. Rates are Wilson 95% intervals. "Correct" = the answer contains a hand-written key phrase, so it is a lower bound.

## Answerable queries

- gold chunk was in the context the model saw: 79% (55/70; 95% CI 68-87)
- answered (did not refuse): 100% (70/70; 95% CI 95-100)
- answered and cites a chunk that holds the gold snippet: 63% (44/70; 95% CI 51-73)
- answered and contains the expected fact: 83% (58/70; 95% CI 72-90)
- answered and passed every gate: 34% (24/70; 95% CI 24-46)

## Do the gates discriminate?

- correct, among answers that **passed** the gates: 88% (21/24; 95% CI 69-96)
- correct, among answers the gates **flagged**: 80% (37/46; 95% CI 67-89)

## Unanswerable queries (the right behaviour is to refuse)

- refused: 13% (2/15; 95% CI 4-38)
- answered but flagged by the gates: 60% (9/15; 95% CI 36-80)
- answered and passed the gates (the dangerous case): 27% (4/15; 95% CI 11-52)

## If `strict=True` were used (flagged answers become refusals)

- answerable queries answered: 34% (24/70; 95% CI 24-46)
- answerable queries answered correctly: 30% (21/70; 95% CI 21-42)
- unanswerable queries refused: 73% (11/15; 95% CI 48-89)

Mean latency 2.6s per question. Why answers were flagged: {'no verified quote from cited source(s) [2]': 2, 'Unsupported number in answer': 5, 'no verified quote from cited source(s) [1]': 4, 'no verified quote from cited source(s) [1, 3]': 3, 'no verified quote from cited source(s) [1, 5]': 1, 'no verified quote from cited source(s) [2, 3, 4]': 1, 'no verified quote from cited source(s) [4]': 2, 'no verified quote from cited source(s) [2, 4]': 2, 'Unsupported identifier in answer': 10, 'no verified quote from cited source(s) [1, 2, 3]': 3, 'the answer cites no source': 11, 'no verified quote from cited source(s) [1, 2]': 3, 'no verified quote from cited source(s) [2, 3]': 1, 'no verified quote from cited source(s) [3]': 1, 'no verified quote from cited source(s) [1, 2, 5]': 1, 'no verified quote from cited source(s) [1, 2, 3, 5]': 1, 'no verified quote from cited source(s) [3, 4]': 1, 'no verified quote from cited source(s) [4, 5]': 1, 'no verified quote from cited source(s) [5]': 1, 'Unsupported sentence in answer (4 of 6 words not in the sour': 1}

## Per-query record

| id | type | refused | gates | correct | cites gold | answer |
|---|---|---|---|---|---|---|
| d01 | doc | no | flag: no verified quote from cited source(s) [ | True | False | The single-use ticket for the live status stream is valid for approxim |
| d02 | doc | no | flag: Unsupported number in answer: [260000] | True | False | The application uses PBKDF2 with SHA256 for password hashing, employin |
| d03 | doc | no | pass | True | False | If the same user uploads the exact same PDF twice, the system checks f |
| d04 | doc | no | pass | True | True | The environment variable for the maximum upload size in megabytes is ` |
| d05 | doc | no | flag: no verified quote from cited source(s) [ | True | True | The default token lifetime is 7 days [1]. |
| d06 | doc | no | flag: no verified quote from cited source(s) [ | True | False | You can check for drift between SQLite and Chroma by running `scripts/ |
| d07 | doc | no | flag: no verified quote from cited source(s) [ | True | True | The delete order is Chroma $\rightarrow$ SQLite [1]. Specifically, Chr |
| d08 | doc | no | flag: no verified quote from cited source(s) [ | True | True | A chunk counts as attempted once it has an enrichment row, as this is  |
| d09 | doc | no | pass | True | True | Difficulty adaptation uses hand-set constants: Easy below 0.35, Medium |
| d10 | doc | no | pass | False | False | The NLI cross-encoder is consulted when the bi-encoder score is greate |
| d11 | doc | no | flag: no verified quote from cited source(s) [ | True | True | EventSource cannot send an Authorization header, so the client trades  |
| d12 | doc | no | flag: no verified quote from cited source(s) [ | True | True | The service worker (`sw.js`) must never cache `/api/*` requests becaus |
| d13 | doc | no | pass | True | True | The browser storage keys are `qp_token` and `qp_user_id` [1]. |
| d14 | doc | no | flag: no verified quote from cited source(s) [ | True | True | When an account is deleted but some embeddings could not be removed, t |
| d15 | doc | no | pass | True | False | If an upload is too large, the API returns a status code of 413 with t |
| d16 | doc | no | pass | True | True | Unknown or foreign ids return a 404 status code, which means existence |
| d17 | doc | no | pass | True | True | The rate limits are 5/min for signup and 10/min for login [1]. |
| d18 | doc | no | flag: Unsupported identifier in answer: `REASO | True | False | The `REASONING_BUDGET` variable controls the reasoning budget, which i |
| d19 | doc | no | pass | True | False | The ingest function can report a status of 'ok', 'duplicate', or 'fail |
| d20 | doc | no | flag: no verified quote from cited source(s) [ | True | True | The torch device is chosen based on a preference order: CUDA, then App |
| d21 | doc | no | flag: no verified quote from cited source(s) [ | True | True | The external decision model, Liquid AI's decision model D1, is optiona |
| d22 | doc | no | pass | False | False | Known weaknesses of near-duplicate detection are listed in [docs/devel |
| d23 | doc | no | pass | True | False | The legacy modules with no importers are `qp_core.CSVManager` and `qp_ |
| d24 | doc | no | pass | True | True | To run the tests that use the real bge + NLI models, you can use the c |
| d25 | doc | no | pass | True | True | After a change to security-relevant code, you should perform a mutatio |
| d26 | doc | no | pass | True | True | Interview history is stored in `session_results.history_json`, which h |
| d27 | doc | no | flag: Unsupported identifier in answer: `_buil | True | False | The application starts the LLM server by executing the command specifi |
| d28 | doc | no | pass | True | False | Spoken audio is turned into a transcript by using the `SpeechToText` c |
| d29 | doc | no | flag: the answer cites no source | True | False | The `POST /api/tts` endpoint accepts text with a maximum length of 200 |
| d30 | doc | no | flag: no verified quote from cited source(s) [ | True | True | The `auth-fetch.js` script wraps `fetch` to add the `Authorization: Be |
| d31 | doc | no | pass | True | True | Rules for the .env file include: one `KEY=VALUE` per line, blank lines |
| d32 | doc | no | flag: no verified quote from cited source(s) [ | True | True | When an LLM server is unavailable, the system does not record a reject |
| d33 | doc | no | flag: no verified quote from cited source(s) [ | True | False | The Chroma collection is called "qa_pairs" [1, 2], and it uses cosine  |
| d34 | doc | no | flag: no verified quote from cited source(s) [ | True | True | An answer whose embedding is far from its quote does not follow from i |
| d35 | doc | no | pass | False | False | The audit endpoint returns metadata, the total number of questions, a  |
| c01 | code | no | flag: Unsupported identifier in answer: `verif | True | True | The function that finds the exact chunk text a generated quote refers  |
| c02 | code | no | pass | True | True | The check_support function verifies that every number in the answer mu |
| c03 | code | no | flag: the answer cites no source | False | False | the\s+text\s+does\s+not\s+(specify/mention/state/provide/include/addre |
| c04 | code | no | flag: Unsupported identifier in answer: `per_d | False | False | The number of questions requested per difficulty depends on the `per_d |
| c05 | code | no | flag: no verified quote from cited source(s) [ | False | True | The client verifies that the LLM server is reachable by attempting to  |
| c06 | code | no | flag: no verified quote from cited source(s) [ | False | True | Inline /$)` with an empty string and then strips whitespace from the r |
| c07 | code | no | flag: no verified quote from cited source(s) [ | False | False | Code blocks, math, and table blocks are never split during header-awar |
| c08 | code | no | flag: Unsupported number in answer: [3] | False | False | A table of contents is recognized if the text contains more than 3 lin |
| c09 | code | no | flag: Unsupported identifier in answer: `_get_ | True | True | Character n-gram features are generated by taking substrings of a spec |
| c10 | code | no | flag: no verified quote from cited source(s) [ | True | True | The function `get_device()` picks the device in the order of preferenc |
| c11 | code | no | flag: no verified quote from cited source(s) [ | True | True | The regular expression used to match lines starting with `export` and  |
| c12 | code | no | pass | True | False | Orphan embeddings, which are Chroma documents whose `file_id` metadata |
| c13 | code | no | flag: Unsupported identifier in answer: `IDGen | True | True | The `generate_file_id` method in the `IDGenerator` class generates a u |
| c14 | code | no | flag: no verified quote from cited source(s) [ | False | False | Heavy models are loaded once per process in `qp_core/src/qp_core/model |
| c15 | code | no | flag: no verified quote from cited source(s) [ | True | True | The `SerializedConverter` shares one Docling converter between threads |
| c16 | code | no | flag: Unsupported identifier in answer: `PDFDo | True | True | Formula enrichment is controlled by the `enable_formula_enrichment` ar |
| c17 | code | no | flag: Unsupported identifier in answer: `delet | True | True | To remove all Chroma embeddings belonging to a specific file, you shou |
| c18 | code | no | flag: no verified quote from cited source(s) [ | True | True | The near-duplicate check is performed after conversion, where the PDF  |
| c19 | code | no | flag: no verified quote from cited source(s) [ | True | True | Files that still have usable chunks nobody has attempted are retrieved |
| c20 | code | no | flag: Unsupported number in answer: [260000] | True | True | A password is hashed with salt and pbkdf2 by first generating a salt u |
| c21 | code | no | flag: no verified quote from cited source(s) [ | True | True | The NLI check rejects an answer if the probability of contradiction ($ |
| c22 | code | no | flag: no verified quote from cited source(s) [ | False | False | For how/why questions, the answer must state the mechanism in the pass |
| c23 | code | no | flag: Unsupported identifier in answer: `_norm | True | True | The function `_normalize_tags` in `LLMClient._normalize_tags` normaliz |
| c24 | code | no | flag: Unsupported sentence in answer (4 of 6 w | False | False | Near-duplicate questions are handled by making the `ingest()` function |
| c25 | code | no | flag: Unsupported number in answer: [4096] | True | False | The `max_tokens` is computed using the method `self._max_tokens(answer |
| c26 | code | no | pass | True | True | The D1_URL is "https://api.liquid.ai/decisions/v1/systemone" [1]. |
| c27 | code | no | flag: Unsupported identifier in answer: `_BLOO | True | True | Rule 5 in the `_BLOOM_ANSWER_RULES` forbids hedging words, stating, "N |
| c28 | code | no | pass | True | True | The default prompt set used is `fewshot` [4]. |
| c29 | code | no | flag: no verified quote from cited source(s) [ | True | True | The `SharedModel` class wraps a sentence-transformers model to allow c |
| c30 | code | no | flag: no verified quote from cited source(s) [ | True | True | Chunk IDs are linked to the previous and next chunk by setting the `pr |
| c31 | code | no | pass | True | False | A table is considered useful if its alpha ratio is less than 0.30 and  |
| c32 | code | no | pass | True | True | The reference answer is checked for the refusal sentinel when the answ |
| c33 | code | no | pass | True | False | When the NLI result is neutral, the adjusted score is calculated by sc |
| c34 | code | no | flag: Unsupported number in answer: [5, 429] | True | True | If the D1 judge encounters a rate limiting error (HTTP 429), it will r |
| c35 | code | no | flag: no verified quote from cited source(s) [ | True | True | Rejected pairs are saved with their reason in the `chunk_rejections` t |
| u01 | none | no | flag: the answer cites no source | None | None | The provided sources do not contain information on how to configure Ku |
| u02 | none | no | flag: the answer cites no source | None | None | The provided sources do not contain information about the Postgres con |
| u03 | none | yes | pass | None | None | I don't know based on the provided sources. |
| u04 | none | no | pass | None | None | The application sends notifications when enrichment finishes by emitti |
| u05 | none | no | flag: the answer cites no source | None | None | The provided sources do not state how much GPU memory the speech recog |
| u06 | none | no | flag: the answer cites no source | None | None | The provided sources do not contain information on how to enable OAuth |
| u07 | none | no | pass | None | None | Results live only in `active_sessions`, and they vanish after a 30-min |
| u08 | none | no | flag: the answer cites no source | None | None | The provided sources do not specify which Kafka topic receives enrichm |
| u09 | none | yes | pass | None | None | I don't know based on the provided sources. |
| u10 | none | no | flag: the answer cites no source | None | None | The provided sources do not specify the maximum number of concurrent i |
| u11 | none | no | flag: the answer cites no source | None | None | The provided sources do not contain information about who the on-call  |
| u12 | none | no | pass | None | None | The text-to-speech voice supports the 'alba' voice [2]. |
| u13 | none | no | flag: the answer cites no source | None | None | The provided sources do not state the cost of the external judge API p |
| u14 | none | no | flag: the answer cites no source | None | None | The provided sources do not contain information on how to reset a forg |
| u15 | none | no | pass | None | None | The profile page (`profile.html`) has scripts loaded, including `app.j |

## Gate policies, same replies re-judged

| policy | answered | flagged | false alarms (correct answers flagged) | errors missed (wrong answers passed) | usable (correct and accepted) | passed answers citing the gold chunk | unanswerable that passed |
|---|---:|---:|---:|---:|---:|---:|---:|
| strict | 70 | 66% (46/70) | 64% (37/58) | 25% (3/12) | 30% (21/70) | 54% (13/24) | 27% (4/15) |
| tolerant | 70 | 63% (44/70) | 62% (36/58) | 33% (4/12) | 31% (22/70) | 58% (15/26) | 27% (4/15) |
| lenient | 70 | 20% (14/70) | 19% (11/58) | 75% (9/12) | 67% (47/70) | 62% (35/56) | 27% (4/15) |
