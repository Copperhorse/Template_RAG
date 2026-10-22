# Answer-level evaluation

70 answerable and 15 unanswerable queries. Rates are Wilson 95% intervals. "Correct" = the answer contains a hand-written key phrase, so it is a lower bound.

## Answerable queries

- gold chunk was in the context the model saw: 79% (55/70; 95% CI 68-87)
- answered (did not refuse): 100% (70/70; 95% CI 95-100)
- answered and cites a chunk that holds the gold snippet: 50% (35/70; 95% CI 39-61)
- answered and contains the expected fact: 83% (58/70; 95% CI 72-90)
- answered and passed every gate: 67% (47/70; 95% CI 56-77)

## Do the gates discriminate?

- correct, among answers that **passed** the gates: 83% (39/47; 95% CI 70-91)
- correct, among answers the gates **flagged**: 83% (19/23; 95% CI 63-93)

## Unanswerable queries (the right behaviour is to refuse)

- refused: 60% (9/15; 95% CI 36-80)
- answered but flagged by the gates: 13% (2/15; 95% CI 4-38)
- answered and passed the gates (the dangerous case): 27% (4/15; 95% CI 11-52)

## If `strict=True` were used (flagged answers become refusals)

- answerable queries answered: 67% (47/70; 95% CI 56-77)
- answerable queries answered correctly: 56% (39/70; 95% CI 44-67)
- unanswerable queries refused: 73% (11/15; 95% CI 48-89)

Mean latency 2.6s per question. Why answers were flagged: {'Unsupported number in answer': 4, 'no verified quote from cited source(s) [1]': 2, 'the answer cites no source': 4, 'no verified quote from cited source(s) [4]': 1, 'Unsupported identifier in answer': 9, 'no verified quote from cited source(s) [5]': 1, 'no verified quote from cited source(s) [2]': 2, 'cites sources that do not exist': 1, 'no verified quote from cited source(s) [3]': 1}

## Per-query record

