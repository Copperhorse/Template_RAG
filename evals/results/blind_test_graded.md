# Blind test: Mamba-3 and Pakistan Penal Code (hand-graded)

Frozen code: `freeze_blind_test.txt` (one addendum: conversion cache rule, no effect on retrieval or answers). Generator: Sharp-MiniCPM5-2B, production defaults (k=5, 3000-token sources, no expansion, policy balanced). Store: your five documents in one index (992 chunks), Mamba-3 re-ingested cleanly from the Desktop PDF in a scratch copy (223 chunks, 0 undecoded formulas; 56 replacement characters from math symbols Docling cannot map). Each file run once. No question was read before the run. Grader: one reader (Claude) against the ground truth; rubric as in `golden_minicpm4_graded.md` (C correct / P partly right / W wrong). Neither file has `facts`, so nothing here is automatic. Penal Code: a seeded random sample of 60 of the 185 answerable questions (seed 11, ids not stored); everything else is graded in full.

## Retrieval and gates (all questions, automatic; evidence matched with the 80%-of-tokens rule)
| | Mamba-3 | Penal Code |
|---|---:|---:|
| evidence chunk in the top 5 | 93% (51/55) | 98% (193/196) |
| ranked first | 71% | 92% |
| answered / delivered (passed the gates), answerable | 48/50, 34/50 | 182/185, 152/185 |

## Answerable, hand-graded
| | Mamba-3 (all 50) | Penal Code (sample 60 of 185) |
|---|---:|---:|
| correct | 26 (52%) | 50 (83%) |
| partly right | 11 (22%) | 4 (7%) |
| wrong | 13 (26%) | 6 (10%) |
| wrong answers delivered through the gate | 6 of 34 delivered (18%) | 1 of 47 (2%) |
| wrong or partly right, delivered | 12 of 34 (35%) | 3 of 47 (6%) |
| gate flags: false alarms / partly right / wrong | 4 / 5 / 5 (+2 false refusals) | 6 / 2 / 3 (+2 false refusals) |
A 95% interval on 50 of 60 is about 72-90%; on 26 of 50, about 38-65%.

Mamba-3 by type (C/P/W): table 4/4/3 (11), conflict 0/2/6 (8, again none correct), definition 3/0/1, mechanism 6/1/0, numeric 4/2/0, factual 3/1/2, list 1/1/0, reasoning 2/0/0, comparison 1/1/0, multi-hop 0/1/1.

## Partially answerable and unanswerable (graded in full)
| | Mamba-3 | Penal Code |
|---|---:|---:|
| partial (5 / 11): C / P / W | 3 / 1 / 1 | 5 / 2 / 4 |
| unanswerable (5 / 11): right behaviour / misleading / fabricated | 2 / 0 / 3 | 8 / 1 / 2 |
The run report counts every non-refused unanswerable answer that passed as "dangerous" (3 of 5, 7 of 11); reading them, most of the 7 on the Penal Code are honest "the text does not say" answers, so the real fabrication rate is 2 of 11 there and 3 of 5 on Mamba-3.

## What the failures show
- Other documents leak in. In the shared index 8 of the 60 Mamba-3 questions retrieved a chunk of another document, and 4 answers cite one: q020 (describes MiniCPM4's evaluation instead of Mamba-3's setup), q021, q051 (hyperparameters from the TRM paper, though the paper gives none), q057 ("1,200 GPU hours", a MiniCPM4 figure). The quote check passes because the quote really is in a source; it cannot know the source is the wrong document. q029 also answered from the TRM Sudoku table.
- Conflict questions: 0 of 8 correct on Mamba-3 (6 wrong), as on MiniCPM4 (0 of 8). The model repeats the paper's own claim (q042, q044, q045, q046) instead of checking it against the tables.
- False refusals despite evidence in the top 5: Mamba-3 q005, q026; Penal Code q072, q185.
- Wrong numbers delivered: Penal Code q162 ("160 years" for s.406, passed the gate), Mamba-3 q036, q038.
- Statute lookups work: 50 of 60 correct, 98% retrieval. Math- and table-heavy questions are where it breaks.
