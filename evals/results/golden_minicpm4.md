# Golden QA evaluation: minicpm4

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

- answered (did not refuse): 99% (79/80)
- delivered (answered and passed the gates): 86% (69/80)
- contains every required fact: 0% (0/80)
- contains every required fact **and** delivered: 0% (0/80)
- mean share of required facts present: 0.00 (over the 0 questions that list facts)
- mean item recall over the 9 list questions that name their items: 0.89
- a verified quote comes from an evidence chunk: 69% (55/80)
- correct among flagged answers (false alarms): 0% (0/10)

## 4. Unanswerable questions (right behaviour: refuse)

- refused: 60% (3/5)
- answered but flagged: 40% (2/5)
- answered and passed the gates (the dangerous case): 0% (0/5)

## 4b. Partially answerable (the right reply cites what exists and says what the source does not give)

- refused outright (a fail: the part that exists should be given): 67% (4/6)
- answered and passed the gates: 17% (1/6)
- answered and flagged: 17% (1/6)
- whether a reply states what is missing needs reading; see section 6.

## 5. By question type (answerable)

| type | n | evidence in top-k | delivered | every fact | delivered and every fact |
|---|---:|---:|---:|---:|---:|
| comparison | 2 | 2 | 2 | 0 | 0 |
| conflict | 8 | 7 | 7 | 0 | 0 |
| factual | 9 | 7 | 9 | 0 | 0 |
| list | 17 | 12 | 16 | 0 | 0 |
| mechanism | 15 | 14 | 13 | 0 | 0 |
| multi-hop | 5 | 5 | 3 | 0 | 0 |
| numeric | 6 | 6 | 6 | 0 | 0 |
| reasoning | 6 | 5 | 6 | 0 | 0 |
| table | 12 | 4 | 7 | 0 | 0 |

## 6. Every question

