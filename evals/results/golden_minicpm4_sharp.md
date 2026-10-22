# Golden QA evaluation: sharp-minicpm5-2b

Golden file `/home/copper/Downloads/minicpm4_golden_qa.jsonl` (91 questions: 80 answerable, 5 unanswerable, 6 partially answerable). Store: `/tmp/claude-1000/-home-copper-Git-Template-RAG/24d159d4-229a-4570-887a-d29472273e1a/scratchpad/mcpm4_store` (221 chunks, 189 usable). LLM json_mode=`schema`, policy=`balanced`, k=5. 'Correct' = the answer contains the facts listed in the gold sidecar: a lower bound, read the answers below.

## 1. Ingestion: is the evidence in a usable chunk?

- usable: 71% (97/136)
- rejected: 0% (0/136)
- split: 0% (0/136)
- absent: 29% (39/136)
- questions with unreachable evidence: 006, 010, 012, 016, 022, 023, 026, 027, 028, 029, 030, 039, 041, 045, 046, 047, 053, 054, 055, 056, 058, 060, 062, 064, 065, 067, 071, 074, 075, 076, 078, 082, 084, 086

## 2. Retrieval (answerable questions and partially answerable ones)

- an evidence chunk in the top 5: 74% (64/86)
- evidence chunk ranked first: 60% (52/86)
- all of a question's evidence quotes covered by the top 5: 56% (48/86)

## 3. Answers

- answered (did not refuse): 100% (80/80)
- delivered (answered and passed the gates): 80% (64/80)
- contains every required fact: 0% (0/80)
- contains every required fact **and** delivered: 0% (0/80)
- mean share of required facts present: 0.00 (over the 0 questions that list facts)
- mean item recall over the 9 list questions that name their items: 0.72
- a verified quote comes from an evidence chunk: 72% (58/80)
- correct among flagged answers (false alarms): 0% (0/16)

## 4. Unanswerable questions (right behaviour: refuse)

- refused: 100% (5/5)
- answered but flagged: 0% (0/5)
- answered and passed the gates (the dangerous case): 0% (0/5)

## 4b. Partially answerable (the right reply cites what exists and says what the source does not give)

- refused outright (a fail: the part that exists should be given): 50% (3/6)
- answered and passed the gates: 33% (2/6)
- answered and flagged: 17% (1/6)
- whether a reply states what is missing needs reading; see section 6.

## 5. By question type (answerable)

| type | n | evidence in top-k | delivered | every fact | delivered and every fact |
|---|---:|---:|---:|---:|---:|
| comparison | 2 | 2 | 2 | 0 | 0 |
| conflict | 8 | 7 | 7 | 0 | 0 |
| factual | 9 | 7 | 9 | 0 | 0 |
| list | 17 | 12 | 16 | 0 | 0 |
| mechanism | 15 | 14 | 11 | 0 | 0 |
| multi-hop | 5 | 5 | 3 | 0 | 0 |
| numeric | 6 | 6 | 6 | 0 | 0 |
| reasoning | 6 | 5 | 5 | 0 | 0 |
| table | 12 | 4 | 5 | 0 | 0 |

## 6. Every question

