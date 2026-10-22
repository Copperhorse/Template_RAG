# Golden QA evaluation: TRM re-ingested with table captions; json_mode off; default retrieval settings (GPU embedder, 20 rerank candidates)

Golden file `evals/gold/trm.jsonl` (69 questions: 63 answerable, 6 unanswerable). Store: `/tmp/claude-1000/-home-copper-Git-Template-RAG/24d159d4-229a-4570-887a-d29472273e1a/scratchpad/trm_fixed_default` (63 chunks, 58 usable). LLM json_mode=`off`, policy=`balanced`, k=5. 'Correct' = the answer contains the facts listed in the gold sidecar: a lower bound, read the answers below.

## 1. Ingestion: is the evidence in a usable chunk?

- usable: 100% (101/101)
- rejected: 0% (0/101)
- split: 0% (0/101)
- absent: 0% (0/101)

## 2. Retrieval (answerable questions)

- an evidence chunk in the top 5: 95% (60/63)
- evidence chunk ranked first: 78% (49/63)
- all of a question's evidence quotes covered by the top 5: 89% (56/63)

## 3. Answers

- answered (did not refuse): 97% (61/63)
- delivered (answered and passed the gates): 83% (52/63)
- contains every required fact: 67% (42/63)
- contains every required fact **and** delivered: 60% (38/63)
- mean share of required facts present: 0.78
- a verified quote comes from an evidence chunk: 86% (54/63)
- correct among flagged answers (false alarms): 44% (4/9)

## 4. Unanswerable questions (right behaviour: refuse)

- refused: 50% (3/6)
- answered but flagged: 0% (0/6)
- answered and passed the gates (the dangerous case): 50% (3/6)

## 5. By question type (answerable)

| type | n | evidence in top-k | delivered | every fact | delivered and every fact |
|---|---:|---:|---:|---:|---:|
| comparison | 2 | 2 | 2 | 2 | 2 |
| conditional | 1 | 1 | 1 | 0 | 0 |
| factual | 17 | 16 | 12 | 12 | 9 |
| list | 8 | 7 | 8 | 6 | 6 |
| mechanism | 6 | 5 | 5 | 4 | 4 |
| multi-hop | 8 | 8 | 4 | 0 | 0 |
| numeric | 12 | 12 | 11 | 12 | 11 |
| reasoning | 3 | 3 | 3 | 2 | 2 |
| table | 6 | 6 | 6 | 4 | 4 |

## 6. Every question

