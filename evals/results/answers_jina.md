# Answer-level evaluation

70 answerable and 59 unanswerable queries. Rates are Wilson 95% intervals. "Correct" = the answer contains a hand-written key phrase, so it is a lower bound.

## Answerable queries

- gold chunk was in the context the model saw: 86% (60/70; 95% CI 76-92)
- answered (did not refuse): 100% (70/70; 95% CI 95-100)
- answered and cites a chunk that holds the gold snippet: 59% (41/70; 95% CI 47-69)
- answered and contains the expected fact: 81% (57/70; 95% CI 71-89)
- answered and passed every gate: 66% (46/70; 95% CI 54-76)

## Do the gates discriminate?

- correct, among answers that **passed** the gates: 83% (38/46; 95% CI 69-91)
- correct, among answers the gates **flagged**: 79% (19/24; 95% CI 60-91)

## Unanswerable queries (the right behaviour is to refuse)

- refused: 64% (38/59; 95% CI 52-75)
- answered but flagged by the gates: 12% (7/59; 95% CI 6-23)
- answered and passed the gates (the dangerous case): 24% (14/59; 95% CI 15-36)

## If `strict=True` were used (flagged answers become refusals)

- answerable queries answered: 66% (46/70; 95% CI 54-76)
- answerable queries answered correctly: 54% (38/70; 95% CI 43-65)
- unanswerable queries refused: 76% (45/59; 95% CI 64-85)

Mean latency 3.2s per question. Why answers were flagged: {'no verified quote from cited source(s) [1]': 5, 'no verified quote from cited source(s) [3, 4]': 1, 'no verified quote from cited source(s) [4]': 3, 'no verified quote from cited source(s) [2]': 3, 'Unsupported identifier in answer': 9, 'Unsupported sentence in answer (4 of 7 words not in the sour': 2, 'the answer cites no source': 3, 'Unsupported number in answer': 3, 'Unsupported sentence in answer (10 of 15 words not in the so': 1, 'no verified quote from cited source(s) [5]': 1}

## Per-query record

