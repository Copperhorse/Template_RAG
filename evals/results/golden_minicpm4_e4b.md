# Golden QA evaluation: gemma4-e4b

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
- delivered (answered and passed the gates): 94% (75/80)
- contains every required fact: 0% (0/80)
- contains every required fact **and** delivered: 0% (0/80)
- mean share of required facts present: 0.00 (over the 0 questions that list facts)
- mean item recall over the 9 list questions that name their items: 0.89
- a verified quote comes from an evidence chunk: 74% (59/80)
- correct among flagged answers (false alarms): 0% (0/5)

## 4. Unanswerable questions (right behaviour: refuse)

- refused: 60% (3/5)
- answered but flagged: 20% (1/5)
- answered and passed the gates (the dangerous case): 20% (1/5)

## 4b. Partially answerable (the right reply cites what exists and says what the source does not give)

- refused outright (a fail: the part that exists should be given): 50% (3/6)
- answered and passed the gates: 50% (3/6)
- answered and flagged: 0% (0/6)
- whether a reply states what is missing needs reading; see section 6.

## 5. By question type (answerable)

| type | n | evidence in top-k | delivered | every fact | delivered and every fact |
|---|---:|---:|---:|---:|---:|
| comparison | 2 | 2 | 2 | 0 | 0 |
| conflict | 8 | 7 | 8 | 0 | 0 |
| factual | 9 | 7 | 9 | 0 | 0 |
| list | 17 | 12 | 17 | 0 | 0 |
| mechanism | 15 | 14 | 15 | 0 | 0 |
| multi-hop | 5 | 5 | 4 | 0 | 0 |
| numeric | 6 | 6 | 6 | 0 | 0 |
| reasoning | 6 | 5 | 6 | 0 | 0 |
| table | 12 | 4 | 8 | 0 | 0 |

## 6. Every question

