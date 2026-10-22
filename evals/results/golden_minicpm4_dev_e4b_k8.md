# Golden QA evaluation: e4b-k8-ctx4500-dev

Golden file `/home/copper/Downloads/minicpm4_golden_qa.jsonl` (54 questions: 48 answerable, 3 unanswerable, 3 partially answerable). Store: `/tmp/claude-1000/-home-copper-Git-Template-RAG/24d159d4-229a-4570-887a-d29472273e1a/scratchpad/mcpm4_store` (221 chunks, 189 usable). LLM json_mode=`schema`, policy=`balanced`, k=8. 'Correct' = the answer contains the facts listed in the gold sidecar: a lower bound, read the answers below.

## 1. Ingestion: is the evidence in a usable chunk?

- usable: 72% (59/82)
- rejected: 0% (0/82)
- split: 0% (0/82)
- absent: 28% (23/82)
- questions with unreachable evidence: 006, 010, 022, 027, 029, 041, 046, 047, 053, 054, 056, 058, 064, 065, 067, 074, 075, 078, 084, 086

## 2. Retrieval (answerable questions and partially answerable ones)

- an evidence chunk in the top 8: 78% (40/51)
- evidence chunk ranked first: 61% (31/51)
- all of a question's evidence quotes covered by the top 8: 59% (30/51)

## 3. Answers

- answered (did not refuse): 100% (48/48)
- delivered (answered and passed the gates): 94% (45/48)
- contains every required fact: 0% (0/48)
- contains every required fact **and** delivered: 0% (0/48)
- mean share of required facts present: 0.00 (over the 0 questions that list facts)
- mean item recall over the 5 list questions that name their items: 0.81
- a verified quote comes from an evidence chunk: 77% (37/48)
- correct among flagged answers (false alarms): 0% (0/3)

## 4. Unanswerable questions (right behaviour: refuse)

- refused: 67% (2/3)
- answered but flagged: 0% (0/3)
- answered and passed the gates (the dangerous case): 33% (1/3)

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
| factual | 5 | 4 | 5 | 0 | 0 |
| list | 10 | 9 | 10 | 0 | 0 |
| mechanism | 8 | 7 | 7 | 0 | 0 |
| multi-hop | 4 | 4 | 3 | 0 | 0 |
| numeric | 3 | 3 | 3 | 0 | 0 |
| reasoning | 4 | 3 | 4 | 0 | 0 |
| table | 7 | 3 | 6 | 0 | 0 |

## 6. Every question

