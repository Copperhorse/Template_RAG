# Golden QA evaluation: sharp-k5-ctx4500-dev

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
- delivered (answered and passed the gates): 83% (40/48)
- contains every required fact: 0% (0/48)
- contains every required fact **and** delivered: 0% (0/48)
- mean share of required facts present: 0.00 (over the 0 questions that list facts)
- mean item recall over the 5 list questions that name their items: 0.76
- a verified quote comes from an evidence chunk: 75% (36/48)
- correct among flagged answers (false alarms): 0% (0/8)

## 4. Unanswerable questions (right behaviour: refuse)

- refused: 100% (3/3)
- answered but flagged: 0% (0/3)
- answered and passed the gates (the dangerous case): 0% (0/3)

## 4b. Partially answerable (the right reply cites what exists and says what the source does not give)

- refused outright (a fail: the part that exists should be given): 67% (2/3)
- answered and passed the gates: 33% (1/3)
- answered and flagged: 0% (0/3)
- whether a reply states what is missing needs reading; see section 6.

## 5. By question type (answerable)

| type | n | evidence in top-k | delivered | every fact | delivered and every fact |
|---|---:|---:|---:|---:|---:|
| comparison | 2 | 2 | 2 | 0 | 0 |
| conflict | 5 | 4 | 5 | 0 | 0 |
| factual | 5 | 3 | 5 | 0 | 0 |
| list | 10 | 9 | 9 | 0 | 0 |
| mechanism | 8 | 7 | 4 | 0 | 0 |
| multi-hop | 4 | 4 | 2 | 0 | 0 |
| numeric | 3 | 3 | 3 | 0 | 0 |
| reasoning | 4 | 3 | 4 | 0 | 0 |
| table | 7 | 3 | 6 | 0 | 0 |

## 6. Every question

