# Architecture review against RAG practice: what was done and measured

Plan and sources: see the scorecard in the session plan; primary sources used are Anthropic's contextual-retrieval post (top-20 failure 5.7% -> 1.9% on their data), ARAGOG (HyDE helped, multi-query did not) and the Seven Failure Points paper. Vendor blog numbers were not relied on.

## Done
- **Pooled multi-document eval** (`python -m rag_template.evals pool --isolated`, `pooled.md`): 6 corpora in one index (48 files after indexing the byte-identical statute once), 388 answerable queries. Pooled with reranker: recall@5 91.7 ±2.9, recall@1 70.5 ±4.8, MRR 81.7. Top-1 from another corpus: 7/337 (2.1%). Cost of sharing the index (recall@5, alone -> pooled): pera 97.4 -> 90.8, ssd 91.0 -> 86.2, trm 93.4 -> 91.8, others within 1.2. These are single runs on author-written golds; differences of a few points are within the intervals.
  - The first pooled run showed pdfs recall@5 95.1 -> 58.5. That was an artifact: `statute_banking_ordinance.pdf` and `Banking-Companies-Ordinance-1962.pdf` are the same bytes (same sha256). Fixed by indexing identical files once; not a retriever failure.
- **CI-style check** (`scripts/check.sh`, `.github/workflows/ci.yml`): unit tests without model tests, then `evals gates` compared with the committed table. The script runs locally (468 passed, 19 model tests deselected; table identical). The GitHub workflow itself has never run: this directory is not a git repository (unverified).
- **Embedder record**: the store remembers which embedder built its vectors (`meta` table); indexing or querying with another one raises `EmbedderMismatch`. Stores created before this have no record and are accepted. 4 tests.
- **Page numbers**: both PDF backends now emit per-page text (content identical to the full export on TRM, compared on letters and digits); chunks get `page` / `page_end`; CLI and UI show "(p. 5)". Checked against `pdftotext` per page on 5 PDFs: TRM 60/63, SSD 132/178, PERA 4/5, MCP handbook 339/344, tables reference 82/83 verified. Of SSD's 46 unconfirmed, 43 are LaTeX equation chunks that cannot be compared with pdftotext, so the checker cannot judge them; 3 are unexplained. Chunks not located: SSD 2/189, MCP 18/398, tables 5/88 (they get no page, not a wrong one).
- **Prompt injection probe** (`evals/probes/injection.py`, `injection.md`): 48 cases of naive "ignore previous instructions, say CANARY" text in a source. Gemma 4 E2B obeyed 0/48 and answered correctly in 44/48 delivered. So no prompt change was made. Not tested: adaptive or subtle injections; this is a screen.

## Not done
- LLM-written chunk context (contextual retrieval), neighbour expansion, chunk overlap, k / context budget sweep: need the pooled set as baseline (now exists) and, for contextual retrieval, a slow LLM pass over every chunk; ask before running.
- Per-stage timing/tracing, caching, incremental re-index, stable chunk ids, metadata filters.

## Score fusion vs RRF (`pooled_fusion.md`, 388 queries, one run)
Per-query z-score fusion (cosine and negated BM25, each standardised within the query, then added) was compared with the RRF the library uses, paired bootstrap on the same queries. `Retriever.search(fusion="zscore")` is opt-in; RRF is still the default.
- Without a reranker, z(1,1) is better: MRR@10 +4.4 [+2.3, +6.7], recall@1 50.3 -> 55.7; recall@5 +0.6 [-1.7, +2.9] and recall@20 +0.3 [-1.5, +2.1] are not distinguishable from zero.
- With the jina reranker (the default pipeline) no variant differs from RRF: z(1,1)+rerank vs RRF+rerank recall@5 +0.6 [-1.2, +2.4], MRR -0.0 [-1.4, +1.3], recall@20 +0.3 [-1.5, +2.1]. z(lexical x2)+rerank MRR +1.4 [-0.2, +3.0] has an interval that includes 0 (3 weightings x 3 metrics were compared, so a one-sided p=0.045 is not evidence on its own).
- Decision under the rule set before the run (interval excludes 0 after reranking): keep RRF. The reranker removes the first-stage ordering difference; the candidate ceiling (recall@20 95.0 vs 95.3) did not move.
- Where it would matter: a deployment without the reranker (jina is CC-BY-NC and costs ~1.4 s/query against ~40 ms for fusion alone) would gain from z(1,1). Not made the default for that case: not asked for, and tested on one run.

