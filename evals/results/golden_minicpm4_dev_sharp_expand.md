# Golden QA evaluation: sharp-k5-expand3-ctx4500-dev

Golden file `/home/copper/Downloads/minicpm4_golden_qa.jsonl` (54 questions: 48 answerable, 3 unanswerable, 3 partially answerable). Store: `/tmp/claude-1000/-home-copper-Git-Template-RAG/24d159d4-229a-4570-887a-d29472273e1a/scratchpad/mcpm4_store` (221 chunks, 189 usable). LLM json_mode=`schema`, policy=`balanced`, k=5. 'Correct' = the answer contains the facts listed in the gold sidecar: a lower bound, read the answers below.

## 1. Ingestion: is the evidence in a usable chunk?

- usable: 72% (59/82)
- rejected: 0% (0/82)
- split: 0% (0/82)
- absent: 28% (23/82)
- questions with unreachable evidence: 006, 010, 022, 027, 029, 041, 046, 047, 053, 054, 056, 058, 064, 065, 067, 074, 075, 078, 084, 086

## 2. Retrieval (answerable questions and partially answerable ones)

- an evidence chunk in the top 5: 76% (39/51)
- evidence chunk ranked first: 61% (31/51)
- all of a question's evidence quotes covered by the top 5: 55% (28/51)

## 3. Answers

- answered (did not refuse): 100% (48/48)
- delivered (answered and passed the gates): 88% (42/48)
- contains every required fact: 0% (0/48)
- contains every required fact **and** delivered: 0% (0/48)
- mean share of required facts present: 0.00 (over the 0 questions that list facts)
- mean item recall over the 5 list questions that name their items: 0.76
- a verified quote comes from an evidence chunk: 75% (36/48)
- correct among flagged answers (false alarms): 0% (0/6)

## 4. Unanswerable questions (right behaviour: refuse)

- refused: 100% (3/3)
- answered but flagged: 0% (0/3)
- answered and passed the gates (the dangerous case): 0% (0/3)

## 4b. Partially answerable (the right reply cites what exists and says what the source does not give)

- refused outright (a fail: the part that exists should be given): 33% (1/3)
- answered and passed the gates: 33% (1/3)
- answered and flagged: 33% (1/3)
- whether a reply states what is missing needs reading; see section 6.

## 5. By question type (answerable)

| type | n | evidence in top-k | delivered | every fact | delivered and every fact |
|---|---:|---:|---:|---:|---:|
| comparison | 2 | 2 | 2 | 0 | 0 |
| conflict | 5 | 4 | 5 | 0 | 0 |
| factual | 5 | 3 | 5 | 0 | 0 |
| list | 10 | 9 | 9 | 0 | 0 |
| mechanism | 8 | 7 | 6 | 0 | 0 |
| multi-hop | 4 | 4 | 2 | 0 | 0 |
| numeric | 3 | 3 | 3 | 0 | 0 |
| reasoning | 4 | 3 | 4 | 0 | 0 |
| table | 7 | 3 | 6 | 0 | 0 |

## 6. Every question

