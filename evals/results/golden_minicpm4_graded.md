# MiniCPM4 golden set, hand-graded (80 answerable + 6 partial)

Graded by reading each answer against the ground truth in `golden_minicpm4.md` (run: policy balanced, k=5, schema mode). One grader, no second opinion; judgement calls are noted.
C = answers what the question asks and nothing in it is wrong (omitting a secondary detail is still C). P = right in part: a required part is missing, or a true statement that does not answer the question. W = wrong, a non-answer, or a false refusal.
A "gate" outcome is what the system's own answer gate did (pass / flag / refuse).

## Totals (answerable, n=80)
| grade | n | of which passed the gate | flagged by the gate |
|---|---:|---:|---:|
| C | 51 (64%) | 48 | 3 (false alarms: 002, 008, 077) |
| P | 17 (21%) | 15 | 2 (029, 057) |
| W | 12 (15%) | 6 | 5 (045, 054, 067, 076, 079) + 1 refused (055) |

Delivered with a wrong answer: 6 of 69 delivered (9%): 013, 036, 069, 073, 074, 078. Delivered wrong or partial: 21 of 69 (30%).
The gate caught 5 of the 12 wrong answers and 2 of the 17 partial ones; it raised 3 false alarms. 002 was flagged "Unsupported number [3]": the "3." of a numbered list was read as a number.

## By type (C / P / W)
list 15/2/0 (17) · mechanism 9/6/0 (15) · table 5/3/4 (12) · factual 6/2/1 (9) · numeric 6/0/0 (6) · reasoning 5/0/1 (6) · multi-hop 3/1/1 (5) · conflict 0/3/5 (8) · comparison 2/0/0 (2)

## Not C, with the reason
| id | grade | gate | what went wrong |
|---|---|---|---|
| 009 | P | pass | block score = max over kernels not given |
| 012 | P | pass | cost of the LSE approximation written as "s_c of the original", should be s/s_c |
| 013 | W | pass | restates token-level vs block-level; gives no reason (training/inference mismatch) |
| 017 | P | pass | no specifics (1.1T tokens, 10B-token annealing, 30/70 mix) |
| 026 | P | pass | construction right; validation (sigmoid fit, 7B/80B held out) missing |
| 029 | P | flag | MTP head right; does not say how the loss is combined (gives L_MTP only) |
| 035 | P | pass | math reward: no rule-based/SymPy check, only the zero-for-format rule |
| 036 | W | pass | describes dynamic sampling (all right/all wrong) instead of the 4-prediction pre-filter |
| 037 | P | pass | lists 1 of 4 GRPO modifications |
| 042 | P | pass | gives temperature/top-p only; 6 of 7 hyperparameters missing |
| 045 | W | flag | "performs similarly"; truth is 56.03 vs 43.31 |
| 054 | W | flag | gives CMMLU values labelled as the Table 8 average, wrong for all four models |
| 055 | W | refuse | false refusal; the table holds the answer |
| 056 | P | pass | direction right, no numbers, adds an unrelated BitCPM4 sentence |
| 057 | P | flag | both averages and the 3.09 drop right; the largest drop (NIAH-MK) missing |
| 058 | P | pass | says trained at 4K, extended with YaRN to 128K; the 32K training length is missing |
| 063 | P | pass | four metrics described; no SurveyEval, GPT-4o judge or Fact Score |
| 064 | P | pass | "comparable", no numbers |
| 067 | W | flag | no numbers; only says the table exists |
| 069 | W | pass | uses the prose numbers (79.93/79.14), not the table's, and does not notice the conflict |
| 070 | P | pass | says three applications, as the paper does; misses that only two are described |
| 071 | P | pass | gives 5x and 7x side by side without saying they conflict |
| 072 | P | pass | gives the intro split (7T+1.3T); does not mention Section 5.1's 7T+1T |
| 073 | W | pass | repeats "sparsity is only 5%" (it is density; sparsity is about 95%) |
| 074 | W | pass | says 3.65pp; the table gives +1.13pp |
| 075 | P | pass | "Yes ... on knowledge tasks" omits that it is worse overall |
| 076 | W | flag | says "Yes" and then quotes 57.1 vs 81.8, which shows the opposite |
| 078 | W | pass | says Qwen3-0.5B; Table 8 and later text say 0.6B |
| 079 | W | flag | says extended 4K to 128K in training; trained to 32K |

## Partial and unanswerable
- Partial (6): 082 and 084 correct. 081, 083, 085, 086 refused: each correctly says the asked value is not given, but none states the part that does exist (the loss form, the 7x speedup, the parameter counts); counted P. 4 of 6 refused outright, as the run report says.
- Unanswerable (5): 3 refused, 2 flagged (088, 090), none delivered.

## What the grades say
- The weak spots are not random: all 8 conflict questions fail (the system answers from one passage and never notes a contradiction), tables fail 7 of 12, and "why" or multi-part questions lose a required part.
- List, numeric and comparison questions are strong: 23 of 25 correct (list 15/17, numeric 6/6, comparison 2/2). The 8 conflict questions are adversarial by design (they probe contradictions inside the paper), so the all-fail result there is a measure of one capability, not of typical use.

