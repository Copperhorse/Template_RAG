# Golden QA evaluation: TRM, table-aware chunking + table-cell gate, schema mode

Golden file `evals/gold/trm.jsonl` (69 questions: 63 answerable, 6 unanswerable). Store: `/tmp/claude-1000/-home-copper-Git-Template-RAG/24d159d4-229a-4570-887a-d29472273e1a/scratchpad/trm_t` (63 chunks, 58 usable). LLM json_mode=`schema`, policy=`balanced`, k=5. 'Correct' = the answer contains the facts listed in the gold sidecar: a lower bound, read the answers below.

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
- delivered (answered and passed the gates): 87% (55/63)
- contains every required fact: 76% (48/63)
- contains every required fact **and** delivered: 70% (44/63)
- mean share of required facts present: 0.84
- a verified quote comes from an evidence chunk: 87% (55/63)
- correct among flagged answers (false alarms): 67% (4/6)

## 4. Unanswerable questions (right behaviour: refuse)

- refused: 33% (2/6)
- answered but flagged: 0% (0/6)
- answered and passed the gates (the dangerous case): 67% (4/6)

## 5. By question type (answerable)

| type | n | evidence in top-k | delivered | every fact | delivered and every fact |
|---|---:|---:|---:|---:|---:|
| comparison | 2 | 2 | 2 | 2 | 2 |
| conditional | 1 | 1 | 1 | 0 | 0 |
| factual | 17 | 16 | 14 | 16 | 14 |
| list | 8 | 7 | 8 | 6 | 6 |
| mechanism | 6 | 5 | 5 | 4 | 3 |
| multi-hop | 8 | 8 | 5 | 1 | 0 |
| numeric | 12 | 12 | 12 | 12 | 12 |
| reasoning | 3 | 3 | 3 | 2 | 2 |
| table | 6 | 6 | 5 | 5 | 5 |

## 6. Every question