| id | type | ev. | rank | outcome | facts | answer |
|---|---|---|---|---|---|---|
| 001 | factual | u,u | - | pass | - | MiniCPM4 comes in two parameter sizes: 0.5B and 8B [S1]. MiniCPM4.1 is a hybrid reasoning model developed from MiniCPM4, capable of being used in both |
| 002 | list | u | 1 | flag: the answer cites no source | - | MiniCPM4 innovates on four dimensions: model architecture (InfLLM v2), training data (UltraClean and UltraChat v2), training algorithms (ModelTunnel v |
| 003 | numeric | u | 4 | pass | - | MiniCPM4-8B uses 8 trillion tokens, which is 22% of Qwen3-8B's 36 trillion tokens [S1, S4]. |
| 005 | reasonin | u | 1 | pass | - | MoBA cannot accelerate decoding because it uses a query block design that prevents acceleration during the decoding phase [S1]. |
| 006 | list | u,a | 1 | pass | - | According to the MiniCPM4 paper, NSA's drawbacks are increased computational overhead for short sequences and threefold key-value storage costs for pr |
| 008 | mechanis | u | 1 | pass | - | The two stages are: (1) dynamically selecting the top-k relevant key-value blocks based on relevance scores, and (2) computing attention between the q |
| 010 | factual | a,u | 1 | pass | - | InfLLM v2 always attends to the initial key-value blocks B0 and the local window blocks by setting their relevance scores to infinity [S1]. For short  |
| 014 | reasonin | u,u | 2 | pass | - | InfLLM v2 uses mean pooling for semantic kernels because it is a parameter-free operation that ensures the representation of semantic kernels remains  |
| 017 | mechanis | u,u | 1 | pass | - | The efficient verification strategy pre-trains a 1B-parameter LLM using the WSD scheduler over 1.1 trillion tokens, then applies a two-stage annealing |
| 018 | list | u | 1 | pass | - | The positive seeds for the quality classifier included high-quality in-domain data with LLM scores above 4, instruction-formatted datasets (e.g., OH-2 |
| 020 | comparis | u | 2 | pass | - | A fastText classifier is used instead of an LLM classifier because it drastically reduces inference overhead while maintaining competitive performance |
| 021 | list | u | 1 | pass | - | The fastText classifier's hyperparameters are: vector dimension 256, learning rate 0.1, maximum n-gram length 3, minimum word frequency 5, and number  |
| 022 | table | a | - | pass | - | UltraFineWeb-en has the highest English average score, exceeding FineWeb by 3.61pp and FineWeb-edu by 1.3pp [S2, S1]. |
| 027 | comparis | a,u | 1 | pass | - | µP and StepLaw showed comparable effectiveness for hyperparameter search under the experimental conditions described. While StepLaw demonstrated sligh |
| 029 | mechanis | a,u | - | pass | - | The multi-token prediction head is a one-layer Transformer with embedding layers and output heads shared with the main model [S1]. The loss is combine |
| 031 | list | u | 2 | pass | - | UltraChat v2 covers five skill areas: knowledge applications, reasoning, instruction following, long-context processing, and tool use [S2]. |
| 032 | mechanis | u | 1 | flag: no verified quote from cited source(s) [ | - | The long-context SFT data is constructed by sampling a document d from the pretraining corpus, using an LLM to generate n task-oriented queries Q, ret |
| 034 | factual | u | 1 | pass | - | Function-calling samples are filtered by removing those where the tool invoked in the ground truth is not in the available tool set or where parameter |
| 035 | mechanis | u,u | 1 | pass | - | For code, RL rewards are computed based on the proportion of test cases passed, with a full reward of 1.0 assigned when all test cases pass [S1]. For  |
| 036 | factual | u | 1 | pass | - | Too-easy RL problems are filtered out during the RL rollout phase by removing prompts whose responses are all right or wrong [S3]. |
| 037 | list | u | 1 | pass | - | MiniCPM4 uses a modified version of GRPO [S1] and incorporates dynamic sampling during the RL rollout phase to filter out prompts with all right or wr |
| 040 | table | u,u | 1 | pass | - | Chunk-8k performed best in the Table 5 ablation, achieving the highest performance on both AIME 2024 (34.79) and AIME 2025 (26.67) [S1]. |
| 041 | reasonin | a | - | pass | - | Going from 8k to 4k chunks doesn't reduce step time because the smaller chunk size introduces more frequent log probability computations for chunk-lev |
| 042 | list | u,u | 1 | pass | - | MiniCPM4 uses the µP learning rate strategy [S1], with temperature and top-p set to 1.0 during rollout [S1], and 16 rollouts generated per query [S1]. |
| 043 | mechanis | u,u | 1 | pass | - | BitCPM4 avoids training a ternary model from scratch by initializing the model with a pre-trained high-precision checkpoint, thereby reducing the requ |
| 044 | multi-ho | u,u,u | 1 | pass | - | BitCPM4's QAT uses 10% of the tokens required for BitNet-2B [S1]. |
| 046 | mechanis | a,u | 1 | pass | - | FR-Spec speeds up drafting by reducing the computational complexity of the language modeling head. It restricts the draft model to a reduced vocabular |
| 047 | mechanis | u,a | 3 | flag: no verified quote from cited source(s) [ | - | P-GPTQ changes GPTQ by implementing a position-aware calibration strategy that eliminates initial token interference during Hessian computation [S3],  |
| 048 | table | u | 1 | pass | - | S-P-GPTQ degrades least from FP16 [S1, S2]. |
| 050 | reasonin | u | 1 | pass | - | A quantized target model should use fewer draft tokens [S1, S2] because the quantization alleviates memory access bottlenecks, and using more draft to |
| 051 | list | u | 1 | pass | - | ArkInfer integrates platforms such as MediaTek, Nvidia, Qualcomm, and Rockchip, with native backends including NeuroPilot, Genie, RK-LLM, TensorRT-LLM |
| 053 | list | a,a | - | pass | - | According to Section 5.1, MiniCPM4's pre-training pipeline consists of a four-stage process: (1) a stable pre-training stage using 7 trillion tokens w |
| 054 | table | a,a | - | flag: no verified quote from cited source(s) [ | - | MiniCPM4-8B outperforms Qwen3-8B, Phi4-14B, and Gemma3-12B on Table 8 average [S1]. The table shows MiniCPM4-8B with an average of 81.36, while Qwen3- |
| 056 | table | a | - | pass | - | MiniCPM4-0.5B outperforms the ~1B baselines on knowledge-related tasks such as MMLU, CMMLU, and CEval [S2], and achieves superior performance compared |
| 058 | factual | a | - | pass | - | MiniCPM4 was trained at a context length of 32K [S1]. It can process 128K sequences using YaRN [S1]. |
| 059 | numeric | u | 1 | pass | - | The efficiency evaluation used Jetson AGX Orin and RTX 4090 [S1]. The reported speedup versus Qwen3-8B is approximately 7x decoding acceleration on Je |
| 061 | numeric | u,u | 1 | pass | - | MiniCPM4-Survey uses approximately 2.71 million paper abstracts from Kaggle as foundational data, and builds an efficient retrieval index using MiniCP |
| 064 | table | a,u | 1 | pass | - | MiniCPM4-Survey achieves performance comparable to OpenAI Deep Research [S2]. It also attains the highest scores among the examined systems for factua |
| 065 | list | a,u | 1 | pass | - | MCP training data was constructed through three main parts: data generation, reverse data generation, and conversion from existing tool learning data  |
| 067 | table | a | - | pass | - | The average MCP tool-call accuracies across the MCP servers are: func 80.2%, param 70.2%, p_v 49.1% [S2], and for Qwen3 8B: func 83.5%, param 67.7%, p |
| 070 | conflict | u,u,u | 1 | pass | - | The paper presents three applications of MiniCPM4 [S1]. |
| 072 | conflict | u,u,u | 1 | pass | - | MiniCPM4-8B saw 8.3T pre-training tokens, split into 7T for the warmup and stable phase and 1.3T for the annealing phase [S1], [S3]. |
| 073 | conflict | u,u | 1 | pass | - | MiniCPM4's attention sparsity is 81% [S4]. |
| 074 | conflict | a,u | 2 | pass | - | UltraFineWeb-zh improves CMMLU by 3.65 percentage points over Chinese-FineWeb-edu-v2 [S1, S2]. |
| 075 | multi-ho | u,a | 1 | flag: no verified quote from cited source(s) [ | - | Yes, based on the provided sources, BitCPM4-0.5B outperforms Qwen3-0.6B on knowledge-related tasks such as MMLU, CMMLU, and C-EVAL [S1]. Table 6 shows |
| 077 | multi-ho | u,u | 2 | flag: the answer cites no source | - | No. According to S1, MiniCPM4-Survey still lags behind some baseline methods in Coverage and Novelty despite improvements from SFT to RL. The table in |
| 078 | conflict | a,a | - | pass | - | Qwen3-0.5B is the 0.5B baseline [S5]. S1 also references Qwen3-0.6B in the context of comparison, but S5 explicitly lists Qwen3-0.5B as the baseline f |
| 080 | multi-ho | u,u | 1 | pass | - | 16 rollouts per prompt are used in MiniCPM4's RL [S1]. |
| 084 | partial | a | - | refused | - | I don't know based on the provided sources. |
| 085 | partial | u,u | 3 | pass | - | The provided sources do not specify the layer count, hidden size, or head configuration for MiniCPM4-0.5B and MiniCPM4-8B. [S1], [S3] |
| 086 | partial | a | - | flag: Unsupported sentence in answer (4 of 7 w | - | The sources do not provide the exact number of GPU hours for MiniCPM4-8B pre-training. [S1] mentions that MiniCPM4-8B used only 22% of the pre-trainin |
| 087 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
| 089 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
| 091 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
