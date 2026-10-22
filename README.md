# rag-template

A template RAG for documents **and source code**, built around retrieval quality and verifiable
evidence rather than around generating questions:

- **Hybrid retrieval**: bi-encoder (dense) + BM25 (lexical), fused with **reciprocal rank fusion**, then
  re-ordered by a **reranker** (default: jina-reranker-v3.5, a listwise model; see the licence note below).
- **Source-quote gates**: every answer must cite sources and quote them; each quote is located in the
  chunk it claims to come from and replaced by the exact chunk text; the answer must be supported by
  those verified quotes. Retrieval can also return the best supporting span of each hit, extracted verbatim.
- **Ingest-time gates**: a chunk quality evaluator keeps tables of contents, references, licence headers,
  generated code and noise out of the index (rejected chunks are stored with the reason).
- **Chunking that respects structure**: header-aware Markdown; Python split along its **AST** (functions,
  classes, methods), other languages by top-level blocks.
- **A Streamlit UI** (`rag ui`): ask with verified quotes highlighted in their sources, a per-stage search view
  (dense rank, BM25 rank, RRF, rerank score, evidence span, each stage switchable), a library with the quality
  gate's verdict and reason for every chunk, and the eval reports.
- **Measured, not assumed**: `evals/` has a frozen corpus, hand-written and synthetic gold sets and runners for
  Recall@k / MRR / nDCG with bootstrap confidence intervals and paired significance tests. See `evals/README.md`
  and `evals/results/`.
- **Optional enrichment** (off unless you run it): LLM summaries/tags and *gated* question/answer pairs per
  chunk, indexed as extra vectors. Everything above works without it, and without an LLM until you call `ask`.

```
 ingest:  file → convert → dedupe → chunk (markdown / AST) → quality gate → SQLite (+FTS5/BM25)
 index:   chunks → bi-encoder → vector store
 search:  query → dense ┐
                        ├→ RRF → rerank → score gates → [evidence span]
                 BM25  ┘
 ask:     search → sources S1, S2, … → LLM {answer, quotes} → gates (citations, quotes found, support)
 (opt.)   enrich: chunk → summary/tags + Q&A candidates → provenance/support gates → extra vectors
```

## Quick start

```bash
uv venv && uv pip install -e ".[dev,tokens,chroma,local,ui]"  # add ,pdf for PDF support
cp .env.example .env                                           # LLM_BASE_URL is only needed for `ask`/`enrich`
scripts/serve_llm.sh &                                         # Gemma 4 E2B on :8080 (only needed for `ask`)
rag ui                                                         # Streamlit app: http://127.0.0.1:8501

rag chunks pkg/service.py                  # preview chunking + the quality gate's verdict
rag run ./my-repo ./docs                   # ingest + index (no LLM involved)
rag search "where is the retry backoff computed" --quotes
rag ask "How does retry decide how long to wait?"
rag status
```

```python
from rag_template import RAG

rag = RAG()                                    # settings from the environment / .env
rag.ingest_directory("./my-repo")              # chunks cite paths relative to this root
rag.index()

for h in rag.search("retry backoff", k=5, quotes=True):
    print(h.label, h.dense_rank, h.lexical_rank, h.rerank_score, "\n  >", h.quote.text)

a = rag.ask("How does retry decide how long to wait?")
print(a.text, a.grounded, a.reason)
for q in a.quotes:                             # verbatim text of the chunk, never the model's paraphrase
    print(q.source, q.hit.label, q.text)
```

Without the `local` extra the pipeline still runs (hash embedder, no rerank, text-only gates), which is
useful for CI and for wiring things up; with it you get EmbeddingGemma 2 embeddings and the reranker.

## Retrieval

`Retriever.search(query, k, ...)` runs these stages; every stage is switchable and every hit records what
each stage thought of it (`dense_rank`, `lexical_rank`, `rrf_score`, `rerank_score`).