| id | type | ev. | rank | outcome | facts | answer |
|---|---|---|---|---|---|---|
| 001 | factual | u,u | - | pass | - | MiniCPM4 comes in two parameter versions: 0.5B and 8B, each with general and deep inference variants [S1]. MiniCPM4.1 is a hybrid model that is traine |
| 002 | list | u | 1 | flag: Unsupported number in answer: [3] | - | MiniCPM4 innovates on four key dimensions: model architecture, training data, training algorithms, and inference systems. The main techniques in each  |
| 003 | numeric | u | 4 | pass | - | MiniCPM4-8B uses 8 trillion tokens for pre-training, which is 22% of the 36 trillion tokens used for Qwen3-8B's training data scale [S4, S3]. |
| 004 | numeric | u | 1 | pass | - | InfLLM v2 enables MiniCPM4 to achieve comparable long-context processing ability with the full attention mechanism with 81% attention sparsity [S1]. |
| 005 | reasonin | u | 1 | pass | - | MoBA cannot accelerate decoding because it uses the design of query blocks, which prevents it from achieving acceleration during the decoding phase [S |
| 006 | list | u,a | 1 | pass | - | NSA introduces three different attention components to capture long-distance information, which results in increased computational overhead for short  |
| 007 | numeric | u | 1 | pass | - | InfLLM v2's Top-K context block selection method can reduce computational costs by 60% compared to NSA [S1]. |
| 008 | mechanis | u | 1 | flag: the answer cites no source | - | The sparse attention computation of InfLLM v2 consists of two stages: in the first stage, relevant blocks are dynamically selected from B based on the |
| 009 | mechanis | u,u | 1 | pass | - | InfLLM v2 computes the relevance score between a query token and a key-value block, denoted as rblock(qi,Bj), and then selects the k blocks with the h |
| 010 | factual | a,u | 1 | pass | - | InfLLM v2 sets the relevance scores between each query token qi and the initial key-value blocks B0 and local window blocks to infinity, which allows  |
| 011 | mechanis | u | 1 | pass | - | In InfLLM v2, query heads within the same group are required to share the same top-k relevant blocks to minimize memory access [S1]. |
| 012 | mechanis | u,a | 1 | pass | - | Top-K selection requires two passes because relevance computation, softmax normalization, and score aggregation across the query group dimension do no |
| 013 | reasonin | u | 1 | pass | - | In InfLLM v2, the computational unit for queries is token-level, while the computational unit for key-values is block-level [S2]. |
| 014 | reasonin | u,u | 2 | pass | - | InfLLM v2 uses mean pooling because it is a parameter-free operation, and it ensures that the representation of semantic kernels remains in the same s |
| 015 | numeric | u,u | 1 | pass | - | InfLLM v2 chose a kernel size of 32 and a stride of 16 [S1]. Furthermore, a query group must contain at least 16 heads to ensure hardware is fully uti |
| 016 | table | a | - | pass | - | The efficient verification strategy reduces training time from approximately 1,200 GPU hours (for training 100B tokens on an LLM with 1B parameters) t |
| 017 | mechanis | u,u | 1 | pass | - | The efficient verification strategy is designed to rapidly evaluate the actual impact of data on LLM training at minimal computational costs [S3]. It  |
| 018 | list | u | 1 | pass | - | The positive seeds for the quality classifier included high-quality in-domain data with LLM scores above 4, instruction-formatted datasets such as OH- |
| 019 | list | u | 1 | pass | - | Negative samples are constructed using raw data from diverse sources [S1]. Specifically, English negative samples are drawn from FineWeb, C4, Dolma, T |
| 020 | comparis | u | 2 | pass | - | A fastText-based classifier is adopted instead of an LLM-based classifier to drastically reduce inference overhead while maintaining competitive perfo |
| 021 | list | u | 1 | pass | - | The fastText classifier's hyperparameters include a vector dimension set to 256, a learning rate set to 0.1, a maximum n-gram length set to 3, a minim |
| 022 | table | a | - | pass | - | The English average score for UltraFineWeb-en is 45.891pp, which is 3.61pp higher than that of FineWeb (42.287pp) and 1.3pp higher than that of FineWe |
| 023 | table | a | - | pass | - | UltraFineWeb-en has a slight drop of 0.15 percentage points (pp) in HellaSwag compared to FineWeb [S2]. |
| 024 | list | u | 1 | pass | - | The reasoning-data pipeline synthesizes two typical paradigms of knowledge construction: the textbook paradigm and the forum paradigm [S1]. |
| 025 | factual | u | 1 | pass | - | Open-source LLMs under 10B parameters are used to automatically edit and restructure web text in the structured data curation and generation mechanism |
| 026 | mechanis | a,u | 2 | pass | - | ScalingBench is constructed from the validation datasets of downstream tasks [S1]. In ScalingBench, GPT-4o (OpenAI, 2023) is used to generate reasonin |
| 027 | comparis | a,u | 1 | pass | - | The text indicates that steplaw demonstrates slightly more instances of advantage, but the differences in both loss values and scalingbench scores bet |
| 028 | list | a | - | pass | - | The comparable effectiveness of hyperparameter search in the µP framework under the experimental conditions is attributed to several factors, includin |
| 029 | mechanis | a,u | - | flag: no verified quote from cited source(s) [ | - | The multi-token prediction (MTP) requires the LLM to output multiple tokens with additional prediction heads, which are a one-layer Transformer with e |
| 030 | mechanis | a,u | 1 | pass | - | For FP8 mix-precision training in MiniCPM4, online block-wise FP8 quantization is applied to both parameters and activations, using a block size of 12 |
| 031 | list | u | 2 | pass | - | UltraChat v2 covers five key skill areas: knowledge applications, reasoning, instruction following, long-context processing, and tool use [S2]. |
| 032 | mechanis | u | 1 | pass | - | Long-context supervised fine-tuning data is constructed by sampling a document $d$ from various sources in the pretraining corpus, such as web pages,  |
| 033 | factual | u | 1 | pass | - | An in-house code-interpreter example is discarded if the model fails to solve the problem within 10 attempts [S1]. |
| 034 | factual | u | 1 | pass | - | Function-calling samples are filtered by removing those where the tool invoked in the ground truth is not in the available tool set, or where the para |
| 035 | mechanis | u,u | 1 | pass | - | For math data, outputs that do not conform to the expected reasoning format are assigned a reward of zero during the evaluation phase [S1]. For code d |
| 036 | factual | u | 1 | pass | - | In the RL rollout phase, prompts whose responses are all correct or all wrong are filtered out to ensure that all prompts in the batch contribute effe |
| 037 | list | u | 1 | pass | - | MiniCPM4 adopts a modified version of Group Relative Policy Optimization (GRPO) (Shao et al., 2024b) and incorporates the following improvements: Dyna |
| 038 | mechanis | u,u | 1 | pass | - | The chunk-wise rollout strategy involves three steps: (1) the policy model generates trajectories of a fixed chunk length for all input samples; (2) t |
| 039 | list | a | - | pass | - | Techniques that stabilize chunk-wise rollout include chunk-level importance sampling to account for distributional differences across policy model ver |
| 040 | table | u,u | 1 | pass | - | Chunk-8k performed best in the performance - AIME 2025 metric with a value of 26.67 [S1]. |
| 041 | reasonin | a | - | pass | - | The total training time per step remains largely unchanged when reducing the chunk size from 8k to 4k because the smaller chunk size introduces more f |
| 042 | list | u,u | 1 | pass | - | For the rollout phase, both the temperature and top-p are set to 1.0 to encourage broader exploration [S1]. Additionally, a chunk-wise rollout strateg |
| 043 | mechanis | u,u | 1 | pass | - | BitCPM4 avoids training a ternary model from scratch by initializing the ternary model with a pre-trained high-precision checkpoint, which reduces the |
| 044 | multi-ho | u,u,u | 1 | pass | - | The number of tokens required for BitCPM4 is only 10% of that for BitNet-2B [S1]. |
| 045 | table | a,a | - | flag: no verified quote from cited source(s) [ | - | BitCPM4-1B performs similarly to competing 2B-parameter models [S3]. |
| 046 | mechanis | a,u | 1 | pass | - | FR-Spec speeds up drafting by restricting the draft search to a frequency-prioritized subset of tokens, which reduces the computational overhead of th |
| 047 | mechanis | u,a | 3 | pass | - | P-GPTQ is an extension of the GPTQ method that eliminates initial token interference during Hessian computation [S3]. |
| 048 | table | u | 1 | pass | - | S-P-GPTQ achieves superior performance among quantized methods, exhibiting the smallest performance degradation compared to the FP16 baseline [S2]. |
| 049 | reasonin | u | 1 | pass | - | The EAGLE-2 draft model is changed to use QAT instead of GPTQ because QSpec (Zhao et al., 2024) found that using GPTQ on EAGLE-2 would cause a substan |
| 050 | reasonin | u | 1 | pass | - | When using EAGLE-2 with W4A16 target models (such as the model quantized by GPTQ (Frantar et al., 2023)), the drafting process should use fewer draft  |
| 051 | list | u | 1 | pass | - | ArkInfer integrates support for diverse platforms such as MediaTek, Nvidia, Qualcomm, and Rockchip, which have native inference frameworks including N |
| 052 | factual | u,u | 1 | pass | - | ArkInfer uses an advanced speculative decoding mechanism based on the BiTA algorithm [S1] and a constrained decoding method leveraging the Guidance al |
| 053 | list | a,a | - | pass | - | MiniCPM4's pre-training pipeline involves a four-stage process [S1]. This includes a stable pre-training stage using 7 trillion tokens with a learning |
| 054 | table | a,a | - | flag: no verified quote from cited source(s) [ | - | Table 8 shows the following average scores for the specified models: MiniCPM4-8B has a CMMLU score of 80.62 [S1], Qwen3-8B has a CMMLU score of 77.58  |
| 055 | table | a,a | - | refused | - | The provided sources do not contain information on which Table 8 benchmarks Qwen3-8B beats MiniCPM4-8B. |
| 056 | table | a | - | pass | - | MiniCPM4-0.5B achieves superior performance compared to Llama3.2-1B and Gemma3-1B, even though these models have twice the parameter scale of MiniCPM4 |
| 057 | table | u,u | 1 | flag: no verified quote from cited source(s) [ | - | MiniCPM4.1's RULER (32K) weighted averages are 88.93% for the full attention variant and 85.84% for the sparse attention variant [S1]. The sparse atte |
| 058 | factual | a | - | pass | - | MiniCPM4 was initially trained with a context length of 4K [S1]. However, the context window was extended to 128K using YaRN [S2, S4]. |
| 059 | numeric | u | 1 | pass | - | The efficiency evaluation was conducted on two typical end-side chips: Jetson AGX Orin and RTX 4090 [S1]. Compared to Qwen3-8B, MiniCPM4 achieved appr |
| 060 | list | a | - | pass | - | The three core stages of MiniCPM4-Survey are Planning, Retrieval, and Writing [S1]. |
| 061 | numeric | u,u | 1 | pass | - | MiniCPM4-Survey uses approximately 2.71 million paper abstracts from Kaggle 7 as foundational data [S1]. It also builds an efficient retrieval index u |
| 062 | list | a | - | pass | - | The context manager in the reinforcement learning process has three essential functionalities: Prompt Updating, which dynamically adjusts prompts base |
| 063 | factual | u,u | 1 | pass | - | MiniCPM4-Survey is evaluated using four metrics to assess the quality of model-generated surveys: Relevance, which checks if the survey maintains clea |
| 064 | table | a,u | 1 | pass | - | The proposed method, which includes MiniCPM4-Survey, achieves performance comparable to OpenAI Deep Research, indicating its effectiveness and competi |
| 065 | list | a,u | 1 | pass | - | MCP training data construction involves three main parts: data generation, reverse data generation, and the conversion of existing function call datas |
| 066 | mechanis | u,u | 1 | pass | - | A tool quality inspection mechanism is incorporated into the client to address issues with independently deployed community MCP servers that may lack  |
| 067 | table | a | - | flag: no verified quote from cited source(s) [ | - | The average MCP tool-call accuracies are provided in Table 13, which shows sample-weighted average accuracy across the MCP servers [S1, S2, S3]. |
| 068 | list | u | 1 | pass | - | The MiniCPM4 team plans to continually investigate efficient training and inference of LLMs [S1]. Specifically, their future work includes: in model a |
| 069 | conflict | u,u | 1 | pass | - | MiniCPM4.1-8B achieves an overall average score of 79.93, with a full attention average of 79.93 and a sparse attention average of 79.14 [S2]. |
| 070 | conflict | u,u,u | 1 | pass | - | The paper presents three applications of MiniCPM4: trustworthy survey generation, tool use with model context protocol (MCP), and another application  |
| 071 | conflict | u,u,a | 2 | pass | - | MiniCPM4 can achieve a 5× speedup for long-sequence processing due to its efficient architecture and inference systems [S1]. Specifically, compared to |
| 072 | conflict | u,u,u | 1 | pass | - | MiniCPM4-8B was trained on 8.3T high-quality tokens [S1]. These tokens were allocated as 7T tokens for the warmup and stable phases and 1.3T tokens fo |
| 073 | conflict | u,u | 1 | pass | - | On a 128K context, the sparsity of MiniCPM4 is only 5% [S1]. |
| 074 | conflict | a,u | 2 | pass | - | UltraFineWeb-zh improves by 3.65pp over Chinese FineWeb-edu-v2 on CMMLU [S2]. |
| 075 | multi-ho | u,a | 1 | pass | - | Yes, at the 0.5B-parameter level, BitCPM4-0.5B outperforms qwen3-0.6B on knowledge-related tasks such as MMLU, CMMLU, and C-EVAL [S1]. |
| 076 | multi-ho | a,u | 2 | flag: no verified quote from cited source(s) [ | - | Yes, MiniCPM4-MCP performs better on the arXiv server. According to Table 13 in [S2], MiniCPM4-MCP has an accuracy of 57.1 for the Arxiv-MCP-Server, w |
| 077 | multi-ho | u,u | 2 | flag: the answer cites no source | - | RL improved Coverage, Depth, and Novelty for MiniCPM4-Survey, but it did not improve every content metric. |
| 078 | conflict | a,a | - | pass | - | The small Qwen3 model selected as a baseline for MiniCPM4-0.5B is Qwen3-0.5B [S5]. |
| 079 | conflict | u,u,u | 1 | flag: no verified quote from cited source(s) [ | - | MiniCPM4 was trained with a context length of 4K during the initial two pre-training stages [S1]. Subsequently, the context window was extended from 4 |
| 080 | multi-ho | u,u | 1 | pass | - | 16 rollouts per query are generated in MiniCPM4's RL to promote diversity and robustness [S1]. |
| 081 | partial | u | - | refused | - | The provided sources do not mention a weight $\lambda$ used for the multi-token-prediction loss. |
| 082 | partial | a | - | pass | - | The 1B-parameter BitCPM4 model is trained based on the internal experimental model [S1]. |
| 083 | partial | u,u | 2 | refused | - | The provided sources do not contain the exact prefilling and decoding tokens/s for MiniCPM4-8B on RTX 4090 at 128K. |
| 084 | partial | a | - | flag: the answer cites no source | - | The provided sources mention Table 13, which shows MCP tool use accuracy percentages, but they do not explicitly state the number of test samples for  |
| 085 | partial | u,u | 3 | refused | - | The provided sources do not specify the layer count, hidden size, or head configuration for MiniCPM4-0.5B and 8B. |
| 086 | partial | a | - | refused | - | The provided sources do not state the number of GPU hours required for MiniCPM4-8B pre-training. |
| 087 | unanswer | - | - | refused | - | The provided sources do not state how fast MiniCPM4 runs on an iPhone or Apple Silicon Mac. |
| 088 | unanswer | - | - | flag: no verified quote from cited source(s) [ | - | The model parameters and inference code of MiniCPM4 are released to facilitate the development of the open-source community [S1]. |
| 089 | unanswer | - | - | refused | - | The provided sources do not contain information about how MiniCPM4 scores on SWE-bench. |
| 090 | unanswer | - | - | flag: no verified quote from cited source(s) [ | - | The score for MiniCPM4 on the MMLU benchmark is 55.55 [S3]. |
| 091 | unanswer | - | - | refused | - | The provided sources do not state MiniCPM4's training cost in dollars. |