| id | type | ev. | rank | outcome | facts | answer |
|---|---|---|---|---|---|---|
| 001 | factual | u,u | - | pass | - | MiniCPM4 comes in two parameter sizes: 0.5B and 8B [S1]. MiniCPM4.1 is a hybrid reasoning model developed from MiniCPM4, utilizing long CoT data for S |
| 002 | list | u | 1 | flag: the answer cites no source | - | MiniCPM4 innovates on four dimensions: model architecture (InfLLM v2), training data (UltraClean and UltraChat v2), training algorithms (ModelTunnel v |
| 003 | numeric | u | 4 | pass | - | MiniCPM4-8B uses 8 trillion tokens, which is 22% of Qwen3-8B's 36 trillion tokens [S1, S4]. |
| 004 | numeric | u | 1 | pass | - | InfLLM v2 operates at 81% attention sparsity [S1]. |
| 005 | reasonin | u | 1 | pass | - | MoBA cannot accelerate decoding because it uses a query block design that prevents acceleration during the decoding phase [S1]. |
| 006 | list | u,a | 1 | pass | - | According to the MiniCPM4 paper, NSA's drawbacks are increased computational overhead for short sequences and threefold key-value storage costs for pr |
| 007 | numeric | u | 1 | pass | - | InfLLM v2's Top-K context block selection method reduces computational costs by 60% compared with NSA [S1]. |
| 008 | mechanis | u | 1 | pass | - | The two stages are: (1) dynamically selecting the top-k relevant blocks based on relevance scores, and (2) computing attention between the query token |
| 009 | mechanis | u,u | 1 | pass | - | InfLLM v2 scores a key-value block against a query by computing relevance scores using fine-grained semantic kernels. The query token qi is compared a |
| 010 | factual | a,u | 1 | pass | - | InfLLM v2 always attends to the initial key-value blocks B0 and the local window blocks, setting their relevance scores to infinity so that each query |
| 011 | mechanis | u | 1 | pass | - | InfLLM v2 handles grouped-query attention by requiring query heads within the same group to share the same top-k relevant blocks [S1]. This sharing al |
| 012 | mechanis | u,a | 1 | flag: no verified quote from cited source(s) [ | - | Top-K selection requires two passes because the operations of relevance computation, softmax normalization, and score aggregation do not satisfy the c |
| 013 | reasonin | u | 1 | flag: no verified quote from cited source(s) [ | - | InfLLM v2 uses token-level queries because decoding requires token-by-token generation, and query tokens cannot always form a complete block, so block |
| 014 | reasonin | u,u | 2 | pass | - | InfLLM v2 uses mean pooling for semantic kernels because the top-k selection operation in sparse attention is nondifferentiable, preventing optimizati |
| 015 | numeric | u,u | 1 | pass | - | InfLLM v2 uses a kernel size of 32, a stride of 16, and requires query groups to contain at least 16 heads [S1]. |
| 016 | table | a | - | flag: Unsupported number in answer: [4, 9] | - | UltraClean's efficient verification strategy requires approximately 110 GPU hours, compared to 1,200 GPU hours for training 100B tokens from scratch [ |
| 017 | mechanis | u,u | 1 | flag: no verified quote from cited source(s) [ | - | The efficient verification strategy works by pre-training a 1B-parameter LLM using the WSD scheduler over 1.1 trillion tokens, then applying a two-sta |
| 018 | list | u | 1 | pass | - | The positive seeds for the quality classifier included high-quality in-domain data with LLM scores above 4, instruction-formatted datasets (e.g., OH-2 |
| 019 | list | u | 1 | pass | - | The classifier's negative samples come from diverse raw data sources such as FineWeb, C4, Dolma, The Pile, RedPajama for English data and CCI3, Chines |
| 020 | comparis | u | 2 | pass | - | A fastText classifier is used instead of an LLM classifier because it drastically reduces inference overhead while maintaining competitive performance |
| 021 | list | u | 1 | pass | - | The fastText classifier's hyperparameters are: vector dimension 256, learning rate 0.1, maximum n-gram length 3, minimum word frequency 5, and number  |
| 022 | table | a | - | pass | - | UltraFineWeb-en has the highest average score among the three, being 3.61pp higher than FineWeb and 1.3pp higher than FineWeb-edu [S1, S2]. |
| 023 | table | a | - | pass | - | HellaSwag [S2] |
| 024 | list | u | 1 | pass | - | The reasoning-data pipeline synthesizes the textbook and forum paradigms of knowledge construction [S1]. |
| 025 | factual | u | 1 | pass | - | Open-source LLMs under 10B parameters [S1]. |
| 026 | mechanis | a,u | 2 | pass | - | ScalingBench is built from the validation datasets of downstream tasks. GPT-4o is used to generate reasoning steps for all test instances, and the con |
| 027 | comparis | a,u | 1 | pass | - | µP and StepLaw showed comparable effectiveness for hyperparameter search under the experimental conditions described [S1]. The differences in loss val |
| 028 | list | a | - | pass | - | The authors attribute the comparable effectiveness of µP and StepLaw to three factors: practical hardware constraints preventing strict adherence to S |
| 029 | mechanis | a,u | - | flag: no verified quote from cited source(s) [ | - | The multi-token prediction head is a one-layer Transformer with embedding layers and output heads shared with the main model [S1]. The MTP loss is com |
| 030 | mechanis | a,u | 1 | pass | - | FP8 training in MiniCPM4 involves online block-wise FP8 quantization of parameters (block size 128×128) and activations (128×1), using FP8 MMA with FP |
| 031 | list | u | 2 | pass | - | UltraChat v2 covers five skill areas: knowledge applications, reasoning, instruction following, long-context processing, and tool use [S2]. |
| 032 | mechanis | u | 1 | pass | - | The long-context SFT data is constructed by sampling a document d from the pretraining corpus, using an LLM to generate n task-oriented queries Q, ret |
| 033 | factual | u | 1 | pass | - | An in-house code-interpreter example is discarded if the model fails to solve the problem within 10 attempts [S1]. |
| 034 | factual | u | 1 | pass | - | Function-calling samples are filtered by removing those where the tool invoked in the ground truth is not in the available tool set or where parameter |
| 035 | mechanis | u,u | 1 | pass | - | For code problems, RL rewards are computed based on the proportion of test cases passed, with a full reward of 1.0 when all test cases pass [S1]. The  |
| 036 | factual | u | 1 | pass | - | Too-easy RL problems are filtered out during the RL rollout phase by removing prompts whose responses are all right or wrong, ensuring that only promp |
| 037 | list | u | 1 | pass | - | MiniCPM4 uses a modified version of GRPO [S1]. The modifications include dynamic sampling during the RL rollout phase, where prompts with all right or |
| 038 | mechanis | u,u | 1 | pass | - | Chunk-wise rollout works by breaking long responses into smaller chunks across iterations. The policy model generates trajectories of a fixed chunk le |
| 039 | list | a | - | pass | - | The techniques that stabilize chunk-wise rollout are chunk-level importance sampling, dual-clip, KL regularization with dynamic reference updates, and |
| 040 | table | u,u | 1 | pass | - | Based on the performance metrics in Table 5, the Chunk-8k strategy achieved the highest performance on both AIME 2024 (34.79) and AIME 2025 (26.67), m |
| 041 | reasonin | a | - | pass | - | Going from 8k to 4k chunks does not reduce step time because the smaller chunk size introduces more frequent log probability computations for chunk-le |
| 042 | list | u,u | 1 | pass | - | MiniCPM4 uses a chunk-wise rollout strategy with 16 rollouts per query, temperature and top-p set to 1.0 [S1]. |
| 043 | mechanis | u,u | 1 | pass | - | BitCPM4 avoids training a ternary model from scratch by initializing the model with a pre-trained high-precision checkpoint, thereby reducing the requ |
| 044 | multi-ho | u,u,u | 1 | pass | - | BitCPM4's QAT uses only 10% of the tokens required for BitNet-2B [S1]. Additionally, BitCPM4 uses twice the number of tokens used in the learning rate |
| 045 | table | a,a | - | flag: no verified quote from cited source(s) [ | - | Based on the provided sources, BitCPM4-1B performs similarly to competing 2B-parameter models [S1]. The comparison table in S3 shows that at the 1B-pa |
| 046 | mechanis | a,u | 1 | pass | - | FR-Spec speeds up drafting by reducing the computational complexity of the language modeling head. Instead of operating over the entire vocabulary V,  |
| 047 | mechanis | u,a | 3 | flag: no verified quote from cited source(s) [ | - | P-GPTQ changes GPTQ by implementing a position-aware calibration strategy that eliminates initial token interference during Hessian computation [S3],  |
| 048 | table | u | 1 | pass | - | S-P-GPTQ degrades least from FP16 [S2]. |
| 049 | reasonin | u | 1 | pass | - | QSpec finds that using GPTQ on EAGLE-2 would lead to substantial degradation of the acceptance rate, so they switch to QAT [S1]. |
| 050 | reasonin | u | 1 | pass | - | A quantized target model should use fewer draft tokens [S1, S2] because the quantization alleviates memory access bottlenecks, and using more draft to |
| 051 | list | u | 1 | pass | - | ArkInfer integrates platforms such as MediaTek, Nvidia, Qualcomm, and Rockchip, with native backends including NeuroPilot, Genie, RK-LLM, TensorRT-LLM |
| 052 | factual | u,u | 1 | pass | - | ArkInfer uses the BiTA algorithm for speculative decoding and the Guidance algorithm for constrained decoding [S1]. |
| 053 | list | a,a | - | pass | - | MiniCPM4's pre-training pipeline consists of a stable pre-training stage using 7 trillion tokens, an annealing pre-training stage using 1 trillion tok |
| 054 | table | a,a | - | flag: no verified quote from cited source(s) [ | - | MiniCPM4-8B surpasses Gemma3-12B and Phi4-14B [S1], and demonstrates comparable performance to Qwen3 [S2]. |
| 055 | table | a,a | - | flag: no verified quote from cited source(s) [ | - | Qwen3-8B does not beat MiniCPM4-8B on any of the benchmarks listed in Table 8. On MMLU, CMMLU, CEval, BBH, GSM8K, MATH500, MBPP, HumanEval, MiniCPM4-8 |
| 056 | table | a | - | flag: no verified quote from cited source(s) [ | - | MiniCPM4-0.5B outperforms the ~1B baselines on knowledge-related tasks such as MMLU, CMMLU, and C-EVAL [S2]. It also achieves superior performance com |
| 057 | table | u,u | 1 | flag: no verified quote from cited source(s) [ | - | MiniCPM4.1's RULER (32K) weighted averages are 88.93 for full attention and 85.84 for sparse attention [S1]. The sparse variant drops most on the over |
| 058 | factual | a | - | pass | - | MiniCPM4 was trained at a context length of 32K, but it can also process 128K sequences [S1], [S2]. |
| 059 | numeric | u | 1 | pass | - | The efficiency evaluation used Jetson AGX Orin and RTX 4090 [S1]. The reported speedup versus Qwen3-8B is approximately 7x decoding acceleration on Je |
| 060 | list | a | - | pass | - | The three stages of MiniCPM4-Survey are Planning, Retrieval, and Writing [S1]. |
| 061 | numeric | u,u | 1 | pass | - | MiniCPM4-Survey uses approximately 2.71 million paper abstracts from Kaggle as foundational data and builds an efficient retrieval index using MiniCPM |
| 062 | list | a | - | pass | - | The survey RL context manager dynamically adjusts prompts based on historical interactions, maintains a detailed record of interactions (prompts, resp |
| 063 | factual | u,u | 1 | pass | - | MiniCPM4-Survey is evaluated using the SurveyEval dataset [S1] with five metrics: Relevance, Coverage, Depth, Novelty, and Fact Score, judged by GPT-4 |
| 064 | table | a,u | 1 | pass | - | MiniCPM4-Survey achieves performance comparable to OpenAI Deep Research [S2]. In the provided evaluation metrics, MiniCPM4-Survey scores 3.45 on Relev |
| 065 | list | a,u | 1 | pass | - | MCP training data was constructed through three main parts: data generation, reverse data generation, and conversion from existing tool learning data  |
| 066 | mechanis | u,u | 1 | pass | - | Unreliable MCP tools are screened out by a tool quality inspection mechanism. The client prompts Claude-4 to generate 10 queries for each tool. If the |
| 067 | table | a | - | flag: no verified quote from cited source(s) [ | - | The average MCP tool-call accuracies are: GPT-4o - func: 80.2%, GPT-4o - param: 70.2%, GPT-4o - p_v: 49.1%, Qwen3 8B - func: 83.5%, Qwen3 8B - param:  |
| 068 | list | u | 1 | pass | - | The MiniCPM4 team plans to continue investigating efficient training and inference of LLMs. This includes developing efficient sparse model architectu |
| 069 | conflict | u,u | 1 | pass | - | MiniCPM4.1-8B achieves an overall average score of 79.93 for full attention and 79.14 for sparse attention [S2]. |
| 070 | conflict | u,u,u | 1 | flag: no verified quote from cited source(s) [ | - | The paper presents three applications of MiniCPM4 [S1, S2]. |
| 071 | conflict | u,u,a | 2 | pass | - | MiniCPM4 claims approximately 7x decoding acceleration on Jetson AGX Orin [S2]. |
| 072 | conflict | u,u,u | 1 | pass | - | MiniCPM4-8B saw 8.3T pre-training tokens, split into 7T for the warmup and stable phases and 1.3T for the annealing phase [S1]. |
| 073 | conflict | u,u | 1 | pass | - | MiniCPM4 has 81% attention sparsity [S4]. |
| 074 | conflict | a,u | 2 | pass | - | UltraFineWeb-zh improves CMMLU by 3.65 percentage points over Chinese-FineWeb-edu-v2 [S1, S2]. |
| 075 | multi-ho | u,a | 1 | flag: Number 0 is in the sources, but not in a | - | Yes, based on the provided sources, BitCPM4-0.5B outperforms Qwen3-0.6B on knowledge-related tasks such as MMLU, CMMLU, and C-EVAL [S1]. Table 6 also  |
| 076 | multi-ho | a,u | 2 | flag: no verified quote from cited source(s) [ | - | Yes. The paper states that Qwen3 is less familiar with specialized tools like arXiv [S1], and the evaluation table shows MiniCPM4-MCP has higher accur |
| 077 | multi-ho | u,u | 2 | pass | - | No. According to the results, MiniCPM4-Survey still lags behind some baseline methods in Coverage and Novelty despite improvements from SFT to RL [S1] |
| 078 | conflict | a,a | - | pass | - | Qwen3-0.5B is the 0.5B baseline for MiniCPM4-0.5B [S5]. |
| 079 | conflict | u,u,u | 1 | pass | - | MiniCPM4 was trained on a 32K context length during long-context pre-training [S1], though the model can process 128K sequences [S1]. The long-context |
| 080 | multi-ho | u,u | 1 | pass | - | 16 [S1] |
| 081 | partial | u | - | refused | - | I don't know based on the provided sources. |
| 082 | partial | a | - | pass | - | BitCPM4-1B is trained based on the internal experimental model [S1]. |
| 083 | partial | u,u | 2 | refused | - | The provided sources do not contain the exact prefilling and decoding tokens/s for MiniCPM4-8B on RTX 4090 at 128K. |
| 084 | partial | a | - | flag: Unsupported sentence in answer (5 of 9 w | - | The provided sources do not contain information about the number of test samples for each MCP server in Table 13. The tables only show accuracy percen |
| 085 | partial | u,u | 3 | pass | - | The provided sources do not specify the layer count, hidden size, or head configuration for MiniCPM4-0.5B and MiniCPM4-8B [S3]. |
| 086 | partial | a | - | refused | - | The sources do not provide a direct statement of the GPU hours taken for MiniCPM4-8B pre-training. While S4 mentions computational costs for a differe |
| 087 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
| 088 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
| 089 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
| 090 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
| 091 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