| id | type | refused | gates | correct | cites gold | answer |
|---|---|---|---|---|---|---|
| d01 | doc | no | pass | True | False | The single-use ticket for the live status stream is valid for approxim |
| d02 | doc | no | flag: Unsupported number in answer: [260000] | True | False | The application uses PBKDF2 with SHA256 for password hashing, employin |
| d03 | doc | no | pass | True | False | When the same user uploads the exact same PDF twice, the system checks |
| d04 | doc | no | pass | True | False | The environment variable for the maximum upload size in megabytes is ` |
| d05 | doc | no | flag: no verified quote from cited source(s) [ | True | True | The default lifetime of an authentication token is 604800 seconds, whi |
| d06 | doc | no | pass | True | False | You can check for drift between SQLite and Chroma by running `scripts/ |
| d07 | doc | no | pass | True | False | Chroma is removed first, followed by the SQLite rows [5]. |
| d08 | doc | no | pass | True | False | A chunk counts as attempted once it has a question, an enrichment row, |
| d09 | doc | no | pass | True | True | The difficulty adaptation uses hand-set constants where Easy is below  |
| d10 | doc | no | pass | False | False | The NLI cross-encoder is consulted when the bi-encoder score is high e |
| d11 | doc | no | flag: the answer cites no source | True | False | EventSource cannot send headers, so the client trades its token for a  |
| d12 | doc | no | pass | True | True | The service worker (`sw.js`) must never cache requests for `/api/*` be |
| d13 | doc | no | pass | True | True | The browser storage keys mentioned are `qp_token` and `qp_user_id` [1] |
| d14 | doc | no | pass | False | False | If some files could not be fully removed because the vector store was  |
| d15 | doc | no | pass | True | False | The API returns a JSON response with a status code of 413 if the uploa |
| d16 | doc | no | pass | True | True | Unknown or foreign IDs return a `404` status code instead of a `403`,  |
| d17 | doc | no | flag: no verified quote from cited source(s) [ | True | True | The per-minute rate limit for signup is 5/min [1], [2], [4], and the p |
| d18 | doc | no | flag: Unsupported identifier in answer: `llama | True | False | The reasoning budget setting is controlled by the environment variable |
| d19 | doc | no | pass | True | False | The ingest function can report one of the following statuses: 'ok', 'd |
| d20 | doc | no | pass | True | False | The torch device is chosen based on a preference order: CUDA, then App |
| d21 | doc | no | pass | False | False | The external decision model, specifically Liquid AI's decision model ` |
| d22 | doc | no | flag: no verified quote from cited source(s) [ | False | False | Known weaknesses of near-duplicate detection are tracked in Phase 3.4  |
| d23 | doc | no | flag: no verified quote from cited source(s) [ | True | False | The legacy modules with no importers are `qp_core.CSVManager` and `qp_ |
| d24 | doc | no | pass | True | False | You can run the tests that use the real embedding and NLI models by ex |
| d25 | doc | no | pass | True | True | After a change to security-relevant code, you should perform a mutatio |
| d26 | doc | no | pass | True | True | Interview history is stored in `session_results.history_json` [4]. The |
| d27 | doc | no | flag: Unsupported identifier in answer: `_buil | False | False | The application starts the LLM server by building a command using `_bu |
| d28 | doc | no | flag: Unsupported identifier in answer: `Qwen3 | True | False | Spoken audio can be turned into a transcript through the `SpeechToText |
| d29 | doc | no | pass | True | True | The text for the text-to-speech endpoint must be less than or equal to |
| d30 | doc | no | pass | True | False | The front-end script that adds the Authorization header to fetch calls |
| d31 | doc | no | pass | True | True | The rules for the `.env` file format include having one `KEY=VALUE` pe |
| d32 | doc | no | pass | True | False | When an LLM outage occurs, the system is designed so that callers shou |
| d33 | doc | no | flag: no verified quote from cited source(s) [ | True | False | The Chroma collection is called "qa_pairs" [1, 2]. It uses cosine simi |
| d34 | doc | no | pass | True | True | An answer that only repeats the question or a "how many" question with |
| d35 | doc | no | pass | False | False | The audit endpoint returns an object containing the file's metadata, t |
| c01 | code | no | pass | True | True | The function that finds the exact chunk text a generated quote refers  |
| c02 | code | no | pass | True | True | The check for whether every number in an answer also appears in the so |
| c03 | code | no | pass | True | True | The regex deflection pattern includes the pattern 'the\s+text\s+does\s |
| c04 | code | no | flag: Unsupported number in answer: [150] | True | False | The number of questions requested per difficulty is determined by call |
| c05 | code | no | pass | False | True | The client verifies that the LLM server is reachable by attempting to  |
| c06 | code | no | flag: the answer cites no source | False | False | Inline |
| c07 | code | no | flag: the answer cites no source | False | False | Code blocks, math blocks, and table blocks are protected from being sp |
| c08 | code | no | flag: Unsupported number in answer: [3, 4] | True | False | A table of contents is recognized by counting lines that match the pat |
| c09 | code | no | pass | False | True | The document fingerprint is generated by creating character n-gram fea |
| c10 | code | no | flag: no verified quote from cited source(s) [ | True | True | The function `get_device()` picks the device in the order: CUDA, then  |
| c11 | code | no | flag: cites sources that do not exist: [0] | True | False | The `parse_dotenv` function in `packages/qp-core/src/qp_core/env.py` u |
| c12 | code | no | pass | True | False | Chroma vectors that belong to a deleted file are detected as 'orphan e |
| c13 | code | no | flag: Unsupported identifier in answer: `gener | True | True | The `generate_file_id` method in the `IDGenerator` class generates a u |
| c14 | code | no | pass | False | False | Heavy models are loaded once per process in `models.py` and are lazy,  |
| c15 | code | no | flag: Unsupported identifier in answer: `threa | True | True | The `SerializedConverter` shares one Docling converter between threads |
| c16 | code | no | pass | True | True | Formula enrichment is switched on by setting the `enable_formula_enric |
| c17 | code | no | flag: Unsupported identifier in answer: `quest | True | True | To remove all Chroma embeddings belonging to a specific file, the `del |
| c18 | code | no | pass | True | True | The near-duplicate check is performed after conversion, as Step 2 in t |
| c19 | code | no | pass | True | True | The function `DBManager.get_pending_files` retrieves files that still  |
| c20 | code | no | flag: Unsupported number in answer: [260000] | True | True | A password is hashed with salt and pbkdf2 by first generating a salt u |
| c21 | code | no | pass | True | True | The NLI check rejects an answer if the probability of contradiction (p |
| c22 | code | no | pass | True | True | For why or how questions, the answer must contain a causal or mechanis |
| c23 | code | no | flag: Unsupported identifier in answer: `_to_s | True | True | The function `_to_snake` in `LLMClient._normalize_tags` converts a tag |
| c24 | code | no | pass | False | False | Near-duplicate checks are only known after Docling conversion, and to  |
| c25 | code | no | pass | True | False | The `max_tokens` is computed using the method `self._max_tokens(answer |
| c26 | code | no | pass | True | True | The D1_URL for the liquid decisions endpoint is "https://api.liquid.ai |
| c27 | code | no | pass | True | True | Rule 5 in the instructions for reference answers forbids hedging words |
| c28 | code | no | pass | True | True | When no prompt set is configured, the system defaults to `DEFAULT_PROM |
| c29 | code | no | flag: Unsupported identifier in answer: `RLock | True | True | The `SharedModel` class makes sentence-transformers safe for concurren |
| c30 | code | no | pass | True | True | Chunk IDs are linked to the previous and next chunk as follows: for ea |
| c31 | code | no | pass | True | False | A table is considered useful if the alpha ratio is less than 0.30 and  |
| c32 | code | no | pass | True | True | The reference answer is checked for the refusal sentinel when the gene |
| c33 | code | no | pass | True | False | When the NLI result is neutral, the bi-encoder score is scaled by the  |
| c34 | code | no | pass | True | True | The D1 judge retries after a network error by sleeping for a duration  |
| c35 | code | no | flag: Unsupported identifier in answer: `chunk | True | True | Rejected pairs are saved with their reason. In the `_process_chunk_imp |
| u01 | none | yes | pass | None | None | The provided sources do not contain information on how to configure Ku |
| u02 | none | no | pass | None | None | The app uses an SQLite connection format, as shown by the line `con =  |
| u03 | none | yes | pass | None | None | I don't know based on the provided sources. |
| u04 | none | no | flag: no verified quote from cited source(s) [ | None | None | The application emits a message with the format "[INFO] enricher: ✓ En |
| u05 | none | yes | pass | None | None | The provided sources do not specify how much GPU memory the speech rec |
| u06 | none | yes | pass | None | None | The provided sources do not contain information on how to enable OAuth |
| u07 | none | no | pass | None | None | Results live only in `active_sessions`, and they vanish after a 30-min |
| u08 | none | yes | pass | None | None | The provided sources do not explicitly state which Kafka topic receive |
| u09 | none | no | flag: the answer cites no source | None | None | The base image used to build the Docker container is not explicitly me |
| u10 | none | yes | pass | None | None | The provided sources do not specify the maximum number of concurrent i |
| u11 | none | yes | pass | None | None | I don't know based on the provided sources. |
| u12 | none | no | pass | None | None | The text-to-speech voice supports the 'alba' voice [2]. |
| u13 | none | yes | pass | None | None | The provided sources do not state the cost per request for the externa |
| u14 | none | yes | pass | None | None | The provided sources do not contain information on how to reset a forg |
| u15 | none | no | pass | None | None | The profile page (`profile.html`) has functionality for uploading PDFs |

## Gate policies, same replies re-judged

| policy | answered | flagged | false alarms (correct answers flagged) | errors missed (wrong answers passed) | usable (correct and accepted) | passed answers citing the gold chunk | unanswerable that passed |
|---|---:|---:|---:|---:|---:|---:|---:|
| strict | 70 | 33% (23/70) | 33% (19/58) | 67% (8/12) | 56% (39/70) | 53% (25/47) | 27% (4/15) |
| tolerant | 70 | 31% (22/70) | 31% (18/58) | 67% (8/12) | 57% (40/70) | 54% (26/48) | 27% (4/15) |
| balanced | 70 | 17% (12/70) | 16% (9/58) | 75% (9/12) | 70% (49/70) | 55% (32/58) | 27% (4/15) |
| lenient | 70 | 10% (7/70) | 9% (5/58) | 83% (10/12) | 76% (53/70) | 54% (34/63) | 33% (5/15) |
