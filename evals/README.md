# Evaluations

Everything here measures the retrieval and answer pipeline against labelled data. Nothing is a claim until
it has a number in `results/`; read the caveats before quoting one.

## Layout

| Path | What it is |
|---|---|
| `corpus/questionprep/` | A frozen snapshot of the QuestionPrep repository (40 files: 9 Markdown docs, the Python packages and the FastAPI app, ~8.7k lines of code). Real code and real documentation, with real near-duplicates and distractors. |
| `gold/handwritten.jsonl` | 70 answerable queries (35 documentation, 35 code) and 15 unanswerable ones, written by reading the files. Every evidence snippet is verified to occur exactly once in the corpus. Styles: `natural`, `keyword`, `paraphrase`. |
| `gold/synthetic.jsonl` | 149 queries written by Gemma 4 E2B from sampled chunks (see *Caveats*). |
| `results/` | `retrieval.md` (ablation), `ablations.md` (reranker, breadcrumb, merge threshold), `retrieval_synthetic.md`, `gates.md` (adversarial gate test), `answers_*.md` (real LLM). Each has a `.json` with per-query data. |

Code: `src/rag_template/evals/` (`metrics.py`, `gold.py`, `workspace.py`, `retrieval.py`, `gates.py`,
`answers.py`, `synth.py`, `report.py`, `cli.py`). Unit tests: `tests/test_eval_*.py`.

## What counts as relevant

A gold item is `{file, snippet}`. A retrieved chunk is relevant when it comes from that file and contains the
snippet (lower-cased alphanumerics, so whitespace and indentation do not matter). Because relevance is judged
on text and not on chunk ids, the same gold set scores any chunker, which is what makes "AST chunks vs fixed
windows" a fair comparison. Gold that a chunker splits across two chunks, or that the quality gate rejected, is
counted and reported (`gold reachable / gated out / split`), not silently dropped.

## Metrics

Recall@{1,3,5,10,20} (share of gold items covered by the top k; equals hit rate when a query has one gold
item), MRR@10, nDCG@10 (binary gains; the ideal ranking uses the number of relevant chunks that exist in the
index), MAP@10. Intervals are 95% percentile bootstraps over queries; comparisons between systems use a
*paired* bootstrap on the same queries and report the difference, its interval and a one-sided p-value. With
70 queries a difference of a few points is noise: look for bold (interval excludes 0) before believing one.

## Results at a glance

Full tables, confidence intervals and per-query data are in `results/`; every number below is copied from the file named in the last
column. "Significant" means the paired-bootstrap 95% interval excludes 0. Recall@5 unless stated; 70 hand-written queries (35 docs,
35 code) and 149 synthetic ones.

**Retrieval**

| Question | Hand-written | Synthetic | Reading | File |
|---|---|---|---|---|
| Hybrid RRF vs BM25 alone | +8.6 (sig.) | +24.2 (sig.) | BM25 alone is clearly worse. | retrieval*.md |
| Hybrid RRF vs dense alone | +5.7 (n.s.) | -2.7 (n.s.) | **Undecided**: the sets disagree, neither is significant. | retrieval*.md |
| EmbeddingGemma 2 vs bge-small, dense | +5.7 (n.s.); MRR +12.6 (sig.) | +6.7 (sig.) | Better when used alone; after jina reranking the gap is +1.4 (n.s.). | retrieval*.md |
| AST chunks vs fixed 250-token windows, dense | +15.7 (sig.) | not run | AST wins, and the gain survives removing the breadcrumb: it is the chunk *boundaries*. | retrieval.md, ablations.md |
| Breadcrumb as the document title | +0.0 (n.s.) | not run | No measurable gain on its own. | ablations.md |
| Code-retrieval task prefix vs search prefix | +2.9 (n.s.) | MRR -4.4 (sig., worse) | Not worth switching. | retrieval*.md |
| 256-d Matryoshka vs 768-d | -2.9 (n.s.) | MRR -5.1 (sig.) | A small real loss; only for storage. | retrieval*.md |

**Rerankers** (hybrid RRF + reranker, 20 candidates)

| Question | Hand-written | Synthetic | File |
|---|---|---|---|
| jina-reranker-v3.5, `replace`, vs plain RRF | recall@1 **+18.6**, recall@5 **+10.0**, MRR **+15.4** (all sig.) | recall@1 **+25.5**, recall@5 **+11.4**, MRR **+20.2** (all sig.) | rerankers_*.md |
| jina, `fuse`, vs plain RRF | recall@5 +2.9 (n.s.), MRR +6.9 (sig.) | recall@5 +8.1 (sig.), MRR +8.9 (sig.) | rerankers_*.md |
| jina vs ms-marco-MiniLM-L-6 (both `replace`) | recall@5 +14.3, MRR +20.8 (sig.) | recall@5 +18.1, MRR +23.5 (sig.) | rerankers_*.md |
| ms-marco `replace` vs plain RRF | -4.3 (n.s.); on code -11.4 at 20 and -14.3 (sig.) at 60 candidates | -6.7 (sig.) | rerankers_*.md |
| ms-marco `fuse` vs plain RRF | -1.4 (n.s.) | +2.0 (n.s.) | rerankers_*.md |

