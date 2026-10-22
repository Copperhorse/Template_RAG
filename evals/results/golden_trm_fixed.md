# Golden QA evaluation: TRM re-ingested with table captions attached; json_mode off; embedder on CPU, 10 rerank candidates

Golden file `evals/gold/trm.jsonl` (69 questions: 63 answerable, 6 unanswerable). Store: `/tmp/claude-1000/-home-copper-Git-Template-RAG/24d159d4-229a-4570-887a-d29472273e1a/scratchpad/trm_fixed` (63 chunks, 58 usable). LLM json_mode=`off`, policy=`balanced`, k=5. 'Correct' = the answer contains the facts listed in the gold sidecar: a lower bound, read the answers below.

## 1. Ingestion: is the evidence in a usable chunk?

- usable: 100% (101/101)
- rejected: 0% (0/101)
- split: 0% (0/101)
- absent: 0% (0/101)

## 2. Retrieval (answerable questions)

- an evidence chunk in the top 5: 97% (61/63)
- evidence chunk ranked first: 81% (51/63)
- all of a question's evidence quotes covered by the top 5: 90% (57/63)

## 3. Answers

- answered (did not refuse): 95% (60/63)
- delivered (answered and passed the gates): 86% (54/63)
- contains every required fact: 68% (43/63)
- contains every required fact **and** delivered: 62% (39/63)
- mean share of required facts present: 0.78
- a verified quote comes from an evidence chunk: 89% (56/63)
- correct among flagged answers (false alarms): 67% (4/6)

## 4. Unanswerable questions (right behaviour: refuse)

- refused: 33% (2/6)
- answered but flagged: 0% (0/6)
- answered and passed the gates (the dangerous case): 67% (4/6)

## 5. By question type (answerable)

| type | n | evidence in top-k | delivered | every fact | delivered and every fact |
|---|---:|---:|---:|---:|---:|
| comparison | 2 | 2 | 2 | 2 | 2 |
| conditional | 1 | 1 | 0 | 0 | 0 |
| factual | 17 | 16 | 14 | 13 | 11 |
| list | 8 | 8 | 8 | 6 | 6 |
| mechanism | 6 | 6 | 6 | 3 | 3 |
| multi-hop | 8 | 8 | 5 | 0 | 0 |
| numeric | 12 | 11 | 10 | 12 | 10 |
| reasoning | 3 | 3 | 3 | 3 | 3 |
| table | 6 | 6 | 6 | 4 | 4 |

## 6. Every question

