# Golden QA evaluation: ornith9b-dev

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
- delivered (answered and passed the gates): 56% (27/48)
- contains every required fact: 0% (0/48)
- contains every required fact **and** delivered: 0% (0/48)
- mean share of required facts present: 0.00 (over the 0 questions that list facts)
- mean item recall over the 5 list questions that name their items: 0.81
- a verified quote comes from an evidence chunk: 90% (43/48)
- correct among flagged answers (false alarms): 0% (0/21)

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
| conflict | 5 | 5 | 3 | 0 | 0 |
| factual | 5 | 4 | 3 | 0 | 0 |
| list | 10 | 10 | 7 | 0 | 0 |
| mechanism | 8 | 8 | 3 | 0 | 0 |
| multi-hop | 4 | 4 | 2 | 0 | 0 |
| numeric | 3 | 3 | 3 | 0 | 0 |
| reasoning | 4 | 4 | 1 | 0 | 0 |
| table | 7 | 4 | 3 | 0 | 0 |

## 6. Every question

| id | type | ev. | rank | outcome | facts | answer |
|---|---|---|---|---|---|---|
| 001 | factual | u,u | 1 | pass | - | MiniCPM4 comes in two parameter sizes: 0.5B and 8B, each with general and deep inference variants [S1]. MiniCPM4.1 is a hybrid reasoning model built o |
| 002 | list | u | 1 | flag: Unsupported number in answer: [3] | - | MiniCPM4 innovates across four key dimensions: model architecture, training data, training algorithms, and inference systems. The main technique in ea |
| 003 | numeric | u | 4 | pass | - | MiniCPM4-8B uses only 22% of the pre-training tokens of Qwen3-8B. Specifically, Qwen3-8B was trained with 36 trillion tokens, while MiniCPM4-8B achiev |
| 005 | reasonin | u | 1 | flag: the answer cites no source | - | MoBA cannot accelerate decoding because it uses the design of query blocks. This design prevents it from achieving acceleration during the decoding ph |
| 006 | list | u,f | 1 | pass | - | According to the MiniCPM4 paper, NSA's drawbacks are that it introduces three different attention components to capture long-distance information, whi |
| 008 | mechanis | u | 1 | flag: the answer cites no source | - | InfLLM v2 sparse attention consists of two stages. In the first stage, relevant blocks are dynamically selected from the key-value cache based on the  |
| 010 | factual | f,u | 1 | flag: the answer cites no source | - | InfLLM v2 always attends to the initial key-value block B0 and the local window blocks, because it sets the relevance scores between each query token  |
| 014 | reasonin | u,u | 2 | flag: the answer cites no source | - | InfLLM v2 uses mean pooling for semantic kernels because the top-k selection operation in sparse attention is nondifferentiable, meaning the represent |
| 017 | mechanis | u,u | 1 | flag: the answer cites no source | - | The efficient verification strategy works by leveraging a nearly-trained LLM as a foundation rather than training from scratch. It pre-trains a 1B-par |
| 018 | list | u | 1 | pass | - | The positive seeds for the quality classifier were selected from an initial pool of candidate seed samples using an efficient verification strategy, c |
| 020 | comparis | u | 2 | pass | - | A fastText classifier is used instead of an LLM classifier primarily to reduce inference costs and overhead. LLM-based classifiers incur significantly |
| 021 | list | u | 1 | pass | - | The fastText classifier is configured with a vector dimension of 256, a learning rate of 0.1, a maximum n-gram length of 3, a minimum word frequency o |
| 022 | table | a | - | pass | - | On average, UltraFineWeb-en outperforms both baselines: its English average score of 45.891pp is 3.61pp higher than FineWeb (42.287pp) and 1.3pp highe |
| 027 | comparis | f,u | 1 | pass | - | µP and StepLaw performed comparably for hyperparameter search. As shown in Table 3, StepLaw demonstrated slightly more instances of advantage, but the |
| 029 | mechanis | f,u | 1 | flag: the answer cites no source | - | The multi-token prediction (MTP) head is an additional prediction head that is a one-layer Transformer with embedding layers and output heads shared w |
| 031 | list | u | 2 | pass | - | UltraChat v2 covers five key skill areas: knowledge applications, reasoning, instruction following, long-context processing, and tool use [S2]. |
| 032 | mechanis | u | 1 | pass | - | The long-context SFT data is constructed from existing pretraining corpora, inspired by LongAlign. A document d is sampled from various sources (web p |
| 034 | factual | u | 1 | pass | - | Function-calling samples are filtered using strict criteria: samples are removed when the tool invoked in the ground truth is not included in the avai |
| 035 | mechanis | u,u | 1 | pass | - | For math problems, rewards are computed during the evaluation phase: outputs that do not conform to the expected reasoning format are assigned a rewar |
| 036 | factual | u | 1 | pass | - | Too-easy RL problems are filtered out through difficulty-based stratification, which actively reduces the proportion of easy questions during training |
| 037 | list | u | 1 | pass | - | MiniCPM4 modifies GRPO in three ways. First, it adds Dynamic Sampling: during the RL rollout phase, it filters out prompts whose responses are all rig |
| 040 | table | u,u | 1 | flag: the answer cites no source | - | Chunk-8k performed best in the Table 5 ablation. It achieved the highest performance on both AIME 2024 (34.79) and AIME 2025 (26.67), while also maint |
| 041 | reasonin | f | 1 | pass | - | Going from 8k to 4k chunks reduces step time only in sampling, not in total training time, because the smaller chunk size introduces more frequent log |
| 042 | list | u,u | 1 | flag: the answer cites no source | - | MiniCPM4's RL hyperparameters include: retaining the KL penalty with a coefficient of 0.001 (removing the entropy constraint), setting temperature and |
| 043 | mechanis | u,u | 1 | pass | - | BitCPM4 avoids training a ternary model from scratch by initializing the ternary model with a pre-trained high-precision checkpoint, which reduces the |
| 044 | multi-ho | u,u,u | 1 | flag: the answer cites no source | - | BitCPM4's QAT uses only 10% of the tokens required by BitNet-2B, which corresponds to 10× fewer training tokens. Since BitCPM4's QAT process uses 350B |
| 046 | mechanis | a,u | 1 | flag: the answer cites no source | - | FR-Spec speeds up drafting by restricting the draft model's computation to a frequency-prioritized subset of high-frequency tokens (Vhigh) rather than |
| 047 | mechanis | u,f | 3 | flag: the answer cites no source | - | P-GPTQ is an extension of GPTQ that eliminates initial token interference during Hessian computation. While standard GPTQ computes the Hessian matrix  |
| 048 | table | u | 1 | pass | - | S-P-GPTQ degrades least from FP16. According to [S2], "S-P-GPTQ achieves superior performance among quantized methods, exhibiting the smallest perform |
| 050 | reasonin | u | 1 | flag: the answer cites no source | - | A quantized target model should use fewer draft tokens. According to SpecMQuant, when using EAGLE-2 with W4A16 target models (such as the model quanti |
| 051 | list | u | 1 | pass | - | ArkInfer integrates the following platforms and native backends: MediaTek, Nvidia, Qualcomm, and Rockchip, with their respective native inference fram |
| 053 | list | f,f | 1 | flag: the answer cites no source | - | According to Section 5.1, MiniCPM4's pre-training pipeline is a four-stage process. The first stage is a stable pre-training stage using 7 trillion to |
| 054 | table | a,a | - | flag: Unsupported number in answer: [76, 78, 8 | - | On Table 8, MiniCPM4-8B outperforms all three baselines on the average score. MiniCPM4-8B achieves an average of 81.13, which surpasses Qwen3-8B (80.5 |
| 056 | table | a | - | pass | - | MiniCPM4-0.5B outperforms the ~1B baselines. It achieves superior performance compared to Llama3.2-1B and Gemma3-1B, despite those models having twice |
| 058 | factual | a | - | flag: the answer cites no source | - | MiniCPM4 was trained at a 32K context length, and yes, it can handle 128K sequences. The model was trained with a 32K context window using LongRoPE po |
| 059 | numeric | u | 1 | pass | - | The efficiency evaluation used two edge chips: Jetson AGX Orin and RTX 4090 [S1]. Versus Qwen3-8B, the reported speedup is approximately 7x decoding a |
| 061 | numeric | u,u | 1 | pass | - | MiniCPM4-Survey uses approximately 2.71 million paper abstracts collected from Kaggle as foundational data, and it built an efficient retrieval index  |
| 064 | table | f,u | 1 | flag: the answer cites no source | - | MiniCPM4-Survey is comparable to OpenAI Deep Research on content-related metrics, but surpasses it on factual metrics. In Table 12, MiniCPM4-Survey sc |
| 065 | list | f,u | 1 | pass | - | MCP training data was constructed through three main parts: data generation, reverse data generation, and conversion of existing function call dataset |
| 067 | table | f | 2 | flag: no verified quote from cited source(s) [ | - | The average MCP tool-call accuracies in Table 13 are: GPT-4o func 80.2%, param 70.2%, p_v 49.1%; Qwen3 8B func 83.5%, param 67.7%, p_v 43.8%; MiniCPM4 |
| 070 | conflict | u,u,u | 1 | flag: no verified quote from cited source(s) [ | - | The paper presents three applications of MiniCPM4: Trustworthy Survey Generation, Tool Use with Model Context Protocol (MCP), and a third application  |
| 072 | conflict | u,u,u | 1 | pass | - | MiniCPM4-8B was trained on 8.3 trillion (8.3T) high-quality pre-training tokens, split into 7 trillion tokens for the warmup and stable phases and 1.3 |
| 073 | conflict | u,u | 1 | pass | - | MiniCPM4's attention sparsity at 128K context is 5% [S1]. |
| 074 | conflict | a,u | 2 | pass | - | UltraFineWeb-zh improves CMMLU by 3.65pp over Chinese-FineWeb-edu-v2 [S1, S2]. |
| 075 | multi-ho | u,f | 1 | flag: Number 0 is in the sources, but not in a | - | Yes. BitCPM4-0.5B outperforms Qwen3-0.6B on knowledge-related tasks (MMLU, CMMLU, C-EVAL), as stated in [S1]. In Table 6 [S2], BitCPM4-0.5B (0.5B Tern |
| 077 | multi-ho | u,u | 2 | pass | - | No. According to the comparison between MiniCPM4-Survey and the w/o RL variant in Table 12 [S2], RL improved Relevance (3.45 vs. 3.55), Coverage (3.70 |
| 078 | conflict | f,a | 2 | flag: the answer cites no source | - | The 0.5B baseline is Qwen3-0.5B. According to S5, the baseline models selected for MiniCPM4-0.5B include Qwen3-0.5B (Yang et al., 2025). |
| 080 | multi-ho | u,u | 1 | pass | - | MiniCPM4 uses 16 rollouts per prompt (query) during its RL rollout phase [S1]. |
| 084 | partial | a | - | refused | - | I don't know based on the provided sources. |
| 085 | partial | u,u | 3 | refused | - | I don't know based on the provided sources. |
| 086 | partial | f | - | refused | - | I don't know based on the provided sources. The sources describe the MiniCPM4-8B pre-training pipeline (a four-stage process totaling 8.3T tokens) but |
| 087 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
| 089 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
| 091 | unanswer | - | - | refused | - | The provided sources do not contain the answer. The sources describe MiniCPM4's training data scale (8 trillion tokens) and compare it to Qwen3's trai |
