# Golden QA evaluation: Protection of Economic Reforms Act, 1992 (`pera_golden_qa.jsonl`, 44 questions)

Golden file supplied by the user: 39 answerable questions (10 types) with evidence quotes, 5 unanswerable with near-miss chunks.
Scored by `python -m rag_template.evals golden` (`evals/gold/pera.jsonl` = the file plus a facts sidecar; `pera_grades.json` = my grades).
Reports: `golden_pera_live.md` (run 1), `golden_pera_live_schema.md` (run 2), `golden_pera_fixed.md` (run 3). Gemma 4 E2B, k=5, `balanced` policy.

| run | store | LLM reply format | code |
|---|---|---|---|
| 1 | copy of the user's live store (6 chunks, **5 usable**) | `json_mode` off (the default; what the UI ran with) | before this session's fixes |
| 2 | same copy | schema-enforced | before the fixes |
| 3 | PDF re-ingested into a fresh store (6 chunks, **6 usable**) | schema-enforced | with the fixes below |

## Results, answerable questions (39)
"Correct/partial/wrong" is **my reading of each answer against the golden `ground_truth`** (subjective; runs 1 and 3 only). The keyword
check in the report ("contains every required fact") is a reproducible lower bound and disagrees with my grades on wording
(e.g. "the seventh day of November, 1990").

| | run 1 | run 3 |
|---|---:|---:|
| correct / partial / wrong (graded) | 30 / 4 / 5 | 28 / 6 / 5 |
| delivered (passed the gates) / flagged | 30 / 9 | 36 / 3 |
| correct and delivered | 25 | 26 |
| correct but flagged (false alarms) | 5 | 2 |
| partial or wrong but delivered | 5 | 10 |
| evidence quote reachable in a usable chunk | 43/51 | 47/48 |
| evidence chunk in the top 5 / ranked first | 34 / 32 | 37 / 34 |

Run 2 (not graded): delivered 34, flagged 5 vs 30 / 9 in run 1, so the reply format alone removed four flags.

**Unanswerable (5):** 0 refused in every run; 3 acceptable abstentions-by-explanation (q041 ceiling is left to the SBP, q043 definition is
in the Income Tax Ordinance, q044 words not provided) and 2 evasive non-answers (q040 restates the secrecy duty and never says there is no
penalty; q042 describes the Schedule's purpose without saying it is not included). None invented a figure or a penalty. 4 of 5 passed the gates.

## What was wrong, by stage
1. **Ingestion (generic bug, fixed):** the header filter matched substrings, so "EXTRAORDINARY PUBLISHED BY AUTHORITY" was rejected as an
   "author" section, taking the Gazette date with it. Now whole words (`evaluator.py`; tests).
2. **Gate false alarms (generic bugs, fixed):** the number check did not read "23rd", "28th", "16th" as 23, 28, 16, so an answer saying
   "July 23" was "unsupported"; a number repeated from the question ("privatized in 1995") counted as invented; a number in the heading the
   model was shown ("ACT NO. XII OF 1992") did not count as evidence (`verify.py`, `retrieve.py`; tests, mutation-checked).
3. **Footnote link (generic, partly fixed):** the converter's superscript markers were stripped and their digits glued to the word
   (`company]3 in Pakistan`), hiding which clause a footnote amends. Now kept as `^3`. The four amendment questions still score 1 of 4:
   in run 3 q030 names the right law but says clause (f) was "omitted", q031 and q032 do not use the footnote, q033 says "substituted".
4. **Model comprehension (not fixed here):** the remaining wrong answers are Gemma 4 E2B misreading text that was retrieved correctly:
   q015 says the sources do not state the answer although section 4(2)(e) is in context; q025 inverts a negation; q016 lists 2 of 7
   exclusions; the multi-hop questions (q034, q035) are answered partially.
5. **The gate cannot see incomplete or evasive answers.** After the fixes it passes 10 partial/wrong answers (was 5), because an answer can be
   supported by its source and still not answer the question; this was already a measured limit (`gates.md`).

## Caveats
- **Retrieval is trivially easy here**: the store has 5-6 chunks and k=5, so "evidence in the top 5" says almost nothing. The golden file's
  `relevant_chunk_ids` (`pera-c00`..`c14`, 15 chunks) come from a different chunking and cannot be used; relevance is judged by evidence quote.
- For q002 (a heading) and q030-q033 (annotated footnote renderings no converter emits) the evidence is replaced by verbatim text
  (`evidence_verbatim`), and the originals are kept in the file.
- 39 questions, one document, a 2B-parameter model, sampling at temperature 0.1: runs 1 and 3 differ on answers that did not depend on the fixes
  (q029, q030, q035). **A change of one or two questions is noise**; the false-alarm drop (5 to 2) and the reachability gain (43 to 47 of 51)
  are the findings that follow from identified causes.
- The user's live store was **not modified**; it still holds the old ingest (5 usable chunks). Re-ingest the PDF to get the fixes.

# Update: source ids (`[S1]`) instead of bare numbers, and quotes located by their text
Re-run in the configuration the UI uses by default (`json_mode` off), same stores and settings as runs 1 of PERA and TRM; not graded by hand,
so the numbers are the gate's and the keyword check's. Reports: `golden_pera_sid_off.md`, `golden_pera_sid2_off.md`, `golden_trm_sid_off.md`, `golden_trm_sid2_off.md`.

| plain-JSON mode: answerable delivered / flagged / refused | PERA (39) | TRM (63) |
|---|---:|---:|
| bare integer ids (before) | 30 / 9 / 0 | 54 / 6 / 3 |
| `[S1]` ids, quotes attributed by id only | 23 / 15 / 1 | **26 / 35** / 2 |
| `[S1]` ids, id-less quotes located by their text (shipped) | **36 / 3** / 0 | 55 / 4 / 4 |
| every required fact **and** delivered (before -> shipped) | 22 -> 24 | 39 -> 44 |
| unanswerable questions that passed the gates (before -> shipped) | 4 -> 4 of 5 | 3 -> 3 of 6 |

**The `S`-ids alone made plain mode much worse** (TRM: 54 -> 26 delivered). Without an enforced schema the 2B model often writes `quotes` as bare
strings, or drops the source field, and the gate threw those quotes away; two prompt rewordings (a placeholder, then a literal `"S1"` example) did not
fix it (the literal example made it worse: 21 of 30 quote entries were bare strings). The fix was at the gate: attribute a quote with no usable id to the
chunk that holds it verbatim. That recovers the loss and removes more false alarms than it adds, because the evidence was always in the reply.
