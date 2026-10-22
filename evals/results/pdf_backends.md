# PDF backends: pymupdf4llm vs Docling

Measured 2026-10-16. **Small, single-run, ad-hoc**: the comparisons below were produced by scratch scripts, not by a
`python -m rag_template.evals` command, so they are not yet reproducible from the repo. The retrieval rows are
(`banking_pymupdf4llm.md`, `banking_docling.md`) and are reproducible: `RAG_PDF_BACKEND=<b> python -m rag_template.evals
retrieval --corpus evals/corpus/banking --gold evals/gold/banking.jsonl --no-baselines`.

Versions: docling 2.139.0 (layout model run on onnxruntime-gpu 1.31.0), pymupdf4llm 1.28.2, RTX A2000 8 GB.

## 1. Born-digital statute (Banking Companies Ordinance 1962, 202 pages)
Reference = the PDF's own text (`pdftotext`). 32 gold snippets, each verified to occur exactly once in it.

| converter | gold snippets intact | time |
|---|---:|---:|
| pdftotext (control) | 32/32 | -- |
| PyMuPDF plain text | 32/32 | 0.1 s |
| pymupdf4llm | 32/32 | 34 s |
| Docling | 30/32 | ~37 s |

Docling's reading order scrambles the Definitions page: section 5(b) comes out as `... withdrawable by cheque, draft,
order securities for the purpose of that sub-section; 1 or otherwise;` (text of the previous definition spliced into
the middle), and clause (d) is pasted inside the Explanation under 5(c). It also splices page-bottom footnotes into
sentences that cross a page break (only 12 of the footnotes in pages 15-40 carry Docling's `footnote` label).

Retrieval, default pipeline (dense + BM25 -> RRF -> jina-reranker-v3.5 `replace`, 20 candidates), 32 questions:

| | gold reachable | recall@1 | recall@5 | MRR@10 |
|---|---:|---:|---:|---:|
| pymupdf4llm | 32 | 78.1 | 100.0 | 86.5 |
| Docling | 29 (3 split) | 68.8 | 87.5 | 77.6 |

n = 32, 95% intervals about +/-10: the gap is suggestive, not proven (no paired test was run).

## 2. Scanned pages (19 statute pages rasterised at 200 dpi, no text layer)
| converter | time | 8-gram recall of the 12 gold snippets in range |
|---|---:|---:|
| Docling (RapidOCR/onnxruntime) | 35.6 s | 1.00 |
| pymupdf4llm (RapidOCR) | 73.6 s | 1.00 |

Optimistic: a clean rendering, not a skewed or noisy scan.

## 3. Code (MCP Engineer's Handbook, pages 1-25)
Docling collapses fenced code to one line (`from typing import Annotated, Literal from pydantic import Field def
search( query: str, ...`) and emits fragments such as ```` ```2))``` ````; pymupdf4llm keeps line breaks and indentation.
Fences: Docling 42, pymupdf4llm 79. Time: 18.3 s vs 6.1 s.

## 4. Formulas (ESLII, pages 62-77)
Docling recovers display equations as LaTeX (49 formulas), but its formula model appends hallucinated junk to some
(`... \intertext{l e f t h e r s u m e s} \exists \text{either} ...`). pymupdf4llm drops display equations entirely.
**Formula quality was not scored** (no gold); this is a visual check of one equation.

## Layout engine (Docling only)
Same 20 pages: torch on GPU 10.7 s / 2008 MB RAM; onnxruntime on GPU 6.4 s / 2085 MB RAM; onnxruntime on CPU 55.3 s /
1281 MB RAM. Output was byte-identical in all three. The lower-RAM claim for ONNX holds only on CPU, where it is 5.8x slower.

## Choosing the backend per document (`pdf_profile.py`, `RAG_PDF_BACKEND=auto`, the default)
A PyMuPDF pass over up to 40 evenly spaced pages (0.1-0.3 s per document, 1.3 s for the scanned file). Rule:
scanned pages >= 50% -> Docling; pages containing math >= 20% -> Docling; otherwise pymupdf4llm.
"Math" = characters in a TeX/Symbol/MathType font or in the Unicode Greek/operator blocks (a lone Symbol-font glyph,
i.e. a Word bullet, does not count; unit-tested).

| document | scanned | math pages | mono | chosen |
|---|---:|---:|---:|---|
| statute | 0.00 | 0.00 | 0.00 | pymupdf4llm |
| MCP handbook (code) | 0.00 | 0.00 | 0.52 | pymupdf4llm |
| LLM reference (tables) | 0.00 | 0.00 | 0.00 | pymupdf4llm |
| ESLII | 0.00 | 0.65 | 0.00 | docling |
| ISLP | 0.00 | 0.55 | 0.14 | docling |
| scanned statute pages | 1.00 | 0.00 | 0.00 | docling |
| Linear Algebra for ML | 0.00 | 0.33 | 0.14 | docling |
| Competitive Programmer's Handbook | 0.00 | 0.10 | 0.06 | pymupdf4llm |
| Statistical Methods for ML | 0.00 | 0.03 | 0.19 | pymupdf4llm |
| 5 others (LLM-from-scratch, DL with Python, Tanenbaum, Atomic Habits) | 0.00 | 0.00 | 0.00-0.19 | pymupdf4llm |

**What this does and does not show.** Only 4 of the 13 documents have a measured better backend (statute and code
-> pymupdf4llm, ESLII -> Docling for its equations, the scan -> Docling for speed); the rest are the rule applied,
not a verified outcome. The 0.2 threshold sits in the gap between 0.10 and 0.33, set after seeing these numbers, so
it is fitted to them. Per document, not per page: ISLP and Linear Algebra for ML mix heavy math with code, and are
sent to Docling, which may flatten their code (not measured on those books).

## Why each statute question was missed (default pipeline, 32 questions; scratch script, not a CLI command)
Questions whose gold chunk was not rank 1, classified by the first stage that failed:

| backend | converter lost the text | chunker split it | gate rejected it | retrieval ranked it low | not in top 20 |
|---|---:|---:|---:|---:|---:|
| pymupdf4llm | 0 | 0 | 0 | 7 (ranks 2-4) | 0 |
| Docling | 2 (b15, b16: scrambled definitions) | 1 (b07) | 0 | 6 (ranks 2-3) | 1 (b26, cause not found) |

b26's chunk has the same shape in both backends (sections 1-2 plus a footnote, 450-480 tokens, answer ~300 characters in),
so the Docling miss is not explained by the converter or chunker; treat it as unexplained.

**Not covered by this test:** (1) footnotes spliced into sentences: the gold snippets were chosen to avoid page breaks, so their
effect on retrieval is unmeasured; (2) matching normalises whitespace and punctuation, so it cannot see pymupdf4llm's blank
lines inside sentences ("This Ordinance / / may be called") or its `**bold**` markers in the text and breadcrumbs, which
would show up in quoted answers; (3) chunks are not section-aligned (the breadcrumb is the Part title, e.g. "PRELIMINARY"),
which this metric does not penalise because 32/32 reach the top 4; (4) the answer step, quote verification and the 12
unanswerable questions were not run on the statute.

## Answer pipeline on the statute (`answers_banking.md`; pymupdf4llm chosen by `auto`; Gemma 4 E2B, 5 chunks, `balanced`, schema JSON)
32 answerable + 12 unanswerable. One run each; the second run (after the change below) refused 8/12 vs 9/12 in the first on
the same questions, so differences of one question are noise.

| | first run | after source re-attribution |
|---|---:|---:|
| gold chunk in the model's context | 31/32 | 31/32 |
| answer contains the expected fact | 31/32 | 31/32 |
| answered and passed every gate | 24/32 (75%) | 26/32 (81%) |
| correct among flagged answers (false alarms) | 8/8 | 5/6 |
| unanswerable: refused / answered-and-passed (dangerous) | 9 / 2 | 8 / 2 |

**Change found by this run.** The model quoted the statute verbatim and correctly but wrote the statute's own number as
the source (`"source": 22` for section 22, with 5 sources), so 4 correct answers were flagged "cites sources that do not
exist". `Answerer._reattribute` now resolves a source number *greater than the number of sources* from the quote when it
is verbatim in exactly one retrieved chunk, and rewrites `[22]` to it. An in-range but wrong number, an ambiguous quote and
an invented quote are all still flagged (tests; mutation-checked). `evals gates` (adversarial) is unchanged. Not re-run on the
QuestionPrep answers, where the model cited correctly.

**Still open.** 4 of the 6 remaining flags are "no verified quote" (cause not diagnosed). The 2 dangerous unanswerable
answers (n10, n12) are near-misses; n12 may be mislabelled (the statute may contain a Mohtasib complaint-response time).
**Chunk labels from pymupdf4llm are poor**: most of the Ordinance body is labelled `**ORDINANCE No. LVII OF 1962** > **engage.—**`
(a stray bold fragment became a heading), and some labels contain raw `<sup>`/`<u>` tags. Retrieval metrics cannot see this;
every citation shown to a user does.

# Multi-document PDF benchmark (`evals/corpus/pdfs/`, `evals/gold/pdfs.jsonl`)
Five PDFs indexed together (867 chunks), 82 answerable questions (statute 32, code 14, tables 14, math 12, scan 10) and 24
unanswerable (not yet run). Every snippet is verbatim from the PDF's own text (`pdftotext`) and occurs exactly once in it.
Default pipeline (hybrid RRF + jina `replace`, 20 candidates). Results: `pdfs_pymupdf4llm.md`, `pdfs_docling.md`,
`pdfs_auto.md` (+ `.json` per query). The documents are third-party material from the author's machine (MCP handbook, an LLM
reference, an ESLII excerpt, ISLP pages re-rendered as a tilted, noisy, JPEG-compressed scan): **do not redistribute**.

| kind (n) | pymupdf4llm R@1 / R@5 / MRR | docling R@1 / R@5 / MRR | auto R@1 / R@5 / MRR |
|---|---|---|---|
| statute (32) | 84.4 / 93.8 / 89.4 | 81.2 / 93.8 / 86.2 | 84.4 / 93.8 / 89.4 |
| code (14) | 85.7 / 92.9 / 89.3 | 85.7 / 100.0 / 92.9 | 85.7 / 92.9 / 89.3 |
| tables (14) | 71.4 / 100.0 / 85.7 | 71.4 / 100.0 / 84.5 | 78.6 / 100.0 / 89.3 |
| math (12) | 91.7 / 100.0 / 95.8 | 91.7 / 100.0 / 95.8 | 91.7 / 100.0 / 95.8 |
| scan (10) | 90.0 / 100.0 / 95.0 | 80.0 / 90.0 / 85.0 | 80.0 / 90.0 / 85.0 |
| **all (82)** | 84.1 / 96.3 / 90.4 | 81.7 / 96.3 / 88.3 | 84.1 / 95.1 / 89.8 |
| gold reachable intact | 82 | 79 | 81 |

**How to read it.**
- **Noise is about one question.** The tables row uses the identical converter in the pymupdf4llm and `auto` columns and still
  differs by 7 points in R@1 (one question of 14: the other documents in the index changed). Differences of one question are not signal.
- **After cleanup the backends are close on retrieval**: same overall R@5 (96.3). Docling loses 3 gold items outright (the scrambled
  definitions b15/b16 and a split); pymupdf4llm loses none.
- **`auto` did not beat pymupdf4llm alone** (R@5 95.1 vs 96.3). Its only difference is routing the scan to Docling, one question worse.
  The math gold is prose by necessity (a formula cannot be matched by snippet across converters), so **the formula benefit of Docling,
  the reason for routing math to it, is not measured by this benchmark.**
- **Noisy scan, OCR fidelity** (10-gram overlap with the true text, cache off): pymupdf4llm 56.1 s, recall 95.6%, precision 95.8%;
  Docling 28.2 s, recall 92.4%, precision 94.3%. Docling is 2x faster and ~3 points less faithful.
- Only the statute's unanswerable questions have been run through the answer step; the other 12 negatives are not run.

## What generic cleanup changed (`mdclean.py`, applied to every PDF conversion; unit-tested)
Before cleanup (pymupdf4llm, same gold and corpus) 76/82 gold items were reachable and tables scored R@5 64.3: wrapped table
cells were written `constant<br>compute per token`, so the words did not match. After: 82/82 reachable, tables 100.0, code 85.7 -> 92.9.
The statute's R@5 moved 100.0 -> 93.8 (two questions) in the same change; the earlier per-query file was overwritten, so I cannot say why.
The one inspected case (b15) is a mislabelled chunk: pymupdf4llm marked only some of the statute's bold lines as headings, so the
definitions chunk is labelled "3. Limited application of Ordinance to Co-operative Banks (Omitted)" and starts with footnote debris.

## Known limits of this benchmark
Questions were written by the person who built the system; one document per kind; snippets avoid page breaks (footnote splicing unmeasured);
no formula-answer questions; 24 negatives mostly unrun; OCR scored on a synthetic scan of one book.

## Addendum: a research paper (TRM, 12 pages), question-level (see `golden_trm.md`)
On answers to 63 golden questions the two backends retrieved the same evidence; Docling's text produced more correct answers (49 vs 44 graded;
sign test on the differing answers p = 0.11) because pymupdf4llm fused a footnote marker into a value ("15M" for 5M), mislabelled sections and dropped
equations. The auto detector routes this paper to pymupdf4llm. Together with the statute (pymupdf4llm kept all snippets, Docling scrambled two
definitions) and the code handbook (Docling flattened code), the evidence now says the better backend depends on the document in ways the
detector's math/scan signals do not capture.

## Update: source ids on the statute (`answers_banking_final_*.md`; 32 answerable + 12 unanswerable, Gemma 4 E2B)
| | original (integer ids, schema) | `[S1]` ids, schema | `[S1]` ids, plain JSON |
|---|---:|---:|---:|
| answerable delivered | 24/32 | 23/32 | 24/32 |
| flagged "cites sources that do not exist" | **4** | **0** | 0 |
| flagged "no verified quote" | 2 | 6 | 6 |
| unanswerable passed the gates (of 12) | 2 | 3 | **6** |

With the id enum enforced by the schema the model can no longer cite a statute's own section number as a source (4 -> 0). The delivered count is unchanged within
noise (n = 32). **The unanswerable row in plain mode is a worse number (6 of 12 passed vs 2 in the original schema-mode run; there is no plain-mode baseline for the statute),
and I cannot separate the effect of the ids from the effect of plain mode.** On PERA and TRM, where a plain-mode baseline exists, that number did not change (4 -> 4, 3 -> 3).
