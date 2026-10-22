# SSD paper (`ssd_golden_qa.jsonl`, 70 questions) - PARTIAL RESULTS, grading unfinished

Paper: "Embarrassingly Simple Self-Distillation Improves Code Generation" (`2604.01193v2.pdf`, 37 pages), fresh ingest at default settings.
`auto` picked **Docling** (43% of pages contain math). Golden file: 60 answerable, 5 partially answerable, 5 unanswerable; `answerable` is yes/partial/no
(the harness now reads that; older reports regenerate byte-for-byte). Reports: `golden_ssd.md` (exact quotes), `golden_ssd_auto.md` (Docling, fuzzy evidence),
`golden_ssd_pymupdf4llm.md` (pymupdf4llm, fuzzy evidence). Gold sidecar `evals/gold/ssd.jsonl`.

## Measurement problem found first
With exact quote matching, 21 of 101 evidence quotes looked "absent" from the index. **20 of the 21 are not in the PDF's own text layer either**: the golden
author's evidence is a rendering of the source (`Qwen3-30B-Thinking base: v6 pass@1 [66.1, 99.8, 73.0, 41.5]` for a table row, `L(theta) = -log KeptMass...` for an
equation). So exact matching blames the system for an artefact. `--fuzzy-evidence` (opt-in) counts a chunk as holding a quote when it has >= 80% of the quote's
digit-bearing tokens (or of all tokens when it has fewer than 3 numbers).

## Retrieval (65 questions with evidence, fuzzy relevance, k = 5)
| | Docling (auto) | pymupdf4llm |
|---|---:|---:|
| evidence found in the index | 95/101 | 96/101 |
| evidence chunk in the top 5 | 58/65 | 60/65 |
| evidence chunk ranked first | 37/65 | 47/65 |
| chunks (usable) | 188 (182) | 98 (85) |

## Answers (60 answerable), gates only (NOT a correctness measure)
Docling 51 delivered / 9 flagged / 0 refused; pymupdf4llm 51 / 7 / 2. The keyword check (numbers taken from the ground truths) finds all numbers in only 7 of 32
questions for both backends, item recall on the 7 list questions 0.55 (Docling) and 0.69 (pymupdf4llm). Unanswerable: 4 of 5 refused, 0 passed the gates, both backends.
Partially answerable: 2 of 5 refused outright (a fail), the rest answered; whether they say what is missing has not been read.

## Hand grading (Docling/auto run only, first 24 of 70 questions; the rest NOT graded)
16 correct, 4 partial, 4 wrong. The wrong ones: q015 (does not answer the hyperparameters question), q020 (flagged, one number), q022 and q023 (table lookups with the
wrong "after" value: 59.7 for 46.7, and 0.8 for 1.6; q022 passed the gates, q023 was flagged). Partial: q001 adds a name not in the equal-contribution footnote, q005 lists
one of seven exclusions, q018 gives one of six models, q019 omits pass@5. So 2 of the first 2 table-cell questions were wrong, and the gate let one wrong number through.

## Not done
Grading of questions 25-70 and of the pymupdf4llm run; the conversion check's warnings on this PDF (11% of words missing, 10 replacement characters, 4 flattened code
blocks) have not been tied to specific wrong answers. Do not read the delivered counts above as accuracy.
