# Golden QA evaluation: TRM converted by Docling; json_mode off; default retrieval settings

Golden file `evals/gold/trm.jsonl` (69 questions: 63 answerable, 6 unanswerable). Store: `/tmp/claude-1000/-home-copper-Git-Template-RAG/24d159d4-229a-4570-887a-d29472273e1a/scratchpad/trm_docling_store` (60 chunks, 55 usable). LLM json_mode=`off`, policy=`balanced`, k=5. 'Correct' = the answer contains the facts listed in the gold sidecar: a lower bound, read the answers below.

## 1. Ingestion: is the evidence in a usable chunk?

- usable: 99% (100/101)
- rejected: 0% (0/101)
- split: 0% (0/101)
- absent: 1% (1/101)
- questions with unreachable evidence: 001

## 2. Retrieval (answerable questions)

- an evidence chunk in the top 5: 95% (60/63)
- evidence chunk ranked first: 78% (49/63)
- all of a question's evidence quotes covered by the top 5: 90% (57/63)

## 3. Answers

- answered (did not refuse): 98% (62/63)
- delivered (answered and passed the gates): 86% (54/63)
- contains every required fact: 73% (46/63)
- contains every required fact **and** delivered: 68% (43/63)
- mean share of required facts present: 0.80
- a verified quote comes from an evidence chunk: 84% (53/63)
- correct among flagged answers (false alarms): 38% (3/8)

## 4. Unanswerable questions (right behaviour: refuse)

- refused: 50% (3/6)
- answered but flagged: 0% (0/6)
- answered and passed the gates (the dangerous case): 50% (3/6)

## 5. By question type (answerable)

| type | n | evidence in top-k | delivered | every fact | delivered and every fact |
|---|---:|---:|---:|---:|---:|
| comparison | 2 | 2 | 2 | 2 | 2 |
| conditional | 1 | 1 | 0 | 1 | 0 |
| factual | 17 | 16 | 16 | 13 | 13 |
| list | 8 | 7 | 8 | 7 | 7 |
| mechanism | 6 | 5 | 4 | 4 | 3 |
| multi-hop | 8 | 8 | 3 | 1 | 0 |
| numeric | 12 | 12 | 12 | 11 | 11 |
| reasoning | 3 | 3 | 3 | 2 | 2 |
| table | 6 | 6 | 6 | 5 | 5 |

## 6. Every question

