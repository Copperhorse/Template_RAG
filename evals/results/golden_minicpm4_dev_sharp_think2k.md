# Golden QA evaluation: sharp-think2k

Golden file `/home/copper/Downloads/minicpm4_golden_qa.jsonl` (54 questions: 48 answerable, 3 unanswerable, 3 partially answerable). Store: `/tmp/claude-1000/-home-copper-Git-Template-RAG/24d159d4-229a-4570-887a-d29472273e1a/scratchpad/mcpm4_store` (221 chunks, 189 usable). LLM json_mode=`schema`, policy=`balanced`, k=5. 'Correct' = the answer contains the facts listed in the gold sidecar: a lower bound, read the answers below.

## 1. Ingestion: is the evidence in a usable chunk?

- usable: 72% (59/82)
- fuzzy-usable: 17% (14/82)
- rejected: 0% (0/82)
- split: 0% (0/82)
- absent: 11% (9/82)
- (fuzzy-usable: no exact match, but a chunk holds at least 80% of the quote's tokens; relevance below uses the same rule)
- questions with unreachable evidence: 022, 046, 054, 056, 058, 074, 078, 084

## 2. Retrieval (answerable questions and partially answerable ones)

- an evidence chunk in the top 5: 88% (45/51)
- evidence chunk ranked first: 69% (35/51)
- all of a question's evidence quotes covered by the top 5: 73% (37/51)

## 3. Answers

- answered (did not refuse): 100% (48/48)
- delivered (answered and passed the gates): 83% (40/48)
- contains every required fact: 0% (0/48)
- contains every required fact **and** delivered: 0% (0/48)
- mean share of required facts present: 0.00 (over the 0 questions that list facts)
- mean item recall over the 5 list questions that name their items: 0.76
- a verified quote comes from an evidence chunk: 85% (41/48)
- correct among flagged answers (false alarms): 0% (0/8)

## 4. Unanswerable questions (right behaviour: refuse)

- refused: 100% (3/3)
- answered but flagged: 0% (0/3)
- answered and passed the gates (the dangerous case): 0% (0/3)

## 4b. Partially answerable (the right reply cites what exists and says what the source does not give)

- refused outright (a fail: the part that exists should be given): 100% (3/3)
- answered and passed the gates: 0% (0/3)
- answered and flagged: 0% (0/3)
- whether a reply states what is missing needs reading; see section 6.

## 5. By question type (answerable)

| type | n | evidence in top-k | delivered | every fact | delivered and every fact |
|---|---:|---:|---:|---:|---:|
| comparison | 2 | 2 | 2 | 0 | 0 |
| conflict | 5 | 5 | 5 | 0 | 0 |
| factual | 5 | 4 | 5 | 0 | 0 |
| list | 10 | 10 | 9 | 0 | 0 |
| mechanism | 8 | 8 | 5 | 0 | 0 |
| multi-hop | 4 | 4 | 3 | 0 | 0 |
| numeric | 3 | 3 | 2 | 0 | 0 |
| reasoning | 4 | 4 | 4 | 0 | 0 |
| table | 7 | 4 | 5 | 0 | 0 |

## 6. Every question

| id | type | ev. | rank | outcome | facts | answer |
|---|---|---|---|---|---|---|
| 001 | factual | u,u | 1 | pass | - | MiniCPM4 comes in 0.5B and 8B parameter sizes [S1]. MiniCPM4.1 is a hybrid reasoning model built on MiniCPM4, using long CoT data and reinforcement le |
| 002 | list | u | 1 | pass | - | MiniCPM4 innovates on four dimensions: model architecture (InfLLM v2), training data (UltraClean and UltraChat v2), training algorithms (ModelTunnel v |
| 003 | numeric | u | 4 | pass | - | MiniCPM4-8B uses 8 trillion tokens, which is 22% of Qwen3-8B's 36 trillion tokens. [S4] [S1] |
| 005 | reasonin | u | 1 | pass | - | MoBA cannot accelerate decoding because it uses a query block design that prevents acceleration during the decoding phase [S1]. |
| 006 | list | u,f | 1 | pass | - | According to the MiniCPM4 paper, NSA's drawbacks are that its three attention components introduce additional parameters, leading to increased computa |
| 008 | mechanis | u | 1 | flag: the answer cites no source | - | The two stages are: (1) dynamically selecting the top-k relevant key-value blocks for a query token based on relevance scores, and (2) computing atten |
| 010 | factual | f,u | 1 | pass | - | InfLLM v2 always attends to the initial key-value blocks B0 and local window blocks by setting their relevance scores to infinity [S1]. For short inpu |
| 014 | reasonin | u,u | 2 | pass | - | InfLLM v2 uses mean pooling for semantic kernels because the top-k selection operation is nondifferentiable, which prevents optimization of semantic k |
| 017 | mechanis | u,u | 1 | flag: no verified quote from cited source(s) [ | - | The efficient verification strategy uses a pre-trained small LLM (1B parameters) as a classifier. Candidate data is incorporated during final training |
| 018 | list | u | 1 | pass | - | The positive seeds included high-quality in-domain data with LLM scores above 4, instruction-formatted datasets (e.g., OH-2.5 and ELI5), real-world ed |
| 020 | comparis | u | 2 | pass | - | A fastText classifier is used instead of an LLM classifier to drastically reduce inference overhead and improve processing efficiency, as LLM-based me |
| 021 | list | u | 1 | pass | - | The fastText classifier's hyperparameters are: vector dimension = 256, learning rate = 0.1, maximum n-gram length = 3, minimum word frequency = 5, and |
| 022 | table | a | - | pass | - | UltraFineWeb-en outperforms both FineWeb and FineWeb-edu on average. Its English average score is 45.891, which is 3.61pp higher than FineWeb (42.287) |
| 027 | comparis | f,u | 1 | pass | - | µP and StepLaw demonstrated comparable effectiveness for hyperparameter search, with minimal differences in loss values and ScalingBench scores [S1].  |
| 029 | mechanis | f,u | 1 | flag: no verified quote from cited source(s) [ | - | The multi-token prediction head is a one-layer Transformer with embedding layers and output heads shared with the main model [S1]. The loss is combine |
| 031 | list | u | 2 | pass | - | UltraChat v2 covers five skill areas: knowledge applications, reasoning, instruction following, long-context processing, and tool use. [S2] |
| 032 | mechanis | u | 1 | pass | - | The long-context SFT data is constructed by sampling a document d from the pretraining corpus, using an LLM to generate n task-oriented queries, retri |
| 034 | factual | u | 1 | pass | - | Function-calling samples are filtered by removing those where the tool invoked in the ground truth is not in the available tool set, or where paramete |
| 035 | mechanis | u,u | 1 | pass | - | For code, RL rewards are computed based on the proportion of test cases passed, with a full reward of 1.0 when all pass [S1]. For math, outputs that d |
| 036 | factual | u | 1 | pass | - | Too-easy RL problems are filtered out through difficulty-based stratification, which actively reduces the proportion of easy questions during training |
| 037 | list | u | 1 | pass | - | MiniCPM4 uses a modified version of GRPO that incorporates dynamic sampling during the RL rollout phase, filtering out prompts whose responses are all |
| 040 | table | u,u | 1 | pass | - | Chunk-8k performed best in the Table 5 ablation, achieving the highest performance scores on both AIME 2024 (34.79) and AIME 2025 (26.67) [S1]. |
| 041 | reasonin | f | 1 | pass | - | Going from 8k to 4k chunks does not reduce step time because the smaller chunk size introduces more frequent log probability computations for chunk-le |
| 042 | list | u,u | 1 | pass | - | MiniCPM4's RL hyperparameters include temperature=1.0, top-p=1.0, 16 rollouts per query, a KL penalty coefficient of 0.001, and no entropy constraint. |
| 043 | mechanis | u,u | 1 | pass | - | BitCPM4 avoids training a ternary model from scratch by initializing it with a pre-trained high-precision checkpoint (such as MiniCPM4-0.5B) and then  |
| 044 | multi-ho | u,u,u | 1 | pass | - | BitCPM4's QAT uses 10% of the tokens required for BitNet-2B [S1]. |
| 046 | mechanis | a,u | 1 | pass | - | FR-Spec speeds up drafting by restricting the draft model to a reduced vocabulary subset of high-frequency tokens (Vhigh), thereby reducing the comput |
| 047 | mechanis | u,f | 3 | pass | - | P-GPTQ changes GPTQ by implementing a prefix-aware calibration strategy that eliminates initial token interference during Hessian computation. It comp |
| 048 | table | u | 1 | flag: the answer cites no source | - | S-P-GPTQ |
| 050 | reasonin | u | 1 | pass | - | Fewer draft tokens [S1]} |
| 051 | list | u | 1 | flag: no verified quote from cited source(s) [ | - | ArkInfer integrates platforms such as MediaTek, Nvidia, Qualcomm, and Rockchip, along with native backends including NeuroPilot, Genie, RK-LLM, Tensor |
| 053 | list | f,f | 1 | pass | - | MiniCPM4's pre-training pipeline starts with hyperparameter search using the µP architecture, then a four-stage pipeline: stable pre-training on 7T to |
| 054 | table | a,a | - | pass | - | On Table 8 average, MiniCPM4-8B achieves 81.13, which is higher than Qwen3-8B (80.55), Phi4-14B (78.47), and Gemma3-12B (76.14) [S3]. |
| 056 | table | a | - | pass | - | MiniCPM4-0.5B outperforms the ~1B parameter baselines such as Llama3.2-1B and Gemma3-1B on knowledge-related tasks [S5]. |
| 058 | factual | a | - | pass | - | MiniCPM4 was trained at a context length of 32K, and it can process 128K sequences using YaRN [S1]. |
| 059 | numeric | u | 1 | flag: no verified quote from cited source(s) [ | - | The efficiency evaluation used two devices: Jetson AGX Orin and RTX 4090. The reported speedup versus Qwen3-8B is approximately 7x decoding accelerati |
| 061 | numeric | u,u | 1 | pass | - | MiniCPM4-Survey uses approximately 2.71 million paper abstracts from Kaggle (Cornell University/arxiv) as foundational data, and builds an efficient r |
| 064 | table | f,u | 1 | flag: the answer cites no source | - | MiniCPM4-Survey is comparable to OpenAI Deep Research in content quality metrics, with higher Depth (3.85 vs 3.55) and the highest Fact Score (68.73). |
| 065 | list | f,u | 1 | pass | - | MCP training data was constructed through three main parts: data generation, reverse data generation, and conversion from existing tool learning data. |
| 067 | table | f | 2 | pass | - | The average MCP tool-call accuracies for the servers listed in Table 13 (S2) are: GPT-4o: 80.2% (function), 70.2% (parameter), 49.1% (parameter value) |
| 070 | conflict | u,u,u | 1 | pass | - | The paper presents three applications of MiniCPM4 [S1, S2]. |
| 072 | conflict | u,u,u | 1 | pass | - | MiniCPM4-8B saw 8.3T pre-training tokens, split into 7T for the warmup and stable phases and 1.3T for the annealing phase [S1]. |
| 073 | conflict | u,u | 1 | pass | - | 5% [S1] |
| 074 | conflict | a,u | 2 | pass | - | UltraFineWeb-zh improves CMMLU by 3.65 percentage points over Chinese-FineWeb-edu-v2 [S2] |
| 075 | multi-ho | u,f | 1 | flag: Number 0 is in the sources, but not in a | - | Yes, BitCPM4-0.5B outperforms Qwen3-0.6B on knowledge-related tasks [S1], [S2]. |
| 077 | multi-ho | u,u | 2 | pass | - | No. RL improved Coverage, Depth, and Novelty but decreased Relevance [S2][S1]. |
| 078 | conflict | f,a | 2 | pass | - | Qwen3-0.5B [S5]. |
| 080 | multi-ho | u,u | 1 | pass | - | 16 [S1]} |
| 084 | partial | a | - | refused | - | I don't know based on the provided sources. |
| 085 | partial | u,u | 3 | refused | - | I don't know based on the provided sources. |
| 086 | partial | f | - | refused | - | I don't know based on the provided sources. |
| 087 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
| 089 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
| 091 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
