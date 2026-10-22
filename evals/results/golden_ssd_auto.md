# Golden QA evaluation: SSD paper, auto backend (Docling), json_mode schema, fuzzy evidence

Golden file `evals/gold/ssd.jsonl` (70 questions: 60 answerable, 5 unanswerable, 5 partially answerable). Store: `/tmp/claude-1000/-home-copper-Git-Template-RAG/24d159d4-229a-4570-887a-d29472273e1a/scratchpad/ssd_store` (188 chunks, 182 usable). LLM json_mode=`schema`, policy=`balanced`, k=5. 'Correct' = the answer contains the facts listed in the gold sidecar: a lower bound, read the answers below.

## 1. Ingestion: is the evidence in a usable chunk?

- usable: 79% (80/101)
- fuzzy-usable: 15% (15/101)
- rejected: 0% (0/101)
- split: 0% (0/101)
- absent: 6% (6/101)
- (fuzzy-usable: no exact match, but a chunk holds at least 80% of the quote's tokens; relevance below uses the same rule)
- questions with unreachable evidence: 015, 022, 023, 033, 051, 052

## 2. Retrieval (answerable questions and partially answerable ones)

- an evidence chunk in the top 5: 89% (58/65)
- evidence chunk ranked first: 57% (37/65)
- all of a question's evidence quotes covered by the top 5: 77% (50/65)

## 3. Answers

- answered (did not refuse): 100% (60/60)
- delivered (answered and passed the gates): 85% (51/60)
- contains every required fact: 12% (7/60)
- contains every required fact **and** delivered: 10% (6/60)
- mean share of required facts present: 0.37 (over the 32 questions that list facts)
- mean item recall over the 7 list questions that name their items: 0.55
- a verified quote comes from an evidence chunk: 77% (46/60)
- correct among flagged answers (false alarms): 11% (1/9)

## 4. Unanswerable questions (right behaviour: refuse)

- refused: 80% (4/5)
- answered but flagged: 20% (1/5)
- answered and passed the gates (the dangerous case): 0% (0/5)

## 4b. Partially answerable (the right reply cites what exists and says what the source does not give)

- refused outright (a fail: the part that exists should be given): 40% (2/5)
- answered and passed the gates: 20% (1/5)
- answered and flagged: 40% (2/5)
- whether a reply states what is missing needs reading; see section 6.

## 5. By question type (answerable)

| type | n | evidence in top-k | delivered | every fact | delivered and every fact |
|---|---:|---:|---:|---:|---:|
| comparison | 2 | 2 | 2 | 0 | 0 |
| definition | 4 | 3 | 4 | 0 | 0 |
| factual | 10 | 10 | 10 | 0 | 0 |
| list | 9 | 7 | 8 | 0 | 0 |
| mechanism | 4 | 4 | 4 | 0 | 0 |
| multi-hop | 6 | 6 | 3 | 1 | 0 |
| numeric | 14 | 14 | 13 | 6 | 6 |
| reasoning | 4 | 4 | 4 | 0 | 0 |
| table | 7 | 3 | 3 | 0 | 0 |

## 6. Every question

| id | type | ev. | rank | outcome | facts | answer |
|---|---|---|---|---|---|---|
| 001 | factual | f | 1 | pass | - | The organization that produced the SSD paper is Apple [S1]. The equal-contribution authors are Ruixiang Zhang, Richard He Bai, Huangjie Zheng, and Yiz |
| 002 | factual | u | 2 | pass | - | The SSD code is released at https://github.com/apple/ml-ssd [S2]. |
| 003 | definiti | u | 2 | pass | - | Simple self-distillation (SSD) is an embarrassingly simple method where solutions are sampled from the base model with specific temperature and trunca |
| 004 | numeric | u | 1 | pass | 0.50 | SSD yields large gains on LiveCodeBench [S1], and it yields substantial LiveCodeBench v6 gains across six models spanning three families and multiple  |
| 005 | list | u | - | pass | - | SSD does not require learning from correctness labels, reward signals, or verification outcomes [S1]. |
| 006 | numeric | u | 4 | pass | 0.00 | For Qwen3-30B-Instruct on LCB v6, the hard-problem pass@5 improves by +23.0pp, while the pass@1 improves by +15.3pp [S3]. |
| 007 | definiti | u,f | 1 | pass | - | 'Lock' positions are where the distribution is sharply peaked, with very few tokens carrying most of the mass and a long distractor tail carrying the  |
| 008 | definiti | u,u | 2 | pass | - | The precision-exploration conflict is the tension arising because certain positions in code generation demand precision (locks), where the distributio |
| 009 | list | u | 2 | pass | - | The paper's three contributions are: First, showing that SSD can substantially improve code generation models' performance using only their own unveri |
| 010 | factual | u,u | 2 | pass | - | In practice, N=1 (a single sample per prompt) is sufficient for SSD [S2]. The solutions are not verified in any way, meaning no execution, no test cas |
| 011 | list | u | 2 | pass | - | The six models evaluated are Llama-3.1-8B-Instruct, Qwen3-4B-Instruct-2507, Qwen3-4B-Thinking-2507, Qwen3-30BA3B-Instruct-2507, Qwen3-30B-A3B-Thinking |
| 012 | numeric | u,u | 1 | pass | 1.00 | The active parameter counts for the MoE models are 3B for Qwen3-30B-Instruct and Qwen3-30B-Thinking, and 3.6B for GPT-OSS-20B [S1]. |
| 013 | numeric | u | 1 | pass | 1.00 | SSD is trained on competitive-programming prompts synthesized from the seed subset of the rSTARcoder dataset (Liu et al., 2025), which results in appr |
| 014 | factual | u | 2 | pass | - | SSD applies only a minimal degeneracy filter to remove clearly unusable outputs, such as empty responses and single-line stubs, and no correctness ver |
| 015 | list | f,a | - | pass | 0.00 | SSD samples from the base model with training-time decoding temperature Ttrain, fine-tunes on its own raw outputs, and then decodes at evaluation time |
| 016 | numeric | u,u | 1 | pass | 1.00 | LiveCodeBench v6 has 131 problems and covers the period from February to May 2025 [S1]. LiveCodeBench v5 has 374 problems and covers the period from A |
| 017 | numeric | u | 1 | pass | - | 10 independent samples per problem are used to estimate pass@k [S1]. |
| 018 | list | u | 1 | flag: no verified quote from cited source(s) [ | - | SSD improves Qwen3-30B-Instruct's pass@1 on LiveCodeBench v6 from 42.4% to 55.3%, which is a gain of +12.9pp [S1, S2]. |
| 019 | numeric | u,u | 1 | pass | 0.50 | For Qwen3-30B-Instruct on LCB v6, the pass@1 improvement is +6.5pp on easy problems, +14.2pp on medium problems, and +15.3pp on hard problems [S1]. |
| 020 | numeric | u | 1 | flag: no verified quote from cited source(s) [ | 0.25 | Qwen3-30B-Instruct's result on LiveCodeBench v5 for PASS@1 is 45.8 [S2]. |
| 021 | reasonin | u,u | 1 | pass | 0.00 | The paper provides evidence that SSD does not collapse diversity through several observations. First, the gains in pass@5 are often larger than those  |
| 022 | table | f,a | 2 | pass | 0.33 | Qwen3-30B-Thinking's LCB v6 hard pass@1 before SSD was 41.5 and after SSD it is 59.7 [S2]. |
| 023 | table | f,a | 2 | flag: no verified quote from cited source(s) [ | 0.50 | Llama-3.1-8B-Instruct's LCB v6 hard pass@1 before SSD was 0.0, and after SSD it was 0.8 [S4]. |
| 024 | numeric | u | 1 | pass | 0.80 | Temperature tuning yields only modest gains on the base model, as the pass@1 for Qwen3-30B-Instruct ranges from 41.3% to 43.5% across the evaluated te |
| 025 | list | u,u | 1 | pass | - | SSD outperforms the best-tuned base model by the following amounts for pass@1: +11.8 pp for Qwen3-30B-Instruct, +5.8 pp for Qwen3-4B-Instruct, +2.2 pp |
| 026 | definiti | u,u | - | pass | 0.00 | Effective temperature $T_{eff}$ is defined as $T_{eff} = T_{train}T_{eval}$ when inside a fixed retained support, and this is the cleanest local forma |
| 027 | numeric | u | 1 | pass | 1.00 | The best observed setting among the truncated runs used Ttrain=2.0, Teval=1.1, and training-time top-k=10, which achieved 49.7% pass@1 (+7.3 pp), surp |
| 028 | factual | u | 1 | pass | - | When a nontrivial training-time truncation configuration ρtrain is used during SSD data generation, the optimal effective temperature (Teff) generally |
| 029 | reasonin | u | 3 | pass | - | A single evaluation temperature cannot fix the precision-exploration conflict because different contexts demand contradictory things: locks require pr |
| 030 | mechanis | u,u | 2 | pass | - | The toy simulation is structured as a finite-state machine with a vocabulary of V = 16 [S2]. The root state branches into two symmetric successful pat |
| 031 | reasonin | u,u | 1 | pass | - | Training and decoding are complementary in SSD because training makes the locks less fragile, and decoding uses the extra room created by training to  |
| 032 | list | u,u | 1 | pass | - | The real-model analysis of Qwen3-30B-Instruct showed that relative to the base model, the SSD version reaches decoding with a cleaner head and a weake |
| 033 | mechanis | a,f,u | 1 | pass | - | The three terms of the SSD loss decomposition are: the first term drives support compression, the second reshapes the head within that set, and the th |
| 034 | mechanis | u | 4 | pass | - | SSD can lower total entropy while preserving exploration because total entropy measures uncertainty over the full vocabulary, whereas evaluation-time  |
| 035 | factual | u,u | 1 | pass | 0.14 | When SSD trains on near-gibberish data, the resulting fine-tuned model still improves substantially, even though the synthesized outputs devolve into  |
| 036 | reasonin | f | 1 | pass | - | The gains in the stress test setting are smaller than those of the headline truncated setting because, in the stress test, the distractor tails are no |
| 037 | numeric | u,u | 1 | pass | 0.67 | 62 checkpoint/temperature configurations exceeded the 42.4% frozen-base pass@1 baseline [S1]. The final training loss in this stress test was 11.29 [S |
| 038 | numeric | u,u | 1 | pass | 0.50 | The stress-test model performs competitively in the evaluation-temperature range roughly between [0.6, 1.1] [S1]. Furthermore, the optimum for the mod |
| 039 | mechanis | u | 1 | pass | 0.00 | The vLLM decoding pipeline applies four steps in sequence: (1) temperature scaling, which divides all logits by T; (2) top-k filtering, which keeps th |
| 040 | factual | u | 1 | pass | - | Temperatures below 10-5 trigger greedy (argmax) decoding, which bypasses all subsequent steps [S1]. |
| 041 | table | u | - | pass | 0.00 | The sources mention sweeping temperature extensively to probe the strongest decode-only performance achievable by the base model when comparing SSD to |
| 042 | table | u | - | pass | 0.00 | The model-specific baseline decoding settings used for the frozen-model comparisons are detailed in Table 4 [S2]. |
| 043 | factual | u | 1 | pass | - | For instruct models, each problem is wrapped in a system message requesting a Python solution inside a markdown code block, followed by the problem st |
| 044 | list | f | 2 | pass | - | The out-of-domain benchmarks used include AIME to probe mathematical reasoning, HumanEval (Chen et al., 2021) to probe general code generation in Pyth |
| 045 | factual | u,u | 1 | pass | 0.00 | No, SSD does not substantially damage the out-of-domain performance for the 30B models; they remain broadly stable under programming-only SSD training |
| 046 | factual | u | 2 | pass | 0.00 | Llama-3.1-8B-Instruct exhibits the sharpest tradeoff, which includes losing ground on AIME while improving on HumanEval and CruxEval [S2]. |
| 047 | table | u,u | 1 | flag: no verified quote from cited source(s) [ | 0.00 | The HumanEval Shell score for Qwen3-4B-Instruct is 25.3 [S1]. |
| 048 | list | u,u,u | 1 | pass | 0.25 | At lock states, the training time support compression collapses the student's lock to a 2-token support, where the correct token absorbs 94.8% of the  |
| 049 | numeric | u | 3 | pass | 1.00 | The global optimum shifts upward after SSD. The student's advantage grows with temperature, moving from comparable at low temperature (5.5% vs 6.4%) t |
| 050 | numeric | u | 1 | pass | 1.00 | Yes, the toy student's advantage is sensitive to the top-p threshold, as repeating the grid search across top-p values from 0.65 to 0.90 leaves the st |
| 051 | table | a | - | flag: the answer cites no source | - | Table 1 is not provided in the sources, so it is not possible to determine which property on-policy self-distillation lacks that SSD has based on the  |
| 052 | table | a | - | flag: the answer cites no source | - | Table 1 is not provided in the sources, so it is not possible to compare GRPO with SSD based on the given information. |
| 053 | comparis | u | 1 | pass | - | SSD differs from STaR and ReSTEM in that it trains directly on raw, unverified model outputs, whereas related self-training approaches like STaR and R |
| 054 | comparis | u,u | 1 | pass | - | SSD differs from unsupervised RLVR or entropy-minimization methods in both its method and mechanism. Specifically, SSD is not a reinforcement learning |
| 055 | multi-ho | u,u,u | 1 | flag: no verified quote from cited source(s) [ | 0.25 | The best observed setting among the truncated runs reached 49.7% pass@1, which is above all no-truncation results [S2]. The headline result of 55.3% p |
| 056 | multi-ho | u,f,f | 1 | pass | 0.00 | The caption for Table 2 states that SSD improves every evaluated model [S4]. |
| 057 | multi-ho | u,f,f | 1 | pass | 0.00 | Yes, the pattern where the 'pass@5 gain exceeds pass@1 gain' holds for non-Qwen models. For example, for Qwen3-4B-Instruct, the pass@5 gain (+15.8pp)  |
| 058 | multi-ho | u,u,u | 3 | flag: no verified quote from cited source(s) [ | 0.20 | Without truncation, performance for Qwen3-30B-Instruct is largely organized by the effective temperature Teff = TtrainTeval [S1, S4]. The broad peak n |
| 059 | multi-ho | u,u | 1 | pass | 0.00 | Temperature tuning yields only modest gains on the base model, with Qwen3-30B-Instruct's pass@1 ranging from 41.3% to 43.5% across evaluated temperatu |
| 060 | multi-ho | u,f | 1 | flag: the answer cites no source | 1.00 | The base-model baselines used in the stress test (S1) are not explicitly stated to be the same as those in Table 2. However, S1 mentions that dashed l |
| 061 | partial | u | 4 | refused | - | The provided sources do not explicitly state how SSD performs when sampling more than one solution per prompt (N > 1). |
| 062 | partial | f,u | 1 | refused | - | The provided sources do not state the number of GPU-hours required for SSD fine-tuning. |
| 063 | partial | f | 2 | pass | - | SSD provides a gain of +5.3pp for GPT-OSS-20B [S1]. |
| 064 | partial | u | 3 | flag: no verified quote from cited source(s) [ | - | The lock/fork asymmetry arises because the same global objective acts on different retained-support geometries [S2]. At a lock, only one or a few toke |
| 065 | partial | u | 5 | flag: no verified quote from cited source(s) [ | - | For Llama-3.1-8B-Instruct, the generation settings were T=0.9, top-k=none, and top-p=0.8 [S3]. In the full experimental setup, the evaluation results  |
| 066 | unanswer | - | - | flag: Unsupported sentence in answer (6 of 8 w | - | SSD shows various performance metrics across different LiveCodeBench scenarios. For instance, on LiveCodeBench v6 02/2025 05/2025 - PASS@1 - EASY, SSD |
| 067 | unanswer | - | - | refused | - | The provided sources do not contain information about whether SSD helps models larger than 30B, such as 70B. |
| 068 | unanswer | - | - | refused | - | The provided sources do not contain information comparing SSD's pass@1 against GRPO on LiveCodeBench. |
| 069 | unanswer | - | - | refused | - | The provided sources do not explicitly state whether applying SSD repeatedly (multiple rounds) keeps improving the model. |
| 070 | unanswer | - | - | refused | - | The provided sources do not state whether SSD trained on math prompts improves math benchmarks. Source S1 mentions evaluating transfer on benchmarks f |
