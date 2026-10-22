# Golden QA evaluation: sharp-5doc-routed-dev

Golden file `/home/copper/Downloads/minicpm4_golden_qa.jsonl` (54 questions: 48 answerable, 3 unanswerable, 3 partially answerable). Store: `/tmp/claude-1000/-home-copper-Git-Template-RAG/24d159d4-229a-4570-887a-d29472273e1a/scratchpad/blind_store` (992 chunks, 939 usable). LLM json_mode=`schema`, policy=`balanced`, k=5. 'Correct' = the answer contains the facts listed in the gold sidecar: a lower bound, read the answers below.

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
- delivered (answered and passed the gates): 79% (38/48)
- contains every required fact: 0% (0/48)
- contains every required fact **and** delivered: 0% (0/48)
- mean share of required facts present: 0.00 (over the 0 questions that list facts)
- mean item recall over the 5 list questions that name their items: 0.76
- a verified quote comes from an evidence chunk: 92% (44/48)
- correct among flagged answers (false alarms): 0% (0/10)

## 4. Unanswerable questions (right behaviour: refuse)

- refused: 67% (2/3)
- answered but flagged: 0% (0/3)
- answered and passed the gates (the dangerous case): 33% (1/3)

## 4b. Partially answerable (the right reply cites what exists and says what the source does not give)

- refused outright (a fail: the part that exists should be given): 67% (2/3)
- answered and passed the gates: 0% (0/3)
- answered and flagged: 33% (1/3)
- whether a reply states what is missing needs reading; see section 6.

## 5. By question type (answerable)

| type | n | evidence in top-k | delivered | every fact | delivered and every fact |
|---|---:|---:|---:|---:|---:|
| comparison | 2 | 2 | 2 | 0 | 0 |
| conflict | 5 | 5 | 4 | 0 | 0 |
| factual | 5 | 4 | 5 | 0 | 0 |
| list | 10 | 10 | 8 | 0 | 0 |
| mechanism | 8 | 8 | 5 | 0 | 0 |
| multi-hop | 4 | 4 | 3 | 0 | 0 |
| numeric | 3 | 3 | 3 | 0 | 0 |
| reasoning | 4 | 4 | 4 | 0 | 0 |
| table | 7 | 4 | 4 | 0 | 0 |

## 6. Every question