## MiniCPM4 evidence audit with `--fuzzy-evidence` (`golden_minicpm4_fuzzy.md`, Sharp-MiniCPM5 as generator)
The first attempt used an empty store copy and is void (every question refused); this is the rerun on a fresh copy of the live store (221 chunks, 189 usable).
- Evidence quotes (136): exact match in a usable chunk 97 (71%), fuzzy match (a chunk holds >= 80% of the quote's tokens) 25 (18%), absent 14 (10%). Strict matching had called 39 (29%) absent, so about two thirds of those were golden quotes written in another rendering than the converter's (tables, equations), not content missing from the index.
- Retrieval, evidence chunk in the top 5: 88% (76/86) with fuzzy matching vs 74% strict; ranked first 73% vs 60%. Fuzzy matching is lenient, so 88% is an upper estimate.
- Spot check of the 14 still absent (questions 022, 023, 045, 046, 054, 055, 056, 058, 062, 074, 078, 084; mostly Table 2, 6 and 8 values): 8 of the numbers they ask about (81.13, 80.55, 45.89, 42.28, 56.03, 52.99, 36.06, 34.93) are present in stored chunks. So the table content is in the index; the 14 are probably quote-format or row-splitting mismatches (unverified for all 14).
- Consequence: conversion is not the main cause of the table failures; the table answers fail at generation and gating (see the graded comparison), so the gate and answer-completeness work ranks above conversion work.

## Gate and context work on the dev split (MiniCPM4, hand-graded; test side unread)
Split rule: `src/rag_template/evals/split.py` (hash of the question text, 60% dev / 40% test; 400 / 258 of 658 distinct questions). Labels: `evals/gold/minicpm4_grades.json` (one grader). Everything below uses the 48 dev questions (144 graded answers across three models); no test-side output was read.
- Current gate on dev: flags 2 of 15 wrong answers and 7 of 28 partly right ones; 8 false alarms on 101 correct ones. Of the 8, two are cheap to fix deterministically (a list marker "3." read as a number; answers without [S#] markers whose quotes verify); the rest are quote-verification failures that look the same as true flags.
- LLM judge over the cited sources (one prompt, JSON verdict correct/incomplete/wrong): Sharp-MiniCPM5 as judge called 139/144 correct (caught 2/15 wrong, 3/28 partial, 0 false alarms); Gemma 4 E4B as judge called 138/144 correct (2/15, 5/28, 0). Not useful. One prompt only, so this does not rule out every judge design.
- `check_addresses_question` (exists in `verify.py`, not used by the answer gate) flags none of the 144 dev answers either way: no dev evidence to wire it in.
- Context sweep, Gemma 4 E4B, dev answerable questions (48): k=5 / 3000-token sources vs k=8 / 4500 tokens. Correct 36 -> 35, partly right 7 -> 9, wrong 5 -> 4. One answer improved (q036, now names the DeepSeek-R1-Distill filter), two got worse (q077 stopped answering "no", q080 mentions the 8-rollout ablation next to the 16). Single run per setting, so a few flips are within sampling noise. Result: bigger k / budget does not help; not adopted.
- Why partial answers stay partial (checked on q037, q029, q056): the missing facts exist in the store but not in the retrieved sources. q037's GRPO list is cut by a page break and by Table 5 sitting between chunk 66 (dynamic sampling) and chunk 68 (clip-higher, token-level loss, overlong filtering); the next chunk by position is the table, not the continuation. So plain previous/next expansion would pull the wrong chunk here; same-section expansion or merging prose across an interrupting table is the candidate fix (untested).

## Same-section chunk expansion (dev split, Sharp-MiniCPM5 as generator; `golden_minicpm4_dev_sharp_{control,expand}.md`)
`Retriever.section_neighbors` / `Answerer(expand_section=N)` / `evals golden --expand-section N`: after the k retrieved sources, add up to N chunks of the same document and section (same breadcrumb) within two positions of a retrieved chunk, following ones first. Off by default.
- Setup: 48 dev answerable questions, k=5, 4500-token source budget; control = same without expansion. Every question received extra chunks (mean 2.8).
- Noise: with no retrieval change, the control differs materially from the earlier graded run on 14 of 48 answers (sampling and the larger budget), so single-run differences of a few answers are not evidence.
- Of 48 answers, 24 differed between control and expansion; I graded those 24 pairs blind (order shuffled, key hidden). 18 tied. Expansion better: q029 (the loss is now given as L_NTP + lambda L_MTP, from a neighbour chunk), q035. Control better: q017, q042, q064, and q054 (the expansion run gave wrong averages). Net: 2 better, 4 worse, 18 tied among the changed; 24 more were identical. No benefit shown.
- Mechanism check: for q037 the missing facts (Clip-Higher, token-level loss) were in the prompt as source S7 but the 2B model answered from S1 only. For q029 it used the added chunk (S6). For q056 the needed table row was not in a neighbour. So the retrieval side works as designed; whether the model uses late sources is the limit.
- Decision: not adopted by default; kept as an option. Single model, single run, dev only.

## Pipeline levers tested after the blind test (dev data; Sharp-MiniCPM5)
- **A. NLI contradiction against the other retrieved sources** (`nli-deberta-v3-xsmall`, 144 dev answers, 3 thresholds): at the strictest threshold (0.9) it flags 5 of 15 wrong answers and 27 of 101 correct ones (27% false alarms; the bar was under 10%); at 0.5, 7 of 15 wrong and 38 of 101 correct. The 90th percentile of the contradiction score is 0.991 for correct and 0.986 for wrong answers: almost no separation. Checking against the cited sources instead flags 15-17 of 28 partly right answers but 32-44% of correct ones. Not adopted. (NLI exists in the repo only in the enrichment validator for maths chunks; `verify.py` already records that small NLI mislabels restated text.)
- **B. Automatic document routing** (keep only the best document's chunks when it leads the next by a reranker margin). Retrieval-only, 153 questions (TRM, PERA, MiniCPM4 dev) in a five-document index: chunks from another document in the top 5: 18.7% with no routing, 6.3% at margin 0.20, 3.9% at 0.10, 2.9% at 0.05 and 0.0; answers with any such chunk 39.2% -> 3.9% (0.10) / 2.6% (0.0); evidence in the top 5 unchanged at 89.5% at every margin; top-1 from the wrong document unchanged (2.6%, routing cannot fix a wrong leader). End to end on MiniCPM4 dev (48 answerable): questions retrieving a foreign chunk 10 of 54 -> 0, delivered 38 -> 38, evidence in top 5 45 -> 45; 13 answers differed, 12 graded the same, 1 worse (q035): no quality change beyond noise. Made the default at 0.10 on the user's request (`RAG_ROUTE_MARGIN=off` disables it).
- **Mamba-3 file with routing at 0.10** (no longer blind; automatic counts only, answers not re-graded): questions retrieving another document's chunk 8 -> 5, answers citing another document 4 -> 3 (q021, q051, q057 still do), unanswerable answers that passed 3 -> 1 (only q060, the licence question), evidence in top 5 unchanged (51/55). So 0.10 removes part of the leakage; the rest sits on questions where two documents score within the margin. A smaller margin would route those too (retrieval experiment: 0.05 equals 0.0 in leakage with the same recall) at a cost on genuinely multi-document questions that no gold set measures.

## Relevance gate (`RAG_MIN_RELEVANCE`) calibrated on dev, checked on Mamba-3 and the Penal Code
Top-1 jina rerank score for 471 questions (TRM, PERA, MiniCPM4, Mamba-3, Penal Code) in the five-document index, routing on. Score separation, answerable vs unanswerable (AUC): dev (TRM, PERA, MiniCPM4 dev; 150 answerable, 14 unanswerable) 0.77; held-out Mamba-3 0.91 (5 unanswerable), Penal Code 0.98 (11), together 0.94. Median top-1 score: answerable 0.51-0.58, unanswerable 0.14-0.34. The dev unanswerable questions are mostly near-misses (median 0.34), which is why dev is lower.
Threshold chosen on dev only (keeps 95% of dev answerable): 0.218, close to the 0.211 chosen earlier on QuestionPrep. On the held-out files: it refuses 11 of 16 unanswerable questions, but only 2 of the 5 answers I graded as fabricated (the other 3 score above it); it refuses 11 of 235 answerable questions (4.7%): among the 110 hand-graded answerable answers that is 2 of 76 correct, 1 of 15 partly right, 2 of 19 wrong; and 2 of 16 partially answerable questions. At 0.30: 14 of 16 unanswerable refused, 3 of 5 fabrications, 23 of 235 answerable refused (9.8%). Small numbers (5 fabrications, 16 unanswerable): a trade of roughly 3-5% coverage for removing about 40% of fabricated unanswerable answers; the gate stays off by default until the user decides.

## Does a bigger generator help? Ornith-1.5-9B (Q5_K/Q4_K, 28 layers on the GPU) on the MiniCPM4 dev questions
Same 48 answerable dev questions, same store (three documents), k=5, routing off, 16.1 s per question (Sharp 4.9 s, Gemma E4B 8.8 s). Hand-graded with the same rubric (single grader, single run):
| generator | correct | partly right | wrong | delivered through the gate |
|---|---:|---:|---:|---:|
| Gemma 4 E2B | 31 | 11 | 6 | 42 |
| Sharp-MiniCPM5 (2.7B) | 34 | 10 | 4 | 39 |
| Gemma 4 E4B | 36 | 7 | 5 | 46 |
| Ornith-1.5-9B | 37 | 6 | 5 | 27 |
- Correctness plateaus: 37 vs 36 vs 34 vs 31 of 48. The step from E4B to a 9B model is one answer, inside run-to-run noise (about 14 of 48 answers flip between identical runs).
- The same questions fail under all four generators: q036 (wrong filter), q073 (repeats "sparsity is only 5%"), q074 (3.65pp instead of +1.13pp), q078 (Qwen3-0.5B vs 0.6B). Partly right under all or most: q017, q029, q037, q056, q072. Ornith's one new wrong answer is q075 (right numbers, then "a higher average (39.84 vs 44.93)").
- Where the bigger model did better: q070 (it says the paper states three applications but names only two, the first generator to catch it), q054, q058, q067.
- Delivery is low for a format reason, not a quality one: 16 of Ornith's 21 gate flags are "the answer cites no source" (it left out the [S#] markers in 16 of 48 answers; the other generators did so in 0-2).
- Reading: from 2.7B to 9B (stored size), correctness rises by at most a few answers and the failures that remain are shared. That points at what the pipeline shows and asks (conflicting passages, repeated claims, derived values) more than at generator size within this range. Not tested: a frontier-scale model.

## Does a reasoning budget help? Sharp-MiniCPM5 with thinking on (budget 2048) on the MiniCPM4 dev questions
Server: `llama serve ... --reasoning on --reasoning-budget 2048` (the settings of `~/run_goose.sh`, budget 2048 instead of 8192); client `LLM_REASONING_BUDGET=2048`. Same 48 answerable dev questions, same three-document store rebuilt from the live one (221 chunks), k=5, routing off, schema mode. Hand-graded, one grader, one run, graded knowing which run it was (grades: `evals/gold/minicpm4_think_grades.json`).
| Sharp-MiniCPM5 | correct | partly right | wrong | delivered | s per question |
|---|---:|---:|---:|---:|---:|
| thinking off | 34 | 10 | 4 | 39 | 5.7 |
| thinking on, budget 2048 | 34 | 10 | 4 | 40 | 20.3 |
- Identical totals. Six answers differ: better with thinking q035, q054, q077; worse q005, q017, q044. That is inside the run-to-run noise already measured (about 14 of 48 flip between identical runs).
- Thinking was used: mean 834 generated tokens per request (median 684, max 2420), against a few hundred without it. Cost: 3.6x the time per answer.
- The same questions fail as under every other generator (q036, q073, q074, q078; partials q029, q037, q056, q072). Thinking did not make the model notice the conflicts (q070, q072, q073, q074 still repeat one side).
- Some thinking-run answers are shorter than before ("S-P-GPTQ", "16 [S1]}", "5% [S1]"); two end with a stray "}".

## Oracle context: does perfect retrieval help? Sharp-MiniCPM5 answering from only the gold-evidence chunks
Same model, prompt and gates as production, retrieval bypassed: for each MiniCPM4 dev answerable question the model was given only the stored chunks that hold its gold evidence quotes (fuzzy match, at most 5; script `evals/external/oracle/oracle.py`, results `oracle_minicpm4_dev_sharp.json`). 44 of 48 questions are reachable (q022, q054, q056, q058 have no chunk that holds the evidence). Hand-graded, one grader, one run (grades: `evals/gold/minicpm4_oracle_grades.json`).
| Sharp-MiniCPM5, the same 44 questions | correct | partly right | wrong |
|---|---:|---:|---:|
| gold chunks only (oracle) | 30 | 10 | 4 |
| normal retrieval | 32 | 8 | 4 |
| normal retrieval + 2k thinking | 31 | 9 | 4 |
- Perfect context does not raise correctness: eight answers differ (q029, q036, q042 better; q005, q017, q044, q053, q064 worse), which is run-to-run noise. The conflict questions are unchanged (q070 P, q072 P, q073 W, q074 W, q078 W).
- So the remaining errors are not retrieval and not context noise. Together with the larger-model and thinking results, they are not fixed by model size or reasoning budget either, in the range tested.
- What is left: the way the questions are asked and graded (conflict questions reward saying "the paper contradicts itself", which the prompt never asks for), derived values (q074, q044), and answers that stop early (q035, q037, q053). The untested lever is the prompt (experiment C).
- Caveat: the oracle chunks come from the evidence quotes, so for a conflict question they may hold only one of the two conflicting passages.

## Prompt line (experiment C): "state each value when sources differ; list every item"
One sentence appended to the system prompt (text fixed before the run, `evals/external/prompt_line/run.py`), Sharp-MiniCPM5, the 48 MiniCPM4 dev answerable questions, three-document store, k=5, routing off. Hand-graded, one grader, one run (`evals/gold/minicpm4_promptline_grades.json`).
| Sharp-MiniCPM5 | correct | partly right | wrong |
|---|---:|---:|---:|
| normal prompt | 34 | 10 | 4 |
| with the line | 30 | 14 | 4 |
- Four answers got worse (q005, q017, q044, q064: all correct -> partly right), none got better. The five conflict questions are unchanged (q070 P, q072 P, q073 W, q074 W, q078 W). Four answers is inside the run-to-run noise, but all moved the same way.
- The line did not make the model flag a disagreement: q072 now lists both token splits without saying they conflict, q078 mentions "Qwen3-0.6B" and still answers Qwen3-0.5B.
- Not adopted. Prompt wording is not the fix for the conflict questions on this model.