| Stage | Detail | Knobs |
|---|---|---|
| bi-encoder | `google/embeddinggemma-2` by default, loaded text-only in bfloat16 (never float16: it returns NaN). Queries and documents get the model's task prefixes (`store/formats.py`); a chunk's breadcrumb (`pkg/retry.py > Cache.get`) is its document title | `dense=False`, `RAG_EMBEDDER`, `RAG_EMBED_MODEL` |
| BM25 | SQLite FTS5 over chunk text + breadcrumb, porter stemming; finds identifiers, error codes and acronyms embeddings blur | `lexical=False` |
| RRF | `score = Σ weight / (k + rank)` over both rankings; no score calibration needed | `rrf_k=60`, `weights=(dense, lexical)` |
| reranker | reads the top fused candidates (`rerank_top`, default 20) and re-orders them. Default `jinaai/jina-reranker-v3.5`: a 0.6B *listwise* model that reads the query and all candidates in one pass (**CC-BY-NC-4.0, non-commercial; needs `trust_remote_code`: the audited commit is pinned and trusted by default**, see `rerankers.py`). Any sentence-transformers cross-encoder id works too. `fuse` (default) makes it a third voter next to dense and BM25; `replace` orders by it alone, which lost 14 points of recall@5 on code with ms-marco (`evals/results/`) | `rerank=False`, `rerank_mode`, `rerank_top`, `RAG_RERANK=auto\|on\|off`, `RAG_RERANK_MODEL`, `RAG_TRUST_REMOTE_CODE` |
| score gates | drop weak candidates. A chunk BM25 also found survives `min_dense_score`; `min_rerank_score` applies to reranked hits | `min_dense_score`, `min_rerank_score` |
| evidence | `quotes=True`: the best sentence (prose) or 4-line window (code) per hit, scored by the reranker (bi-encoder if none), returned as an exact substring | `quotes=True` |

Reranker scores are model-specific numbers (jina: cosines in roughly [-0.3, 0.6]; ms-marco: unbounded logits) and cosine scores are not comparable
between embedding models, so **there is no default score threshold in retrieval**. Measured operating points for refusing unanswerable questions
are below.

**Reranker: what the evals say** (`evals/results/rerankers_*.md`). jina-reranker-v3.5 beat plain hybrid retrieval by +18.6 recall@1 / +15.4 MRR on 70
hand-written queries and +25.5 / +20.2 on 149 synthetic ones (all significant), and beat ms-marco-MiniLM by +14 to +18 recall@5; ms-marco never helped.
The price: about 1 s per query at 20 candidates, 1.1 GB of GPU memory, a **non-commercial licence (CC-BY-NC-4.0)**, and sensitivity to the order of the
candidates it is shown (re-scoring in shuffled order kept the best candidate in 69% of shuffles). If any of that is a problem, set
`RAG_RERANK_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2` (Apache-2.0, fast): it is then used in `fuse` mode, where it neither helps nor hurts.