jina's costs: about 1.0 s per query at 20 candidates (0.5 s at 10, 2.8 s at 40, 5.4 s at 60), 1.1 GB of GPU memory, a non-commercial licence
(CC-BY-NC-4.0), and **sensitivity to candidate order**: re-scoring the same 20 candidates in shuffled order gave a mean Kendall tau of 0.61
with the best candidate unchanged in 69% of shuffles (ms-marco: 1.00 and 100%, it scores each candidate alone). `replace` is the better mode
for jina and the worse one for ms-marco, so the default mode depends on the model (`rerankers.default_rerank_mode`).

**Unanswerable questions** (`answerability.md`, `gate_stability.md`, `answer_policies.md` section 2b). 59 unanswerable questions: 15 written
first, then 44 more in three labelled kinds (far-off, near-miss, false-premise), each checked to contain no word that occurs in the corpus.

| Signal available before the LLM is called | AUC (95% CI), 70 + 149 answerable vs 59 unanswerable |
|---|---|
| jina top-1 relevance score | 0.96 (0.94-0.98) |
| dense cosine of the nearest chunk | 0.92 (0.87-0.96) |
| ms-marco top-1 relevance score | 0.86 (0.81-0.92) |
| question-term coverage in the top 5 | 0.69 (0.62-0.77) |

A threshold set from the hand-written answerable questions only (keeping 95% of them) was **0.211** for jina. On data it was not chosen from
it refused 83% of the unanswerable questions (49/59) and wrongly refused 9% of the synthetic answerable ones (14/149; 4% of the hand-written
ones it came from). ms-marco's threshold did not transfer (4% wrong refusals on the tuning set, 30% held-out). End to end with the real LLM,
the same recorded replies re-judged with the gate: unanswerable questions answered and passed fell from 16/59 (27%) to 4/59 (7%) at 0.211,
for one fewer usable answer out of 70. **The gate is off by default** (`RAG_MIN_RELEVANCE`) because jina's order sensitivity makes single-pass
decisions noisy near the threshold: two independent measurements of the same unanswerable question disagree 11% of the time at 0.211 (answerable
questions: 3%); averaging three candidate orders halves that (5% and 0%) at three times the latency, and does not change the AUC.

**Answer gate** (Gemma 4 E2B; `answer_policies.md`). Reply format changed the share of correct answers wrongly flagged more than any policy
did; the default (`balanced`, schema-enforced replies, quotes first) flagged 18% of correct answers on this set against 57% for strict
with a plain reply, and 14% vs 26% of all answers on the held-out synthetic set.