| id | type | ev. | rank | outcome | facts | answer |
|---|---|---|---|---|---|---|
| 001 | factual | u | - | refused | 0.00 | The provided sources do not state who wrote 'Less is More: Recursive Reasoning with Tiny Networks' or where the author is affiliated. |
| 002 | numeric | u | 2 | pass | 1.00 | TRM uses 7M parameters [3]. The abstract reports that TRM obtains 45% test-accuracy on ARC-AGI1 and 8% on ARC-AGI-2 [2]. |
| 003 | factual | u | 1 | pass | 1.00 | TRM has only 2 layers [2]. |
| 004 | numeric | u | 1 | pass | 1.00 | TRM uses 7M parameters, which is less than 0.01% of the parameters used by most LLMs like Deepseek R1, o3-mini, and Gemini 2.5 Pro [1]. |
| 005 | factual | u | 1 | pass | 1.00 | Large Language models (LLMs) can struggle on hard question-answer problems because they generate their answer auto-regressively, which carries a high  |
| 006 | list | u | 1 | pass | 1.00 | Chain-of-thought (CoT) has several drawbacks listed, including being expensive, requiring high-quality reasoning data which may not be available, and  |
| 007 | numeric | u | 2 | pass | 1.00 | Gemini 2.5 Pro obtains 4.9% test accuracy on ARC-AGI-2 [2]. |
| 008 | factual | u | 1 | pass | 1.00 | The two main novelties of HRM are recursive hierarchical reasoning and deep supervision [1, 2]. |
| 009 | factual | u,u | 1 | pass | 1.00 | An independent analysis on the ARC-AGI benchmark showed that deep supervision seems to be the primary driver of the performance gains [1]. |
| 010 | numeric | u | 1 | flag: no verified quote from cited source(s) [ | 1.00 | TRM improved the state-of-the-art test accuracy on several benchmarks: SudokuExtreme from 55% to 87% [1], Maze-Hard from 75% to 85% [1], ARC-AGI-1 fro |
| 011 | mechanis | u,u | 1 | pass | 1.00 | In each improvement step, Tiny Recursion Model (TRM) performs two update steps: i) recursively updating its latent feature _z_ _n_ times given the que |
| 012 | list | u | 1 | pass | 1.00 | HRM contains four learnable components: the input embedding $f_I$ ($\cdot ; 	heta_I$), the low-level recurrent network $f_L$ ($\cdot ; 	heta_L$), the  |
| 013 | factual | u | 1 | pass | 1.00 | HRM contains four learnable components: the input embedding f I ( · ; θI ), a low-level recurrent network fL ( · ; θL ), a high-level recurrent networ |
| 014 | numeric | u | 1 | pass | 1.00 | A forward pass of HRM consists of applying 6 function evaluations, and only the last two steps are tracked for gradients, which means only the last tw |
| 015 | numeric | u | 2 | pass | 1.00 | In all experiments, HRM uses n_ = 2 with T_ = 2, although it can be generalized to allow for an arbitrary number of L steps (n_) and recursions (T_) [ |
| 016 | factual | u | 1 | flag: no verified quote from cited source(s) [ | 1.00 | HRM uses the Implicit Function Theorem (IFT) with a 1-step gradient approximation to justify back-propagating only through the last two function evalu |
| 017 | numeric | u | - | pass | 1.00 | The maximum number of supervision steps used in deep supervision is _Nsup_ = 16 [1]. |
| 018 | factual | u | 1 | pass | 1.00 | No, Adaptive computational time (ACT) is only used during training, while the full _Nsup_ = 16 supervision steps are performed at test time to maximiz |
| 019 | numeric | u | 1 | pass | 1.00 | On average, ACT spends less than 2 steps per example on the Sudoku-Extreme dataset, compared to the full _Nsup_ = 16 steps [1, 2]. |
| 020 | numeric | u | 1 | flag: no verified quote from cited source(s) [ | 1.00 | HRM effectively reasons over _nlayers_ (_n_ + 1) _TNsup_ = 4 _∗_ (2 + 1) _∗_ 2 _∗_ 16 = 384 layers of effective depth [1]. The effective depth is comp |
| 021 | factual | u | 1 | pass | 1.00 | Deep supervision and the 1-step gradient approximation offer a more biologically plausible and less computationally-expansive alternative to Backpropa |
| 022 | factual | u,u | 1 | pass | 1.00 | The main concern with applying the Implicit Function Theorem to HRM is that there is no guarantee that a fixed-point is reached [1]. Furthermore, the  |
| 023 | list | u,u | 1 | pass | 1.00 | In the setting where n = 7 and T = 7, the authors observed that the residual for zH was clearly well above 0 at every step [1]. Furthermore, the resid |
| 024 | factual | u,u | 1 | pass | 1.00 | The cost of HRM's Adaptive computational time (ACT) implementation is that the continue loss, which is part of the Q-learning objective, requires an e |
| 025 | factual | u,u | 1 | pass | 0.50 | The paper criticizes HRM's biological justification because it makes it incredibly hard to parse out why HRM is designed the way it is [1]. Furthermor |
| 026 | table | u,u | 1 | pass | 1.00 | In Table 1, HRM achieved an accuracy of 55.0% with a depth of 24, 2 forward passes (NFP), and 27M parameters. TRM with _T_ = 3 and _n_ = 6 achieved an |
| 027 | table | u,u | 1 | pass | 0.50 | Using the 1-step gradient approximation results in an accuracy of 56.5% for TRM on Sudoku-Extreme [2]. |
| 028 | mechanis | u,u | 1 | pass | 0.50 | TRM defines a full recursion process as containing $n$ evaluations of $f_L$ and 1 evaluation of $f_H$ [1]. It is trained using deep supervision, where |
| 029 | mechanis | u,u | 2 | pass | 1.00 | _zH_ is the current (embedded) solution, while _zL_ is a latent feature that does not directly correspond to a solution but can be transformed into a  |
| 030 | reasonin | u,u | 1 | pass | 1.00 | Both the previous solution _y_ and the previous reasoning _z_ are needed separately because if only _z_ were passed, the model would forget the previo |
| 031 | table | u,u,u | 1 | pass | 0.33 | The Sudoku-Extreme accuracy for TRM_y_,_z_(Ours) with 2 features was 87.4% [1]. |
| 032 | mechanis | u | 1 | pass | 0.00 | A single network is enough to perform both tasks in TRM, which involves recursing on its latent reasoning feature and progressively improving its fina |
| 033 | table | u | 2 | pass | 1.00 | When TRM replaced two networks with one, it obtained better generalization on Sudoku-Extreme (improving TRM from 82.4% to 87.4%; see Table 1) while re |
| 034 | factual | u,u | 1 | pass | 0.33 | When the number of layers was increased to scale the model, it was found that adding layers decreased generalization due to overfitting [1]. Conversel |
| 035 | reasonin | u | 1 | pass | 1.00 | The paper suggests that using tiny networks with deep recursion and deep supervision allows the model to bypass a lot of the overfitting that can occu |
| 036 | conditio | u,u | 1 | flag: Unsupported number in answer: [10] | 0.33 | Replacing the self-attention layer with a multilayer perceptron (MLP) worked extremely well on Sudoku-Extreme, improving the test accuracy by 10% [1]. |
| 037 | mechanis | u,u | 4 | pass | 0.67 | TRM simplifies ACT by removing the need for the expensive second forward pass, which is required in HRM when implementing ACT through Q-learning, by g |
| 038 | multi-ho | u,u | 1 | pass | 0.00 | HRM tends to overfit quickly and then diverge on small data like Sudoku-Extreme and MazeHard, so an Exponential Moving Average (EMA) of the weights is |
| 039 | numeric | u | 1 | pass | 1.00 | For HRM, the optimal settings were _T_ = 3 and _n_ = 3, which corresponds to 48 recursions [1]. For TRM, the optimal settings were _T_ = 3 and _n_ = 6 |
| 040 | reasonin | u,u | 1 | pass | 1.00 | Increasing 'n' too much causes Out Of Memory (OOM) errors for TRM because it requires backpropagation through a full recursion process [1]. In the Tin |
| 041 | numeric | u | 1 | pass | 1.00 | Sudoku-Extreme uses 1K training samples and 423K samples for testing [1]. |
| 042 | factual | u,u | 1 | pass | 0.67 | The Maze-Hard dataset consists of 30x30 mazes generated by the procedure by Lehnert et al. (2024), and the shortest path in these mazes is above 110 [ |
| 043 | list | u,u,u | 1 | pass | 1.00 | Sudoku-Extreme uses 1000 shuffling augmentations per data example [1]. Maze-Hard uses 8 dihedral transformations per data example [1]. ARC-AGI uses 10 |
| 044 | numeric | u,u | 1 | pass | 1.00 | ARC-AGI-1 contains 800 tasks, and ARC-AGI-2 contains 1120 tasks [1]. The data was also augmented with 160 tasks from the closely related ConceptARC da |
| 045 | factual | u | 1 | flag: no verified quote from cited source(s) [ | 1.00 | The final score for ARC-AGI puzzles is computed as the accuracy over all test inputs from two attempts to produce the correct output grid [2]. |
| 046 | table | u | 2 | pass | 1.00 | TRM with self-attention obtains 85.3% accuracy on Maze-Hard, 44.6% accuracy on ARC-AGI-1, and 7.8% accuracy on ARC-AGI-2 with 7M parameters, which is  |
| 047 | comparis | u,u | 1 | pass | 1.00 | TRM without self-attention obtains the best generalization on SudokuExtreme with an accuracy of 87.4% [1]. However, TRM with self-attention generalize |
| 048 | table | u,u | 2 | pass | 1.00 | TRM-MLP uses 5M/19M parameters and obtained 0.0% accuracy on Maze-Hard [2]. |
| 049 | list | u | 1 | pass | 0.83 | The models are trained with the AdamW optimizer with $\beta_1 = 0.9$, $\beta_2 = 0.95$, a small learning rate warmup of 2K iterations, a batch-size of |
| 050 | comparis | u,u | 1 | pass | 1.00 | For Sudoku-Extreme and Maze-Hard, the training involves 60k epochs with a learning rate of 1e-4 and a weight decay of 1.0 [1]. In contrast, for ARC-AG |
| 051 | list | u,u | 1 | pass | 1.00 | Experiments on Sudoku-Extreme were run on 1 L40S with 40Gb of RAM for generally less than 36 hours [1]. Experiments on Maze-Hard were run on 4 L40S wi |
| 052 | mechanis | u | 1 | pass | 1.00 | At test-time for ARC-AGI, the most common answer out of the 1000 data augmentations is given as the answer [1]. |
| 053 | factual | u | 1 | pass | 1.00 | The numbers for Deepseek R1, Claude 3.7 8K, O3-mini-high, Direct prediction, and HRM are taken from Table 4 and Table 5 in Wang et al. (2025) [1]. |
| 054 | list | u,u,u | 1 | pass | 0.33 | The author tried replacing the SwiGLU MLPs by SwiGLU Mixture-of-Experts (MoEs), but this resulted in a massive decrease in generalization [1]. Additio |
| 055 | factual | u | 1 | pass | 1.00 | When TorchDEQ was used to replace the recursion steps with fixed-point iteration, it slowed down training due to the fixed-point iteration and resulte |
| 056 | list | u,u | 3 | pass | 1.00 | The limitations and future directions mentioned include the fact that every choice made in the approach is not guaranteed to be optimal on every datas |
| 057 | multi-ho | u,u,u | 1 | pass | 0.00 | The abstract states that TRM obtains 45% test-accuracy on ARC-AGI1, which is higher than most LLMs (e.g., Deepseek R1, o3-mini, Gemini 2.5 Pro) [2]. L |
| 058 | multi-ho | u,u | 1 | pass | 0.50 | Table 5 shows a test accuracy of 44.6% for TRM-Att, while the abstract reports 45% for TRM on ARC-AGI-1 [1, 4]. |
| 059 | multi-ho | u,u | 1 | pass | 0.67 | Table 1 shows that the TRM with MLP (TRM-MLP(Ours)) achieved an accuracy of 87.4% on Sudoku-Extreme [3], which is an improvement from 74.7% when using |
| 060 | multi-ho | u,u,u | 2 | refused | 0.00 | The provided sources do not state TRM's total effective depth across all supervision steps at its default setting. |
| 061 | multi-ho | u | 1 | flag: Unsupported sentence in answer (8 of 15  | 0.00 | The provided sources do not contain a direct comparison of TRM versus HRM at a matched effective depth per supervision step in Table 3, nor do they sp |
| 062 | multi-ho | u,u | 1 | pass | 0.00 | The independent analysis on the ARC-AGI benchmark indicated that deep supervision was the main driver of performance gains, suggesting that reasoning  |
| 063 | multi-ho | u,u,u | 1 | refused | 0.00 | The provided sources do not specify how many TRM parameters were removed by each simplification from a 4-layer, two-network design. |
| 064 | unanswer | - | - | pass | - | TRM obtains 8% accuracy on ARC-AGI-2 [3]. |
| 065 | unanswer | - | - | refused | - | The provided sources do not state where the TRM source code is hosted. |
| 066 | unanswer | - | - | refused | - | The provided sources do not contain information about how TRM performs on language reasoning benchmarks like GSM8K. |
| 067 | unanswer | - | - | pass | - | Experiments on ARC-AGI were run for around 3 days with 4 H100 with 80Gb of RAM [1]. |
| 068 | unanswer | - | - | pass | - | The source indicates that TRM-MLP(Ours) achieves 87.4% test accuracy with 5M parameters, and the table entry for TRM-MLP(Ours) shows a parameter count |
| 069 | unanswer | - | - | pass | - | More recursions could be helpful for harder problems, although the authors have not tested this aspect due to limited resources [1]. |