| id | type | ev. | rank | outcome | facts | answer |
|---|---|---|---|---|---|---|
| 001 | factual | u,u | - | pass | - | MiniCPM4 comes in two parameter sizes: 0.5B and 8B [S1]. MiniCPM4.1 is a hybrid reasoning model developed from MiniCPM4, utilizing long CoT data for S |
| 002 | list | u | 1 | flag: the answer cites no source | - | MiniCPM4 innovates on four dimensions: model architecture (InfLLM v2), training data (UltraClean and UltraChat v2), training algorithms (ModelTunnel v |
| 003 | numeric | u | 4 | pass | - | MiniCPM4-8B uses 8 trillion tokens, which is 22% of Qwen3-8B's 36 trillion tokens [S1, S4]. |
| 005 | reasonin | u | 1 | pass | - | MoBA cannot accelerate decoding because it uses a query block design that prevents acceleration during the decoding phase [S1]. |
| 006 | list | u,a | 1 | pass | - | According to the MiniCPM4 paper, NSA's drawbacks are increased computational overhead for short sequences and threefold key-value storage costs for pr |
| 008 | mechanis | u | 1 | pass | - | The two stages are: (1) dynamically selecting the top-k relevant key-value blocks based on relevance scores, and (2) computing attention between the q |
| 010 | factual | a,u | 1 | pass | - | InfLLM v2 always attends to the initial key-value blocks B0 and the local window blocks, setting their relevance scores to infinity so that each query |
| 014 | reasonin | u,u | 2 | pass | - | InfLLM v2 uses mean pooling for semantic kernels because the top-k selection operation in sparse attention is nondifferentiable, preventing optimizati |
| 017 | mechanis | u,u | 1 | flag: no verified quote from cited source(s) [ | - | The efficient verification strategy works by pre-training a 1B-parameter LLM using the WSD scheduler over 1.1 trillion tokens, then applying a two-sta |
| 018 | list | u | 1 | pass | - | The positive seeds for the quality classifier included high-quality in-domain data with LLM scores above 4, instruction-formatted datasets (e.g., OH-2 |
| 020 | comparis | u | 2 | pass | - | A fastText classifier is used instead of an LLM classifier because it drastically reduces inference overhead while maintaining competitive performance |
| 021 | list | u | 1 | pass | - | The fastText classifier's hyperparameters are: vector dimension 256, learning rate 0.1, maximum n-gram length 3, minimum word frequency 5, and number  |
| 022 | table | a | - | pass | - | UltraFineWeb-en has the highest average score among the three, being 3.61pp higher than FineWeb and 1.3pp higher than FineWeb-edu [S1, S2]. |
| 027 | comparis | a,u | 1 | pass | - | µP and StepLaw showed comparable effectiveness for hyperparameter search in the experimental conditions [S1]. The differences in loss values and Scali |
| 029 | mechanis | a,u | - | flag: no verified quote from cited source(s) [ | - | The multi-token prediction head is a one-layer Transformer with embedding layers and output heads shared with the main model [S1]. The loss is combine |
| 031 | list | u | 2 | pass | - | UltraChat v2 covers five skill areas: knowledge applications, reasoning, instruction following, long-context processing, and tool use [S2]. |
| 032 | mechanis | u | 1 | flag: no verified quote from cited source(s) [ | - | The long-context SFT data is constructed by sampling a document d from the pretraining corpus, generating task-oriented queries Q, retrieving k relate |
| 034 | factual | u | 1 | pass | - | Function-calling samples are filtered by removing those where the tool invoked in the ground truth is not in the available tool set or where parameter |
| 035 | mechanis | u,u | 1 | pass | - | For math and code, RL rewards are computed based on the proportion of test cases passed for code problems, with a full reward of 1.0 when all pass, an |
| 036 | factual | u | 1 | pass | - | Too-easy RL problems are filtered out during the RL rollout phase by removing prompts whose responses are all right or wrong [S3]. This ensures that o |
| 037 | list | u | 1 | pass | - | MiniCPM4 uses a modified version of GRPO [S1]. The modifications include dynamic sampling during the RL rollout phase, where prompts with all right or |
| 040 | table | u,u | 1 | pass | - | Based on the performance metrics in Table 5, the Chunk-8k strategy achieved the highest performance on both AIME 2024 (34.79) and AIME 2025 (26.67), m |
| 041 | reasonin | a | - | pass | - | Going from 8k to 4k chunks does not reduce step time because the smaller chunk size introduces more frequent log probability computations for chunk-le |
| 042 | list | u,u | 1 | pass | - | MiniCPM4's RL hyperparameters include a maximum response length of 32,768 tokens, a constant learning rate of 1e-5, the µP learning rate strategy, a K |
| 043 | mechanis | u,u | 1 | pass | - | BitCPM4 avoids training a ternary model from scratch by initializing the model with a pre-trained high-precision checkpoint [S1], which reduces the re |
| 044 | multi-ho | u,u,u | 1 | pass | - | BitCPM4's QAT uses 10% of the tokens required for BitNet-2B [S1]. Specifically, BitCPM4 uses twice the number of tokens used in the learning rate deca |
| 046 | mechanis | a,u | 1 | pass | - | FR-Spec speeds up drafting by reducing the computational complexity of the language modeling head. Instead of operating over the entire vocabulary V,  |
| 047 | mechanis | u,a | 3 | flag: no verified quote from cited source(s) [ | - | P-GPTQ changes GPTQ by implementing a position-aware calibration strategy that eliminates initial token interference during Hessian computation [S3],  |
| 048 | table | u | 1 | pass | - | S-P-GPTQ degrades least from FP16 [S1, S2]. |
| 050 | reasonin | u | 1 | pass | - | A quantized target model should use fewer draft tokens [S1, S2] because the quantization alleviates memory access bottlenecks, and using more draft to |
| 051 | list | u | 1 | pass | - | ArkInfer integrates platforms such as MediaTek, Nvidia, Qualcomm, and Rockchip, with native backends including NeuroPilot, Genie, RK-LLM, TensorRT-LLM |
| 053 | list | a,a | - | pass | - | According to Section 5.1, MiniCPM4's pre-training pipeline consists of a four-stage process: a stable pre-training stage using 7 trillion tokens, an a |
| 054 | table | a,a | - | flag: no verified quote from cited source(s) [ | - | MiniCPM4-8B surpasses both Phi4-14B and Gemma3-12B on Table 8 average [S1]. It also demonstrates comparable performance to Qwen3-8B [S2]. |
| 056 | table | a | - | pass | - | MiniCPM4-0.5B achieves superior performance compared to the ~1B baselines such as Llama3.2-1B and Gemma3-1B, despite these models having twice the par |
| 058 | factual | a | - | pass | - | MiniCPM4 was trained at a context length of 32K, but it can also process 128K sequences [S1], [S2]. |
| 059 | numeric | u | 1 | pass | - | The efficiency evaluation used Jetson AGX Orin and RTX 4090 [S1]. The reported speedup versus Qwen3-8B is approximately 7x decoding acceleration on Je |
| 061 | numeric | u,u | 1 | pass | - | MiniCPM4-Survey uses approximately 2.71 million paper abstracts from Kaggle as foundational data, and builds an efficient retrieval index using MiniCP |
| 064 | table | a,u | 1 | pass | - | MiniCPM4-Survey achieves performance comparable to OpenAI Deep Research [S2]. In the provided table, MiniCPM4-Survey scores 3.45 on Relevance, 3.70 on |
| 065 | list | a,u | 1 | pass | - | MCP training data was constructed through three main parts: data generation, reverse data generation, and conversion from existing tool learning data  |
| 067 | table | a | - | pass | - | The average MCP tool-call accuracies across the MCP servers are: function name accuracy 80.2%, parameter name accuracy 70.2%, and parameter value accu |
| 070 | conflict | u,u,u | 1 | pass | - | The paper presents three applications of MiniCPM4 [S1]. |
| 072 | conflict | u,u,u | 1 | pass | - | MiniCPM4-8B saw 8.3T pre-training tokens total [S1]. They were split into 7T tokens for the warmup and stable phases and 1.3T tokens for the annealing |
| 073 | conflict | u,u | 1 | pass | - | MiniCPM4 has 81% attention sparsity [S4]. |
| 074 | conflict | a,u | 2 | pass | - | UltraFineWeb-zh improves CMMLU by 3.65pp over Chinese-FineWeb-edu-v2 [S2]. |
| 075 | multi-ho | u,a | 1 | flag: Number 0 is in the sources, but not in a | - | Yes, based on the provided sources, BitCPM4-0.5B outperforms Qwen3-0.6B on knowledge-related tasks such as MMLU, CMMLU, and C-EVAL [S1]. Table 6 also  |
| 077 | multi-ho | u,u | 2 | flag: the answer cites no source | - | No. According to S1, MiniCPM4-Survey still lags behind some baseline methods in Coverage and Novelty despite improvements from SFT to RL. The 'w/o RL' |
| 078 | conflict | a,a | - | pass | - | Qwen3-0.5B is the 0.5B baseline [S5]. |
| 080 | multi-ho | u,u | 1 | pass | - | 16 [S1] |
| 084 | partial | a | - | refused | - | I don't know based on the provided sources. |
| 085 | partial | u,u | 3 | pass | - | The provided sources do not specify the layer count, hidden size, or head configuration for MiniCPM4-0.5B and MiniCPM4-8B [S3]. |
| 086 | partial | a | - | refused | - | The sources do not provide a direct statement of the GPU hours taken for MiniCPM4-8B pre-training. While S4 mentions computational costs for different |
| 087 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
| 089 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
| 091 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
