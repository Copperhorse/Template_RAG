# Golden QA evaluation: SSD paper, pymupdf4llm, json_mode schema, fuzzy evidence

Golden file `evals/gold/ssd.jsonl` (70 questions: 60 answerable, 5 unanswerable, 5 partially answerable). Store: `/tmp/claude-1000/-home-copper-Git-Template-RAG/24d159d4-229a-4570-887a-d29472273e1a/scratchpad/ssd_store_p4` (98 chunks, 85 usable). LLM json_mode=`schema`, policy=`balanced`, k=5. 'Correct' = the answer contains the facts listed in the gold sidecar: a lower bound, read the answers below.

## 1. Ingestion: is the evidence in a usable chunk?

- usable: 78% (79/101)
- fuzzy-usable: 17% (17/101)
- rejected: 0% (0/101)
- split: 0% (0/101)
- absent: 5% (5/101)
- (fuzzy-usable: no exact match, but a chunk holds at least 80% of the quote's tokens; relevance below uses the same rule)
- questions with unreachable evidence: 015, 022, 033, 051, 052

## 2. Retrieval (answerable questions and partially answerable ones)

- an evidence chunk in the top 5: 92% (60/65)
- evidence chunk ranked first: 72% (47/65)
- all of a question's evidence quotes covered by the top 5: 78% (51/65)

## 3. Answers

- answered (did not refuse): 97% (58/60)
- delivered (answered and passed the gates): 85% (51/60)
- contains every required fact: 12% (7/60)
- contains every required fact **and** delivered: 12% (7/60)
- mean share of required facts present: 0.38 (over the 32 questions that list facts)
- mean item recall over the 7 list questions that name their items: 0.69
- a verified quote comes from an evidence chunk: 85% (51/60)
- correct among flagged answers (false alarms): 0% (0/7)

## 4. Unanswerable questions (right behaviour: refuse)

- refused: 80% (4/5)
- answered but flagged: 20% (1/5)
- answered and passed the gates (the dangerous case): 0% (0/5)

## 4b. Partially answerable (the right reply cites what exists and says what the source does not give)

- refused outright (a fail: the part that exists should be given): 40% (2/5)
- answered and passed the gates: 40% (2/5)
- answered and flagged: 20% (1/5)
- whether a reply states what is missing needs reading; see section 6.

## 5. By question type (answerable)

| type | n | evidence in top-k | delivered | every fact | delivered and every fact |
|---|---:|---:|---:|---:|---:|
| comparison | 2 | 2 | 2 | 0 | 0 |
| definition | 4 | 3 | 3 | 0 | 0 |
| factual | 10 | 10 | 9 | 0 | 0 |
| list | 9 | 9 | 7 | 0 | 0 |
| mechanism | 4 | 4 | 3 | 0 | 0 |
| multi-hop | 6 | 6 | 6 | 1 | 1 |
| numeric | 14 | 13 | 12 | 6 | 6 |
| reasoning | 4 | 4 | 4 | 0 | 0 |
| table | 7 | 4 | 5 | 0 | 0 |

## 6. Every question

| id | type | ev. | rank | outcome | facts | answer |
|---|---|---|---|---|---|---|
| 001 | factual | f | 1 | pass | - | The correspondence for the paper is Ruixiang Zhang, Richard He Bai, Huangjie Zheng, and Yizhe Zhang [S1]. The contribution is noted as equal contribut |
| 002 | factual | u | 1 | pass | - | The SSD code is released at https://github.com/apple/ml-ssd [S1]. |
| 003 | definiti | u | - | flag: no verified quote from cited source(s) [ | - | Simple self-distillation (SSD) involves writing the raw outputs from sampling a base model as a simple self-distillation dataset D_ SSD, which is then |
| 004 | numeric | u | 1 | pass | 0.50 | SSD yields large gains on LiveCodeBench [S1], and Figure 1 shows that it yields substantial LiveCodeBench v6 gains across six models spanning three fa |
| 005 | list | u | 3 | pass | - | SSD does not require human-labeled solutions, reference answers, a teacher model, a reward model, a verifier, an execution environment, or reinforceme |
| 006 | numeric | u | 5 | flag: no verified quote from cited source(s) [ | 0.00 | For Qwen3-30B-Instruct on LCB v6, the hard-problem pass@5 improves by +23.0pp [S3, S2]. |
| 007 | definiti | u,f | 1 | pass | - | 'Lock' positions are where the distribution is sharply peaked, with very few tokens carrying most of the mass and a long distractor tail carrying the  |
| 008 | definiti | u,u | 2 | pass | - | The precision-exploration conflict is the dilemma where a single evaluation temperature cannot satisfy both exploration at forks and precision at lock |
| 009 | list | u | 1 | pass | - | The paper's three contributions are: First, showing that SSD can substantially improve code generation models’ performance using only their own unveri |
| 010 | factual | u,u | 1 | pass | - | SSD can use $N=1$ sample per prompt, as a single sample per prompt is stated to suffice in practice [S1]. The solutions are not verified in any way, m |
| 011 | list | u | 1 | pass | - | The six models evaluated are Llama-3.1-8B-Instruct (dense, 8B), Qwen3-4B-Instruct-2507 (dense, 4B), Qwen3-4B-Thinking-2507 (dense, 4B), Qwen3-30BA3B-I |
| 012 | numeric | u,u | 1 | pass | 1.00 | The active parameter counts for the MoE models are 3B for Qwen3-30BA3B-Instruct-2507 and Qwen3-30B-A3B-Thinking-2507, and 3.6B for GPT-OSS-20B [S1]. |
| 013 | numeric | u | 1 | pass | 1.00 | SSD training data is synthesized from the seed subset of the rSTARcoder dataset (Liu et al., 2025), which is used as a pool of unlabeled competitive-p |
| 014 | factual | u | 2 | pass | - | Minimal degeneracy filtering is applied to remove clearly unusable outputs, such as empty responses and single-line stubs [S1]. Additionally, minimal  |
| 015 | list | f,a | 4 | flag: no verified quote from cited source(s) [ | 0.00 | The fine-tuning hyperparameters for SSD involve fine-tuning the model on the simple self-distillation dataset D_SSD, which is formed by sampling N can |
| 016 | numeric | u,u | - | pass | 0.50 | LCB v6 covers the period from Feb–May 2025, and LCB v5 covers Aug 2024–Feb 2025 [S1]. |
| 017 | numeric | u | 1 | pass | - | All pass@k estimates use 10 independent samples per problem [S1]. |
| 018 | list | u | 1 | pass | - | For Qwen3-30B-Instruct on LCB v6, SSD improves the pass@1 score from 42.4% to 55.3%, which is a gain of +12.9pp [S1], and the table shows the correspo |
| 019 | numeric | u,u | 1 | pass | 0.50 | For Qwen3-30B-Instruct on LCB v6, the pass@1 improvement from SSD breaks down as follows: +6.5pp on easy problems, +14.2pp on medium problems, and +15 |
| 020 | numeric | u | 1 | pass | 0.25 | On LCB v5, Qwen3-30B-Instruct's SSD result is 54.3% pass@1 [S2]. |
| 021 | reasonin | u,u | 1 | pass | 0.00 | The paper indicates that SSD does not collapse diversity, as the gains are often larger at pass@5 than at pass@1, which suggests that SSD preserves an |
| 022 | table | f,a | 3 | pass | 0.00 | Qwen3-30B-Thinking's LCB v6 hard pass@1 before SSD is 98.9, and after SSD it is 98.9 [S3]. |
| 023 | table | f,f | 2 | pass | 0.00 | Llama-3.1-8B-Instruct's LCB v6 hard pass@1 before SSD is 15.1 and after SSD is 17.1 [S2]. |
| 024 | numeric | u | 1 | pass | 0.80 | Temperature tuning yields only modest gains on the base model, with the pass@1 for Qwen3-30B-Instruct ranging from 41.3% to 43.5% across the evaluated |
| 025 | list | u,u | 1 | pass | - | SSD outperforms the best-tuned base model in pass@1 with advantages of +11.8 pp for Qwen3-30B-Instruct, +5.8 pp for Qwen3-4B-Instruct, +2.2 pp for Qwe |
| 026 | definiti | u,u | 1 | pass | 0.00 | Effective temperature is defined as _T_ eff = _T_ train _· T_ eval, and it governs performance [S1, S2]. |
| 027 | numeric | u | 1 | pass | 1.00 | The best observed setting among the truncated runs used _T_ train=2 _._ 0, _T_ eval=1 _._ 1, and training-time top-k = 10, which achieved a pass@1 of  |
| 028 | factual | u | 1 | pass | - | When a nontrivial training-time truncation configuration $\rho_{train}$ is used during SSD data generation, the optimal effective temperature ($\text{ |
| 029 | reasonin | u | 3 | pass | - | A single evaluation temperature cannot fix the precision-exploration conflict because different positions in the generation process have contradictory |
| 030 | mechanis | u,u | 1 | pass | - | The toy simulation is structured around a finite-state machine with a vocabulary of $V = 16$ tokens [S3]. The root branches into two symmetric success |
| 031 | reasonin | u,u | 1 | pass | - | Training and decoding are complementary in SSD because training makes the locks less fragile, and decoding uses the resulting extra room to explore th |
| 032 | list | u,u | 1 | pass | - | The real-model analysis of Qwen3-30B-Instruct showed that SSD results in reaching decoding with a cleaner head and a weaker distractor tail compared t |
| 033 | mechanis | a,f,f | 1 | pass | - | The three-term decomposition of the SSD loss involves the KL anchor term, the constant $T ullet H(q_s)$, and the Rényi-shaping term, which is derived |
| 034 | mechanis | u | 1 | pass | - | SSD can lower total entropy while preserving exploration because total entropy and useful exploration concern different objects [S1, S3]. Specifically |
| 035 | factual | u,u | 1 | pass | 0.57 | Even when the synthesized outputs devolve into gibberish, the resulting fine-tuned model still improves substantially [S1, S2, S3]. For instance, the  |
| 036 | reasonin | f | 1 | pass | - | The gains in the stress test are smaller than those in the headline setting because, in the present case, the distractor tails are not suppressed duri |
| 037 | numeric | u,u | 1 | flag: Unsupported sentence in answer (3 of 5 w | 0.33 | 62 checkpoint/temperature configurations exceeded the 42.4% frozen-base pass@1 baseline in the high-temperature stress test [S1]. The sources do not p |
| 038 | numeric | u,u | 1 | pass | 1.00 | The performance remains competitive for _T_ eval roughly in the range [0 _._ 6 _,_ 1 _._ 1], but it degrades quickly once the evaluation-time temperat |
| 039 | mechanis | u | 1 | flag: no verified quote from cited source(s) [ | 0.00 | The vLLM decoding pipeline applies four steps in sequence: (1) temperature scaling, (2) top-k filtering, (3) top-p filtering, and (4) Gumbel-max sampl |
| 040 | factual | u | 1 | flag: Unsupported number in answer: [10] | - | vLLM switches to greedy decoding when the temperature is below $10^{-5}$, at which point it bypasses all subsequent steps [S1]. |
| 041 | table | u | - | pass | 0.00 | The evaluation and decoding settings for Qwen3-30B-Instruct with SSD are detailed in Table 3 [S4]. Table 3 shows the performance metrics for the base  |
| 042 | table | u | 1 | pass | 0.50 | The baseline decoding settings used for Qwen3-30B-Instruct were a temperature of 1.6, top-k of 20, top-p of 0.8, and a temperature of 0.9 with top-k o |
| 043 | factual | u | 1 | pass | - | For instruct models, each problem is wrapped in a system message requesting a Python solution inside a markdown code block, followed by the problem st |
| 044 | list | f | 1 | pass | - | The out-of-domain benchmarks used were AIME to probe mathematical reasoning, HumanEval (Chen et al., 2021) to probe general code generation in Python  |
| 045 | factual | u,u | 2 | pass | 0.00 | Programming-only SSD training appears to preserve non-competitive-programming performance reasonably well for the 30B models [S2]. |
| 046 | factual | u | 3 | pass | 0.00 | Llama-3.1-8B-Instruct loses ground on AIME after SSD training, while it improves on HumanEval and CruxEval [S3]. |
| 047 | table | u,u | 1 | pass | 0.00 | The score for Qwen3-4B-Instruct on HumanEval Shell changes from 44.6 to 87.8 when SSD is applied [S1]. |
| 048 | list | u,u,u | 1 | flag: no verified quote from cited source(s) [ | 0.25 | At lock states, the distribution is sharply peaked at the correct token (rank 1) under both teacher and student across all three temperatures, with tr |
| 049 | numeric | u | 3 | pass | 1.00 | After SSD, the global optimum shifts upward. For example, the student's success probability increases from 5.5% at low temperature to 13.8% at high te |
| 050 | numeric | u | 1 | pass | 1.00 | Yes, the student's advantage is sensitive to the top-p threshold, as repeating the grid search across top-p values from 0.65 to 0.90 leaves the studen |
| 051 | table | a | - | refused | - | The provided sources do not contain a Table 1, so it is not possible to determine which property on-policy self-distillation lacks that SSD has. |
| 052 | table | a | - | refused | - | The provided sources do not contain a Table 1 that compares GRPO with SSD. |
| 053 | comparis | u | 1 | pass | - | SSD differs from related self-training approaches like STaR and ReST_EM because SSD trains directly on raw, unverified model outputs, whereas STaR and |
| 054 | comparis | u,u | 1 | pass | - | SSD differs from unsupervised RLVR or entropy-minimization methods in both method and mechanism [S1]. While methods like unsupervised RLVR or intrinsi |
| 055 | multi-ho | u,u,u | 1 | pass | 0.00 | The best observed setting among the truncated runs reached 49.7% pass@1, which is above all no-truncation results [S1]. The headline figure likely ref |
| 056 | multi-ho | u,f,f | 1 | pass | 0.00 | The caption for Table 2 states that SSD improves every evaluated model on LiveCodeBench [S1]. |
| 057 | multi-ho | u,f,f | 1 | pass | 0.40 | The pattern where the 'pass@5 gain exceeds pass@1 gain' holds for the Qwen models on LCB v6, with examples such as Qwen3-4B-Instruct (+15.8pp versus + |
| 058 | multi-ho | u,u,u | 5 | pass | 0.00 | The effective temperature is defined as _T_ eff = _T_ train _· T_ eval [S5]. In the context of Qwen3-30B-Instruct on LCB v6, the performance is organi |
| 059 | multi-ho | u,u | 1 | pass | 0.67 | Temperature tuning yields only modest gains on the base model, as the base-model sweep curves are strikingly flat for Qwen3-30B-Instruct, with pass@1  |
| 060 | multi-ho | u,f | 1 | pass | 1.00 | The base-model pass@5 baseline used in the stress test (Figure 15) is 53.5% [S1, S5]. Table 2 shows the base model results for various models, but it  |
| 061 | partial | u | 1 | refused | - | The provided sources do not state how SSD performs when sampling more than one solution per prompt (N > 1). |
| 062 | partial | f,u | 1 | refused | - | The provided sources do not state how many GPU-hours SSD fine-tuning takes. |
| 063 | partial | f | 1 | flag: no verified quote from cited source(s) [ | - | For GPT-OSS-20B, SSD results in a gain of +5.3pp on pass@1 [S2]. |
| 064 | partial | u | 1 | pass | - | The lock/fork asymmetry arises from what survives into the retained set at each context [S1]. At locks, support compression dominates because only one |
| 065 | partial | u | 4 | pass | - | The base-model decode-tuning results for GPT-OSS-20B show a temperature (T) of 1.2, top-k of none, and top-p of 1.0, with a top-k of 20 and top-p of 0 |
| 066 | unanswer | - | - | flag: the answer cites no source | - | The provided sources discuss the performance of SSD on LiveCodeBench, not SWE-bench. |
| 067 | unanswer | - | - | refused | - | The provided sources do not contain information about whether SSD helps models larger than 30B, such as 70B. |
| 068 | unanswer | - | - | refused | - | The provided sources do not contain a direct head-to-head comparison of SSD's pass@1 against GRPO on LiveCodeBench. |
| 069 | unanswer | - | - | refused | - | The provided sources do not explicitly state whether applying SSD repeatedly (multiple rounds) keeps improving the model. |
| 070 | unanswer | - | - | refused | - | The provided sources do not state whether SSD trained on math prompts improves math benchmarks. |