| id | type | ev. | rank | outcome | facts | answer |
|---|---|---|---|---|---|---|
| 001 | factual | u,u | - | pass | - | MiniCPM4 is available in two parameter versions: 0.5B and 8B, each having general and deep inference variants [S1]. MiniCPM4.1 is a hybrid reasoning m |
| 002 | list | u | 1 | pass | - | MiniCPM4 innovates in four key dimensions: model architecture, training data, training algorithms, and inference systems [S1]. For model architecture, |
| 003 | numeric | u | 4 | pass | - | MiniCPM4-8B uses 8 trillion tokens, which is 22% of the 36 trillion tokens used to train Qwen3-8B [S1, S3, S4]. |
| 004 | numeric | u | 1 | pass | - | InfLLM v2 enables MiniCPM4 to achieve comparable long-context processing ability with the full attention mechanism with 81% attention sparsity [S1]. |
| 005 | reasonin | u | 1 | pass | - | MoBA utilizes the design of query blocks, which prevents it from achieving acceleration during the decoding phase [S1]. |
| 006 | list | u,a | 1 | pass | - | NSA introduces three different attention components to capture long-distance information, and these components introduce additional parameters, which  |
| 007 | numeric | u | 1 | pass | - | InfLLM v2's efficient Top-K context block selection method can reduce 60% computational costs compared with NSA [S1]. |
| 008 | mechanis | u | 1 | pass | - | The sparse attention computation of InfLLM v2 has two stages [S1]. In the first stage, the system dynamically selects relevant blocks from B based on  |
| 009 | mechanis | u,u | 1 | pass | - | InfLLM v2 computes the relevance score between a query token $q_i$ and a semantic kernel using the formula $rkernel(q_i, S_j) = softmax(q_i \cdot Mean |
| 010 | factual | a,u | 1 | pass | - | InfLLM v2 sets the relevance scores between each query token qi and the initial key-value blocks B0 and local window blocks to infinity, which ensures |
| 011 | mechanis | u | 1 | pass | - | In InfLLM v2, query heads within the same group are required to share the same top-k relevant blocks to minimize memory access [S1], [S5]. |
| 012 | mechanis | u,a | 1 | pass | - | Top-K selection requires two passes of memory access and computation on semantic kernels because relevance computation, softmax normalization, and sco |
| 013 | reasonin | u | 1 | pass | - | In InfLLM v2, the computational unit for queries is token-level, while the computational unit for key-values is block-level, allowing each query token |
| 014 | reasonin | u,u | 2 | pass | - | InfLLM v2 uses mean pooling because it is a parameter-free operation used to construct the representation of semantic kernels [S2]. Furthermore, mean  |
| 015 | numeric | u,u | 1 | pass | - | InfLLM v2 set the kernel size to 32 and the stride to 16 to balance effectiveness and efficiency [S1]. Furthermore, a query group must contain at leas |
| 016 | table | a | - | flag: no verified quote from cited source(s) [ | - | Training 100B tokens from scratch requires 1,200 GPU hours, whereas UltraClean's efficient verification strategy requires approximately 110 GPU hours  |
| 017 | mechanis | u,u | 1 | pass | - | The efficient verification strategy works by leveraging a nearly-trained LLM as a foundation, instead of verifying data quality by training LLMs from  |
| 018 | list | u | 1 | pass | - | The positive seeds for the quality classifier included high-quality in-domain data with LLM scores above 4, instruction-formatted datasets such as OH- |
| 019 | list | u | 1 | pass | - | Negative samples for the classifier are constructed using raw data from diverse sources [S1]. Specifically, English negative samples are taken from Fi |
| 020 | comparis | u | 2 | pass | - | A fastText-based classifier is adopted because LLM-based classifiers incur significantly higher inference costs [S1]. Using fastText drastically reduc |
| 021 | list | u | 1 | pass | - | The hyperparameters configured for the fastText classifier for training are: the vector dimension is set to 256, the learning rate is set to 0.1, the  |
| 022 | table | a | - | pass | - | The average score for UltraFineWeb-en is 45.89+3.613 [S1], which is 3.61pp higher than FineWeb's average score of 42.287pp [S2] and 1.3pp higher than  |
| 023 | table | a | - | pass | - | The provided sources indicate that UltraFineWeb-en outperforms FineWeb in the English metrics listed, with the only mention of a slight drop being in  |
| 024 | list | u | 1 | pass | - | The reasoning-data pipeline synthesizes two typical paradigms of knowledge construction: textbook and forum [S1]. |
| 025 | factual | u | 1 | pass | - | Open-source LLMs under 10B parameters are used to automatically edit and restructure web text as part of the structured data curation and generation m |
| 026 | mechanis | a,u | 2 | pass | - | ScalingBench is constructed from the validation datasets of downstream tasks [S1]. To build it, GPT-4o (OpenAI, 2023) is used to generate reasoning st |
| 027 | comparis | a,u | 1 | pass | - | The comparison between µP and StepLaw for hyperparameter search showed that while StepLaw demonstrated slightly more instances of advantage, the diffe |
| 028 | list | a | - | pass | - | The authors attribute the comparable effectiveness of hyperparameter search in the µP framework to steplaw under their experimental conditions to thre |
| 029 | mechanis | a,u | - | pass | - | The multi-token prediction (MTP) utilizes additional prediction heads, which are a one-layer Transformer (Vaswani et al., 2017) that shares embedding  |
| 030 | mechanis | a,u | 1 | pass | - | FP8 mix-precision is adopted in training because NVIDIA's Tensor Core GPUs have powerful FP8 computing capabilities [S1]. The application involves usi |
| 031 | list | u | 2 | pass | - | UltraChat v2 covers five key skill areas: knowledge applications, reasoning, instruction following, long-context processing, and tool use [S2]. |
| 032 | mechanis | u | 1 | pass | - | Long-context supervised fine-tuning data is constructed from existing pretraining corpora [S1]. For a document $d$ sampled from the corpus, an LLM gen |
| 033 | factual | u | 1 | pass | - | An in-house code-interpreter data point is discarded if the model fails to solve the problem within 10 attempts [S1]. |
| 034 | factual | u | 1 | pass | - | For the function calling dataset, strict filtering criteria are applied to ensure data quality, which includes removing samples where the tool used in |
| 035 | mechanis | u,u | 1 | pass | - | For mathematics, outputs that do not match the expected reasoning format receive a reward of zero, and correctness is determined using a combination o |
| 036 | factual | u | 1 | pass | - | Difficulty-based stratification is implemented to actively reduce the proportion of easy questions during training [S2]. |
| 037 | list | u | 1 | pass | - | MiniCPM4 adopts a modified version of Group Relative Policy Optimization (GRPO) [S1], incorporating Dynamic Sampling During the RL rollout phase, whic |
| 038 | mechanis | u,u | 1 | pass | - | The chunk-wise rollout strategy operates in three steps to manage lengthy trajectories and maximize computational resource utilization [S1]. First, th |
| 039 | list | a | - | pass | - | Techniques introduced to stabilize the chunk-wise rollout include chunk-level importance sampling to account for distributional differences across mul |
| 040 | table | u,u | 1 | pass | - | Based on the performance metrics in Table 5, the Chunk-4k strategy achieved the best performance for AIME 2024 with a score of 32.71, and the best per |
| 041 | reasonin | a | - | pass | - | When the chunk size is reduced from 8k to 4k, although the sampling time per step is reduced, the total training time per step stays largely the same  |
| 042 | list | u,u | 1 | pass | - | For MiniCPM4, the training batch size is set to 256 and the mini-batch size is 128 [S1]. A constant learning rate of 1e - 5 is used during training [S |
| 043 | mechanis | u,u | 1 | pass | - | BitCPM4 avoids training a ternary model from scratch by initializing the ternary model with a pre-trained high-precision checkpoint to decrease the ne |
| 044 | multi-ho | u,u,u | 1 | pass | - | The number of tokens required for BitCPM4 is only 10% of that required for BitNet-2B [S1]. |
| 045 | table | a,a | - | pass | - | BitCPM4 requires only 10% of the tokens needed for BitNet-2B, which suggests that the proposed QAT method can achieve competitive results with lower t |
| 046 | mechanis | a,u | 1 | pass | - | FR-Spec speeds up drafting by optimizing draft candidate selection through strategic vocabulary space compression [S2]. It achieves this by restrictin |
| 047 | mechanis | u,a | 3 | pass | - | P-GPTQ is an extension of the GPTQ method that eliminates initial token interference during Hessian computation [S3]. It implements a position-aware c |
| 048 | table | u | 1 | pass | - | S-P-GPTQ exhibits the smallest performance degradation compared to the FP16 baseline [S2]. |
| 049 | reasonin | u | 1 | pass | - | The EAGLE-2 draft model was changed to use QAT instead of GPTQ because QSpec (Zhao et al., 2024) found that using GPTQ on EAGLE-2 would result in a su |
| 050 | reasonin | u | 1 | pass | - | When using EAGLE-2 with W4A16 target models (such as the model quantized by GPTQ (Frantar et al., 2023)), the drafting process should use fewer draft  |
| 051 | list | u | 1 | pass | - | ArkInfer integrates with diverse platforms including MediaTek, Nvidia, Qualcomm, and Rockchip [S1]. The native inference frameworks it integrates as a |
| 052 | factual | u,u | 1 | pass | - | ArkInfer uses the BiTA algorithm for its advanced speculative decoding mechanism [S1], and it employs the Guidance algorithm for its constrained decod |
| 053 | list | a,a | - | pass | - | The pre-training of MiniCPM4 follows a four-stage pipeline [S1]. This pipeline begins with a stable pre-training stage using 7 trillion tokens and a l |
| 054 | table | a,a | - | flag: Unsupported sentence in answer (8 of 14  | - | Table 8 provides evaluation results for MiniCPM4 and other open-source LLMs [S1]. Based on the 'Average' row in Table 8 [S3], MiniCPM4 has an average  |
| 055 | table | a,a | - | flag: Unsupported sentence in answer (12 of 19 | - | The provided tables do not contain a direct comparison between Qwen3-8B and MiniCPM4-8B across all benchmarks in a single, easily comparable format, a |
| 056 | table | a | - | pass | - | MiniCPM4-0.5B achieves superior performance when compared to Llama3.2-1B and Gemma3-1B, even though those models have twice the parameter scale of Min |
| 057 | table | u,u | 1 | flag: Unsupported sentence in answer (11 of 16 | - | The weighted average for MiniCPM4.1 (Full) on RULER (32K) is 88.93 [S1]. The weighted average for MiniCPM4.1 (Sparse) on RULER (32K) is 85.84 [S1]. Th |
| 058 | factual | a | - | pass | - | MiniCPM4 was trained with a context length of 4K in initial stages [S1], and later extended to 32K [S1, S4]. Despite only being trained in 32K context |
| 059 | numeric | u | 1 | pass | - | The devices used for the efficiency evaluation were Jetson AGX Orin and RTX 4090 [S1]. Compared to Qwen3-8B, an approximate 7x decoding acceleration w |
| 060 | list | a | - | pass | - | MiniCPM4-Survey operates in a Plan-Retrieve-Write manner, which consists of three core stages: (1) Planning, which defines the overall structure of th |
| 061 | numeric | u,u | 1 | pass | - | MiniCPM4-Survey used approximately 2.71 million paper abstracts from Kaggle 7 as foundational data [S1]. The efficient retrieval index was built using |
| 062 | list | a | - | pass | - | The context manager in the RL process has three essential functionalities: Prompt Updating, which dynamically adjusts prompts based on historical inte |
| 063 | factual | u,u | 1 | pass | - | MiniCPM4-Survey is evaluated using several metrics to assess the quality of model-generated surveys [S1]. These metrics include: Relevance, which chec |
| 064 | table | a,u | 1 | pass | - | MiniCPM4-Survey achieves performance comparable to OpenAI Deep Research in content-related metrics [S2]. Specifically, in Table 12, OpenAI Deep Resear |
| 065 | list | a,u | 1 | pass | - | The MCP training data construction involved three main parts: data generation, reverse data generation, and converting existing function call datasets |
| 066 | mechanis | u,u | 1 | pass | - | A tool quality inspection mechanism was incorporated into the client to screen out unreliable MCP servers [S1]. This mechanism prompts Claude-4 to gen |
| 067 | table | a | - | pass | - | The average MCP tool-call accuracies in Table 13 are: 80.2% for GPT-4o - func, 70.2% for GPT-4o - param, 49.1% for GPT-4o - p_v, 83.5% for Qwen3 8B -  |
| 068 | list | u | 1 | pass | - | The MiniCPM team plans to continually investigate efficient training and inference of LLMs [S1]. Specifically, future work includes devoting effort to |
| 069 | conflict | u,u | 1 | pass | - | MiniCPM4.1-8B achieves an overall average score of 79.93 [S2]. When comparing full attention to sparse attention, the full attention average is 79.93, |
| 070 | conflict | u,u,u | 1 | pass | - | The paper presents three applications based on MiniCPM4: trustworthy survey generation, tool use with model context protocol (MCP), and one other appl |
| 071 | conflict | u,u,a | 2 | pass | - | MiniCPM4 claims a 5× speedup for long-sequence processing [S1], and it also demonstrates a 7-fold speed improvement in processing 128K-length document |
| 072 | conflict | u,u,u | 1 | pass | - | MiniCPM4-8B was trained on 8.3T high-quality tokens [S1]. The training involved allocating 7T tokens for the warmup and stable phases and 1.3T tokens  |
| 073 | conflict | u,u | 1 | pass | - | On 128K context, the sparsity of MiniCPM4 is only 5% [S1]. |
| 074 | conflict | a,u | 2 | pass | - | UltraFineWeb-zh improves CMMLU by 3.65pp over Chinese FineWeb-edu-v2 [S2]. Table 2 shows the CMMLU scores as 32.41 for Chinese-FineWeb, 34.93+2.52 for |
| 075 | multi-ho | u,a | 1 | flag: Number 0 is in the sources, but not in a | - | Yes, BitCPM4-0.5B outperforms qwen3-0.6B on knowledge-related tasks such as MMLU, CMMLU, and C-EVAL [S1]. For MMLU, BitCPM4-0.5B has a score of 49.88, |
| 076 | multi-ho | a,u | 2 | pass | - | The paper states that Qwen3 appears less familiar with specialized tools such as arXiv [S1]. According to Table 13, for the Arxiv-MCP-Server, MiniCPM4 |
| 077 | multi-ho | u,u | 2 | pass | - | No, RL did not improve every MiniCPM4-Survey content metric; while enhancements were observed in Coverage, Depth, and Novelty, MiniCPM4-Survey still l |
| 078 | conflict | a,a | - | pass | - | The 0.5B baseline model selected for MiniCPM4-0.5B is Qwen3-0.5B [S5]. |
| 079 | conflict | u,u,u | 1 | pass | - | MiniCPM4 was trained to extend its context window to 32K [S1, S4], while another source states that long-context pre-training extended the context win |
| 080 | multi-ho | u,u | 1 | pass | - | For each query, 16 rollouts are generated in MiniCPM4 to promote diversity and robustness [S1]. |
| 081 | partial | u | - | pass | - | The provided sources show the formula for the Multi-Token Prediction loss ($\\mathcal { L } _ { M T P }$) as $\\mathcal { L } _ { M T P } = \frac { 1  |
| 082 | partial | a | - | pass | - | The 1B-parameter model, BitCPM4-1B, is trained based on the internal experimental model [S1]. |
| 083 | partial | u,u | 2 | refused | - | I don't know based on the provided sources. |
| 084 | partial | a | - | pass | - | The provided sources contain Table 13, which shows the MCP tool use accuracy (%), but they do not specify the number of test samples for each MCP serv |
| 085 | partial | u,u | 3 | refused | - | I don't know based on the provided sources. |
| 086 | partial | a | - | refused | - | I don't know based on the provided sources. |
| 087 | unanswer | - | - | pass | - | The provided sources mention that MiniCPM4 can achieve efficient computation on edge-side chips, and evaluation was conducted on the Jetson AGX Orin a |
| 088 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
| 089 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
| 090 | unanswer | - | - | flag: no verified quote from cited source(s) [ | - | MiniCPM4-8B's score on CMMLU is 80.62 [S3], and its score on MMLU is 75.83 [S3]. |
| 091 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
