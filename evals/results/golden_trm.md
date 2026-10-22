# Golden QA evaluation: "Less is More: Recursive Reasoning with Tiny Networks" (`trm_golden_qa.jsonl`, 69 questions)

Golden file supplied by the user: 63 answerable questions (10 types: factual, numeric, list, multi-hop, mechanism, table, reasoning,
comparison, conditional) with evidence quotes, 6 unanswerable. Scored by `python -m rag_template.evals golden` against `evals/gold/trm.jsonl`
(the file plus a facts sidecar); grades in `evals/gold/pera_grades.json` (runs `trm_*`). Gemma 4 E2B, k=5, `balanced` policy.
Reports: `golden_trm_live.md` (run 1), `golden_trm_live_schema.md` (run 2), `golden_trm_fixed.md` (run 3), `golden_trm_fixed_default.md` (run 4).

| run | store | reply format | notes |
|---|---|---|---|
| 1 | copy of the user's live store (PERA + TRM, 63 usable chunks) | `json_mode` off (the UI's default) | embedder on CPU and 10 rerank candidates because the UI and LLM server left 1.8 GB of GPU; the UI reads 20 |
| 2 | same copy | schema | same GPU limits |
| 3 | TRM re-ingested with **table captions attached to their tables** (58 usable) | off | same GPU limits |
| 4 | as run 3 | off | default retrieval settings (GPU embedder, 20 candidates) |

## Results, answerable questions (63)
"Correct / partial / wrong" is **my reading of each answer against the golden `ground_truth`** (subjective). For run 3 I re-read the 21 answers
whose required-fact score or gate outcome changed and carried the other grades over from run 1; answers are paraphrased differently between runs,
so a carried-over grade is an assumption.

| | run 1 | run 3 |
|---|---:|---:|
| correct / partial / wrong | 41 / 10 / 12 | 44 / 12 / 7 |
| delivered / flagged / refused | 54 / 6 / 3 | 54 / 6 / 3 |
| correct and delivered | 39 | 40 |
| correct but flagged or refused | 2 | 4 |
| partial or wrong but delivered | 15 | 14 |
| evidence quote in a usable chunk | 101/101 | 101/101 |
| evidence chunk in the top 5 / ranked first | 57 / 49 | 61 / 51 |
| **table questions** correct / partial / wrong (6) | **1 / 1 / 4** | **4 / 2 / 0** |

Run 2 (schema, ungraded): delivered 54, flagged 7. Unlike on the statute, the reply format made no difference here.

**Unanswerable (6):** run 1: 3 refused, 2 acceptable explanations, 1 bad (q064 answers a question about a private evaluation set with an
unrelated 7.8%). Run 3: 2 refused, 2 acceptable, 2 bad (q064 again; q068 answers a scaling question with an unrelated parameter count).
Passed gates: 3 (run 1), 4 (run 3).

## Run 4: the GPU workaround did not matter
The GPU was freed after runs 1-3 (the UI and LLM server stopped), so run 4 repeats run 3 at the UI's own retrieval settings (GPU embedder, 20 candidates):
evidence in the top 5 60 vs 61, ranked first 49 vs 51, delivered 52 vs 54, flagged 9 vs 6, every required fact 42 vs 43, the six table questions' fact
scores identical. Differences of one to three questions are the run-to-run noise (LLM sampling), so the 10-candidate, CPU-embedder runs are representative.
Run 4's answers were not graded.

## By question type (run 1, graded)
numeric 12/12 correct; comparison 2/2; list 7/8; factual 12/17; mechanism 3/6; reasoning 2/3; multi-hop 2/8; table 1/6; conditional 0/1.
The reliable cases are single-fact lookups; the weak ones need a table, a derivation or two facts joined.

## What was wrong, by stage
1. **Table captions (generic, fixed):** the caption ("Table 1. Ablation of TRM on Sudoku-Extreme ...") sat in the neighbouring prose chunk, apart
   from the numbers, so a question naming the table retrieved the caption chunk and the model answered without the numbers. The chunker now
   puts a table's caption (above, else below) into the table chunk (`chunking/markdown.py`; tests). Table questions went from 1 correct of 6 to 4.
2. **Conversion (not fixed):** pymupdf4llm fused a footnote marker into a value: the paper's footnote "1 5M on Sudoku and 19M on Maze" is stored as
   "15M on Sudoku and 19M on Maze". A reader gets a wrong number; no later stage can detect it. The cell "5M/19M^1" also breaks the golden
   quote, so q048's evidence uses a verbatim anchor (`evidence_verbatim`). Another converter should be compared on this paper.