| id | type | ev. | rank | outcome | facts | answer |
|---|---|---|---|---|---|---|
| 001 | factual | u,u | 1 | pass | - | MiniCPM4 comes in two parameter sizes: 0.5B and 8B [S1]. MiniCPM4.1 is a hybrid reasoning model developed from MiniCPM4, capable of being used in both |
| 002 | list | u | 1 | flag: the answer cites no source | - | MiniCPM4 innovates on four dimensions: model architecture (InfLLM v2), training data (UltraClean and UltraChat v2), training algorithms (ModelTunnel v |
| 003 | numeric | u | 4 | pass | - | MiniCPM4-8B uses 8 trillion tokens, which is 22% of Qwen3-8B's 36 trillion tokens [S1, S4]. |
| 005 | reasonin | u | 1 | pass | - | MoBA cannot accelerate decoding because it uses a query block design that prevents acceleration during the decoding phase [S1]. |
| 006 | list | u,f | 2 | pass | - | According to the MiniCPM4 paper, NSA's drawbacks are increased computational overhead for short sequences and threefold key-value storage costs for pr |
| 008 | mechanis | u | 1 | pass | - | The two stages of InfLLM v2 sparse attention are: (1) dynamically selecting relevant key-value blocks based on the query token's relevance scores, and |
| 010 | factual | f,u | 1 | pass | - | InfLLM v2 always attends to the initial key-value blocks B0 and the local window blocks, setting their relevance scores to infinity so that each query |
| 014 | reasonin | u,u | 2 | pass | - | InfLLM v2 uses mean pooling for semantic kernels because the top-k selection operation in sparse attention is nondifferentiable, preventing optimizati |
| 017 | mechanis | u,u | 1 | flag: no verified quote from cited source(s) [ | - | The efficient verification strategy works by pre-training a 1B-parameter LLM using the WSD scheduler over 1.1 trillion tokens, then applying a two-sta |
| 018 | list | u | 1 | pass | - | The positive seeds for the quality classifier included high-quality in-domain data with LLM scores above 4, instruction-formatted datasets (e.g., OH-2 |
| 020 | comparis | u | 2 | pass | - | A fastText classifier is used instead of an LLM classifier because it drastically reduces inference overhead while maintaining competitive performance |
| 021 | list | u | 1 | pass | - | The fastText classifier's hyperparameters are: vector dimension 256, learning rate 0.1, maximum n-gram length 3, minimum word frequency 5, and number  |
| 022 | table | a | - | flag: no verified quote from cited source(s) [ | - | UltraFineWeb-en has the highest English average score, exceeding both FineWeb and FineWeb-edu by 3.61pp and 1.3pp respectively [S2, S1]. |
| 027 | comparis | f,u | 1 | pass | - | µP and StepLaw showed comparable effectiveness for hyperparameter search [S1], with minimal differences in loss values and ScalingBench scores [S1]. T |
| 029 | mechanis | f,u | 1 | flag: no verified quote from cited source(s) [ | - | The multi-token prediction head is a one-layer Transformer with embedding layers and output heads shared with the main model [S1]. The loss is combine |
| 031 | list | u | 2 | pass | - | UltraChat v2 covers five skill areas: knowledge applications, reasoning, instruction following, long-context processing, and tool use [S2]. |
| 032 | mechanis | u | 1 | pass | - | The long-context SFT data is constructed by sampling documents from pretraining corpora, using an LLM to generate task-oriented queries, retrieving re |
| 034 | factual | u | 1 | pass | - | Function-calling samples are filtered by removing those where the tool invoked in the ground truth is not in the available tool set or where parameter |
| 035 | mechanis | u,u | 1 | pass | - | For math and code, RL rewards are computed based on the proportion of test cases passed, with a full reward of 1.0 when all test cases pass, and a rew |
| 036 | factual | u | 1 | pass | - | Too-easy RL problems are filtered out during the RL rollout phase by removing prompts whose responses are all right or wrong [S3]. Additionally, data  |
| 037 | list | u | 1 | flag: no verified quote from cited source(s) [ | - | MiniCPM4 uses a modified version of Group Relative Policy Optimization (GRPO) [S1]. The modifications include dynamic sampling during the RL rollout p |
| 040 | table | u,u | 1 | pass | - | Based on the performance metrics in Table 5, the Chunk-8k strategy achieved the highest performance on both AIME 2024 (34.79) and AIME 2025 (26.67), m |
| 041 | reasonin | f | 1 | pass | - | Going from 8k to 4k chunks doesn't reduce step time because the smaller chunk size introduces more frequent log probability computations for chunk-lev |
| 042 | list | u,u | 1 | pass | - | MiniCPM4 uses a chunk-wise rollout strategy with 16 rollouts per query, temperature and top-p set to 1.0 [S1]. |
| 043 | mechanis | u,u | 1 | pass | - | BitCPM4 avoids training a ternary model from scratch by initializing the model with a pre-trained high-precision checkpoint [S1], which reduces the re |
| 044 | multi-ho | u,u,u | 1 | pass | - | BitCPM4's QAT uses 10% of the tokens required for BitNet-2B [S1]. |
| 046 | mechanis | a,u | 1 | pass | - | FR-Spec speeds up drafting by reducing the computational complexity of the language modeling head from O(nd/V/) to O(nd/Vhigh/), where Vhigh is a subs |
| 047 | mechanis | u,f | 3 | flag: no verified quote from cited source(s) [ | - | P-GPTQ is an extension of GPTQ that implements a position-aware calibration strategy to eliminate initial token interference during Hessian computatio |
| 048 | table | u | 1 | pass | - | S-P-GPTQ degrades least from FP16 [S1, S2]. |
| 050 | reasonin | u | 1 | pass | - | A quantized target model should use fewer draft tokens [S1]. |
| 051 | list | u | 1 | pass | - | ArkInfer integrates platforms including MediaTek, Nvidia, Qualcomm, and Rockchip, with native backends such as NeuroPilot, Genie, RK-LLM, TensorRT-LLM |
| 053 | list | f,f | 1 | pass | - | According to Section 5.1, MiniCPM4's pre-training pipeline consists of a four-stage process: a stable pre-training stage using 7 trillion tokens, an a |
| 054 | table | a,a | - | flag: no verified quote from cited source(s) [ | - | MiniCPM4-8B surpasses Gemma3-12B and Phi4-14B [S1], and demonstrates comparable performance to Qwen3 [S2]. |
| 056 | table | a | - | pass | - | MiniCPM4-0.5B outperforms the ~1B baselines on knowledge-related tasks such as MMLU, CMMLU, and C-EVAL [S2]. The baselines compared include Qwen3-0.5B |
| 058 | factual | a | - | pass | - | MiniCPM4 was trained at a context length of 32K [S1]. It can process 128K sequences using YaRN [S1] and is evaluated on 128K NIAH with YaRN applied to |
| 059 | numeric | u | 1 | pass | - | The efficiency evaluation used two end-side devices: Jetson AGX Orin and RTX 4090 [S1]. The reported speedup versus Qwen3-8B is approximately 7x decod |
| 061 | numeric | u,u | 1 | pass | - | MiniCPM4-Survey uses approximately 2.71 million paper abstracts from Kaggle as foundational data and builds an efficient retrieval index using MiniCPM |
| 064 | table | f,u | 1 | pass | - | MiniCPM4-Survey achieves comparable content-related metrics to OpenAI Deep Research [S2], though it leads in factual metrics with a Fact Score of 68.7 |
| 065 | list | f,u | 1 | pass | - | MCP training data was constructed through three main parts: data generation, reverse data generation, and conversion of existing function call dataset |
| 067 | table | f | 1 | flag: Unsupported number in answer: [3] | - | The average MCP tool-call accuracies across the MCP servers are: for GPT-4o, function accuracy is 80.2%, parameter accuracy is 70.2%, and parameter va |
| 070 | conflict | u,u,u | 1 | pass | - | The paper presents three applications of MiniCPM4 [S1]. |
| 072 | conflict | u,u,u | 1 | pass | - | MiniCPM4-8B saw 8.3T pre-training tokens, split into 7T for the warmup and stable phases and 1.3T for the annealing phase [S1]. This is consistent wit |
| 073 | conflict | u,u | 1 | pass | - | MiniCPM4's attention sparsity at 128K context is 5% [S1]. |
| 074 | conflict | a,u | 2 | flag: no verified quote from cited source(s) [ | - | UltraFineWeb-zh improves CMMLU by 3.65 percentage points over Chinese-FineWeb-edu-v2 [S1, S2]. |
| 075 | multi-ho | u,f | 1 | flag: Number 0 is in the sources, but not in a | - | Yes, based on the provided sources. BitCPM4-0.5B outperforms Qwen3-0.6B on knowledge-related tasks such as MMLU, CMMLU, and C-EVAL [S1]. Table 6 also  |
| 077 | multi-ho | u,u | 2 | pass | - | No. While RL improved MiniCPM4-Survey in Coverage, Depth, and Novelty [S1], it did not improve Relevance, as the w/o RL row shows a lower Relevance sc |
| 078 | conflict | f,a | 2 | pass | - | The 0.5B baseline is Qwen3-0.6B [S1]. The table in S3 lists Qwen3 at 0.6B parameters, not 0.5B. |
| 080 | multi-ho | u,u | 1 | pass | - | 16 [S1] |
| 084 | partial | a | - | refused | - | I don't know based on the provided sources. |
| 085 | partial | u,u | 3 | refused | - | I don't know based on the provided sources. |
| 086 | partial | f | - | flag: Unsupported sentence in answer (4 of 7 w | - | Based on the provided sources, the pre-training of MiniCPM4-8B took 110 GPU hours [S4]. |
| 087 | unanswer | - | - | pass | - | The sources do not provide specific speed measurements for MiniCPM4 on iPhone or Apple Silicon Mac hardware. However, they state that the model achiev |
| 089 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
| 091 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