| id | type | ev. | rank | outcome | facts | answer |
|---|---|---|---|---|---|---|
| 001 | factual | a | - | refused | 0.00 | I don't know based on the provided sources. |
| 002 | numeric | u | 2 | pass | 1.00 | TRM uses 7M parameters, and the abstract reports that TRM obtains 45% test-accuracy on ARC-AGI1 and 8% on ARC-AGI-2 [2]. |
| 003 | factual | u | 5 | pass | 1.00 | TRM has only 2 layers [2, 3]. |
| 004 | numeric | u | 1 | pass | 1.00 | TRM uses 7M parameters, which is less than 0.01% of the parameters of most LLMs mentioned (e.g., Deepseek R1, o3-mini, Gemini 2.5 Pro) [1]. |
| 005 | factual | u | 1 | pass | 1.00 | Large Language Models (LLMs) can struggle on hard question-answer problems because they generate their answer auto-regressively, which carries a high  |
| 006 | list | u | 1 | pass | 1.00 | The drawbacks of Chain-of-Thought (CoT) mentioned in the paper are that it is expensive, requires high-quality reasoning data (which may not be availa |
| 007 | numeric | u | 2 | pass | 1.00 | Gemini 2.5 Pro obtains 4.9% test accuracy on ARC-AGI-2 [2]. |
| 008 | factual | u | 1 | pass | 1.00 | The two main novelties of HRM are recursive hierarchical reasoning and deep supervision [1]. |
| 009 | factual | u,u | 1 | pass | 0.50 | An independent analysis on the ARC-AGI benchmark indicated that deep supervision was the main factor driving the performance gains of HRM [1]. |
| 010 | numeric | u | 1 | pass | 1.00 | TRM improved the state-of-the-art test accuracy on SudokuExtreme from 55% to 87%, on Maze-Hard from 75% to 85%, on ARC-AGI-1 from 40% to 45%, and on A |
| 011 | mechanis | u,u | 1 | pass | 1.00 | In each improvement step, TRM performs two update steps: i) recursively updating its latent z $n$ times given the question x, current answer y, and cu |
| 012 | list | u | 1 | pass | 1.00 | HRM contains four learnable components: the input embedding fI(·; θI), the low-level recurrent network fL(·; θL), the high-level recurrent network fH( |
| 013 | factual | u | 1 | pass | 1.00 | HRM contains four learnable components: the input embedding fI(·; θI), a low-level recurrent network fL(·; θL), a high-level recurrent network fH(·; θ |
| 014 | numeric | u | 1 | pass | 0.50 | A forward pass of HRM consists of applying 6 function evaluations, and the first 4 function evaluations are detached from the computational graph and  |
| 015 | numeric | u | 1 | pass | 1.00 | HRM uses n = 2 and T = 2 [3]. |
| 016 | factual | u | 3 | pass | 1.00 | HRM uses the Implicit Function Theorem (IFT) with the 1-step gradient approximation to approximate the gradient by backpropagating only the last fL an |
| 017 | numeric | u | 1 | pass | 1.00 | At most Nsup = 16 supervision steps are used in deep supervision [1]. |
| 018 | factual | u | 1 | pass | 1.00 | No, ACT is only used during training, while the full Nsup = 16 supervision steps are performed at test time to maximize downstream performance [1]. |
| 019 | numeric | u | 1 | pass | 1.00 | On average, ACT spends less than 2 steps per example on the Sudoku-Extreme dataset [1]. |
| 020 | numeric | u | 1 | pass | 1.00 | HRM effectively reasons over 384 layers of effective depth, which is computed using the formula nlayers(n + 1)TNsup = 4 * (2 + 1) * 2 * 16, based on t |
| 021 | factual | u | 1 | pass | 1.00 | Deep supervision and the 1-step gradient approximation offer a more biologically plausible and less computationally-expansive alternative to Backpropa |
| 022 | factual | u,u | 1 | pass | 1.00 | The main concern with applying the Implicit Function Theorem to HRM is that there is no guarantee that a fixed-point is reached [1]. |
| 023 | list | u,u | 1 | pass | 1.00 | In the setting with n = 7 and T = 7, the authors observed that the residual for zH was clearly well above 0 at every step, the residual for zL only be |
| 024 | factual | u,u | 1 | pass | 1.00 | The cost of HRM's Adaptive computational time (ACT) implementation is that the continue loss, which is part of the Q-learning objective, requires an e |
| 025 | factual | u,u | 1 | pass | 0.50 | The paper criticizes HRM's biological justification because it makes it incredibly hard to parse out why HRM is designed the way it is, and it relies  |
| 026 | table | u,u | 1 | pass | 1.00 | In Table 1, HRM achieved 55.0% test accuracy with a depth of 24, 2 forward passes, and 27M parameters. TRM (with T = 3, n = 6) achieved 87.4% test acc |
| 027 | table | u,u | 1 | pass | 0.00 | The text mentions that using the 1-step gradient approximation is used to approximate the gradient by backpropagating only the last fL and fH steps [3 |
| 028 | mechanis | u,u | 1 | pass | 1.00 | A full recursion process is defined as containing n evaluations of fL and 1 evaluation of fH [2]. In the context of training, the models learn to take |
| 029 | mechanis | u,u | 2 | pass | 1.00 | zH is simply the current (embedded) solution [2]. zL is a latent feature that does not directly correspond to a solution, but it can be transformed in |
| 030 | reasonin | u,u | 1 | pass | 1.00 | TRM needs both y (the previous solution) and z (the current latent reasoning feature) separately because if the previous reasoning z were not passed,  |
| 031 | table | u,u,u | 1 | pass | 1.00 | The Sudoku-Extreme accuracies for different numbers of latent features in Table 2 are: 87.4% for TRM y, z (Ours) with 2 features, 77.6% for TRMmulti-s |
| 032 | mechanis | u | 1 | flag: no verified quote from cited source(s) [ | 0.00 | A single network can perform both update tasks in TRM by recursing on its latent reasoning feature and progressively improving its final answer [4]. |
| 033 | table | u | 2 | pass | 1.00 | When a single network was used instead of two networks, the approach obtained better generalization on Sudoku-Extreme, improving TRM from 82.4% to 87. |
| 034 | factual | u,u | 1 | pass | 0.33 | Adding layers decreased generalization due to overfitting [1]. Conversely, decreasing the number of layers while scaling the number of recursions (n)  |
| 035 | reasonin | u | 2 | pass | 0.50 | Using tiny networks with deep recursion and deep supervision appears to allow the model to bypass a lot of the overfitting [2]. TRM achieves better ge |
| 036 | conditio | u,u | 1 | flag: Unsupported number in answer: [10] | 1.00 | Replacing self-attention with an MLP worked extremely well on Sudoku-Extreme, improving test accuracy by 10% [1]. This approach was suitable for Sudok |
| 037 | mechanis | u,u | - | pass | 0.00 | TRM simplifies ACT by requiring only a single forward pass instead of two passes [2]. The provided sources do not state what the cost in accuracy was  |
| 038 | multi-ho | u,u | 1 | flag: no verified quote from cited source(s) [ | 0.50 | TRM uses an Exponential Moving Average (EMA) of 0.999 [1]. |
| 039 | numeric | u | 1 | pass | 1.00 | The optimal recursion settings for HRM on Sudoku-Extreme were T = 3 and n = 3, which corresponds to 48 recursions [1]. For TRM on Sudoku-Extreme, the  |
| 040 | reasonin | u,u | 1 | pass | 1.00 | Increasing n too much causes Out Of Memory (OOM) errors because TRM requires backpropagation through a full recursion process [1]. |
| 041 | numeric | u | 1 | pass | 1.00 | Sudoku-Extreme uses 1K training samples and 423K test samples [1]. |
| 042 | factual | u,u | 1 | pass | 1.00 | The Maze-Hard dataset consists of 30x30 mazes generated by the procedure by Lehnert et al. (2024), where the shortest path of the mazes is above 110;  |
| 043 | list | u,u,u | 1 | pass | 1.00 | Sudoku-Extreme uses 1000 shuffling augmentations per data example [1]. Maze-Hard uses 8 dihedral transformations per data example [1]. ARC-AGI uses 10 |
| 044 | numeric | u,u | 1 | pass | 1.00 | ARC-AGI-1 contains 800 tasks, and ARC-AGI-2 contains 1120 tasks [1]. Additionally, the data was augmented with 160 tasks from the closely related Conc |
| 045 | factual | u | 1 | pass | 1.00 | The final score for ARC-AGI is computed as the accuracy over all test inputs from two attempts to produce the correct output grid [1]. For ARC-AGI, at |
| 046 | table | u | 3 | pass | 1.00 | TRM with self-attention achieves 85.3% accuracy on Maze-Hard, 44.6% accuracy on ARC-AGI-1, and 7.8% accuracy on ARC-AGI-2 with 7M parameters, which is |
| 047 | comparis | u,u | 1 | pass | 1.00 | TRM without self-attention obtains the best generalization on SudokuExtreme with an accuracy of 87.4% [1]. However, TRM with self-attention generalize |
| 048 | table | u,u | 2 | pass | 1.00 | TRM-MLP uses 5M/19M 1 parameters, and it obtained 0.0 accuracy on Maze-Hard [2]. |
| 049 | list | u | 1 | pass | 1.00 | All models are trained with the AdamW optimizer (Loshchilov & Hutter, 2017; Kingma & Ba, 2014) with $\beta1 = 0.9$, $\beta2 = 0.95$, a small learning  |
| 050 | comparis | u,u | 1 | pass | 1.00 | For Sudoku-Extreme and Maze-Hard, the training involves 60k epochs with a learning rate of 1e-4 and a weight decay of 1.0 [1]. In contrast, for ARC-AG |
| 051 | list | u,u | 1 | pass | 1.00 | Experiments on Sudoku-Extreme were run on 1 L40S with 40Gb of RAM for generally less than 36 hours [1]. Experiments on Maze-Hard were run on 4 L40S wi |
| 052 | mechanis | u | 1 | flag: the answer cites no source | 1.00 | At test-time for ARC-AGI, the most common answer out of the 1000 data augmentations is given as the answer. |
| 053 | factual | u | 1 | pass | 1.00 | The numbers for Deepseek R1, Claude 3.7 8K, o3-mini-high, Direct prediction, and HRM are taken from Table 4 and Table 5 in Wang et al. (2025) [1]. |
| 054 | list | u,u,u | 1 | pass | 1.00 | The author tried several ideas that failed, including replacing the SwiGLU MLPs with SwiGLU Mixture-of-Experts (MoEs), which resulted in a massive dec |
| 055 | factual | u | 1 | pass | 1.00 | When TorchDEQ was used to replace the recursion steps with fixed-point iteration, it slowed down training because of the fixed-point iteration and res |
| 056 | list | u,u | - | pass | 0.00 | The conclusion names several limitations and future directions. Regarding limitations, it is hard to determine what parts of HRM is helping what and w |
| 057 | multi-ho | u,u,u | 1 | flag: Unsupported number in answer: [15, 28, 3 | 0.00 | The models in Table 5 that score higher than TRM on ARC-AGI-1 are Chain-of-thought, pretrained (28.6%), Deepseek R1 (15.8%), o3-mini-high (34.5%), and |
| 058 | multi-ho | u,u | 1 | flag: no verified quote from cited source(s) [ | 0.50 | The abstract reports 45% test-accuracy on ARC-AGI1, while Table 5 shows 44.6% for TRM-Att (Ours) on ARC-AGI-1 [1, 3]. |
| 059 | multi-ho | u,u | 1 | pass | 0.67 | Table 1 shows that using an MLP instead of self-attention improved the generalization on Sudoku-Extreme from 74.7% to 87.4% [2]. |
| 060 | multi-ho | u,u,u | 2 | pass | 0.50 | TRM's total effective depth across all supervision steps is not explicitly stated as a single value in the provided sources. However, for HRM, it is n |
| 061 | multi-ho | u | 1 | flag: no verified quote from cited source(s) [ | 1.00 | When comparing results at a similar effective depth per supervision step in Table 3, TRM achieves a higher test accuracy than HRM. For instance, when  |
| 062 | multi-ho | u,u | 5 | pass | 0.00 | The independent analysis on the ARC-AGI benchmark indicated that deep supervision was the main factor in performance gains [5]. This relates to HRM's  |
| 063 | multi-ho | u,u,u | 1 | flag: no verified quote from cited source(s) [ | 0.00 | TRM reduces the number of parameters by halving the number of layers and replacing the two networks with a single tiny network [4]. |
| 064 | unanswer | - | - | pass | - | TRM obtains 8% test-accuracy on ARC-AGI-2 [3]. |
| 065 | unanswer | - | - | refused | - | The provided sources do not state where the TRM source code is hosted. |
| 066 | unanswer | - | - | refused | - | The provided sources do not contain information about how TRM performs on language reasoning benchmarks like GSM8K. |
| 067 | unanswer | - | - | pass | - | The training for ARC-AGI took 100K epochs [1]. |
| 068 | unanswer | - | - | refused | - | The provided sources do not contain information on how TRM accuracy scales above 19M parameters. |
| 069 | unanswer | - | - | pass | - | More recursions could be helpful for harder problems, although the authors have not tested this specifically due to limited resources [1]. |
