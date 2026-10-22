# Golden QA evaluation: live store (PERA+TRM), json_mode off, S-ids + text-located quotes

Golden file `evals/gold/trm.jsonl` (69 questions: 63 answerable, 6 unanswerable). Store: `/tmp/claude-1000/-home-copper-Git-Template-RAG/24d159d4-229a-4570-887a-d29472273e1a/scratchpad/trm_live_copy` (70 chunks, 63 usable). LLM json_mode=`off`, policy=`balanced`, k=5. 'Correct' = the answer contains the facts listed in the gold sidecar: a lower bound, read the answers below.

## 1. Ingestion: is the evidence in a usable chunk?

- usable: 100% (101/101)
- rejected: 0% (0/101)
- split: 0% (0/101)
- absent: 0% (0/101)

## 2. Retrieval (answerable questions)

- an evidence chunk in the top 5: 90% (57/63)
- evidence chunk ranked first: 78% (49/63)
- all of a question's evidence quotes covered by the top 5: 81% (51/63)

## 3. Answers

- answered (did not refuse): 94% (59/63)
- delivered (answered and passed the gates): 87% (55/63)
- contains every required fact: 73% (46/63)
- contains every required fact **and** delivered: 70% (44/63)
- mean share of required facts present: 0.79
- a verified quote comes from an evidence chunk: 86% (54/63)
- correct among flagged answers (false alarms): 50% (2/4)

## 4. Unanswerable questions (right behaviour: refuse)

- refused: 50% (3/6)
- answered but flagged: 0% (0/6)
- answered and passed the gates (the dangerous case): 50% (3/6)

## 5. By question type (answerable)

| type | n | evidence in top-k | delivered | every fact | delivered and every fact |
|---|---:|---:|---:|---:|---:|
| comparison | 2 | 2 | 2 | 2 | 2 |
| conditional | 1 | 1 | 1 | 0 | 0 |
| factual | 17 | 15 | 15 | 14 | 13 |
| list | 8 | 8 | 8 | 7 | 7 |
| mechanism | 6 | 6 | 6 | 3 | 3 |
| multi-hop | 8 | 7 | 4 | 1 | 1 |
| numeric | 12 | 11 | 11 | 12 | 11 |
| reasoning | 3 | 3 | 3 | 3 | 3 |
| table | 6 | 4 | 5 | 4 | 4 |

## 6. Every question