| id | type | ev. | rank | outcome | facts | answer |
|---|---|---|---|---|---|---|
| 001 | factual | u,u | 2 | pass | - | MiniCPM4 is available in two parameter versions: 0.5B and 8B [S1], [S2]. MiniCPM4.1 is a hybrid reasoning model that can be used in both deep reasonin |
| 002 | list | u | 1 | pass | - | MiniCPM4 innovates in four key dimensions: model architecture, training data, training algorithms, and inference systems [S1, S2]. The main techniques |
| 003 | numeric | u | 4 | pass | - | MiniCPM4-8B uses 8 trillion tokens, which is 22% of the 36 trillion tokens used to train Qwen3-8B [S1, S2, S4]. |
| 005 | reasonin | u | 1 | pass | - | MoBA cannot achieve acceleration during the decoding phase because it utilizes the design of query blocks [S1]. |
| 006 | list | u,a | 1 | pass | - | NSA introduces three different attention components to capture long-distance information, and these components introduce additional parameters, which  |
| 008 | mechanis | u | 1 | pass | - | The sparse attention computation of InfLLM v2 has two stages [S1]. In the first stage, the system dynamically selects relevant blocks from B based on  |
| 010 | factual | a,u | 1 | pass | - | InfLLM v2 always ensures that each query token can attend to the initial key-value blocks B0 and the blocks within the local window by setting the rel |
| 014 | reasonin | u,u | 2 | pass | - | InfLLM v2 uses mean pooling because it is a parameter-free operation used to construct the representation of semantic kernels [S2]. Furthermore, mean  |
| 017 | mechanis | u,u | 1 | flag: no verified quote from cited source(s) [ | - | The efficient verification strategy works by leveraging a nearly-trained LLM as a foundation, rather than training LLMs from scratch using candidate c |
| 018 | list | u | 1 | pass | - | The positive seeds for the quality classifier included high-quality in-domain data with LLM scores above 4, instruction-formatted datasets such as OH- |
| 020 | comparis | u | 2 | pass | - | A fastText-based classifier is adopted because LLM-based classifiers incur significantly higher inference costs [S1]. Using fastText drastically reduc |
| 021 | list | u | 1 | pass | - | The hyperparameters configured for the fastText classifier for training are: the vector dimension is set to 256, the learning rate is set to 0.1, the  |
| 022 | table | a | - | pass | - | The average score for UltraFineWeb-en is 45.89+3.613 [S1], which is 3.61pp higher than FineWeb's average score of 42.287pp [S2] and 1.3pp higher than  |
| 027 | comparis | a,u | 1 | pass | - | The differences in loss values and ScalingBench scores between µP and StepLaw were minimal, and neither method showed consistently stable superiority  |
| 029 | mechanis | a,u | - | pass | - | The multi-token prediction (MTP) requires the LLM to output multiple tokens using additional prediction heads [S1]. These additional prediction heads  |
| 031 | list | u | 2 | pass | - | UltraChat v2 covers five key skill areas: knowledge applications, reasoning, instruction following, long-context processing, and tool use [S2]. |
| 032 | mechanis | u | 1 | pass | - | Long-context supervised fine-tuning (SFT) data is constructed by first sampling a document $d$ from various sources in the pretraining corpus [S1]. An |
| 034 | factual | u | 1 | pass | - | Function-calling samples are filtered by removing instances where the tool used in the ground truth is missing from the available tool set, or where t |
| 035 | mechanis | u,u | 1 | pass | - | For math, outputs that do not conform to the expected reasoning format are given a reward of zero, and correctness is determined using rule-based matc |
| 036 | factual | u | 1 | pass | - | Difficulty-based stratification is implemented to actively reduce the proportion of easy questions during training [S2]. Furthermore, to keep more cha |
| 037 | list | u | 1 | pass | - | MiniCPM4 adopts a modified version of Group Relative Policy Optimization (GRPO) and incorporates Dynamic Sampling During the RL rollout phase, which f |
| 040 | table | u,u | 1 | pass | - | In Table 5, the Chunk-4k strategy achieved the best performance for AIME 2024 with a score of 32.71, and for AIME 2025 with a score of 26.04 [S1]. |
| 041 | reasonin | a | - | pass | - | When the chunk size is reduced from 8k to 4k, although the sampling time per step is reduced, the total training time per step remains largely unchang |
| 042 | list | u,u | 1 | pass | - | The training batch size for MiniCPM4 was set to 256, and the mini-batch size was 128 [S1]. A constant learning rate of 1e - 5 was used during training |
| 043 | mechanis | u,u | 1 | pass | - | BitCPM4 avoids training a ternary model from scratch by initializing the ternary model with a pre-trained high-precision checkpoint [S1, S2]. This app |
| 044 | multi-ho | u,u,u | 1 | pass | - | The number of tokens required for BitCPM4 is only 10% of the number of tokens required for BitNet-2B [S1]. |
| 046 | mechanis | a,u | 1 | pass | - | FR-Spec speeds up drafting by optimizing draft candidate selection through strategic vocabulary space compression [S2]. It achieves this by restrictin |
| 047 | mechanis | u,a | 3 | pass | - | P-GPTQ is an extension of the GPTQ method [S3] that eliminates initial token interference during Hessian computation [S3]. It implements a position-aw |
| 048 | table | u | 1 | pass | - | S-P-GPTQ exhibits the smallest performance degradation compared to the FP16 baseline [S2]. |
| 050 | reasonin | u | 1 | pass | - | When using EAGLE-2 with W4A16 target models (such as the model quantized by GPTQ (Frantar et al., 2023)), the drafting process should use fewer draft  |
| 051 | list | u | 1 | pass | - | ArkInfer integrates with native inference frameworks for diverse platforms, including MediaTek, Nvidia, Qualcomm, and Rockchip [S1]. The specific nati |
| 053 | list | a,a | - | pass | - | The pre-training of MiniCPM4 follows a four-stage pipeline [S1]. This pipeline begins with a stable pre-training stage using 7 trillion tokens with a  |
| 054 | table | a,a | - | pass | - | Table 8 provides evaluation results for MiniCPM4 and other open-source LLMs [S1]. Based on the 'Average' row in Table 8 [S3], MiniCPM4 has an average  |
| 056 | table | a | - | flag: no verified quote from cited source(s) [ | - | MiniCPM4-0.5B has been compared against several models with approximately 1 billion parameters, such as Qwen3-0.5B, Llama3.2-1B, and Gemma3-1B [S1]. F |
| 058 | factual | a | - | pass | - | MiniCPM4 was trained with a context length of 4K in initial stages [S1], and later extended to 32K [S1, S4]. Despite only being trained in 32K context |
| 059 | numeric | u | 1 | pass | - | The devices used for the efficiency evaluation were Jetson AGX Orin and RTX 4090 [S1]. Compared to Qwen3-8B, MiniCPM4 achieves approximately 7x decodi |
| 061 | numeric | u,u | 1 | pass | - | MiniCPM4-Survey used approximately 2.71 million paper abstracts from Kaggle 7 as foundational data [S1]. The efficient retrieval index was built using |
| 064 | table | a,u | 1 | pass | - | MiniCPM4-Survey achieves performance comparable to OpenAI Deep Research in content-related metrics [S2]. Specifically, in Table 12, OpenAI Deep Resear |
| 065 | list | a,u | 1 | pass | - | The MCP training data was constructed through three main parts: data generation, reverse data generation, and the conversion of existing function call |
| 067 | table | a | - | pass | - | The average MCP tool-call accuracies in Table 13 are: GPT-4o - func: 80.2, GPT-4o - param: 70.2, GPT-4o - p_v: 49.1, Qwen3 8B - func: 83.5, Qwen3 8B - |
| 070 | conflict | u,u,u | 1 | pass | - | The paper presents three applications based on MiniCPM4: Trustworthy Survey Generation, Tool Use with Model Context Protocol, and one other applicatio |
| 072 | conflict | u,u,u | 1 | pass | - | MiniCPM4-8B was trained on 8.3T high-quality tokens [S1]. The training process involved allocating 7T tokens for the warmup and stable phases and 1.3T |
| 073 | conflict | u,u | 1 | pass | - | On 128K context, the sparsity of MiniCPM4 is only 5% [S1]. |
| 074 | conflict | a,u | 2 | pass | - | UltraFineWeb-zh improves CMMLU by 3.65pp over Chinese FineWeb-edu-v2 [S2]. Table 2 shows the CMMLU scores as 32.41 for Chinese-FineWeb, 34.93+2.52 for |
| 075 | multi-ho | u,a | 1 | flag: no verified quote from cited source(s) [ | - | Yes, BitCPM4-0.5B outperforms qwen3-0.6B on knowledge-related tasks such as MMLU, CMMLU, and C-EVAL [S1]. Specifically, in the comparison table, BitCP |
| 077 | multi-ho | u,u | 2 | pass | - | RL led to enhancements in Coverage, Depth, and Novelty for MiniCPM4-Survey [S1]. However, even with these improvements, MiniCPM4-Survey still trails s |
| 078 | conflict | a,a | - | pass | - | The 0.5B baseline model selected for MiniCPM4-0.5B is Qwen3-0.5B [S5]. |
| 080 | multi-ho | u,u | 1 | pass | - | The provided sources mention different numbers for rollouts per query or sample. Specifically, one source states that "For each query, we generate 16  |
| 084 | partial | a | - | flag: Unsupported sentence in answer (9 of 17  | - | The provided sources contain Table 13, which shows the MCP tool use accuracy (%) for different models across various MCP servers, but they do not spec |
| 085 | partial | u,u | 3 | refused | - | I don't know based on the provided sources. |
| 086 | partial | a | - | pass | - | The provided sources mention the amount of tokens used for pre-training MiniCPM4-8B (e.g., 8.3T high-quality tokens [S5], 8 trillion training tokens [ |
| 087 | unanswer | - | - | pass | - | The provided sources mention evaluation on end-side chips such as Jetson AGX Orin and RTX 4090 [S3], and that MiniCPM4 is available in versions with 0 |
| 089 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
| 091 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