| id | type | ev. | rank | outcome | facts | answer |
|---|---|---|---|---|---|---|
| 001 | factual | u | - | refused | 0.00 | The provided sources do not state who wrote 'Less is More: Recursive Reasoning with Tiny Networks' or where the author is affiliated. |
| 002 | numeric | u | 2 | pass | 1.00 | TRM uses 7M parameters [S3]. The abstract reports that TRM obtains 45% test-accuracy on ARC-AGI1 and 8% on ARC-AGI-2 [S2]. |
| 003 | factual | u | 1 | pass | 1.00 | TRM uses a single tiny network with only 2 layers [S2]. |
| 004 | numeric | u | 1 | pass | 1.00 | TRM uses 7M parameters, which is less than 0.01% of the parameters used by most LLMs like Deepseek R1, o3-mini, and Gemini 2.5 Pro [S1]. |
| 005 | factual | u | 1 | pass | 1.00 | Large Language models (LLMs) can struggle on hard question-answer problems because they generate their answer auto-regressively, which carries a high  |
| 006 | list | u | 3 | pass | 1.00 | Chain-of-thought (CoT) has several drawbacks listed in the paper, including being expensive, requiring high-quality reasoning data (which may not be a |
| 007 | numeric | u | 2 | pass | 1.00 | Gemini 2.5 Pro obtains 4.9% test accuracy on ARC-AGI-2 [S2]. |
| 008 | factual | u | 1 | pass | 1.00 | The two main novelties of HRM are recursive hierarchical reasoning and deep supervision [S1]. |
| 009 | factual | u,u | 1 | pass | 1.00 | An independent analysis on the ARC-AGI benchmark showed that deep supervision seems to be the primary driver of the performance gains [S1]. |
| 010 | numeric | u | 1 | pass | 1.00 | TRM improved the state-of-the-art test accuracy on SudokuExtreme from 55% to 87%, on Maze-Hard from 75% to 85%, on ARC-AGI-1 from 40% to 45%, and on A |
| 011 | mechanis | u,u | 1 | flag: the answer cites no source | 1.00 | In each improvement step, the Tiny Recursion Model (TRM) performs two update steps: i) recursively updating its latent variable _z_ _n_ times given th |
| 012 | list | u | 1 | pass | 1.00 | HRM contains four learnable components: the input embedding $f_I$ ($	heta_I$), the low-level recurrent network $f_L$ ($	heta_L$), the high-level recur |
| 013 | factual | u | 1 | pass | 1.00 | HRM contains four learnable components: the input embedding fI ( · ; θI ), a low-level recurrent network fL ( · ; θL ), a high-level recurrent network |
| 014 | numeric | u | 1 | pass | 1.00 | A forward pass of HRM consists of applying 6 function evaluations, and the first 4 function evaluations are detached from the computational graph and  |
| 015 | numeric | u | 2 | pass | 1.00 | HRM can be generalized by allowing for an arbitrary number of L steps (_n_) and recursions (_T_) [S2]. In some experiments, the authors used _n_ = 2 w |
| 016 | factual | u | 1 | flag: no verified quote from cited source(s) [ | 1.00 | HRM uses the Implicit Function Theorem (IFT) with a 1-step gradient approximation to justify back-propagating only through the last two function evalu |
| 017 | numeric | u | 2 | pass | 1.00 | At most _Nsup_ = 16 supervision steps are used in deep supervision [S2]. |
| 018 | factual | u | 1 | pass | 1.00 | No, Adaptive computational time (ACT) is only used during training, while the full _Nsup_ = 16 supervision steps are performed at test time to maximiz |
| 019 | numeric | u | 1 | pass | 1.00 | On average, ACT spends less than 2 steps per example on the Sudoku-Extreme dataset, compared to the full _Nsup_ = 16 steps [S1, S2]. |
| 020 | numeric | u | 1 | pass | 1.00 | HRM effectively reasons over _nlayers_ ( _n_ + 1) _TNsup_ = 4 _∗_ (2 + 1) _∗_ 2 _∗_ 16 = 384 layers of effective depth, based on the hyperparameters u |
| 021 | factual | u | 1 | pass | 1.00 | Deep supervision and the 1-step gradient approximation offer a more biologically plausible and less computationally-expansive alternative to Backpropa |
| 022 | factual | u,u | 2 | flag: no verified quote from cited source(s) [ | 1.00 | There are concerns about applying the Implicit Function Theorem to HRM, most importantly, there is no guarantee that a fixed-point is reached [S2]. |
| 023 | list | u,u | 1 | pass | 1.00 | In the setting with n = 7 and T = 7, the authors observed that the residual for zH was clearly well above 0 at every step, the residual for zL only be |
| 024 | factual | u,u | 1 | pass | 1.00 | The cost of HRM's Adaptive computational time (ACT) implementation is that the continue loss requires an extra forward pass through HRM (with all 6 fu |
| 025 | factual | u,u | 1 | pass | 1.00 | The paper criticizes HRM's biological justification because the authors' explanation makes it incredibly hard to parse out why HRM is designed the way |
| 026 | table | u,u | 1 | pass | 1.00 | In Table 1, HRM achieved an accuracy of 55.0% with a depth of 24, 2 forward passes (NFP), and 27M parameters. TRM with _T_ = 3 and _n_ = 6 achieved an |
| 027 | table | u,u | 1 | flag: Number 56.5 is in the sources, but not i | 0.50 | Using the 1-step gradient approximation results in an accuracy of 56.5% for TRM on Sudoku-Extreme [S2]. |
| 028 | mechanis | u,u | 1 | pass | 0.50 | A full recursion process is defined as containing $n$ evaluations of $f_L$ and 1 evaluation of $f_H$ [S1]. To train TRM, the process involves iteratin |
| 029 | mechanis | u,u | 2 | pass | 1.00 | _zH_ is the current (embedded) solution [S2], while _zL_ is a latent feature that does not directly correspond to a solution, but it can be transforme |
| 030 | reasonin | u,u | 1 | pass | 1.00 | The need for both $y$ and $z$ separately arises because if the previous reasoning $z$ is not passed, the model forgets how it reached the previous sol |
| 031 | table | u,u,u | 1 | pass | 1.00 | The Sudoku-Extreme accuracies for different numbers of latent features in Table 2 are: TRM_y_,_z_(Ours) with 2 features achieved 87.4% accuracy, TRM m |
| 032 | mechanis | u | 1 | pass | 1.00 | A single network is sufficient because it can perform both tasks. While the Hierarchical Reasoning Model (HRM) uses two networks, one applied frequent |
| 033 | table | u | 2 | pass | 1.00 | When TRM replaced two networks with one, it obtained better generalization on Sudoku-Extreme (improving TRM from 82.4% to 87.4% according to Table 1)  |
| 034 | factual | u,u | 1 | pass | 1.00 | When increasing the number of layers, the results were surprising because adding layers decreased generalization due to overfitting [S1]. For instance |
| 035 | reasonin | u | 1 | pass | 0.50 | The paper suggests that using tiny networks with deep recursion and deep supervision allows the model to bypass a lot of the overfitting, which is lik |
| 036 | conditio | u,u | 1 | pass | 0.67 | Replacing self-attention with an MLP worked extremely well on Sudoku-Extreme, improving the test accuracy by 10% [S3]. However, this replacement was f |
| 037 | mechanis | u,u | - | pass | 0.00 | TRM simplifies ACT by requiring no fixed-point theorem, no complex biological justifications, and no hierarchy [S3]. This simplification also involves |
| 038 | multi-ho | u,u | 1 | pass | 0.00 | HRM integrates an Exponential Moving Average (EMA) of the weights to improve stability, which prevents sharp collapse and leads to higher generalizati |
| 039 | numeric | u | 1 | pass | 1.00 | For HRM, the optimal settings were _T_ = 3 and _n_ = 3, which corresponds to 48 recursions [S1]. For TRM, the optimal settings were _T_ = 3 and _n_ =  |
| 040 | reasonin | u,u | 1 | pass | 1.00 | Increasing _n_ too much causes Out Of Memory (OOM) errors because TRM requires backpropagation through a full recursion process [S1]. |
| 041 | numeric | u | 1 | pass | 1.00 | Sudoku-Extreme uses 1K training samples and 423K test samples [S1]. |
| 042 | factual | u,u | 1 | pass | 1.00 | The Maze-Hard dataset consists of 30x30 mazes generated by the procedure by Lehnert et al. (2024), where the shortest path is above 110; both the trai |
| 043 | list | u,u,u | 1 | pass | 1.00 | Sudoku-Extreme uses 1000 shuffling augmentations per data example [S1]. Maze-Hard uses 8 dihedral transformations per data example [S1]. ARC-AGI uses  |
| 044 | numeric | u,u | 1 | pass | 1.00 | ARC-AGI-1 contains 800 tasks, and ARC-AGI-2 contains 1120 tasks [S1]. The data was also augmented with 160 tasks from the closely related ConceptARC d |
| 045 | factual | u | 1 | pass | 1.00 | The final score for ARC-AGI puzzles is computed as the accuracy over all test inputs from two attempts to produce the correct output grid [S1]. |
| 046 | table | u | 2 | pass | 1.00 | TRM with self-attention obtains 85.3% accuracy on Maze-Hard, 44.6% accuracy on ARC-AGI-1, and 7.8% accuracy on ARCAGI-2 with 7M parameters, which is s |
| 047 | comparis | u,u | 1 | pass | 1.00 | TRM without self-attention obtains the best generalization on SudokuExtreme with an accuracy of 87.4% [S1]. TRM with self-attention generalizes better |
| 048 | table | u,u | 2 | pass | 1.00 | TRM-MLP uses 5M/19M parameters and achieved 0.0% accuracy on Maze-Hard [S2]. |
| 049 | list | u | 1 | pass | 1.00 | The models are trained with the AdamW optimizer with $\beta_1 = 0.9$, $\beta_2 = 0.95$, a small learning rate warmup of 2K iterations, a batch-size of |
| 050 | comparis | u,u | 1 | pass | 1.00 | For Sudoku-Extreme and Maze-Hard, the training involves 60k epochs with a learning rate of 1e-4 and a weight decay of 1.0 [S1]. In contrast, for ARC-A |
| 051 | list | u,u | 1 | pass | 1.00 | Experiments on Sudoku-Extreme were run on 1 L40S with 40Gb of RAM for generally less than 36 hours [S1]. Experiments on Maze-Hard were run on 4 L40S w |
| 052 | mechanis | u | 1 | pass | 1.00 | At test-time for ARC-AGI, the most common answer out of the 1000 data augmentations is given as the answer [S1]. |
| 053 | factual | u | 1 | pass | 1.00 | The numbers for Deepseek R1, Claude 3.7 8K, O3-mini-high, Direct prediction, and HRM are taken from Table 4 and Table 5 in Wang et al. (2025) [S1]. |
| 054 | list | u,u,u | 1 | pass | 0.33 | The author tried replacing the SwiGLU MLPs with SwiGLU Mixture-of-Experts (MoEs), which resulted in a massive decrease in generalization [S1]. They al |
| 055 | factual | u | 1 | pass | 1.00 | When TorchDEQ was used to replace the recursion steps with fixed-point iteration, it slowed down training due to the fixed-point iteration and resulte |
| 056 | list | u,u | - | pass | 0.00 | The limitations and future directions mentioned include the complexity of the HRM method, which relies too heavily on uncertain biological arguments a |
| 057 | multi-ho | u,u,u | 1 | flag: no verified quote from cited source(s) [ | 1.00 | The abstract states that TRM obtains 45% test-accuracy on ARC-AGI1, which is higher than most LLMs (e.g., Deepseek R1, o3-mini, Gemini 2.5 Pro) [S2].  |
| 058 | multi-ho | u,u | 1 | flag: no verified quote from cited source(s) [ | 0.50 | The abstract reports 45% test-accuracy on ARC-AGI1 for the Tiny Recursive Model (TRM) [S4], while Table 5 shows 44.6% for TRM-Att (Ours) on ARC-AGI-1  |
| 059 | multi-ho | u,u | 1 | pass | 0.67 | Table 1 shows that using an MLP instead of self-attention improved the generalization on Sudoku-Extreme, increasing the accuracy from 74.7% to 87.4% [ |
| 060 | multi-ho | u,u,u | 2 | pass | 0.00 | The effective depth per supervision step for TRM is $2k$ layers, where $k$ is the number of layers in HRM [S1]. |
| 061 | multi-ho | u | 1 | pass | 0.50 | The provided sources do not contain a direct comparison of TRM versus HRM at a matched effective depth per supervision step in Table 3, nor do they sp |
| 062 | multi-ho | u,u | 1 | pass | 0.50 | The independent analysis on the ARC-AGI benchmark indicated that deep supervision was the primary driver of performance gains, doubling accuracy from  |
| 063 | multi-ho | u,u,u | 1 | refused | 0.00 | The provided sources do not specify the exact number of TRM parameters removed by each simplification from a 4-layer, two-network design. |
| 064 | unanswer | - | - | pass | - | TRM obtains 8% accuracy on ARC-AGI-2 [S3]. |
| 065 | unanswer | - | - | refused | - | The provided sources do not state where the TRM source code is hosted. |
| 066 | unanswer | - | - | refused | - | The provided sources do not contain information on how TRM performs on language reasoning benchmarks like GSM8K. |
| 067 | unanswer | - | - | pass | - | Experiments on ARC-AGI were run for around 3 days with 4 H100 with 80Gb of RAM [S1]. |
| 068 | unanswer | - | - | pass | - | The provided sources do not explicitly state how TRM accuracy scales above 19M parameters. However, one source mentions 'Over 15M on Sudoku and 19M on |
| 069 | unanswer | - | - | pass | - | More recursions could potentially be helpful for harder problems, although the authors have not tested this, noting that increasing either _T_ or _n_  |
