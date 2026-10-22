# Golden QA evaluation: sharp-minicpm5-fuzzy

Golden file `/home/copper/Downloads/minicpm4_golden_qa.jsonl` (91 questions: 80 answerable, 5 unanswerable, 6 partially answerable). Store: `/tmp/claude-1000/-home-copper-Git-Template-RAG/24d159d4-229a-4570-887a-d29472273e1a/scratchpad/mcpm4_store` (221 chunks, 189 usable). LLM json_mode=`schema`, policy=`balanced`, k=5. 'Correct' = the answer contains the facts listed in the gold sidecar: a lower bound, read the answers below.

## 1. Ingestion: is the evidence in a usable chunk?

- usable: 71% (97/136)
- fuzzy-usable: 18% (25/136)
- rejected: 0% (0/136)
- split: 0% (0/136)
- absent: 10% (14/136)
- (fuzzy-usable: no exact match, but a chunk holds at least 80% of the quote's tokens; relevance below uses the same rule)
- questions with unreachable evidence: 022, 023, 045, 046, 054, 055, 056, 058, 062, 074, 078, 084

## 2. Retrieval (answerable questions and partially answerable ones)

- an evidence chunk in the top 5: 88% (76/86)
- evidence chunk ranked first: 73% (63/86)
- all of a question's evidence quotes covered by the top 5: 78% (67/86)

## 3. Answers

- answered (did not refuse): 100% (80/80)
- delivered (answered and passed the gates): 82% (66/80)
- contains every required fact: 0% (0/80)
- contains every required fact **and** delivered: 0% (0/80)
- mean share of required facts present: 0.00 (over the 0 questions that list facts)
- mean item recall over the 9 list questions that name their items: 0.72
- a verified quote comes from an evidence chunk: 86% (69/80)
- correct among flagged answers (false alarms): 0% (0/14)

## 4. Unanswerable questions (right behaviour: refuse)

- refused: 100% (5/5)
- answered but flagged: 0% (0/5)
- answered and passed the gates (the dangerous case): 0% (0/5)

## 4b. Partially answerable (the right reply cites what exists and says what the source does not give)

- refused outright (a fail: the part that exists should be given): 67% (4/6)
- answered and passed the gates: 33% (2/6)
- answered and flagged: 0% (0/6)
- whether a reply states what is missing needs reading; see section 6.

## 5. By question type (answerable)

| type | n | evidence in top-k | delivered | every fact | delivered and every fact |
|---|---:|---:|---:|---:|---:|
| comparison | 2 | 2 | 2 | 0 | 0 |
| conflict | 8 | 8 | 8 | 0 | 0 |
| factual | 9 | 8 | 9 | 0 | 0 |
| list | 17 | 16 | 16 | 0 | 0 |
| mechanism | 15 | 15 | 11 | 0 | 0 |
| multi-hop | 5 | 5 | 3 | 0 | 0 |
| numeric | 6 | 6 | 6 | 0 | 0 |
| reasoning | 6 | 6 | 5 | 0 | 0 |
| table | 12 | 7 | 6 | 0 | 0 |

## 6. Every question

| id | type | ev. | rank | outcome | facts | answer |
|---|---|---|---|---|---|---|
| 001 | factual | u,u | 1 | pass | - | MiniCPM4 comes in two parameter sizes: 0.5B and 8B [S1]. MiniCPM4.1 is a hybrid reasoning model developed from MiniCPM4, utilizing long CoT data for S |
| 002 | list | u | 1 | flag: the answer cites no source | - | MiniCPM4 innovates on four dimensions: model architecture (InfLLM v2), training data (UltraClean and UltraChat v2), training algorithms (ModelTunnel v |
| 003 | numeric | u | 4 | pass | - | MiniCPM4-8B uses 8 trillion tokens for training, which is 22% of Qwen3-8B's 36 trillion tokens [S4]. |
| 004 | numeric | u | 1 | pass | - | InfLLM v2 operates at 81% attention sparsity while matching full attention [S1]. |
| 005 | reasonin | u | 1 | pass | - | MoBA cannot accelerate decoding because it uses a query block design that prevents acceleration during the decoding phase [S1]. |
| 006 | list | u,f | 1 | pass | - | According to the MiniCPM4 paper, NSA's drawbacks are increased computational overhead for short sequences and threefold key-value storage costs for pr |
| 007 | numeric | u | 1 | pass | - | InfLLM v2's Top-K context block selection reduces computational costs by 60% compared with NSA [S1]. |
| 008 | mechanis | u | 1 | pass | - | The two stages are: (1) dynamically selecting relevant blocks from B based on the query token qi by computing relevance scores and selecting the block |
| 009 | mechanis | u,u | 1 | pass | - | InfLLM v2 scores a key-value block against a query using relevance scores computed between the query token and fine-grained semantic kernels that part |
| 010 | factual | f,u | 1 | pass | - | InfLLM v2 always attends to the initial key-value blocks B0 and the local window blocks, setting their relevance scores to infinity so that each query |
| 011 | mechanis | u | 1 | pass | - | InfLLM v2 handles grouped-query attention by requiring query heads within the same group to share the same top-k relevant blocks [S1]. This sharing al |
| 012 | mechanis | u,f | 1 | flag: no verified quote from cited source(s) [ | - | Top-K selection requires two passes because the operations of relevance computation, softmax normalization, and score aggregation do not satisfy the c |
| 013 | reasonin | u | 1 | flag: no verified quote from cited source(s) [ | - | InfLLM v2 uses token-level queries because decoding requires token-by-token generation, and query tokens cannot always form a complete block, so block |
| 014 | reasonin | u,u | 2 | pass | - | InfLLM v2 uses mean pooling for semantic kernels because the top-k selection operation in sparse attention is nondifferentiable, preventing the repres |
| 015 | numeric | u,u | 1 | pass | - | InfLLM v2 uses a kernel size of 32, a stride of 16, and requires query groups to contain at least 16 heads [S1]. |
| 016 | table | f | 2 | flag: Unsupported number in answer: [8] | - | UltraClean's efficient verification strategy requires approximately 110 GPU hours, compared to 1,200 GPU hours for training 100B tokens from scratch [ |
| 017 | mechanis | u,u | 1 | flag: no verified quote from cited source(s) [ | - | The efficient verification strategy works by pre-training a 1B-parameter LLM using the WSD scheduler over 1.1 trillion tokens, then applying a two-sta |
| 018 | list | u | 1 | pass | - | The positive seeds for the quality classifier included high-quality in-domain data with LLM scores above 4, instruction-formatted datasets (e.g., OH-2 |
| 019 | list | u | 1 | pass | - | The classifier's negative samples come from diverse raw data sources such as FineWeb, C4, Dolma, The Pile, RedPajama for English data and CCI3, Chines |
| 020 | comparis | u | 2 | pass | - | A fastText classifier is used instead of an LLM classifier because it drastically reduces inference overhead while maintaining competitive performance |
| 021 | list | u | 1 | pass | - | The fastText classifier's hyperparameters are: vector dimension 256, learning rate 0.1, maximum n-gram length 3, minimum word frequency 5, and number  |
| 022 | table | a | - | pass | - | UltraFineWeb-en has the highest average score among the three, being 3.61pp higher than FineWeb and 1.3pp higher than FineWeb-edu [S1, S2]. |
| 023 | table | a | - | pass | - | HellaSwag [S2] |
| 024 | list | u | 1 | pass | - | The reasoning-data pipeline synthesizes the textbook and forum paradigms of knowledge construction [S1]. |
| 025 | factual | u | 1 | pass | - | Open-source LLMs under 10B parameters [S1]. |
| 026 | mechanis | f,u | 1 | pass | - | ScalingBench is built from the validation datasets of downstream tasks. GPT-4o is used to generate reasoning steps for all test instances, and the con |
| 027 | comparis | f,u | 1 | pass | - | µP and StepLaw showed comparable effectiveness for hyperparameter search under the experimental conditions described [S1]. The differences in loss val |
| 028 | list | f | 1 | pass | - | The authors attribute the comparable effectiveness of µP and StepLaw to three factors: practical hardware constraints preventing strict adherence to S |
| 029 | mechanis | f,u | 1 | flag: no verified quote from cited source(s) [ | - | The multi-token prediction head is a one-layer Transformer with embedding layers and output heads shared with the main model [S1]. The loss is combine |
| 030 | mechanis | f,u | 1 | pass | - | FP8 training in MiniCPM4 uses online block-wise FP8 quantization with a block size of 128×128 for parameters and 128×1 for activations [S1]. FP8 is ap |
| 031 | list | u | 2 | pass | - | UltraChat v2 covers five skill areas: knowledge applications, reasoning, instruction following, long-context processing, and tool use [S2]. |
| 032 | mechanis | u | 1 | flag: no verified quote from cited source(s) [ | - | The long-context SFT data is constructed by sampling a document d from the pretraining corpus, generating task-oriented queries Q, retrieving k relate |
| 033 | factual | u | 1 | pass | - | An in-house code-interpreter example is discarded if the model fails to solve the problem within 10 attempts [S1]. |
| 034 | factual | u | 1 | pass | - | Function-calling samples are filtered by removing those where the tool invoked in the ground truth is not in the available tool set or where parameter |
| 035 | mechanis | u,u | 1 | pass | - | For code problems, RL rewards are computed based on the proportion of test cases passed, with a full reward of 1.0 when all test cases pass [S1]. The  |
| 036 | factual | u | 1 | pass | - | Too-easy RL problems are filtered out during the RL rollout phase by removing prompts whose responses are all right or wrong, ensuring that only promp |
| 037 | list | u | 1 | pass | - | MiniCPM4 uses a modified version of GRPO [S1] and incorporates dynamic sampling during the RL rollout phase to filter out prompts with all right or wr |
| 038 | mechanis | u,u | 1 | pass | - | Chunk-wise rollout works by breaking long responses into smaller chunks across iterations. The policy model generates trajectories of a fixed chunk le |
| 039 | list | f | 1 | pass | - | The techniques that stabilize chunk-wise rollout are chunk-level importance sampling, dual-clip, KL regularization with dynamic reference updates, and |
| 040 | table | u,u | 1 | pass | - | Based on the performance metrics in Table 5, the Chunk-8k strategy achieved the highest performance on both AIME 2024 (34.79) and AIME 2025 (26.67), m |
| 041 | reasonin | f | 1 | pass | - | Going from 8k to 4k chunks does not reduce step time because the smaller chunk size introduces more frequent log probability computations for chunk-le |
| 042 | list | u,u | 1 | pass | - | MiniCPM4 uses the µP learning rate strategy [S1]. The KL penalty is retained with a coefficient of 0.001 and the entropy constraint is removed [S1]. D |
| 043 | mechanis | u,u | 1 | pass | - | BitCPM4 avoids training a ternary model from scratch by initializing the model with a pre-trained high-precision checkpoint, thereby reducing the requ |
| 044 | multi-ho | u,u,u | 1 | pass | - | BitCPM4's QAT uses only 10% of the tokens required for BitNet-2B [S1]. Specifically, BitCPM4 uses twice the number of tokens used in the learning rate |
| 045 | table | f,a | 3 | flag: no verified quote from cited source(s) [ | - | Based on the provided sources, BitCPM4-1B performs similarly to competing 2B-parameter models [S2], but there is no direct comparison of BitCPM4-1B wi |
| 046 | mechanis | a,u | 1 | pass | - | FR-Spec speeds up drafting by reducing the computational complexity of the language modeling head. Instead of operating over the entire vocabulary V,  |
| 047 | mechanis | u,f | 3 | pass | - | P-GPTQ changes GPTQ by implementing a position-aware calibration strategy to eliminate initial token interference during Hessian computation, addressi |
| 048 | table | u | 1 | pass | - | S-P-GPTQ degrades least from FP16 [S1, S2]. |
| 049 | reasonin | u | 1 | pass | - | QSpec finds that using GPTQ on EAGLE-2 would lead to substantial degradation of the acceptance rate, so they switch to QAT [S1]. |
| 050 | reasonin | u | 1 | pass | - | A quantized target model should use fewer draft tokens [S1]. The quantization alleviates the memory access bottleneck, so using more draft tokens woul |
| 051 | list | u | 1 | pass | - | ArkInfer integrates platforms including MediaTek, Nvidia, Qualcomm, and Rockchip, with native backends such as NeuroPilot, Genie, RK-LLM, TensorRT-LLM |
| 052 | factual | u,u | 1 | pass | - | ArkInfer uses the BiTA algorithm for speculative decoding and the Guidance algorithm for constrained decoding [S1]. |
| 053 | list | f,f | 1 | pass | - | According to Section 5.1, MiniCPM4's pre-training pipeline consists of a four-stage process: a stable pre-training stage using 7 trillion tokens, an a |
| 054 | table | a,a | - | flag: no verified quote from cited source(s) [ | - | MiniCPM4-8B surpasses Qwen3-8B, Phi4-14B, and Gemma3-12B on Table 8 average [S1, S2]. |
| 055 | table | a,a | - | flag: no verified quote from cited source(s) [ | - | On the CEval benchmark, Qwen3-8B (81.36) beats MiniCPM4-8B (66.11) [S1]. On the Average benchmark, Qwen3-8B (80.55) beats MiniCPM4-8B (52.99) [S2]. |
| 056 | table | a | - | flag: no verified quote from cited source(s) [ | - | MiniCPM4-0.5B outperforms the ~1B baselines on knowledge-related tasks such as MMLU, CMMLU, and C-EVAL [S2]. It also achieves superior performance com |
| 057 | table | u,u | 1 | flag: no verified quote from cited source(s) [ | - | MiniCPM4.1's RULER (32K) weighted average is 88.93 for full attention and 85.84 for sparse attention [S1]. The sparse variant drops most on the overal |
| 058 | factual | a | - | pass | - | MiniCPM4 was trained at a context length of 32K, but it can process 128K sequences using YaRN [S1]. S2 also confirms that long-context pre-training ex |
| 059 | numeric | u | 1 | pass | - | The efficiency evaluation used Jetson AGX Orin and RTX 4090 [S1]. The reported speedup versus Qwen3-8B is approximately 7x decoding acceleration on Je |
| 060 | list | f | 1 | pass | - | The three stages of MiniCPM4-Survey are Planning, Retrieval, and Writing [S1]. |
| 061 | numeric | u,u | 1 | pass | - | MiniCPM4-Survey uses approximately 2.71 million paper abstracts from Kaggle as foundational data and builds an efficient retrieval index using MiniCPM |
| 062 | list | a | - | pass | - | The survey RL context manager dynamically adjusts prompts based on historical interactions, maintains a detailed record of interactions (prompts, resp |
| 063 | factual | u,u | 1 | pass | - | MiniCPM4-Survey is evaluated using the SurveyEval dataset [S1] with five metrics: Relevance, Coverage, Depth, Novelty, and Fact Score, judged by GPT-4 |
| 064 | table | f,u | 1 | pass | - | MiniCPM4-Survey achieves performance comparable to OpenAI Deep Research [S2]. In the provided table, MiniCPM4-Survey scores 3.45 on Relevance, 3.70 on |
| 065 | list | f,u | 1 | pass | - | MCP training data was constructed through three main parts: data generation, reverse data generation, and conversion from existing tool learning data  |
| 066 | mechanis | u,u | 1 | pass | - | Unreliable MCP tools are screened out by a tool quality inspection mechanism. The client prompts Claude-4 to generate 10 queries for each tool. If the |
| 067 | table | f | 2 | pass | - | The average MCP tool-call accuracies across the MCP servers are: function name accuracy 80.2%, parameter name accuracy 70.2%, and parameter value accu |
| 068 | list | u | 1 | pass | - | The MiniCPM4 team's future work includes investigating efficient training and inference of LLMs, developing an efficient sparse model architecture for |
| 069 | conflict | u,u | 1 | pass | - | MiniCPM4.1-8B achieves an overall average score of 79.93 for full attention and 79.14 for sparse attention [S2]. |
| 070 | conflict | u,u,u | 1 | pass | - | The paper presents three applications of MiniCPM4 [S1]. |
| 071 | conflict | u,u,f | 1 | pass | - | MiniCPM4 claims approximately 7x decoding acceleration on Jetson AGX Orin [S2]. |
| 072 | conflict | u,u,u | 1 | pass | - | MiniCPM4-8B saw 8.3T pre-training tokens total [S1]. These were split into 7T tokens for the warmup and stable phases, and 1.3T tokens for the anneali |
| 073 | conflict | u,u | 1 | pass | - | MiniCPM4's attention sparsity is 81% [S4]. |
| 074 | conflict | a,u | 2 | pass | - | UltraFineWeb-zh improves CMMLU by 3.65 percentage points over Chinese-FineWeb-edu-v2 [S1, S2]. |
| 075 | multi-ho | u,f | 1 | flag: Number 0 is in the sources, but not in a | - | Yes, based on the provided sources. BitCPM4-0.5B outperforms Qwen3-0.6B on knowledge-related tasks such as MMLU, CMMLU, and C-EVAL [S1]. Table 6 also  |
| 076 | multi-ho | f,u | 1 | flag: no verified quote from cited source(s) [ | - | Yes. The paper states that Qwen3 appears less familiar with specialized tools like arXiv [S1]. The evaluation table shows that MiniCPM4-MCP achieves 5 |
| 077 | multi-ho | u,u | 2 | pass | - | No. According to the results, MiniCPM4-Survey still lags behind some baseline methods in Coverage and Novelty despite improvements from SFT to RL [S1] |
| 078 | conflict | f,a | 2 | pass | - | Qwen3-0.5B is the 0.5B baseline for MiniCPM4-0.5B [S5]. |
| 079 | conflict | u,u,u | 1 | pass | - | MiniCPM4 was trained on a 32K context length during long-context pre-training [S1], though the model's extended capability reaches 128K tokens [S2]. |
| 080 | multi-ho | u,u | 1 | pass | - | 16 [S1] |
| 081 | partial | u | - | refused | - | I don't know based on the provided sources. |
| 082 | partial | f | 1 | pass | - | BitCPM4-1B is trained based on the internal experimental model [S1]. |
| 083 | partial | u,u | 2 | refused | - | The provided sources do not contain the exact prefilling and decoding tokens/s for MiniCPM4-8B on RTX 4090 at 128K. |
| 084 | partial | a | - | refused | - | I don't know based on the provided sources. |
| 085 | partial | u,u | 3 | pass | - | The provided sources do not specify the layer count, hidden size, or head configuration for MiniCPM4-0.5B and MiniCPM4-8B [S3]. |
| 086 | partial | f | - | refused | - | The sources do not provide a direct statement of the GPU hours taken for MiniCPM4-8B pre-training. While S4 mentions computational costs for a differe |
| 087 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
| 088 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
| 089 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
| 090 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
| 091 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