**Document routing** (`RAG_ROUTE_MARGIN`, on by default at 0.10, `off` disables it). When several documents are indexed, a question about one of them
also retrieves look-alike chunks from the others, and the answer can blend them (a Mamba-3 answer cited the MiniCPM4 paper's GPU hours). After the reranker,
each document is scored by its best chunk; if the best document leads the next by the margin, only its chunks are kept; on a close call the mix is kept, so
questions that really span documents are not forced into one. Measured on 153 questions across three papers: chunks from another document in the top 5 fell
from 18.7% to 3.9%, evidence recall@5 stayed at 89.5%, and answer quality did not change beyond noise (`evals/results/architecture_review.md`). Not measured:
questions that genuinely need two documents (none in the gold sets). It needs the reranker; with `RAG_RERANK=off` nothing is routed.

**Optional relevance gate for unanswerable questions** (`RAG_MIN_RELEVANCE`, off by default). Before the LLM is called, a question whose best reranker
score is below the threshold is refused outright. The top-1 jina score separates answerable from unanswerable questions with AUC 0.96; a threshold of
0.211 (chosen from hand-written answerable questions only) refused 83% of 59 unanswerable questions and wrongly refused 4 to 9% of good ones; end to end
with the real LLM it cut unanswerable questions that got a passing answer from 16/59 to 4/59 for one fewer usable answer out of 70. It stays off by
default because the score depends on candidate order, so decisions near the threshold are noisy (`evals/results/gate_stability.md`).

## Answer gates (source quotation)

`ask` labels the sources `[S1]`, `[S2]`, … and requires JSON `{quotes[{source, quote}], answer}` (evidence first). The `S` matters: a bare
number is not an id, because documents are full of numbers (section 22, bibliography entries like `[3]`, years) and a model that writes one
where an id belongs must not be taken for citing. With `LLM_JSON_MODE=schema` the `source` of a quote can only be one of the ids shown. Then:

1. every `[Sn]` in the answer exists and was among the sources shown, and a refusal in the model's own words
   ("The provided sources do not contain...") is a refusal, not an uncited answer;
2. every cited source has at least one quote **found in that chunk**. A quote that arrives with no usable id (a bare string, a missing or
   nonexistent id) is attributed to the one retrieved chunk that holds it verbatim; an id that names a real source is never overridden, so a
   real quote filed under the wrong source is still caught. The stored quote is always the chunk's exact
   text (whole sentences, whole lines for code, a whole row for a table), never the model's wording. Quotes that
   cannot be found are dropped and listed in `Answer.unverified_quotes`;
3. **a number taken from a table must come from the right cell** (`tablecheck.py`): a number that occurs in a table of a cited chunk
   passes only if some cell holding it has a row label that shares a word with the answer or the question, and a column header that does not
   contradict the answer (`pass@5` in the header against `pass@1` in the answer). The set-level check below accepts "59.7" if it appears
   anywhere in the table; this one rejects it when it is the baseline's pass@5 cell used as an SSD pass@1 value. Prose is not checked, nor is
   the direction of a change ("from A to B"). `AnswerPolicy.check_table_cells`, off for `lenient`;
4. the answer is supported by the evidence: numbers occur in it (`SHA-256`, `260 000`, and sequencing words such as
   "first" are not counted as claims), no sentence is mostly words the evidence lacks, at most one unfamiliar
   technical word (prose); every `` `identifier` `` occurs in it, qualified names such as `DBManager.get_pending_files`
   being checked against the chunk's breadcrumb as well (code);
5. nothing retrieved means no LLM call; `strict=True` replaces a failing answer with a refusal. `Answer.missing_terms`
   lists question words found in no source ("slack", "redis"): a hint for the reader, not a verdict.

**Policies** (`RAG_ANSWER_POLICY`, `rag ask --policy`, a selector in the UI) trade false alarms against missed errors:

| policy | quotes | support is checked against | a missing / invalid quote |
|---|---|---|---|
| `strict` | verbatim (exact, or fuzzy >= 85) | the verified quotes alone | answer flagged |
| `tolerant` | also accepts one word off (score >= 75 and 80% of words) | the verified quotes alone | answer flagged |
| **`balanced`** (default) | as tolerant | the whole cited chunk | answer flagged |
| `lenient` | as tolerant | the whole cited chunk | replaced by the chunk's best-matching span, labelled `extracted`; the model's attribution is no longer verified |

**Reply format matters more than the policy.** Gemma 4 E2B left the required `quotes` out of about two thirds of
its plain replies, which no policy can repair honestly. `LLM_JSON_MODE=schema` makes llama.cpp enforce the reply's
keys with a grammar, and asking for the quotes before the answer lowered false alarms again. Measured numbers, the
adversarial test of what each policy still catches, and the caveats are in
[`evals/results/answer_policies.md`](evals/results/answer_policies.md).

**What no policy catches** (measured, not hidden): an answer that is supported by what it cites but answers a
different question (adjacent text for an unanswerable question), a flipped meaning ("is" to "is not"), and an
invented plausible sentence with no numbers or names (caught about half the time).

## PDFs
`pip install -e ".[pdf]"` adds Docling, PyMuPDF and pymupdf4llm. Each PDF is converted by one of the two backends (`RAG_PDF_BACKEND=auto` profiles the file and
picks; neither is better everywhere, see `evals/results/pdf_backends.md`), the Markdown is cleaned (`mdclean.py`), and a **conversion check** compares it with the
PDF's own text (`convcheck.py`; flags numbers glued together by footnote markers, dropped text, scrambled order, flattened code) and shows the verdict in the UI's
Library tab and `rag ingest`. The check needs Poppler's `pdftotext` (system package `poppler` / `poppler-utils`); without it the verdict is "not run".
Every PDF option lives in `Settings.pdf` (`.env.example`); the converters take it as an argument.

## Ingest-time gate and chunking
Tables are chunked so that a row says what it is a row of: an oversize table is split by rows, every part repeats the header and carries the
table's caption (`Table 3 ...`, with or without punctuation), and a row whose label only continues the one above (`+ SSD`, `w/ ACT`) is prefixed
with that label (`Qwen3-30B-Thinking / + SSD`, `tables.py`). Padded separator rows are normalised.


| Module | What it does |
|---|---|
| `chunking/code.py` | **`PythonASTChunker`**: one chunk per function/class with decorators and the comment block above. A class over budget becomes a header chunk + one chunk per method (recursively); a function over budget is cut *between statements*, each later part starting `# ... continued: def name(...)`. Imports, constants and `__main__` blocks become module chunks, so every line lands in exactly one chunk. Syntax errors fall back to line chunks. **`LineCodeChunker`** handles other languages. |
| `chunking/markdown.py` | Masks fenced code, `$$math$$` and tables, splits on headings (keeping the heading stack), packs prose to a token budget. Big tables split by rows with the header repeated; big ```` ```python ```` fences split with the AST chunker. |
| `chunking/router.py` | `chunk_file(path, text)` picks a chunker by extension; `register_chunker(".ts", fn)` plugs in another. |
| `evaluator.py` | Rejects TOC, references/index/glossary sections, copyright, bare citations, low-alpha noise; for code: licence-only, generated, imports-only. Rejected chunks stay in the DB with the reason but are never indexed. |
| `store/dedupe.py`, `ingest.py` | SHA-256 (exact) and SimHash (near) duplicate detection before any expensive work. |

## Optional enrichment

`rag enrich` (or `rag run --enrich`) asks an LLM for a summary, tags and triplets (tags/triplets must
literally occur in the chunk) and candidate questions with a verbatim quote, and keeps only pairs that
survive, in order: valid → quote located (replaced by exact chunk text) → reference answer from the quote
alone → not a refusal or deflection → type-specific checker (prose: numbers, unsupported sentences,
addresses the question, embedding similarity; code: identifiers and numbers; maths: lexical → bi-encoder →
NLI) → optional judge. Every rejection is stored with its reason (`rag rejections`). Surviving pairs
become extra vectors, so a user question can match the *question* a chunk answers.

An LLM outage never becomes a rejection: the run stops, the document stays pending, the next run resumes.
Use it when you want question-style retrieval or reviewable Q&A; skip it otherwise.

## Extending

- **Another language with a real parser**: `register_chunker(".ts", fn)` with
  `(text, source, config) -> [chunk dict]` (shape in `chunking/base.py`; reuse `make_chunk`, `breadcrumb`,
  `finalize_chunks`). A tree-sitter chunker follows `PythonASTChunker`'s plan: definitions are units,
  oversized containers recurse into members, gaps become module chunks.
- **Another file format**: `converters.register_converter(".docx", fn)` with `(path) -> (metadata, text)`.
- **A different reranker or scorer**: anything with `.rerank(query, texts) -> [score]` (`RAG(reranker=...)`).
- **A different vector store**: implement the six-method `VectorStore` protocol in `store/vector.py`.
- **Your own answer/enrichment checker**: anything with `.validate(question, answer, chunk, quote) -> (ok, reason)`.

## Tuning

Thresholds (`VerifyConfig`, the evaluator's weights, RRF weights, prompt wording) were tuned on English
technical prose with a small local model. Run on your corpus, read samples of what each gate rejected and
accepted, change one thing, re-run on a fixed set. Known limits: the cheap gates check provenance and
support, not whether a grounded answer *answers* the question. The embedding-similarity gate (0.70) is a
coarse off-topic filter: with bge-small a faithful answer scores 0.97, a paraphrase 0.79, a wrong sentence
of the same chunk 0.73 and an off-topic one 0.46. Only a stronger judge model separates the middle two.

## Configuration and tests

See [`.env.example`](.env.example); everything is also available as `Settings(...)` / `LLMSettings(...)`.

```bash
uv pip install -e ".[dev,chroma]" && pytest            # add ,local and run -m models for the real-model tests
```

The default suite needs no model and no network. A stub OpenAI-compatible server (`tests/llm_stub.py`)
builds replies from the chunk text in each prompt and simulates hangs, 429/5xx, garbage JSON,
reasoning-only replies and unterminated `<think>` blocks.
