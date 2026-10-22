# Conversion check: what it catches and what it does not (`convcheck.py`, table in `conversion_check.md`)

The check compares a converted PDF with the PDF's own text from Poppler's `pdftotext` and **reports** (it never changes what is indexed).
It runs at ingest (`RAG_CONVERSION_CHECK=on` by default), costs ~0.3 s for a 202-page document, is stored with the document and shown in the
UI's Library tab and by `rag ingest`. Reproduce with `python -m rag_template.evals conversion`.

## Why the reference is Poppler and not PyMuPDF
PyMuPDF's own text reads the TRM paper's footnote as "15M": the 7-pt marker and the 9-pt text are adjacent spans with no space. pymupdf4llm
inherits that, so a PyMuPDF reference shares the defect and cannot see it. `pdftotext` keeps "1 5M".

## Result on the five defects found earlier, and on documents without a known defect
| case | backend | verdict | what fired |
|---|---|---|---|
| TRM paper: footnote marker fused into a value ("15M") | pymupdf4llm | warn | fused numeric token `15m` |
| MCP handbook: code collapsed onto one line | Docling | **bad** | 72 code blocks on one line |
| TRM paper: junk letters in a formula | Docling | warn | 1 spaced-letter run ("f o r w a r d p a s s ..."); also a merged page range `9430-9440` |
| ESLII excerpt: display equations dropped | pymupdf4llm | warn | **for a related reason**: 11 replacement characters. Word recall (92%) is above the 90% line, so "equations are missing" is not what it says |
| Statute: definitions page scrambled | Docling | warn, **not detected** | fires only on an unrelated `1981page` fusion |
| Statute: footnote markers fused into words (`2twenty thousand rupees`, `3Provided`) | pymupdf4llm | **bad** | 5 fused tokens; 23 of 45 tables have ragged rows (found by the check, not known beforehand) |
| PERA (a clean 7-page Act) | both | ok | nothing |
| LLM-reference tables | pymupdf4llm / Docling | warn / warn | 1 ragged table of 31 / one fused token `v32` (minor) |
| scanned ISLP pages | both | not-run | no text layer |

So: 3 of the 5 earlier defects flagged outright, 1 flagged for a related symptom, 1 missed; one new real problem found; the one clean document is clean.

## The scramble is not detectable this way (tested)
A windowed order check (120-word windows, 6-word runs) flags the same layout-heavy regions (contents list, forms, annexure tables) for both
backends and does not isolate Docling's two scrambled definitions; at document level the order gap is 0.049 (Docling) vs 0.056 (pymupdf4llm). The order
warning therefore only fires on gross interleaving (gap > 0.25), and a scramble of a few paragraphs passes.

## How the first version went wrong (so the thresholds are not read as more than they are)
The first run called 8 of 12 text-layer conversions "bad" or noisy. Every one of those alarms came from the check itself and was fixed before the table above:
ordinals written `23^rd` / `23 rd` read as dropped numbers; `Pakistan.1` tokenised as one token; page numbers the converter keeps counted as novel;
letter-spaced capitals (`C O N T E N T S`, real typography) counted as junk; and "dropped numbers" inflated by `pdftotext` itself gluing markers to
words (`thursday2`). On equation-heavy PDFs (>= 20% of pages with math, from `pdf_profile`) the numeric findings are shown as examples but do not raise
a warning, because subscripts (`x13`) make them unreliable there.

## Caveats
- **Thresholds were tuned on the same five documents they are evaluated on**, so the table above is optimistic about unseen PDFs. Treat the verdicts as a screen, not a measurement.
- Defects both extractors share (a footnote spliced into a sentence at a page break) are invisible by construction, as are misaligned table columns with the right words, heading levels, and any scan.
- `pdftotext` is a system dependency; without it the verdict is `not-run`, never an error.