3. **Section labels (not fixed):** Table 1's chunk is labelled "3.3 Hierarchical interpretation based on complex biological arguments", 23 of 64
   chunks carry the paper title as their label, and "Deep Supervision" appears as a parent of unrelated sections: the converter's headings are unreliable.
4. **Gate (known limit):** 15 partial or wrong answers passed in run 1 (14 in run 3) because the gate checks support, not completeness or
   direction. q027 states the effect of the 1-step gradient backwards (improved 56.5% to 87.4%; the paper says it dropped 87.4% to 56.5%) and the
   keyword check scores it as correct: **the keyword scores overstate correctness; use the graded numbers.**
5. **Model (not fixed):** refusals and misreadings of retrieved text (q001 refuses to name the author, q060/q063 refuse derivable or tabulated
   answers, q057 invents a comparison); derived-value questions (q060) are beyond a 2B model.
6. **Run-to-run drift:** q061 was answered correctly in run 1 and became "the sources do not contain a comparison" in run 3, and q057 went from flagged to
   delivered and wrong. A change of one or two questions is noise at n=63 with sampling at temperature 0.1.

## Caveats
- One paper, one 2B model, golden questions written by someone else (a strength), graded by me (a weakness).
- The golden `relevant_chunk_ids` (`trm-c00`..`c27`, 28 chunks) belong to a different chunking and are ignored; relevance is by evidence quote.
- Runs 1-3 changed two things at once relative to the UI (CPU embedder, 10 candidates); run 4 removes that deviation (see below).
- The user's live store was not modified; it still holds the pre-caption ingest.

# Docling vs pymupdf4llm on the same paper (runs 4 and 5, identical settings)
Run 5 = the paper converted by Docling (layout model on onnxruntime-gpu, formula enrichment on), fresh store, `json_mode` off, GPU embedder, 20 candidates;
run 4 = the same with pymupdf4llm (+ the table-caption fix). Reports: `golden_trm_fixed_default.md` (4), `golden_trm_docling.md` (5).

| | pymupdf4llm (run 4) | Docling (run 5) |
|---|---:|---:|
| conversion time | seconds | 19 s |
| chunks (usable) | 63 (58) | 60 (55) |
| chunk labels: distinct / paper title as the whole label | 37 / 1 (a spurious "Deep Supervision" parent on unrelated sections) | 32 / 0 |
| display equations kept | 0 | 3 (as LaTeX; one with spaced-out junk letters) |
| footnote "5M on Sudoku and 19M on Maze" | stored as "**15M** ..." (marker fused into the value) | correct |
| evidence quotes reachable | 101/101 (with verbatim anchors) | 100/101 (q001: accent garbled by both) |
| evidence in the top 5 / ranked first | 60 / 49 | 60 / 49 |
| delivered / flagged / refused (answerable) | 52 / 9 / 2 | 54 / 8 / 1 |
| keyword check: every required fact | 42 | 46 |
| **graded correct / partial / wrong** (63) | 44 / 11 / 8 | **49 / 8 / 6** |
| correct and delivered | 40 | 46 |
| partial or wrong but delivered | 12 | 8 |
| table questions correct / partial / wrong (6) | 4 / 2 / 0 | 5 / 0 / 1 |
| unanswerable: refused / acceptable / bad | 3 / 4 / 2 | 3 / 4 / 2 |

**How to read it.**
- Retrieval is identical: the same 60 questions have the evidence in the top 5 and the same 49 rank it first. The difference is in what the model is given to read.
- Of the 21 answers that differed materially I re-read, Docling was better on 8 (q013, q031, q036, q037, q042, q054, q061, q063), pymupdf4llm on 2 (q027, q032),
  and they tied on 11. An exact sign test on those 10 discordant pairs gives p = 0.11: **suggestive, not significant**. The other 42 answers were
  assumed to deserve the same grade in both runs (their required-fact scores and gate outcomes were equal), which is an assumption.
- Docling's gains came from better-formed text: all three Table 2 rows, the footnote value intact, the 4-layer Transformer sentence kept with its
  neighbours, cleaner section labels. Its losses were an answer that refused (q027) and one that omitted the key clause (q032).
- Both backends fail the same hard questions (multi-hop 1-2 of 8 correct) and the same unanswerable one (q064), so the 2B model remains the limit.
- `RAG_PDF_BACKEND=auto` sends this paper to **pymupdf4llm**: the profile sees almost no math fonts (0.1%) and no math pages. The detector looks for
  equations, not for "an academic paper with footnotes and tables", so on this evidence it routes a document that Docling handled better to the
  other backend. Not changed here: one paper does not justify a new rule, and the statute and the code handbook showed the opposite.