| id | type | ev. | rank | outcome | facts | answer |
|---|---|---|---|---|---|---|
| 001 | factual | u | - | refused | 0.00 | The provided sources do not state who wrote 'Less is More: Recursive Reasoning with Tiny Networks' or where the author is affiliated. |
| 002 | numeric | u | 2 | pass | 1.00 | TRM uses 7M parameters [3]. The abstract reports that TRM obtains 45% test-accuracy on ARC-AGI1 and 8% on ARC-AGI-2 [2]. |
| 003 | factual | u | 1 | pass | 1.00 | TRM has 2 layers [2, 5]. |
| 004 | numeric | u | 1 | pass | 1.00 | TRM uses 7M parameters, which is less than 0.01% of the parameters used by most LLMs like Deepseek R1, o3-mini, and Gemini 2.5 Pro [1]. |
| 005 | factual | u | 1 | pass | 1.00 | Large Language models (LLMs) can struggle on hard question-answer problems because they generate their answer auto-regressively, which carries a high  |
| 006 | list | u | 3 | pass | 1.00 | The drawbacks of chain-of-thought (CoT) mentioned in the paper are that it is expensive, requires high-quality reasoning data (which may not be availa |
| 007 | numeric | u | 2 | pass | 1.00 | Gemini 2.5 Pro obtains 4.9% test accuracy on ARC-AGI-2 [2]. |
| 008 | factual | u | 1 | pass | 1.00 | The two main novelties of HRM are recursive hierarchical reasoning and deep supervision [1]. |
| 009 | factual | u,u | 1 | pass | 1.00 | An independent analysis on the ARC-AGI benchmark showed that deep supervision seems to be the primary driver of the performance gains [1]. |
| 010 | numeric | u | 1 | pass | 1.00 | TRM improved the state-of-the-art test accuracy on SudokuExtreme from 55% to 87%, Maze-Hard from 75% to 85%, ARC-AGI-1 from 40% to 45%, and ARC-AGI-2  |
| 011 | mechanis | u,u | 1 | pass | 1.00 | In each improvement step, the Tiny Recursion Model (TRM) performs two update steps: i) recursively updating its latent variable _z_ _n_ times given th |
| 012 | list | u | 1 | pass | 1.00 | HRM contains four learnable components: the input embedding fI ( · ; θI ), the low-level recurrent network fL ( · ; θL ), the high-level recurrent net |
| 013 | factual | u | 1 | pass | 0.00 | HRM contains four learnable components: the input embedding f I ( · ; θI ), a low-level recurrent network fL ( · ; θL ), a high-level recurrent networ |
| 014 | numeric | u | 1 | pass | 1.00 | A forward pass of HRM consists of applying 6 function evaluations, and only the last two steps are tracked for gradients during back-propagation [1, 3 |
| 015 | numeric | u | 2 | pass | 1.00 | HRM uses n_ = 2 with T_ = 2 in all experiments, although it can be generalized to allow for an arbitrary number of L steps (n_) and recursions (T_) [2 |
| 016 | factual | u | 1 | flag: no verified quote from cited source(s) [ | 1.00 | HRM uses the Implicit Function Theorem (IFT) with a 1-step gradient approximation to justify back-propagating only through the last two function evalu |
| 017 | numeric | u | 2 | pass | 1.00 | At most _Nsup_ = 16 supervision steps are used in deep supervision [2]. |
| 018 | factual | u | 1 | pass | 1.00 | No, Adaptive computational time (ACT) is only used during training, while the full _Nsup_ = 16 supervision steps are performed at test time to maximiz |
| 019 | numeric | u | 1 | pass | 1.00 | On average, ACT spends less than 2 steps per example on the Sudoku-Extreme dataset, compared to the full _Nsup_ = 16 steps [1, 2]. |
| 020 | numeric | u | 1 | pass | 1.00 | HRM effectively reasons over _nlayers_ ( _n_ + 1) _TNsup_ = 4 _∗_ (2 + 1) _∗_ 2 _∗_ 16 = 384 layers of effective depth [1]. This is computed based on  |
| 021 | factual | u | 1 | pass | 1.00 | Deep supervision and the 1-step gradient approximation offer a more biologically plausible and less computationally-expansive alternative to Backpropa |
| 022 | factual | u,u | 2 | flag: no verified quote from cited source(s) [ | 1.00 | The main concern with applying the Implicit Function Theorem to HRM is that there is no guarantee that a fixed-point is reached [2], and HRM is not it |
| 023 | list | u,u | 1 | pass | 1.00 | In the setting where n = 7 and T = 7, the authors observed that the residual for zH is clearly well above 0 at every step [1], while the residual for  |
| 024 | factual | u,u | 1 | pass | 1.00 | The cost of HRM's Adaptive computational time (ACT) implementation is that the continue loss, which is part of the Q-learning objective, requires an e |
| 025 | factual | u,u | 1 | flag: no verified quote from cited source(s) [ | 0.50 | The paper criticizes HRM's biological justification because the over-reliance on biological arguments and fixed-point theorems, which are not perfectl |
| 026 | table | u,u | 1 | pass | 1.00 | In Table 1, HRM has an accuracy of 55.0%, a depth of 24, 2 forward passes (NFP), and 27M parameters. TRM with _T_ = 3 and _n_ = 6 has an accuracy of 8 |
| 027 | table | u,u | 1 | pass | 0.50 | Using the 1-step gradient approximation results in an accuracy of 56.5% for TRM on Sudoku-Extreme [2]. |
| 028 | mechanis | u,u | 1 | pass | 0.50 | A full recursion process is defined as containing $n$ evaluations of $f_L$ and 1 evaluation of $f_H$ [1]. The training of TRM involves a deep supervis |
| 029 | mechanis | u,u | 2 | pass | 1.00 | _zH_ is the current (embedded) solution, while _zL_ is a latent feature that does not directly correspond to a solution but can be transformed into a  |
| 030 | reasonin | u,u | 1 | pass | 1.00 | Having both _y_ and _z_ is necessary because if the previous reasoning _z_ is not passed, the model forgets how it reached the previous solution _y_ ( |
| 031 | table | u,u,u | 1 | pass | 0.33 | The Sudoku-Extreme accuracy for TRM_y_,_z_(Ours) with 2 features was 87.4% [1]. |
| 032 | mechanis | u | 1 | pass | 1.00 | A single network is sufficient because the task to achieve (iterating on $z$ versus using $z$ to update $y$) is directly specified by the inclusion or |
| 033 | table | u | 2 | pass | 1.00 | When TRM replaced two networks with one, it obtained better generalization on Sudoku-Extreme (improving TRM from 82.4% to 87.4%; see Table 1) while re |
| 034 | factual | u,u | 1 | pass | 0.33 | When the number of layers was increased, it was found that it decreased generalization due to overfitting [1]. |
| 035 | reasonin | u | 1 | pass | 0.50 | The paper suggests that using tiny networks with deep recursion and deep supervision allows the model to bypass a lot of the overfitting, which is lik |
| 036 | conditio | u,u | 1 | pass | 0.33 | Replacing self-attention with an MLP worked extremely well on Sudoku-Extreme, improving the test accuracy by 10% [3]. However, this replacement was no |
| 037 | mechanis | u,u | - | flag: no verified quote from cited source(s) [ | 0.33 | The provided sources do not explicitly state how TRM simplifies ACT or what the cost in accuracy was for ACT. Source [1] shows a comparison where a me |
| 038 | multi-ho | u,u | 1 | pass | 0.00 | HRM tends to overfit quickly and then diverge on small data like Sudoku-Extreme and MazeHard, so an Exponential Moving Average (EMA) of the weights is |
| 039 | numeric | u | 1 | pass | 1.00 | For HRM and TRM on the Sudoku-Extreme dataset, the optimal recursion settings were _T_ = 3, _n_ = 3 for HRM, which is equivalent to 48 recursions [1]. |
| 040 | reasonin | u,u | 1 | pass | 1.00 | Increasing _n_ too much causes Out Of Memory (OOM) errors because TRM requires backpropagation through a full recursion process [1]. |
| 041 | numeric | u | 1 | flag: no verified quote from cited source(s) [ | 1.00 | The Sudoku-Extreme dataset consists of extremely difficult Sudoku puzzles (9x9 grid) for which only 1K training samples are used to test small-sample  |
| 042 | factual | u,u | 1 | pass | 0.67 | The Maze-Hard dataset consists of 30x30 mazes generated by the procedure by Lehnert et al. (2024), and the shortest path in these mazes is above 110 [ |
| 043 | list | u,u,u | 1 | pass | 1.00 | Sudoku-Extreme uses 1000 shuffling augmentations per data example [1]. Maze-Hard uses 8 dihedral transformations per data example [1]. ARC-AGI uses 10 |
| 044 | numeric | u,u | 1 | pass | 1.00 | ARC-AGI-1 contains 800 tasks, and ARC-AGI-2 contains 1120 tasks [1]. Additionally, the data was augmented with 160 tasks from the closely related Conc |
| 045 | factual | u | 1 | flag: no verified quote from cited source(s) [ | 1.00 | The final score for ARC-AGI puzzles is computed as the accuracy over all test inputs from two attempts to produce the correct output grid [2]. |
| 046 | table | u | 2 | pass | 1.00 | TRM with self-attention obtains 85.3% accuracy on Maze-Hard, 44.6% accuracy on ARC-AGI-1, and 7.8% accuracy on ARC-AGI-2, which is significantly highe |
| 047 | comparis | u,u | 1 | pass | 1.00 | TRM without self-attention obtains the best generalization on SudokuExtreme with an accuracy of 87.4% [1]. However, TRM with self-attention generalize |
| 048 | table | u,u | 2 | pass | 1.00 | TRM-MLP uses 5M or 19M parameters and obtained 0.0% accuracy on Maze-Hard [2]. |
| 049 | list | u | 1 | pass | 1.00 | The models are trained with the AdamW optimizer with $\beta_1 = 0.9$, $\beta_2 = 0.95$, a small learning rate warmup of 2K iterations, a batch-size of |
| 050 | comparis | u,u | 1 | pass | 1.00 | For Sudoku-Extreme and Maze-Hard, the training involves 60k epochs with a learning rate of 1e-4 and a weight decay of 1.0 [1]. In contrast, for ARC-AG |
| 051 | list | u,u | 1 | pass | 1.00 | Experiments on Sudoku-Extreme were run on 1 L40S with 40Gb of RAM for generally less than 36 hours [1]. Experiments on Maze-Hard were run on 4 L40S wi |
| 052 | mechanis | u | 1 | pass | 1.00 | At test-time for ARC-AGI, the most common answer out of the 1000 data augmentations is given as the answer [1]. |
| 053 | factual | u | 1 | pass | 1.00 | The numbers for Deepseek R1, Claude 3.7 8K, O3-mini-high, Direct prediction, and HRM are taken from Table 4 and Table 5, which are from Wang et al. (2 |
| 054 | list | u,u,u | 1 | pass | 0.33 | The author tried replacing the SwiGLU MLPs by SwiGLU Mixture-of-Experts (MoEs), but this resulted in a massive decrease in generalization [1]. They al |
| 055 | factual | u | 1 | pass | 1.00 | When TorchDEQ was used to replace the recursion steps with fixed-point iteration, it slowed down training due to the fixed-point iteration and resulte |
| 056 | list | u,u | - | pass | 0.00 | The limitations and future directions mentioned include the complexity of the HRM method, which relies too heavily on uncertain biological arguments a |
| 057 | multi-ho | u,u,u | 1 | flag: no verified quote from cited source(s) [ | 0.67 | The models in Table 5 that score higher than TRM on ARC-AGI-1 are Gemini 2.5 Pro (37.0%) and Grok-4-thinking (66.7%) [1]. |
| 058 | multi-ho | u,u | 1 | flag: no verified quote from cited source(s) [ | 0.50 | The abstract reports 45% test-accuracy on ARC-AGI1, while Table 5 shows 44.6% for TRM-Att (Ours) on ARC-AGI-1 [1, 2]. |
| 059 | multi-ho | u,u | 1 | pass | 0.67 | Table 1 shows that using an MLP instead of self-attention improved the generalization on Sudoku-Extreme from 74.7% to 87.4% [2]. |
| 060 | multi-ho | u,u,u | 2 | pass | 0.50 | The effective depth for HRM, based on the hyperparameters used by Jang et al. (2023), is 384 layers of effective depth, calculated as _nlayers_ ( _n_  |
| 061 | multi-ho | u | 1 | flag: no verified quote from cited source(s) [ | 0.00 | At matched effective depth per supervision step in Table 3, HRM and TRM matched at a similar effective depth per supervision step (_T_ (_n_ + 1) _nlay |
| 062 | multi-ho | u,u | 1 | pass | 0.25 | The independent analysis showed that deep supervision was the primary driver of performance gains, doubling accuracy from 19% to 39% [1]. Regarding HR |
| 063 | multi-ho | u,u,u | 1 | refused | 0.00 | The provided sources do not specify the exact number of TRM parameters removed by each simplification from a 4-layer, two-network design. |
| 064 | unanswer | - | - | pass | - | TRM obtains 45% test-accuracy on ARC-AGI1 and 8% on ARC-AGI-2 [3]. |
| 065 | unanswer | - | - | refused | - | The provided sources do not state where the TRM source code is hosted. |
| 066 | unanswer | - | - | refused | - | The provided sources do not contain information about how TRM performs on language reasoning benchmarks like GSM8K. |
| 067 | unanswer | - | - | pass | - | Experiments on ARC-AGI were run for around 3 days with 4 H100 with 80Gb of RAM [1]. Additionally, for ARC-AGI, the training involved 100K epochs with  |
| 068 | unanswer | - | - | refused | - | The provided sources do not contain information on how TRM accuracy scales above 19M parameters. |
| 069 | unanswer | - | - | pass | - | More recursions could potentially be helpful for harder problems, although increasing either _T_ or _n_ causes massive slowdowns [1]. For instance, TR |
