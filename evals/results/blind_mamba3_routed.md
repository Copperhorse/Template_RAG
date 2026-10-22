# Golden QA evaluation: mamba3-routed

Golden file `/home/copper/Downloads/mamba3_golden_qa.jsonl` (60 questions: 50 answerable, 5 unanswerable, 5 partially answerable). Store: `/tmp/claude-1000/-home-copper-Git-Template-RAG/24d159d4-229a-4570-887a-d29472273e1a/scratchpad/blind_store` (992 chunks, 939 usable). LLM json_mode=`schema`, policy=`balanced`, k=5. 'Correct' = the answer contains the facts listed in the gold sidecar: a lower bound, read the answers below.

## 1. Ingestion: is the evidence in a usable chunk?

- usable: 68% (65/95)
- fuzzy-usable: 19% (18/95)
- rejected: 0% (0/95)
- split: 0% (0/95)
- absent: 13% (12/95)
- (fuzzy-usable: no exact match, but a chunk holds at least 80% of the quote's tokens; relevance below uses the same rule)
- questions with unreachable evidence: 006, 008, 014, 016, 020, 040, 046, 047, 048, 050

## 2. Retrieval (answerable questions and partially answerable ones)

- an evidence chunk in the top 5: 93% (51/55)
- evidence chunk ranked first: 71% (39/55)
- all of a question's evidence quotes covered by the top 5: 69% (38/55)

## 3. Answers

- answered (did not refuse): 96% (48/50)
- delivered (answered and passed the gates): 66% (33/50)
- contains every required fact: 0% (0/50)
- contains every required fact **and** delivered: 0% (0/50)
- mean share of required facts present: 0.00 (over the 0 questions that list facts)
- mean item recall over the 2 list questions that name their items: 0.58
- a verified quote comes from an evidence chunk: 72% (36/50)
- correct among flagged answers (false alarms): 0% (0/15)

## 4. Unanswerable questions (right behaviour: refuse)

- refused: 20% (1/5)
- answered but flagged: 60% (3/5)
- answered and passed the gates (the dangerous case): 20% (1/5)

## 4b. Partially answerable (the right reply cites what exists and says what the source does not give)

- refused outright (a fail: the part that exists should be given): 20% (1/5)
- answered and passed the gates: 60% (3/5)
- answered and flagged: 20% (1/5)
- whether a reply states what is missing needs reading; see section 6.

## 5. By question type (answerable)

| type | n | evidence in top-k | delivered | every fact | delivered and every fact |
|---|---:|---:|---:|---:|---:|
| comparison | 2 | 2 | 1 | 0 | 0 |
| conflict | 8 | 8 | 5 | 0 | 0 |
| definition | 4 | 4 | 3 | 0 | 0 |
| factual | 6 | 4 | 5 | 0 | 0 |
| list | 2 | 2 | 1 | 0 | 0 |
| mechanism | 7 | 7 | 6 | 0 | 0 |
| multi-hop | 2 | 2 | 0 | 0 | 0 |
| numeric | 6 | 5 | 6 | 0 | 0 |
| reasoning | 2 | 2 | 2 | 0 | 0 |
| table | 11 | 10 | 4 | 0 | 0 |

## 6. Every question

| id | type | ev. | rank | outcome | facts | answer |
|---|---|---|---|---|---|---|
| 001 | factual | u,u | 1 | pass | - | Mamba-3 targets the hardware inefficiency of existing linear (sub-quadratic) models, specifically their low arithmetic intensity during decoding, whic |
| 002 | list | u,u,u | 1 | flag: no verified quote from cited source(s) [ | - | Mamba-3's three core methodological changes over Mamba-2 are: 1) Exponential-Trapezoidal Discretization for more expressive dynamics [S1], 2) Complex- |
| 003 | definiti | u,u | 5 | pass | - | The 'exponential-Euler' discretization is described as stemming from exponential integration followed by Euler approximation [S1]. The paper introduce |
| 004 | definiti | f,f | 1 | pass | - | The exponential-trapezoidal rule generalizes the classical trapezoid rule (when λt = 1/2) and Mamba-2's Euler's rule (when λt = 1) [S1]. |
| 005 | definiti | f | 1 | refused | - | I don't know based on the provided sources. |
| 006 | numeric | a,u | 1 | pass | - | Euler's rule has a first-order local truncation error [S1], while the exponential-trapezoidal rule is second-order accurate [S1]. The caveat is that e |
| 007 | mechanis | u,f | 1 | pass | - | Exponential-trapezoidal discretization is an implicit convolution because it applies a width-2 convolution on the state-input v_t = B_t x_t before the |
| 008 | mechanis | u,a | 2 | pass | - | Mamba-3's SSD mask is a 1-semiseparable matrix composed with a 2-band matrix, generalizing Mamba-2's structure which instead has a diagonal matrix wit |
| 009 | reasonin | u,f | 1 | pass | - | Mamba-2 uses real, non-negative eigenvalue transitions, which cannot represent rotational hidden state dynamics. Parity, for example, requires a 2-D r |
| 010 | definiti | f | 1 | pass | - | A complex SSM of state dimension N/2 is equivalent to a real SSM with doubled state dimension N [S1]. |
| 011 | comparis | f | 2 | pass | - | Mamba-3's data-dependent RoPE uses rotation matrices that depend on the data, whereas vanilla RoPE uses data-independent rotation matrices with a fixe |
| 012 | numeric | u,u | 1 | pass | - | SSM decoding is hardware-inefficient because it is memory-bound, saturating memory bandwidth with idle compute [S1]. Its arithmetic intensity is aroun |
| 013 | mechanis | f | 2 | pass | - | The MIMO formulation raises arithmetic intensity by expanding the input and output dimensions via the rank 𝑅, transforming B𝑡 ∈ R𝑁 → B𝑡 ∈ R𝑁×𝑅 and x𝑡  |
| 014 | numeric | a,a | - | pass | - | For SISO, the arithmetic intensity is Θ(1) (approximately 2.5) [S1]. For MIMO, the arithmetic intensity is Θ(R) = Θ(4) [S1]. |
| 015 | mechanis | f,f | 1 | flag: no verified quote from cited source(s) [ | - | A MIMO SSM is trained by invoking the SISO SSM training algorithm R times as a black box in parallel [S2, S3]. The training cost scales by a factor of |
| 016 | mechanis | a,u | 1 | pass | - | Mamba-3 keeps the parameter count from multiplying by R by keeping the original SISO projection and element-wise scaling each dimension of the project |
| 017 | numeric | u | 1 | pass | - | The MLP inner dimension is reduced by 6.6%, from 4096 to 3824 [S1]. |
| 018 | list | u,u,u,u | 1 | pass | - | The Mamba-3 block modifies the recurrence layer by replacing the SSD layer with a more expressive complex-valued exponential-trapezoidal SSM [S1]. It  |
| 019 | factual | u | 4 | pass | - | The Mamba-3 default is the SISO variant [S4]. This is done to enable fair comparisons with other SISO-like models. |
| 020 | factual | a | - | pass | - | The language modeling comparison uses the Llama-3.1 tokenizer [S1] and is evaluated with LM Evaluation Harness [S1] on the tasks LAMBADA, HellaSwag, P |
| 021 | factual | u | 1 | pass | - | The hybrid model is constructed by interleaving linear layers and NoPE self-attention layers in a 5:1 ratio [S1]. For MiniCPM4.1, a hybrid reasoning m |
| 022 | mechanis | u,u | 1 | pass | - | State-tracking synthetics are trained using a sequence length curriculum that starts at a minimum length of 3 and progresses the maximum length from 4 |
| 023 | factual | u,u | 1 | pass | - | Mamba-3 uses Triton for the prefill (forward) path and CuTe for the decode path [S1]. The specific implementations are: Mamba-3 (SISO) uses a Triton k |
| 024 | mechanis | u | 1 | pass | - | The authors measured vLLM performance at sequence length 16384 with a batch size of 16, then scaled the result by a factor of 8 to approximate perform |
| 025 | reasonin | u,u | 1 | pass | - | The paper states that Mamba-3 is not obviously interpretable under associative-memory frameworks because complex-valued state transitions are meaningl |
| 026 | factual | u | - | refused | - | I don't know based on the provided sources. |
| 027 | comparis | u | 1 | flag: Unsupported sentence in answer (5 of 9 w | - | S5/LRU's MIMO was motivated to simplify training algorithms at the cost of slightly reduced expressivity [S4]. Mamba-3's MIMO is motivated to increase |
| 028 | table | u,u | 1 | pass | - | The average accuracies for the 1.5B models are 56.4 for Mamba-3-SISO-1.5B [S1] and 57.6 for Mamba-3-MIMO-1.5B [S1]. For the 880M models, they are 54.4 |
| 029 | multi-ho | u,u | 1 | flag: Unsupported sentence in answer (7 of 13  | - | The abstract's headline gains (0.6, 1.2, 1.8 points) are not directly confirmed by Table 3 in the provided sources. Table 3 reports test accuracy on t |
| 030 | table | u,u | 3 | flag: Unsupported number in answer: [43, 49, 5 | - | The MIMO-over-SISO average accuracy gain is 1.2 percentage points over SISO across all scales [S1]. For specific scales, the gains are: 1.5B: 57.6 vs  |
| 031 | numeric | u | 1 | pass | - | MIMO gives a perplexity gain of 0.11 at 1.5B [S1]. |
| 032 | table | u,u | 1 | flag: no verified quote from cited source(s) [ | - | On the Table 4 pure-model NIAH-Single-1 task at 4096 tokens, the Pure Mamba-2 model achieves 62.0 [S1], while the Pure Mamba-3 model achieves 100.0 [S |
| 033 | table | u,u | 1 | flag: Number 100.0 is in the sources, but not  | - | Mamba-3 does not lag in real-world retrieval on the NIAH tasks itself, as it scores 100.0 on all NIAH-Single-1, NIAH-Single-2, and NIAH-Single-3 varia |
| 034 | table | f | 4 | pass | - | Table 5a shows that the component ablations for Mamba-3 demonstrate that combining BC bias and exponential-trapezoidal discretization synergize well,  |
| 035 | table | u,u | 2 | pass | - | Mamba-3 solves parity and modular arithmetic without brackets, and nearly closes the accuracy gap on modular arithmetic with brackets [S1, S2]. |
| 036 | table | u,u | 1 | flag: no verified quote from cited source(s) [ | - | The decode kernel latency for Mamba-3 SISO at bf16, d_state = 128 is 0.203 [S1]. The latency for Mamba-2 at bf16, d_state = 128 is not provided in the |
| 037 | table | f,u | 1 | flag: Unsupported number in answer: [3, 11] | - | For 1024 tokens, Mamba-3 (MIMO 𝑅 = 4) has a Prefill+Decode latency of 18.96 ms, while Mamba-3 (SISO) has a Prefill+Decode latency of 17.57 ms, resulti |
| 038 | table | u | 1 | flag: Unsupported number in answer: [17, 20] | - | Based on the provided sources, linear models (specifically Mamba-3 variants) overtake vLLM Llama-3.2-1B on prefill+decode time at sequence lengths bey |
| 039 | numeric | f | 1 | pass | - | According to the paper, Mamba-3's MIMO training speed only incurs a slowdown of 2× when 𝑅 = 4 [S1]. |
| 040 | table | a | - | pass | - | The all-ones initialization is best in Table 10a [S1]. Performance is not very sensitive to the initialization as long as the biases are positive [S1] |
| 041 | table | f | 1 | flag: no verified quote from cited source(s) [ | - | The paper states that applying only the B bias hurts performance slightly, and that B and C biases have synergistic properties [S4]. It also notes tha |
| 042 | conflict | u,u,u | 2 | pass | - | Yes. The sources state that Mamba-3 SISO outperforms Mamba-2 and others at every model scale, and the MIMO variant with rank 𝑅 = 4 further improves mo |
| 043 | conflict | u,u | 1 | flag: no verified quote from cited source(s) [ | - | No. Table 6 reports kernel latency values for Mamba-3 (MIMO) at d_state = 64 as 0.179 ms and for Mamba-2 at d_state = 128 as 0.344 ms [S1]. The claim  |
| 044 | conflict | u,u,u | 1 | pass | - | Yes. SISO achieves the lowest latency among the configurations in Table 6 [S1], and its latency values (0.310, 0.399, 0.110, 0.156) are lower than tho |
| 045 | conflict | u,u | 1 | pass | - | Yes. According to the sources, Mamba-2 fails to learn state-tracking tasks such as parity and modular arithmetic, performing no better than random gue |
| 046 | conflict | u,u,a | 1 | pass | - | Yes. The sources state that adding pre-gate, grouped RMSNorm to Mamba-3 SISO hybrid models results in a 'slight decrease in real-world retrieval perfo |
| 047 | conflict | u,a,a | 2 | flag: no verified quote from cited source(s) [ | - | The perplexity of the default Mamba-3 (both biases, all-ones init) in the 440M ablations is 15.72 [S3]. This is consistent with the model trained at t |
| 048 | conflict | u,a | 1 | flag: no verified quote from cited source(s) [ | - | Yes. The default all-ones initialization gives the lowest perplexity (15.69) among the bias results, and the table in S2 shows 15.72 for all-ones with |
| 049 | conflict | u,u | 1 | pass | - | Table 6 [S1]. |
| 050 | multi-ho | f,a | 1 | flag: the answer cites no source | - | According to S3, when the MIMO chunk size is set to one rank 𝑅 times the SISO chunk size, the overall FLOP count increases by a factor of 𝑅, not 𝑅2. S |
| 051 | partial | u | 5 | pass | - | The 1.5B language models were pretrained with the AdamW optimizer [S3], a batch size of 768 [S3], and a small learning rate warmup of 2K iterations [S |
| 052 | partial | f | 1 | refused | - | The sources do not provide the exact perplexity values for Mamba-3 and Mamba-2 at each d_state in Figure 3. The sources describe the experiment setup  |
| 053 | partial | f | 1 | pass | - | The Mamba-3 kernels use a chunk size of 1𝑅 times the SISO chunk size, where 𝑅 = 4 for MIMO, making the MIMO chunk size 4 times the SISO chunk size [S1 |
| 054 | partial | f | 1 | pass | - | The hidden size (SISO MLP dim) for the 180M, 440M, and 880M models are 1,500, 2,048, and 3,072, respectively. The MIMOMLP dim (with R=4) for these mod |
| 055 | partial | u | 4 | flag: no verified quote from cited source(s) [ | - | Mamba-3's recurrent state uses a fixed-size state per sequence, whereas a Transformer's KV cache uses memory that grows linearly with sequence length  |
| 056 | unanswer | - | - | flag: no verified quote from cited source(s) [ | - | The provided sources do not contain information about Mamba-3's performance at 7B parameters or larger. The sources only discuss performance at 1.5B a |
| 057 | unanswer | - | - | flag: no verified quote from cited source(s) [ | - | The Efficient Verification Strategy reduces training time to approximately 110 GPU hours [S2]. |
| 058 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
| 059 | unanswer | - | - | flag: no verified quote from cited source(s) [ | - | No. The retrieval table in the provided sources does not contain a hybrid Mamba-3 MIMO result. The tables show pure Mamba-3 variants (SISO and MIMO) a |
| 060 | unanswer | - | - | pass | - | The Mamba-3 kernels are released under the Triton license [S1], [S2]. |