| id | type | ev. | rank | outcome | facts | answer |
|---|---|---|---|---|---|---|
| 001 | factual | u | - | refused | 0.00 | The provided sources do not state who wrote 'Less is More: Recursive Reasoning with Tiny Networks' or where the author is affiliated. |
| 002 | numeric | u | 1 | pass | 1.00 | TRM uses 7M parameters [S3]. The abstract reports that TRM obtains 45% test-accuracy on ARC-AGI1 and 8% on ARC-AGI-2 [S1]. |
| 003 | factual | u | 2 | pass | 1.00 | TRM has 2 layers [S1, S3]. |
| 004 | numeric | u | 1 | pass | 1.00 | TRM uses 7M parameters, which is less than 0.01% of the parameters of most LLMs like Deepseek R1, o3-mini, and Gemini 2.5 Pro [S1]. |
| 005 | factual | u | 1 | pass | 1.00 | Auto-regressive Large Language Models (LLMs) are error-prone on hard question-answer problems because they generate their answer auto-regressively, wh |
| 006 | list | u | 1 | pass | 1.00 | Chain-of-thought (CoT) has several drawbacks listed, including being expensive, requiring high-quality reasoning data which may not be available, and  |
| 007 | numeric | u | 1 | pass | 1.00 | Gemini 2.5 Pro obtains 4.9% test accuracy on ARC-AGI-2 [S1, S2]. |
| 008 | factual | u | - | pass | 1.00 | The two main novelties of HRM are leveraging recursion from two networks operating at different frequencies (high frequency versus low frequency) and  |
| 009 | factual | u,u | 1 | pass | 1.00 | An independent analysis on the ARC-AGI benchmark showed that deep supervision seems to be the primary driver of the performance gains [S1]. |
| 010 | numeric | u | 1 | pass | 1.00 | TRM improved the state-of-the-art test accuracy on SudokuExtreme from 55% to 87%, on Maze-Hard from 75% to 85%, on ARC-AGI-1 from 40% to 45%, and on A |
| 011 | mechanis | u,u | 1 | pass | 1.00 | TRM performs two update steps inside each improvement step: i) recursively updating its latent _z_ _n_ times given the question _x_, current answer _y |
| 012 | list | u | 1 | pass | 1.00 | HRM contains four learnable components: the input embedding fI (·; θI), the low-level recurrent network fL (·; θL), the high-level recurrent network f |
| 013 | factual | u | 1 | pass | 1.00 | HRM contains four learnable components: the input embedding fI ( · ; θI ), a low-level recurrent network fL ( · ; θL ), a high-level recurrent network |
| 014 | numeric | u | 1 | pass | 1.00 | A forward pass of HRM consists of applying 6 function evaluations, and only the last 2 of these recursions are back-propagated through [S1, S2]. |
| 015 | numeric | u | 1 | pass | 1.00 | In all experiments, HRM uses _n_ = 2 and _T_ = 2 [S1]. |
| 016 | factual | u | 1 | pass | 1.00 | HRM uses the Implicit Function Theorem (IFT) and one-step approximation to justify back-propagating only through the last two function evaluations [S2 |
| 017 | numeric | u | - | pass | 1.00 | The maximum number of supervision steps used in deep supervision is _Nsup_ = 16 [S1]. |
| 018 | factual | u | 1 | pass | 1.00 | No, ACT is only used during training, while the full _Nsup_ = 16 supervision steps are done at test time to maximize downstream performance [S1], [S2] |
| 019 | numeric | u | 1 | flag: no verified quote from cited source(s) [ | 1.00 | On average, ACT spends less than 2 steps per example on the Sudoku-Extreme dataset, compared to the full _Nsup_ = 16 steps [S1, S2]. |
| 020 | numeric | u | 1 | pass | 1.00 | HRM effectively reasons over _nlayers_ ( _n_ + 1) _TNsup_ = 4 _∗_ (2 + 1) _∗_ 2 _∗_ 16 = 384 layers of effective depth [S1]. |
| 021 | factual | u | 1 | pass | 1.00 | Deep supervision and the 1-step gradient approximation offer a more biologically plausible and less computationally-expansive alternative to Backpropa |
| 022 | factual | u,u | 1 | flag: no verified quote from cited source(s) [ | 1.00 | The main concern with applying the Implicit Function Theorem to HRM is that there is no guarantee that a fixed-point is reached [S1, S2]. |
| 023 | list | u,u | 1 | pass | 1.00 | In the setting where n = 7 and T = 7, the authors observed that the residual for zH was clearly well above 0 at every step [S1], the residual for zL o |
| 024 | factual | u,u | 1 | pass | 1.00 | The cost of HRM's Adaptive computational time (ACT) implementation is that the continue loss, which is part of the Q-learning objective, requires an e |
| 025 | factual | u,u | 1 | pass | 0.50 | The paper criticizes HRM's biological justification because it relies on uncertain biological arguments and fixed-point theorems that are not guarante |
| 026 | table | u,u | - | refused | 0.00 | I don't know based on the provided sources. |
| 027 | table | u,u | 1 | pass | 1.00 | Using the approach that applies a full recursion process containing $n$ evaluations of $f_L$ and 1 evaluation of $f_H$ instead of the 1-step gradient  |
| 028 | mechanis | u,u | 1 | pass | 0.50 | A full recursion process is defined as containing $n$ evaluations of $f_L$ and 1 evaluation of $f_H$ [S1]. To train TRM, the process involves iteratin |
| 029 | mechanis | u,u | 1 | pass | 1.00 | _zH_ is the current (embedded) solution, which is obtained by reversing the embedding and rounding to the nearest token using the argmax operation [S1 |
| 030 | reasonin | u,u | 1 | pass | 1.00 | The model needs both the previous solution (_y_) and the previous reasoning (_z_) because if the previous reasoning (_z_) were not passed, the model w |
| 031 | table | u,u,u | - | pass | 0.00 | The provided sources mention that having only _y_ and _z_ led to better test accuracy on Sudoku-Extreme compared to using more or less latent variable |
| 032 | mechanis | u | 1 | pass | 0.00 | A single network can perform both tasks in TRM by recursing on its latent reasoning feature and progressively improving its final answer [S3]. |
| 033 | table | u | 2 | pass | 1.00 | When TRM replaced two networks with one, it obtained better generalization on Sudoku-Extreme (improving TRM from 82.4% to 87.4%; see Table 1) while re |
| 034 | factual | u,u | 1 | pass | 0.33 | When increasing the number of layers, the results were surprising because adding layers decreased generalization due to overfitting [S1]. Conversely,  |
| 035 | reasonin | u | 1 | pass | 1.00 | The paper suggests that using tiny networks with deep recursion and deep supervision allows the models to bypass a lot of the overfitting that can occ |
| 036 | conditio | u,u | 1 | pass | 0.33 | Replacing the self-attention layer with an MLP worked extremely well on Sudoku-Extreme, improving the test accuracy by 10% [S2]. |
| 037 | mechanis | u,u | 4 | pass | 0.67 | TRM simplifies ACT by removing the need for the expensive second forward pass by getting rid of the continue loss from the Q-learning and instead lear |
| 038 | multi-ho | u,u | 1 | pass | 0.00 | HRM tends to overfit quickly and then diverge on small data like Sudoku-Extreme and MazeHard, so an Exponential Moving Average (EMA) of the weights is |
| 039 | numeric | u | 1 | pass | 1.00 | The optimal recursion settings found for achieving optimal generalization on Sudoku-Extreme were _T_ = 3, _n_ = 3 for HRM (equivalent to 48 recursions |
| 040 | reasonin | u,u | 1 | pass | 1.00 | Increasing $n$ too much causes Out Of Memory (OOM) errors because TRM requires backpropagation through a full recursion process [S1]. |
| 041 | numeric | u | 1 | pass | 1.00 | Only 1K training samples are used to test small-sample learning on Sudoku-Extreme, and testing is done on 423K samples [S1]. |
| 042 | factual | u,u | 1 | pass | 1.00 | The Maze-Hard dataset consists of 30x30 mazes generated by the procedure by Lehnert et al. (2024) where the shortest path is above 110 in length, and  |
| 043 | list | u,u,u | 1 | pass | 1.00 | Sudoku-Extreme uses 1000 shuffling augmentations per data example [S1]. Maze-Hard uses 8 dihedral transformations per data example [S1]. ARC-AGI uses  |
| 044 | numeric | u,u | 1 | pass | 1.00 | ARC-AGI-1 contains 800 tasks, and ARC-AGI-2 contains 1120 tasks. Additionally, the data was augmented with 160 tasks from the closely related ConceptA |
| 045 | factual | u | 1 | pass | 1.00 | The final score for ARC-AGI puzzles is computed as the accuracy over all test inputs from two attempts to produce the correct output grid [S1], [S5]. |
| 046 | table | u | 1 | pass | 1.00 | TRM with self-attention obtains 85.3% accuracy on Maze-Hard, 44.6% accuracy on ARC-AGI-1, and 7.8% accuracy on ARCAGI-2, which is significantly higher |
| 047 | comparis | u,u | 1 | pass | 1.00 | TRM without self-attention obtains the best generalization on SudokuExtreme with an accuracy of 87.4% [S1]. TRM with self-attention generalizes better |
| 048 | table | u,u | 1 | pass | 1.00 | TRM-MLP uses 5M/19M1 parameters, and it achieved 0.0 accuracy on Maze-Hard [S1]. |
| 049 | list | u | 1 | pass | 1.00 | All models are trained with the AdamW optimizer with $\beta_1 = 0.9$, $\beta_2 = 0.95$, a small learning rate warmup of 2K iterations, a batch-size of |
| 050 | comparis | u,u | 1 | pass | 1.00 | For Sudoku-Extreme and Maze-Hard, the training involves 60k epochs with a learning rate of 1e-4 and a weight decay of 1.0 [S1]. In contrast, for ARC-A |
| 051 | list | u,u | 1 | pass | 1.00 | Experiments on Sudoku-Extreme were run on 1 L40S with 40Gb of RAM for generally less than 36 hours [S1]. Experiments on Maze-Hard were run on 4 L40S w |
| 052 | mechanis | u | 1 | pass | 1.00 | At test-time for ARC-AGI, the most common answer out of the 1000 data augmentations is given as the answer [S1]. |
| 053 | factual | u | 2 | pass | 1.00 | The numbers for Deepseek R1, Claude 3.7 8K, O3-mini-high, Direct prediction, and HRM are taken from Table 4 and 5 in Wang et al. (2025) [S2]. |
| 054 | list | u,u,u | 1 | pass | 0.33 | The author tried replacing the SwiGLU MLPs with SwiGLU Mixture-of-Experts (MoEs), but this resulted in a massive decrease in generalization [S1]. They |
| 055 | factual | u | 1 | pass | 1.00 | Replacing the recursion steps with fixed-point iteration using TorchDEQ slowed down training and resulted in worse generalization [S1]. |
| 056 | list | u,u | 3 | pass | 1.00 | The conclusion names several limitations and future directions. Limitations include the fact that every choice made is not guaranteed to be optimal on |
| 057 | multi-ho | u,u,u | 1 | flag: the answer cites no source | 0.00 | The models in Table 5 that score higher than TRM are Deepseek R1 (15.8% on ARC-1), Claude 3.7 16K (28.6% on ARC-1), o3-mini-high (34.5% on ARC-1), and |
| 058 | multi-ho | u,u | 4 | flag: no verified quote from cited source(s) [ | 0.50 | The abstract reports 45% test-accuracy on ARC-AGI-1 for the Tiny Recursive Model (TRM) [S4], while Table 5 shows 44.6% accuracy for TRM with self-atte |
| 059 | multi-ho | u,u | - | pass | 0.67 | Table 1 shows the comparison of TRM on Sudoku-Extreme, which indicates that using an MLP instead of self-attention improved the generalization from 74 |
| 060 | multi-ho | u,u,u | 3 | refused | 0.00 | The provided sources do not state TRM's total effective depth across all supervision steps at its default setting. |
| 061 | multi-ho | u | 3 | pass | 1.00 | At a matched effective depth per supervision step in Table 3, TRM achieves a higher accuracy than HRM when T = 3, with TRM reaching 87.4% compared to  |
| 062 | multi-ho | u,u | 1 | pass | 0.00 | The independent analysis on the ARC-AGI benchmark indicated that deep supervision was the main factor in performance gains, with deep supervision doub |
| 063 | multi-ho | u,u,u | 1 | refused | 0.00 | The provided sources do not specify the exact number of TRM parameters removed by each simplification from a 4-layer, two-network design. |
| 064 | unanswer | - | - | pass | - | TRM obtains 7.8% accuracy on ARCAGI-2 [S1]. |
| 065 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
| 066 | unanswer | - | - | refused | - | The provided sources do not contain information about how TRM performs on language reasoning benchmarks like GSM8K. |
| 067 | unanswer | - | - | pass | - | Experiments on ARC-AGI were run for around 3 days [S1]. |
| 068 | unanswer | - | - | refused | - | The provided sources do not contain information on how TRM accuracy scales above 19M parameters. |
| 069 | unanswer | - | - | pass | - | More recursions could potentially be helpful for harder problems, although the authors have not tested this, given their limited resources, as increas |