# Same set, generator swapped: Sharp-MiniCPM5-2B-Q8_K_M (`golden_minicpm4_sharp.md`)

Same store copy, same retrieval (identical ranks on all 91 questions), same gates and settings; only the model behind `LLM_BASE_URL` changed. Graded with the same rubric, same grader. Mean 4.9 s per question (Gemma 4 E2B: 4.6 s).

| | Gemma 4 E2B | Sharp-MiniCPM5-2B |
|---|---:|---:|
| C (correct) | 51 | 56 |
| P (partly right) | 17 | 17 |
| W (wrong) | 12 | 7 |
| wrong answers delivered through the gate | 6 of 69 | 5 of 64 |
| wrong or partial delivered | 21 of 69 (30%) | 13 of 64 (20%) |
| gate false alarms on correct answers | 3 of 51 | 5 of 56 |
| wrong answers the gate flagged or refused | 6 of 12 | 2 of 7 |
| unanswerable (5): delivered / flagged / refused | 0 / 2 / 3 | 0 / 0 / 5 |
| list-question item recall (9) | 0.89 | 0.72 |

Moved from W or P to C: 013, 017, 026, 058, 063, 064, 067. Moved from C to P: 016 (correct 110 vs 1,200 GPU hours, then wrong ratios "9.6x" and "4x"), 077 (right verdict, wrong reasons). Moved W to P: 045, 054, 079. Got worse in kind: 055 (Gemma refused; Sharp says Qwen3-8B beats MiniCPM4-8B on none, which is wrong).

Wrong under both models (7): 036, 055, 069, 073, 074, 076, 078. Partly right under both (12): 009, 012, 029, 035, 037, 042, 056, 057, 070, 071, 072, 075. Of these 19, the evidence chunk was retrieved at rank 1 or 2 and covered all of the question's evidence for 15; the retriever missed it (no evidence chunk in the top 5) for 4: 055, 078, 029, 056. Both generators are about 2B parameters, so the shared failures say "2B-class model or system", not which; this run cannot separate them.

# Same set, third generator: Gemma 4 E4B (`golden_minicpm4_e4b.md`)

Same store, retrieval, gates and settings (4.22 GB Q4 file; Gemma 4 E2B is 2.62 GB Q4, Sharp-MiniCPM5 2.93 GB Q8). Mean 8.8 s per question (E2B 4.6 s, Sharp 4.9 s). Same rubric and grader; borderline calls: 012 (C: it copies the source's garbled "s sc" ratio instead of asserting a wrong one), 058 (C despite a contradictory last sentence), 077 (C: right verdict and right improved metrics, Relevance drop not named), 055 (P: the table numbers it lists are right, its closing sentence is wrong).

| | Gemma 4 E2B | Sharp-MiniCPM5-2B | Gemma 4 E4B |
|---|---:|---:|---:|
| C (correct) | 51 | 56 | 61 |
| P (partly right) | 17 | 17 | 11 |
| W (wrong) | 12 | 7 | 8 |
| wrong answers delivered through the gate | 6 of 69 | 5 of 64 | 8 of 75 |
| wrong or partial delivered | 21 of 69 (30%) | 13 of 64 (20%) | 17 of 75 (23%) |
| gate false alarms on correct answers | 3 of 51 | 5 of 56 | 3 of 61 |
| wrong answers the gate flagged | 6 of 12 | 2 of 7 | 0 of 8 |
| table questions correct (12) | 5 | 6 | 8 |
| list-question item recall (9) | 0.89 | 0.72 | 0.89 |
| seconds per question | 4.6 | 4.9 | 8.8 |

E4B by type (C/P/W): list 16/1/0 · mechanism 13/2/0 · table 8/2/2 · factual 8/0/1 · numeric 6/0/0 · reasoning 5/0/1 · multi-hop 3/2/0 · comparison 2/0/0 · conflict 0/4/4.

- Better with E4B: tables (q054, q057 and q067 now give the right numbers), q009, q035, q042, q081 (gives the MTP loss and says the weight is not stated, the ideal reply), q032 (includes the 8K-64K length).
- Worse with E4B than the other two: q040 (names Chunk-4k as best; the others said Chunk-8k), q013, q045.
- Wrong under all three models (5): q036, q069, q073, q074, q078. Conflict questions: 0 correct out of 8 under every model.
- E4B's gate flagged none of its 8 wrong answers: its quotes verify even when the claim is wrong (q040, q073, q074 cite real passages). A better model makes the quote gate less informative, not more.
- For E4B's 19 non-correct answers the evidence was fully inside the top 5 for 10, partly for 4, and no evidence chunk was retrieved for 5 (q045, q078, q029, q055, q056).
- Unanswerable (5): 3 refused; q087 answered "no information on iPhone or Apple Silicon" (acceptable; the run's "answered and passed" count of 1 is a false positive of the harness); q090 did not answer the MMMU question and was flagged.