## PDFs (`results/pdf_backends.md`)
`corpus/banking/` is a 202-page Pakistani statute (born-digital); `gold/banking.jsonl` has 32 answerable questions
(snippets taken from the PDF's own text, so a converter that scrambles text is penalised) and 12 unanswerable ones
(not yet run). Backend comparison, in short: pymupdf4llm kept all 32 snippets intact, Docling 30 (it scrambles
the Definitions page and flattens code to one line); both OCR clean scans equally well; only Docling recovers
formulas (as LaTeX, with some junk). Retrieval on the statute, default pipeline: recall@5 100.0 (pymupdf4llm) vs 87.5
(Docling), n = 32, one document -- suggestive, not proven. `RAG_PDF_BACKEND=auto` (default) picks per file: scans and formula-heavy documents go to Docling, the rest to pymupdf4llm (`pdf_profile.py`; thresholds fitted to 13 documents, see the results file).

### Multi-document PDF benchmark
`corpus/pdfs/` (5 PDFs of different kinds, third-party, not for redistribution) + `gold/pdfs.jsonl` (82 answerable, 24 unanswerable).
After generic Markdown cleanup (`mdclean.py`), pymupdf4llm and Docling reach the same overall recall@5 (96.3); `auto` 95.1. See
`results/pdf_backends.md` for the table, the noise caveat (one question = 7 points on a 14-question kind) and what is not measured.
Run: `RAG_PDF_BACKEND=<auto|pymupdf4llm|docling> python -m rag_template.evals retrieval --corpus evals/corpus/pdfs --gold evals/gold/pdfs.jsonl --no-baselines`
(stop the LLM server first: Docling, the embedder, the reranker and a loaded LLM together exceed 8 GB).

### External golden QA (`results/golden_pera.md`)
`python -m rag_template.evals golden --golden FILE --data-dir DIR [--ingest PDF] [--json-mode schema]` scores an already ingested store through
the same `RAG` facade as the UI: evidence reachability, retrieval, then answers and gates, with a per-question table to read. Copy the live `data/`
first if the app is running. Uses so far: the Protection of Economic Reforms Act set (44 questions, `results/golden_pera.md`) and the TRM paper set (69 questions, `results/golden_trm.md`). `RAG_EMBED_DEVICE=cpu` and `RAG_RERANK_TOP=10` let it run beside a UI and LLM server on an 8 GB GPU (measured not to change the results beyond noise).

### Experiments run outside the harness (`external/`)
Scripts, kept so a result can be rerun; each takes its paths as arguments. `results/architecture_review.md` is the running log of what they found, including the negative results.
- `external/open_ragbench/`: retrieval-only run on a frozen slice of the Open RAG Benchmark (arXiv PDFs, CC-BY-NC-4.0): `select.py` (hash-picked slice), `fetch.py`, `ingest.py`, `evaluate.py` (four variants), `report.py`, `control.py` (validity check of the section-level proxy). Raw per-query results are the `res_*.json` files; numbers in `results/open_ragbench.md`; freeze record in `results/freeze_open_ragbench.txt`.
- `external/oracle/oracle.py`: answers each MiniCPM4 dev question from only its gold-evidence chunks (does perfect retrieval help? no).
- `external/prompt_line/run.py`: one extra sentence in the system prompt (not adopted).
- Hand grades behind those runs are in `gold/minicpm4_*grades.json` (one grader, one run each).

### Conversion check (`results/conversion_check_findings.md`)
`python -m rag_template.evals conversion [--corpus DIR ...] [--backends pymupdf4llm docling]` converts each PDF with each backend and runs the same
check ingestion runs (`convcheck.py`: converted text vs Poppler's `pdftotext`). Flags 3 of 5 known defects outright, 1 by a related symptom, misses the
Docling statute scramble; tuned on these same documents, so optimistic.

## Commands

```bash
python -m rag_template.evals retrieval            # all systems and chunkers -> results/retrieval.{md,json}
python -m rag_template.evals ablations            # reranker mode, breadcrumb, merge threshold -> results/ablations.*
python -m rag_template.evals retrieval --gold evals/gold/synthetic.jsonl --out evals/results/retrieval_synthetic --no-baselines
python -m rag_template.evals rerankers --tops 10 20 40 60   # jina vs ms-marco: mode x candidates, latency, VRAM, order stability
python -m rag_template.evals answerability        # can retrieval scores detect unanswerable questions? (AUC, operating points)
python -m rag_template.evals gate-stability       # does candidate order flip the relevance gate's decisions?
python -m rag_template.evals quotes               # how tolerant should quote matching be?
python -m rag_template.evals summarize            # rebuild results/answer_policies.md from the saved files
python -m rag_template.evals gates                # adversarial answer-gate test, no model needed
python -m rag_template.evals synth -n 150         # regenerate synthetic queries (needs scripts/serve_llm.sh running)
python -m rag_template.evals answers              # real LLM end to end (needs scripts/serve_llm.sh running)
```

## Caveats (read before quoting any number)

- **One corpus, one project.** Python and Markdown from a single repository. Nothing here says how this
  behaves on Java, on scanned PDFs or on a different domain. Re-run on yours; the harness takes `--corpus`
  and `--gold`.
- **The hand-written gold was written by the person who built the system.** I wrote the queries from the files,
  not from retrieval results, and varied them (identifier-style, natural, paraphrased), but the bias is real.
- **The synthetic set is lexically and structurally biased.** Each question was written *from* a chunk, so that
  chunk is the only one labelled relevant even if another also answers it (recall is underestimated), the
  generator is a small LLM reading the same text, and 75% of the sampled chunks are code. Filters remove
  questions that copy a 4-word phrase and gold whose evidence also appears in another file, which reduces but
  does not remove this. It is reported separately and not mixed into the hand-written numbers.
- **"Correct" in the answer eval is a substring check** on a hand-written key phrase. It misses correct answers
  worded differently, so correctness rates are lower bounds.
- **Adversarial gate scenarios are easy by construction** (clean answers are copied from the gold snippet). They
  measure what the gates *can* detect, not their false-reject rate on real model output; the `answers`
  evaluation measures that, with a real small model.
- **Reranker conclusions are about the two rerankers tested** (`jina-reranker-v3.5` and `ms-marco-MiniLM-L-6-v2`), not about reranking in
  general. The synthetic set favours dense retrieval and paraphrase; the hand-written set was written by the author of the system.
- **The 59 unanswerable questions are hand-written by the system's author**, in three kinds. They are adversarial in different ways
  (near-miss and false-premise are the hard ones) but a different author would write different ones, and 59 is small: the operating-point
  intervals are wide. The synthetic *answerable* questions are only used to estimate false refusals, never to choose a threshold.
- **jina scores depend on candidate order**, so every jina number here is for the natural fused order (best first), which is what the
  system uses. Different orders give different scores (`gate_stability.md`).
