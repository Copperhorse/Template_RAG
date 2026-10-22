# Answer-gate adversarial evaluation

70 scenarios (one per answerable gold query: gold chunk + 2 distractors). Each row corrupts the same clean answer in one way; each column is a gate policy (`retrieve.POLICIES`: strict = quotes must be verbatim, support checked against the quotes; tolerant = also accepts a quote that is one word off; lenient = support checked against the cited chunk, and a missing quote is replaced by the chunk's best-matching span).

| corruption | n | expected | strict: flagged | tolerant: flagged | balanced: flagged | lenient: flagged | what it is |
|---|---:|---|---:|---:|---:|---:|---|
| clean | 70 | accept | 0% | 0% | 0% | 0% | answer and quote copied from the gold snippet |
| quote_retyped | 70 | accept | 0% | 0% | 0% | 0% | the real quote, lower-cased with punctuation and spacing dropped |
| fabricated_quote | 70 | flag | 100% | 100% | 100% | **0%** | quote replaced by text from an unrelated chunk |
| quote_from_wrong_source | 70 | flag | 100% | 100% | 100% | **0%** | real text, but taken from source 2 while citing source 1 |
| no_quotes | 70 | flag | 100% | 100% | 100% | **0%** | answer cites [S1] but gives no quotes |
| no_citation | 70 | flag | 100% | 100% | 100% | 100% | good quote, but the answer cites nothing |
| nonexistent_citation | 70 | flag | 100% | 100% | 100% | 100% | answer cites [S9] |
| wrong_number | 15 | flag | **93%** | **93%** | **93%** | **93%** | a number in the answer changed (+7) |
| invented_identifier | 70 | flag | 100% | 100% | **97%** | **97%** | answer adds a `backticked` name that exists nowhere |
| answer_from_other_source | 70 | flag | 100% | 100% | **94%** | **94%** | answer is text from an unrelated chunk, with a real quote for the right one |
| paraphrased_quote | 70 | info | 70% | 31% | 31% | 0% | the real quote with its longest word replaced by 'banana' (fuzzy match tolerance) |
| negation | 5 | info | 0% | 0% | 0% | 0% | the answer asserts the opposite (is -> is not); the quote is unchanged |
| fluent_unsupported_claim | 70 | info | 49% | 49% | 49% | 49% | a plausible extra sentence with no numbers or names |

Bold = the gate did not do what that row expects (a `flag` row below 100%, an `accept` row above 0%).

## Examples where the gate did not behave as expected

- **fabricated_quote**: [lenient] d01: accepted | answer='single-use, 30-second ticket. [S1]'; [lenient] d02: accepted | answer='PBKDF2-SHA256 (260 000 iterations). [S1]'; [lenient] d03: accepted | answer='The same user re-uploading identical bytes gets 409 before any conversion work. [S1]'; [lenient] d04: accepted | answer='QP_MAX_UPLOAD_MB 50 Upload size limit. [S1]'
- **quote_from_wrong_source**: [lenient] d01: accepted | answer='single-use, 30-second ticket. [S1]'; [lenient] d02: accepted | answer='PBKDF2-SHA256 (260 000 iterations). [S1]'; [lenient] d03: accepted | answer='The same user re-uploading identical bytes gets 409 before any conversion work. [S1]'; [lenient] d04: accepted | answer='QP_MAX_UPLOAD_MB 50 Upload size limit. [S1]'
- **no_quotes**: [lenient] d01: accepted | answer='single-use, 30-second ticket. [S1]'; [lenient] d02: accepted | answer='PBKDF2-SHA256 (260 000 iterations). [S1]'; [lenient] d03: accepted | answer='The same user re-uploading identical bytes gets 409 before any conversion work. [S1]'; [lenient] d04: accepted | answer='QP_MAX_UPLOAD_MB 50 Upload size limit. [S1]'
- **wrong_number**: [strict] d22: accepted | answer='SimHash (k = 10) misses lightly edited documents (about 10 % changed text). [S1]'; [tolerant] d22: accepted | answer='SimHash (k = 10) misses lightly edited documents (about 10 % changed text). [S1]'; [balanced] d22: accepted | answer='SimHash (k = 10) misses lightly edited documents (about 10 % changed text). [S1]'; [lenient] d22: accepted | answer='SimHash (k = 10) misses lightly edited documents (about 10 % changed text). [S1]'
- **invented_identifier**: [balanced] d12: accepted | answer='sw.js must never cache /api/ (responses are per user). It also calls `legacy_sync_worker`.'; [balanced] d30: accepted | answer='auth-fetch.js wraps fetch to add Authorization: Bearer <qp_token>. It also calls `legacy_s'; [lenient] d12: accepted | answer='sw.js must never cache /api/ (responses are per user). It also calls `legacy_sync_worker`.'; [lenient] d30: accepted | answer='auth-fetch.js wraps fetch to add Authorization: Bearer <qp_token>. It also calls `legacy_s'
- **answer_from_other_source**: [balanced] d15: accepted | answer='row is written; the API retries at start-up and after any delete. To audit or repair: [S1]'; [balanced] d20: accepted | answer='audio, and the Qwen3-ASR weights if you use voice input (a Qwen3-ASR-0.6B/ folder in the r'; [balanced] c15: accepted | answer='The code defines `__init__` [S1].'; [balanced] c18: accepted | answer='The code defines `continued` [S1].'
