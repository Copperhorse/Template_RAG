# Golden QA evaluation: SSD, table-aware chunking + table-cell gate, fuzzy evidence, schema mode

Golden file `evals/gold/ssd.jsonl` (70 questions: 60 answerable, 5 unanswerable, 5 partially answerable). Store: `/tmp/claude-1000/-home-copper-Git-Template-RAG/24d159d4-229a-4570-887a-d29472273e1a/scratchpad/ssd_t` (189 chunks, 183 usable). LLM json_mode=`schema`, policy=`balanced`, k=5. 'Correct' = the answer contains the facts listed in the gold sidecar: a lower bound, read the answers below.

## 1. Ingestion: is the evidence in a usable chunk?

- usable: 79% (80/101)
- fuzzy-usable: 17% (17/101)
- rejected: 0% (0/101)
- split: 0% (0/101)
- absent: 4% (4/101)
- (fuzzy-usable: no exact match, but a chunk holds at least 80% of the quote's tokens; relevance below uses the same rule)
- questions with unreachable evidence: 015, 033, 051, 052

## 2. Retrieval (answerable questions and partially answerable ones)

- an evidence chunk in the top 5: 91% (59/65)
- evidence chunk ranked first: 58% (38/65)
- all of a question's evidence quotes covered by the top 5: 82% (53/65)

## 3. Answers

- answered (did not refuse): 98% (59/60)
- delivered (answered and passed the gates): 85% (51/60)
- contains every required fact: 18% (11/60)
- contains every required fact **and** delivered: 18% (11/60)
- mean share of required facts present: 0.47 (over the 32 questions that list facts)
- mean item recall over the 7 list questions that name their items: 0.55
- a verified quote comes from an evidence chunk: 78% (47/60)
- correct among flagged answers (false alarms): 0% (0/8)

## 4. Unanswerable questions (right behaviour: refuse)

- refused: 60% (3/5)
- answered but flagged: 0% (0/5)
- answered and passed the gates (the dangerous case): 40% (2/5)

## 4b. Partially answerable (the right reply cites what exists and says what the source does not give)

- refused outright (a fail: the part that exists should be given): 20% (1/5)
- answered and passed the gates: 20% (1/5)
- answered and flagged: 60% (3/5)
- whether a reply states what is missing needs reading; see section 6.

## 5. By question type (answerable)

| type | n | evidence in top-k | delivered | every fact | delivered and every fact |
|---|---:|---:|---:|---:|---:|
| comparison | 2 | 2 | 2 | 0 | 0 |
| definition | 4 | 3 | 4 | 0 | 0 |
| factual | 10 | 10 | 10 | 1 | 1 |
| list | 9 | 7 | 8 | 1 | 1 |
| mechanism | 4 | 4 | 3 | 0 | 0 |
| multi-hop | 6 | 6 | 3 | 0 | 0 |
| numeric | 14 | 13 | 13 | 7 | 7 |
| reasoning | 4 | 4 | 4 | 0 | 0 |
| table | 7 | 5 | 4 | 2 | 2 |

## 6. Every question

| id | type | ev. | rank | outcome | facts | answer |
|---|---|---|---|---|---|---|
| 001 | factual | f | 1 | pass | - | The organization that produced the SSD paper is Apple [S1]. The equal-contribution authors are Ruixiang Zhang, Richard He Bai, Huangjie Zheng, and Yiz |
| 002 | factual | u | 2 | pass | - | The SSD code is released at https://github.com/apple/ml-ssd [S2]. |
| 003 | definiti | u | 2 | pass | - | Simple self-distillation (SSD) is an embarrassingly simple method where solutions are sampled from the base model with certain temperature and truncat |
| 004 | numeric | u | 4 | pass | 0.00 | SSD yields substantial LiveCodeBench v6 gains across six models spanning three families and multiple scales, with both instruct and thinking variants  |
| 005 | list | u | - | pass | - | SSD does not require learning from correctness labels, reward signals, or verification outcomes [S1]. It is not learning from correctness labels, rewa |
| 006 | numeric | u | - | pass | 0.00 | For Qwen3-30B-Instruct on LCB v6, the pass@5 score improves by +23.0pp on hard problems [S3]. |
| 007 | definiti | u,f | 1 | pass | - | 'Lock' positions are where the distribution is sharply peaked, with very few tokens carrying most of the mass and a long distractor tail carrying the  |
| 008 | definiti | u,u | 2 | pass | - | The precision-exploration conflict arises because different positions in code generation present contradictory demands on the decoding temperature Tev |
| 009 | list | u | 2 | pass | - | The paper's three contributions are: First, showing that SSD can substantially improve code generation models' performance using only their own unveri |
| 010 | factual | u,u | 2 | pass | - | In practice, N=1 (a single sample per prompt) is sufficient [S2]. The samples are not verified in any way, as there is no execution, no test cases, or |
| 011 | list | u | 2 | pass | - | The six models evaluated are Llama-3.1-8B-Instruct, Qwen3-4B-Instruct-2507, Qwen3-4B-Thinking-2507, Qwen3-30BA3B-Instruct-2507, Qwen3-30B-A3B-Thinking |
| 012 | numeric | u,u | 1 | pass | 1.00 | The active parameter counts for the MoE models are 3B for Qwen3-30B-Instruct and Qwen3-30B-Thinking, and 3.6B for GPT-OSS-20B [S1]. |
| 013 | numeric | u | 1 | pass | 1.00 | SSD training data is synthesized from the seed subset of the rSTARcoder dataset, which yields approximately 10,168 unique problems [S1]. |
| 014 | factual | u | 2 | pass | - | SSD applies only a minimal degeneracy filter to remove clearly unusable outputs, such as empty responses and single-line stubs, and no correctness ver |
| 015 | list | f,a | - | flag: no verified quote from cited source(s) [ | 0.00 | SSD samples solutions from the model with certain temperature and truncation configurations, and then fine-tunes on those samples with standard superv |
| 016 | numeric | u,u | 1 | pass | 1.00 | LiveCodeBench v6 has 131 problems and covers the period from February to May 2025 [S1]. LiveCodeBench v5 has 374 problems and covers the period from A |
| 017 | numeric | u | 1 | pass | - | All pass@k estimates use 10 independent samples per problem [S1]. |
| 018 | list | u | 1 | pass | - | SSD improves every evaluated model on LiveCodeBench, with the largest gains on medium and hard problems [S2]. For Qwen3-30B-Instruct on LCB v6, pass@1 |
| 019 | numeric | u,u | 1 | pass | 0.50 | For Qwen3-30B-Instruct on LCB v6, the pass@1 improvement with SSD is +6.5pp on easy problems, +14.2pp on medium problems, and +15.3pp on hard problems |
| 020 | numeric | u | 1 | flag: no verified quote from cited source(s) [ | 0.00 | Qwen3-30B-Instruct's SSD result on LCB v5 for PASS@1 - EASY is 92.9 with a gain of +1.7 [S2]. |
| 021 | reasonin | u,u | 1 | pass | 0.00 | The paper indicates that SSD does not collapse diversity, as a second clear pattern in the table shows that the gains are often larger at pass@5 than  |
| 022 | table | f,f | 1 | flag: Number 59.7 is in the sources, but not i | 0.33 | Qwen3-30B-Thinking's LCB v6 hard pass@1 is 41.5 before SSD and 59.7 after SSD [S1]. |
| 023 | table | f,f | 1 | pass | 0.50 | Llama-3.1-8B-Instruct's LiveCodeBench v6 hard pass@1 score before SSD was 1.6, and after SSD it was 1.6 +1.6 [S1]. |
| 024 | numeric | u | 1 | pass | 0.00 | Temperature tuning yields only modest gains on the base model [S1]. |
| 025 | list | u,u | 1 | pass | - | SSD beats the best decode-tuned base model by the following amounts for pass@1: +11.8 pp for Qwen3-30B-Instruct, +5.8 pp for Qwen3-4B-Instruct, +2.2 p |
| 026 | definiti | u,u | - | pass | 0.00 | Effective temperature $T_{eff}$ is defined as $T_{eff} = T_{train}T_{eval}$ when inside a fixed retained support, and this is the cleanest local forma |
| 027 | numeric | u | 1 | pass | 1.00 | The best observed setting among the truncated runs used Ttrain=2.0, Teval=1.1, and training-time top-k=10, which achieved a pass@1 of 49.7% (+7.3 pp), |
| 028 | factual | u | 1 | pass | - | The optimal Teff generally shifts towards a higher temperature when using more stringent training-time truncation [S1]. |
| 029 | reasonin | u | 3 | pass | - | A single evaluation temperature cannot fix the precision-exploration conflict because different positions in the model demand contradictory decoding c |
| 030 | mechanis | u,u | 2 | flag: no verified quote from cited source(s) [ | - | The toy simulation is structured with a finite-state machine with a vocabulary of V = 16 [S2]. The root state branches into two symmetric successful p |
| 031 | reasonin | u,u | 1 | pass | - | Training and decoding are complementary in SSD because training makes the locks less fragile, and decoding-only temperature tuning does not clean up t |
| 032 | list | u,u | 1 | pass | - | The real-model analysis of Qwen3-30B-Instruct showed that after applying SSD, the model reached decoding with a cleaner head and a weaker distractor t |
| 033 | mechanis | a,f,u | 1 | pass | - | The three terms of the SSD loss decomposition are: the first term drives support compression, the second reshapes the head within that set, and the th |
| 034 | mechanis | u | 4 | pass | - | SSD can lower total entropy while preserving exploration because total entropy measures uncertainty over the full vocabulary, whereas evaluation-time  |
| 035 | factual | u,u | 1 | pass | 0.29 | When SSD trains on near-gibberish data, the resulting fine-tuned model still improves substantially, reaching 48.1% pass@1 and 64.0% pass@5, which is  |
| 036 | reasonin | f | 1 | pass | - | The gains in the stress test setting are smaller than those of the headline truncated setting because, in the stress test, the distractor tails are no |
| 037 | numeric | u,u | 1 | pass | 0.67 | 62 checkpoint/temperature configurations exceeded the 42.4% frozen-base pass@1 baseline [S1]. The final training loss in this stress test was 11.29 [S |
| 038 | numeric | u,u | 1 | pass | 1.00 | Performance remains competitive for Teval roughly in the range [0.6, 1.1], but it degrades quickly once the evaluation-time temperature becomes too hi |
| 039 | mechanis | u | 1 | pass | 0.00 | The vLLM decoding pipeline applies the four steps in the order: temperature scaling, followed by top-k filtering, then top-p filtering, and finally Gu |
| 040 | factual | u | 1 | pass | - | vLLM switches to greedy (argmax) decoding when the temperature is below 10-5 [S1]. |
| 041 | table | u | 1 | pass | 1.00 | The generation decoding settings used for Qwen3-30B-Instruct are Generation - Ttrain of 1.6, Generation - top-k of 20, and Generation - top-p of 0.8 [ |
| 042 | table | u | 1 | pass | 1.00 | The base Qwen3-30B-Instruct model used the following decoding settings for generation: Generation - Ttrain=1.6, Generation - top-k=20, and Generation  |
| 043 | factual | u | 1 | pass | - | For instruct models, each problem is wrapped in a system message requesting a Python solution inside a markdown code block, followed by the problem st |
| 044 | list | f | 3 | pass | - | The out-of-domain benchmarks used were AIME to probe mathematical reasoning, HumanEval (Chen et al., 2021) to probe general code generation in Python  |
| 045 | factual | u,u | 4 | pass | 0.00 | No, SSD does not substantially damage the out-of-domain performance for the 30B models. The 30B models remain broadly stable under programming-only SS |
| 046 | factual | u | 3 | pass | 1.00 | Llama-3.1-8B-Instruct's AIME score collapsed after SSD, dropping from 4.7 to 0.3 [S1]. |
| 047 | table | u,u | 2 | flag: no verified quote from cited source(s) [ | 0.50 | Qwen3-4B-Instruct's HumanEval Shell score changes from 47.5 to 29.1 when SSD is applied [S2]. |
| 048 | list | u,u,u | 1 | pass | 1.00 | After applying SSD, the student's support looks as follows: for lock states, it collapses to a 2-token support where the correct token absorbs 94.8% o |
| 049 | numeric | u | 3 | pass | 1.00 | After SSD, the student's advantage grows with temperature, moving from comparable success at low temperature (5.5% vs 6.4%) to substantially better su |
| 050 | numeric | u | 1 | pass | 1.00 | Yes, the toy student's advantage is sensitive to the top-p threshold, as repeating the grid search across top-p values from 0.65 to 0.90 leaves the st |
| 051 | table | a | - | pass | - | On-policy self-distillation (SSD) avoids the fixed-point failure of naive self-training because temperature and truncation modify the teacher-induced  |
| 052 | table | a | - | flag: the answer cites no source | - | Table 1 is not provided in the sources, so it is not possible to compare GRPO with SSD based on the given text. |
| 053 | comparis | u | 1 | pass | - | SSD differs from STaR and ReSTEM because STaR and ReSTEM convert self-generated outputs into supervision through correctness-based filtering or extern |
| 054 | comparis | u,u | 1 | pass | - | SSD differs from unsupervised RLVR or entropy-minimization methods in both method and mechanism. While unsupervised RLVR or intrinsic-signal learning  |
| 055 | multi-ho | u,u,u | 1 | flag: no verified quote from cited source(s) [ | 0.25 | The best observed setting among the truncated runs reached 49.7% pass@1, which is above all no-truncation results [S2]. The headline result of 55.3% i |
| 056 | multi-ho | u,f,f | 1 | flag: no verified quote from cited source(s) [ | 0.00 | No, not every cell improves. The caption states that SSD improves every evaluated model, but the table itself shows cell shading which encodes the cha |
| 057 | multi-ho | u,f,f | 1 | pass | 0.40 | The pattern where the 'pass@5 gain exceeds pass@1 gain' holds for the Qwen models on LCB v6, as evidenced by the gains listed for Qwen3-4B-Instruct (+ |
| 058 | multi-ho | u,u,u | 3 | pass | 0.00 | The effective temperature (Teff) governs performance for Qwen3-30B-Instruct when there is no training-time truncation, where Teff is defined as Ttrain |
| 059 | multi-ho | u,u | 1 | pass | 0.67 | Temperature tuning yields only modest gains on the base model, with Qwen3-30B-Instruct's pass@1 ranging from 41.3% to 43.5% across evaluated temperatu |
| 060 | multi-ho | u,f | 2 | refused | 0.00 | The sources do not explicitly state whether the base-model pass@5 baseline used in the stress test (C.5 High-TemperatureCaseStudy) is the same as in T |
| 061 | partial | u | 3 | refused | - | The provided sources do not contain information on how SSD performs when sampling more than one solution per prompt (N > 1). |
| 062 | partial | f,u | 1 | flag: the answer cites no source | - | The provided sources describe the fine-tuning process in terms of iterations and hardware (e.g., 8×B200 GPUs), but they do not specify the total GPU-h |
| 063 | partial | f | 1 | flag: the answer cites no source | - | For GPT-OSS-20B (high), SSD shows improvements across various metrics, with gains of +5.3 on ALL, +3.3 on LiveCodeBench v6 02/2025 05/2025 - PASS@1 -  |
| 064 | partial | u | 3 | flag: no verified quote from cited source(s) [ | - | SSD sharpens locks while preserving forks because the lock/fork asymmetry arises from what survives into the retained set at each context [S3]. At a l |
| 065 | partial | u | 5 | pass | - | For GPT-OSS-20B (high), the base-model decoding settings were T=1.0, top-k=none, and top-p=1.0 [S1]. For Llama-3.1-8B-Instruct, the base-model decodin |
| 066 | unanswer | - | - | pass | - | SSD improves every evaluated model on LiveCodeBench, with the largest gains observed on medium and hard problems [S2, S3, S4, S5]. |
| 067 | unanswer | - | - | refused | - | The provided sources do not contain information about whether SSD helps models larger than 30B, such as 70B. |
| 068 | unanswer | - | - | refused | - | The provided sources do not contain information comparing SSD's pass@1 against GRPO on LiveCodeBench. |
| 069 | unanswer | - | - | refused | - | The provided sources do not explicitly state whether applying SSD repeatedly (multiple rounds) keeps improving the model. |
| 070 | unanswer | - | - | pass | - | The provided sources indicate that SSD training on competitive-programming prompts is evaluated on benchmarks for math reasoning, and the results are  |