| id | type | refused | gates | correct | cites gold | answer |
|---|---|---|---|---|---|---|
| d01 | doc | no | pass | True | False | The SSE ticket lifetime is 30 seconds [4]. |
| d02 | doc | no | pass | True | True | The app uses PBKDF2-SHA256 for password hashing with 260,000 iteration |
| d03 | doc | no | pass | True | False | If the same user uploads the exact same PDF twice, the system immediat |
| d04 | doc | no | flag: no verified quote from cited source(s) [ | True | True | The environment variable for the maximum upload size in megabytes is ` |
| d05 | doc | no | flag: no verified quote from cited source(s) [ | True | True | The default lifetime of an authentication token is 604800 seconds, whi |
| d06 | doc | no | flag: no verified quote from cited source(s) [ | True | True | You can check for drift between SQLite and Chroma by running the scrip |
| d07 | doc | no | pass | True | True | The delete order is Chroma first, followed by SQLite [2]. |
| d08 | doc | no | pass | True | False | A chunk counts as attempted once it has a question, an enrichment row, |
| d09 | doc | no | pass | True | True | The difficulty levels in the adaptive interview are determined by the  |
| d10 | doc | no | pass | True | True | The NLI cross-encoder is consulted when the bi-encoder score is greate |
| d11 | doc | no | flag: no verified quote from cited source(s) [ | True | False | EventSource cannot send an Authorization header [1]. The default metho |
| d12 | doc | no | pass | True | True | The service worker (`sw.js`) must never cache `/api/*` requests [1], a |
| d13 | doc | no | pass | True | True | The browser storage keys mentioned are `qp_token` and `qp_user_id` [1] |
| d14 | doc | no | pass | True | False | When an account is deleted but some embeddings could not be removed, a |
| d15 | doc | no | pass | True | True | The API returns a JSON response with a status code of 413 if the uploa |
| d16 | doc | no | pass | True | True | The API avoids leaking the existence of someone else's resource by ret |
| d17 | doc | no | flag: no verified quote from cited source(s) [ | True | True | The per-minute rate limit for signup is 5/min [1, 2], and the per-minu |
| d18 | doc | no | pass | True | True | The reasoning budget setting controls the thinking-token budget, and i |
| d19 | doc | no | pass | True | False | The ingest function can report an `IngestResult` with a `status` that  |
| d20 | doc | no | pass | True | False | The torch device is chosen based on a preference order: CUDA, then App |
| d21 | doc | no | pass | False | False | The external decision model, Liquid AI's D1, answers yes/no questions  |
| d22 | doc | no | flag: no verified quote from cited source(s) [ | False | False | Known weaknesses of near-duplicate detection are listed in [docs/devel |
| d23 | doc | no | flag: no verified quote from cited source(s) [ | True | False | The legacy modules with no importers are `qp_core.CSVManager` and `qp_ |
| d24 | doc | no | pass | True | True | You can run the tests that use the real embedding and NLI models by us |
| d25 | doc | no | pass | True | True | After a change to security-relevant code, a mutation check should be p |
| d26 | doc | no | pass | True | True | Interview history is stored in `session_results.history_json` in the S |
| d27 | doc | no | flag: Unsupported identifier in answer: `subpr | True | False | The application starts the LLM server by running `llama serve` itself  |
| d28 | doc | no | flag: Unsupported identifier in answer: `self. | False | False | Spoken audio can be turned into a transcript through methods such as ` |
| d29 | doc | no | flag: Unsupported sentence in answer (4 of 7 w | True | True | The text input for the text-to-speech endpoint must be less than or eq |
| d30 | doc | no | pass | True | False | The `auth-fetch.js` script adds the token to fetch calls [2]. |
| d31 | doc | no | pass | True | True | The rules for the .env file format include having one `KEY=VALUE` per  |
| d32 | doc | no | pass | True | False | When an LLM server fails, the system is designed so that nothing is le |
| d33 | doc | no | pass | True | True | The Chroma collection is called `qa_pairs` [2], and it uses cosine dis |
| d34 | doc | no | pass | True | False | Prose chunks are checked by the Verifier, which rejects an answer if i |
| d35 | doc | no | pass | False | False | The audit endpoint returns a dictionary containing the file's metadata |
| c01 | code | no | pass | True | True | The function that finds the exact chunk text a generated quote refers  |
| c02 | code | no | pass | True | True | The check for every number in an answer appearing in the source is per |
| c03 | code | no | flag: the answer cites no source | True | False | The regex deflection pattern includes the phrase "the\s+text\s+does\s+ |
| c04 | code | no | pass | True | False | The number of questions requested per difficulty is determined by the  |
| c05 | code | no | flag: Unsupported identifier in answer: `and r | False | True | The client verifies that the LLM server is reachable by attempting to  |
| c06 | code | no | flag: the answer cites no source | False | False | Inline |
| c07 | code | no | pass | False | False | Code, math, and table blocks are protected from being split in markdow |
| c08 | code | no | pass | True | False | A table of contents is recognized by checking for patterns defined in  |
| c09 | code | no | pass | False | True | The document fingerprint is computed by generating character n-gram fe |
| c10 | code | no | flag: no verified quote from cited source(s) [ | True | True | The function `get_device()` picks the device in the order of preferenc |
| c11 | code | no | flag: the answer cites no source | True | False | The `parse_dotenv` function handles lines that start with `export` and |
| c12 | code | no | flag: Unsupported identifier in answer: `index | False | False | Chroma embeddings belonging to a deleted file are detected by querying |
| c13 | code | no | flag: Unsupported identifier in answer: `gener | True | True | The `generate_file_id` method in the `IDGenerator` class generates a u |
| c14 | code | no | pass | False | False | Heavy models are loaded once and safely across threads through lazy lo |
| c15 | code | no | flag: Unsupported identifier in answer: `threa | True | True | The `SerializedConverter` class shares one Docling converter between t |
| c16 | code | no | pass | True | True | Formula enrichment is switched on by setting `self.pipeline_options.do |
| c17 | code | no | flag: Unsupported identifier in answer: `self. | True | True | To remove all Chroma embeddings belonging to a specific file, the `del |
| c18 | code | no | pass | True | True | The near-duplicate check is done after conversion, as Step 2 in the `i |
| c19 | code | no | pass | True | True | The function `DBManager.get_pending_files` retrieves files that still  |
| c20 | code | no | flag: Unsupported number in answer: [260000] | True | True | A password is hashed with salt and pbkdf2 by first generating a salt u |
| c21 | code | no | pass | True | True | The NLI check rejects an answer if the contradiction probability is gr |
| c22 | code | no | pass | False | False | For how/why questions, the answer must state the mechanism in the pass |
| c23 | code | no | pass | True | True | The tags are normalized to snake case by first applying a substitution |
| c24 | code | no | pass | False | True | Near-duplicate questions are removed by checking if the source quote h |
| c25 | code | no | pass | False | False | The `max_tokens` is computed using the method `self._max_tokens(answer |
| c26 | code | no | pass | True | False | D1 is an optional judge that is off by default [5]. It is implemented  |
| c27 | code | no | flag: Unsupported number in answer: [5] | True | False | Rule 5 in the grounded answer rules states that there should be no hed |
| c28 | code | no | pass | True | True | The prompt set used when none is configured defaults to "fewshot" [2]. |
| c29 | code | no | flag: Unsupported identifier in answer: `RLock | True | True | The `SharedModel` class makes sentence-transformers safe for concurren |
| c30 | code | no | pass | True | True | Chunk IDs are linked to the previous and next chunk as follows: in `Ma |
| c31 | code | no | pass | True | True | A table is considered useful if it has more than 5 rows and the ratio  |
| c32 | code | no | flag: Unsupported number in answer: [2] | True | True | The reference answer is checked for the refusal sentinel in Pass 2, wh |
| c33 | code | no | pass | True | False | When the NLI result is neutral, the bi-encoder score is scaled by the  |
| c34 | code | no | pass | True | True | The D1 judge retries after rate limiting by looping for a number of at |
| c35 | code | no | flag: Unsupported identifier in answer: `self. | True | True | Rejected generated pairs are saved to `chunk_rejections` with a reason |
| u01 | none | yes | pass | None | None | I don't know based on the provided sources. |
| u02 | none | no | flag: Unsupported sentence in answer (10 of 15 | None | None | The provided sources mention SQLite database files like `data/rag_stag |
| u03 | none | yes | pass | None | None | I don't know based on the provided sources. |
| u04 | none | no | pass | None | None | The application sends a notification when enrichment and indexing are  |
| u05 | none | yes | pass | None | None | The provided sources do not specify the exact GPU memory required for  |
| u06 | none | yes | pass | None | None | The provided sources do not contain information on how to enable OAuth |
| u07 | none | no | pass | None | None | The session TTL is 1800 seconds, which is 30 minutes [1]. |
| u08 | none | yes | pass | None | None | The provided sources do not contain information about a Kafka topic th |
| u09 | none | yes | pass | None | None | The provided sources do not state which base image is used to build th |
| u10 | none | yes | pass | None | None | The provided sources do not explicitly state the maximum number of con |
| u11 | none | yes | pass | None | None | I don't know based on the provided sources. |
| u12 | none | no | pass | None | None | The text-to-speech voice supports the 'alba' voice, as indicated by th |
| u13 | none | no | pass | None | None | The external judge API costs about 2 seconds per pair [5]. |
| u14 | none | yes | pass | None | None | The provided sources do not contain information on how to reset a forg |
| u15 | none | no | flag: no verified quote from cited source(s) [ | None | None | The profile page (`profile.html` at route `/profile`) includes functio |
| n01 | none | yes | pass | None | None | I don't know based on the provided sources. |
| n02 | none | yes | pass | None | None | I don't know based on the provided sources. |
| n03 | none | yes | pass | None | None | I don't know based on the provided sources. |
| n04 | none | yes | pass | None | None | I don't know based on the provided sources. |
| n05 | none | yes | pass | None | None | I don't know based on the provided sources. |
| n06 | none | yes | pass | None | None | I don't know based on the provided sources. |
| n07 | none | yes | pass | None | None | I don't know based on the provided sources. |
| n08 | none | yes | pass | None | None | I don't know based on the provided sources. |
| n09 | none | yes | pass | None | None | I don't know based on the provided sources. |
| n10 | none | yes | pass | None | None | I don't know based on the provided sources. |
| n11 | none | yes | pass | None | None | I don't know based on the provided sources. |
| n12 | none | yes | pass | None | None | I don't know based on the provided sources. |
| n13 | none | yes | pass | None | None | I don't know based on the provided sources. |
| n14 | none | yes | pass | None | None | The provided sources do not contain information on how to file a paten |
| n15 | none | yes | pass | None | None | I don't know based on the provided sources. |
| n16 | none | yes | pass | None | None | The provided sources do not mention how the app uses Elasticsearch for |
| n17 | none | yes | pass | None | None | The provided sources do not state which encryption algorithm protects  |
| n18 | none | no | pass | None | None | The API exposes system status through the GET endpoint `/api/status`.  |
| n19 | none | no | pass | None | None | The `profile.html` template has a `status-panel.js` script, which is a |
| n20 | none | yes | pass | None | None | The provided sources do not detail how the app implements two-factor a |
| n21 | none | yes | pass | None | None | The provided sources do not mention which CDN serves the static JavaSc |
| n22 | none | yes | pass | None | None | The provided sources do not contain information about how the Kubernet |
| n23 | none | no | pass | None | None | Temporary uploads of PDFs are removed after ingestion [1]. |
| n24 | none | no | pass | None | None | The Redis rate limiter is configured using `Limiter(key_func=get_remot |
| n25 | none | no | pass | None | None | The interview chat uses `interview.js` and an ONNX runtime, and is des |
| n26 | none | no | flag: no verified quote from cited source(s) [ | None | None | The server's error reports are logged in `server_log.txt`, which is th |
| n27 | none | yes | pass | None | None | The provided sources do not contain information on how the app handles |
| n28 | none | no | flag: no verified quote from cited source(s) [ | None | None | The stress detector is controlled by the `DEBUG` flag in `audio-workle |
| n29 | none | no | flag: no verified quote from cited source(s) [ | None | None | The enrichment jobs are handled by `EnrichmentManager.run`, which uses |
| n30 | none | no | pass | None | None | The configuration shows that `QP_PORT` defaults to `8000` for `python  |
| n31 | none | no | flag: Unsupported sentence in answer (4 of 7 w | None | None | The provided sources mention that `data/server_log.txt` is truncated o |
| n32 | none | no | flag: no verified quote from cited source(s) [ | None | None | The `profile.html` template has a purpose that includes the ability to |
| n33 | none | yes | pass | None | None | The provided sources do not state which SMTP server the signup flow us |
| n34 | none | yes | pass | None | None | The provided sources do not contain information on how to enable the d |
| n35 | none | no | pass | None | None | The command `python game_loop.py --list-users` lists all users and exi |
| n36 | none | yes | pass | None | None | The provided sources do not specify how the Docling converter handles  |
| n37 | none | yes | pass | None | None | The provided sources do not state how many Chroma collections are crea |
| n38 | none | no | pass | None | None | The command `uv run pytest -m gpu` runs the 34 labelled scoring cases  |
| n39 | none | no | pass | None | None | The configuration for the Chroma directory is managed in `qp_core/conf |
| n40 | none | yes | pass | None | None | The provided sources do not contain an endpoint that allows a user to  |
| n41 | none | yes | pass | None | None | The provided sources do not contain information about a setting that s |
| n42 | none | yes | pass | None | None | The provided sources do not contain information about the schedule of  |
| n43 | none | no | pass | None | None | The API route `GET /api/files/{file_id}/audit` provides metadata, incl |
| n44 | none | yes | pass | None | None | The provided sources do not contain information on how to switch the s |

## Gate policies, same replies re-judged

| policy | answered | flagged | false alarms (correct answers flagged) | errors missed (wrong answers passed) | usable (correct and accepted) | accepted and citing the gold chunk | unanswerable that passed |
|---|---:|---:|---:|---:|---:|---:|---:|
| strict | 70 | 34% (24/70) | 33% (19/57) | 62% (8/13) | 54% (38/70) | 39% (27/70) | 24% (14/59) |
| tolerant | 70 | 33% (23/70) | 32% (18/57) | 62% (8/13) | 56% (39/70) | 40% (28/70) | 27% (16/59) |
| balanced | 70 | 19% (13/70) | 18% (10/57) | 77% (10/13) | 67% (47/70) | 49% (34/70) | 27% (16/59) |
| lenient | 70 | 9% (6/70) | 7% (4/57) | 85% (11/13) | 76% (53/70) | 54% (38/70) | 32% (19/59) |
| balanced + relevance gate 0.183 | 69 | 19% (13/69) | 18% (10/57) | 75% (9/12) | 67% (47/70) | 49% (34/70) | 15% (9/59) |
| balanced + relevance gate 0.211 | 67 | 18% (12/67) | 16% (9/55) | 75% (9/12) | 66% (46/70) | 47% (33/70) | 7% (4/59) |
| balanced + relevance gate 0.304 | 61 | 18% (11/61) | 17% (9/52) | 78% (7/9) | 61% (43/70) | 43% (30/70) | 3% (2/59) |
