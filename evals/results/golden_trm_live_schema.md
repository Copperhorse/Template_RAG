# Golden QA evaluation: live store (PERA + TRM), json_mode schema; embedder on CPU, 10 rerank candidates

Golden file `evals/gold/trm.jsonl` (69 questions: 63 answerable, 6 unanswerable). Store: `/tmp/claude-1000/-home-copper-Git-Template-RAG/24d159d4-229a-4570-887a-d29472273e1a/scratchpad/trm_live_copy` (70 chunks, 63 usable). LLM json_mode=`schema`, policy=`balanced`, k=5. 'Correct' = the answer contains the facts listed in the gold sidecar: a lower bound, read the answers below.

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

- answered (did not refuse): 97% (61/63)
- delivered (answered and passed the gates): 86% (54/63)
- contains every required fact: 65% (41/63)
- contains every required fact **and** delivered: 62% (39/63)
- mean share of required facts present: 0.76
- a verified quote comes from an evidence chunk: 83% (52/63)
- correct among flagged answers (false alarms): 29% (2/7)

## 4. Unanswerable questions (right behaviour: refuse)

- refused: 33% (2/6)
- answered but flagged: 17% (1/6)
- answered and passed the gates (the dangerous case): 50% (3/6)

## 5. By question type (answerable)

| type | n | evidence in top-k | delivered | every fact | delivered and every fact |
|---|---:|---:|---:|---:|---:|
| comparison | 2 | 2 | 2 | 2 | 2 |
| conditional | 1 | 1 | 1 | 0 | 0 |
| factual | 17 | 15 | 14 | 12 | 11 |
| list | 8 | 8 | 8 | 7 | 7 |
| mechanism | 6 | 6 | 6 | 2 | 2 |
| multi-hop | 8 | 7 | 3 | 1 | 1 |
| numeric | 12 | 11 | 11 | 12 | 11 |
| reasoning | 3 | 3 | 3 | 2 | 2 |
| table | 6 | 4 | 6 | 3 | 3 |

## 6. Every question

| id | type | ev. | rank | outcome | facts | answer |
|---|---|---|---|---|---|---|
| 001 | factual | u | - | refused | 0.00 | The provided sources do not state who wrote 'Less is More: Recursive Reasoning with Tiny Networks' or where the author is affiliated. |
| 002 | numeric | u | 1 | pass | 1.00 | TRM can use 7M parameters when using the TRM-Att configuration [3], and 19M parameters when using the TRM-MLP configuration [3]. The abstract reports  |
| 003 | factual | u | 2 | flag: no verified quote from cited source(s) [ | 0.00 | The provided sources do not explicitly state the number of layers for TRM's network. However, one source mentions that HRM has 4 layers [1], and anoth |
| 004 | numeric | u | 1 | pass | 1.00 | TRM uses 7M parameters, which is less than 0.01% of the parameters of most LLMs mentioned, such as Deepseek R1, o3-mini, and Gemini 2.5 Pro [1]. |
| 005 | factual | u | 1 | pass | 1.00 | Auto-regressive Large Language Models (LLMs) are error-prone on hard question-answer problems because they generate their answers auto-regressively, w |
| 006 | list | u | 1 | pass | 1.00 | Chain-of-thought (CoT) has several drawbacks, including being expensive, requiring high-quality reasoning data which may not be available, and being b |
| 007 | numeric | u | 1 | pass | 1.00 | Gemini 2.5 Pro obtains 4.9% test accuracy on ARC-AGI-2 [2]. |
| 008 | factual | u | - | pass | 0.50 | HRM leverages recursion from two networks operating at different frequencies (high frequency versus low frequency) and deep supervision to learn to im |
| 009 | factual | u,u | 1 | pass | 1.00 | An independent analysis on the ARC-AGI benchmark showed that deep supervision seems to be the primary driver of the performance gains [1]. |
| 010 | numeric | u | 1 | pass | 1.00 | TRM improved the state-of-the-art test accuracy on SudokuExtreme from 55% to 87%, on Maze-Hard from 75% to 85%, on ARC-AGI-1 from 40% to 45%, and on A |
| 011 | mechanis | u,u | 1 | pass | 1.00 | Inside each improvement step, TRM performs two update steps: i) recursively updating its latent _z_ _n_ times given the question _x_, current answer _ |
| 012 | list | u | 1 | pass | 1.00 | HRM contains four learnable components: the input embedding $f_I$ ($	heta_I$), the low-level recurrent network $f_L$ ($	heta_L$), the high-level recur |
| 013 | factual | u | 1 | pass | 1.00 | HRM contains four learnable components: the input embedding f I ( · ; θI ), a low-level recurrent network fL ( · ; θL ), a high-level recurrent networ |
| 014 | numeric | u | 1 | pass | 1.00 | A forward pass of HRM consists of applying 6 function evaluations, and only the last 2 of these recursions are back-propagated through [1, 2]. |
| 015 | numeric | u | 1 | pass | 1.00 | In all experiments, HRM uses n_ = 2 and T_ = 2 [1, 2]. |
| 016 | factual | u | 1 | pass | 1.00 | HRM uses the Implicit Function Theorem (IFT) and one-step approximation to justify back-propagating only through the last two function evaluations [2, |
| 017 | numeric | u | - | pass | 1.00 | The maximum number of supervision steps used in deep supervision is _Nsup_ = 16 [1]. |
| 018 | factual | u | 1 | pass | 1.00 | No, Adaptive computational time (ACT) is only used during training, while the full _Nsup_ = 16 supervision steps are performed at test time to maximiz |
| 019 | numeric | u | 1 | flag: no verified quote from cited source(s) [ | 1.00 | On average, ACT spends less than 2 steps per example on the Sudoku-Extreme dataset, compared to the full _Nsup_ = 16 steps [1, 2]. |
| 020 | numeric | u | 1 | pass | 1.00 | HRM effectively reasons over _nlayers_ ( _n_ + 1) _TNsup_ = 4 _∗_ (2 + 1) _∗_ 2 _∗_ 16 = 384 layers of effective depth, based on the hyperparameters u |
| 021 | factual | u | 1 | pass | 1.00 | Deep supervision and the 1-step gradient approximation offer a more biologically plausible and less computationally-expansive alternative to Backpropa |
| 022 | factual | u,u | 1 | pass | 1.00 | The main concern with applying the Implicit Function Theorem to HRM is that there is no guarantee that a fixed-point is reached [1]. |
| 023 | list | u,u | 1 | pass | 1.00 | In the setting where n = 7 and T = 7, the authors observed that the residual for zH is clearly well above 0 at every step [1], the residual for zL onl |
| 024 | factual | u,u | 1 | pass | 1.00 | The cost of HRM's Adaptive computational time (ACT) implementation is that the continue loss in the Q-learning objective requires an extra forward pas |
| 025 | factual | u,u | 1 | pass | 0.50 | The paper criticizes HRM's biological justification because it makes it incredibly hard to parse out why HRM is designed the way it is [1]. Furthermor |
| 026 | table | u,u | - | pass | 0.40 | Table 1 shows comparisons for HRM and TRM on the Sudoku-Extreme dataset, including % Test accuracy, effective depth per supervision step (T (n + 1) nl |
| 027 | table | u,u | 1 | pass | 1.00 | Using the 1-step gradient approximation in TRM resulted in an improvement on Sudoku-Extreme, increasing the performance from 56.5% to 87.4% [1]. |
| 028 | mechanis | u,u | 1 | pass | 0.50 | TRM defines a full recursion process as containing $n$ evaluations of $f_L$ and 1 evaluation of $f_H$ [1]. The training involves a deep supervision pr |
| 029 | mechanis | u,u | 1 | pass | 0.50 | _zH_ corresponds to the predicted response, while _zL_ is a latent feature that cannot be decoded to a sensible output unless transformed into _zH_ by |
| 030 | reasonin | u,u | 1 | pass | 1.00 | TRM needs both $y$ and $z$ because $z$ acts similarly to a chain-of-thought, helping the model remember how it arrived at the previous solution $y$ [1 |
| 031 | table | u,u,u | - | pass | 0.00 | The provided sources mention that having only _y_ and _z_ led to better test accuracy on Sudoku-Extreme [1]. However, the sources do not provide speci |
| 032 | mechanis | u | 1 | pass | 0.00 | A single network can perform both tasks by doing both tasks, such as iterating on the latent reasoning feature and updating the solution, as considere |
| 033 | table | u | 2 | pass | 1.00 | When TRM replaced two networks with one, it obtained better generalization on Sudoku-Extreme (improving TRM from 82.4% to 87.4%; see Table 1) while re |
| 034 | factual | u,u | 1 | pass | 0.33 | When the number of layers was increased, it was found that adding layers decreased generalization due to overfitting [1]. Conversely, decreasing the n |
| 035 | reasonin | u | 1 | pass | 0.50 | The paper suggests that using tiny networks with deep recursion and deep supervision allows the model to bypass a lot of the overfitting [1]. Addition |
| 036 | conditio | u,u | 1 | pass | 0.33 | Replacing self-attention with an MLP worked extremely well on Sudoku-Extreme, improving test accuracy by 10% [2]. This replacement resulted in better  |
| 037 | mechanis | u,u | 4 | pass | 0.67 | TRM simplifies ACT by removing the need for the expensive second forward pass by getting rid of the continue loss from the Q-learning and instead lear |
| 038 | multi-ho | u,u | 1 | pass | 0.00 | HRM tends to overfit quickly and then diverge on small data like Sudoku-Extreme and MazeHard, so an Exponential Moving Average (EMA) of the weights is |
| 039 | numeric | u | 1 | pass | 1.00 | The optimal recursion settings found were _T_ = 3, _n_ = 3 for HRM, which is equivalent to 48 recursions, and _T_ = 3, _n_ = 6 for TRM, which is equiv |
| 040 | reasonin | u,u | 1 | pass | 1.00 | Increasing $n$ too much causes Out Of Memory (OOM) errors because TRM requires backpropagation through a full recursion process [1]. |
| 041 | numeric | u | 1 | pass | 1.00 | Sudoku-Extreme uses 1K training samples and 423K samples for testing [1]. |
| 042 | factual | u,u | 1 | pass | 1.00 | The Maze-Hard dataset consists of 30x30 mazes generated by the procedure by Lehnert et al. (2024), where the shortest path is above 110; both the trai |
| 043 | list | u,u,u | 1 | pass | 1.00 | Sudoku-Extreme uses 1000 shuffling augmentations per data example [1]. Maze-Hard uses 8 dihedral transformations per data example [1]. ARC-AGI uses 10 |
| 044 | numeric | u,u | 1 | pass | 1.00 | ARC-AGI-1 contains 800 tasks, and ARC-AGI-2 contains 1120 tasks [1]. Additionally, the data was augmented with 160 tasks from the closely related Conc |
| 045 | factual | u | 1 | pass | 1.00 | The final score for ARC-AGI puzzles is computed as the accuracy over all test inputs from two attempts to produce the correct output grid [1]. |
| 046 | table | u | 1 | pass | 0.83 | TRM-Att obtains 85.3% accuracy on Maze-Hard, 44.6% accuracy on ARC-AGI-1, and 7.8% accuracy on ARCAGI-2 [1, 4]. In comparison, HRM obtained 74.5% accu |
| 047 | comparis | u,u | 1 | pass | 1.00 | TRM without self-attention obtains the best generalization on SudokuExtreme with an accuracy of 87.4% [1]. However, TRM with self-attention generalize |
| 048 | table | u,u | 1 | pass | 1.00 | TRM-MLP uses 5M/19M1 parameters and achieved 0.0 accuracy on Maze-Hard [1]. |
| 049 | list | u | 1 | pass | 1.00 | All models are trained with the AdamW optimizer, with _β_ 1 = 0.9, _β_ 2 = 0.95, a small learning rate warmup of 2K iterations, a batch-size of 768, a |
| 050 | comparis | u,u | 1 | pass | 1.00 | For Sudoku-Extreme and Maze-Hard, the training involves 60k epochs with a learning rate of 1e-4 and a weight decay of 1.0 [1]. For ARC-AGI, the traini |
| 051 | list | u,u | 1 | pass | 1.00 | Experiments on Sudoku-Extreme were run on 1 L40S with 40Gb of RAM for generally less than 36 hours [1]. Experiments on Maze-Hard were run on 4 L40S wi |
| 052 | mechanis | u | 1 | pass | 1.00 | At test-time for ARC-AGI, the most common answer out of the 1000 data augmentations is given as the answer [1]. |
| 053 | factual | u | 2 | flag: no verified quote from cited source(s) [ | 1.00 | The numbers for Deepseek R1, Claude 3.7 8K, O3-mini-high, Direct prediction, and HRM are taken from Wang et al. (2025) [2]. |
| 054 | list | u,u,u | 1 | pass | 0.33 | The author tried replacing the SwiGLU MLPs by SwiGLU Mixture-of-Experts (MoEs), but found that generalization decreased massively [1]. They also tried |
| 055 | factual | u | 1 | pass | 1.00 | When TorchDEQ was used to replace the recursion steps with fixed-point iteration, it slowed down training due to the fixed-point iteration and resulte |
| 056 | list | u,u | 3 | pass | 1.00 | The conclusion names several limitations and future directions. Limitations include the fact that every choice made in the approach is not guaranteed  |
| 057 | multi-ho | u,u,u | 1 | flag: no verified quote from cited source(s) [ | 0.00 | The models in Table 5 that score higher than TRM are Deepseek R1 (15.8% on ARC-1), Claude 3.7 16K (28.6% on ARC-1), o3-mini-high (34.5% on ARC-1), and |
| 058 | multi-ho | u,u | 4 | flag: no verified quote from cited source(s) [ | 0.50 | The abstract reports a 45% test-accuracy on ARC-AGI-1 for the Tiny Recursive Model (TRM) [4], while Table 5 shows 44.6% for TRM with self-attention (T |
| 059 | multi-ho | u,u | - | pass | 0.67 | Table 1 shows that using an MLP instead of self-attention obtained better generalization on Sudoku-Extreme, improving the accuracy from 74.7% to 87.4% |
| 060 | multi-ho | u,u,u | 3 | flag: no verified quote from cited source(s) [ | 0.00 | The total effective depth for TRM is 2k layers [1]. |
| 061 | multi-ho | u | 3 | pass | 1.00 | At a matched effective depth per supervision step in Table 3, TRM achieves 87.4% accuracy when T = 3, while HRM achieves 61.6% accuracy [3]. |
| 062 | multi-ho | u,u | 1 | flag: no verified quote from cited source(s) [ | 0.00 | The independent analysis on the ARC-AGI benchmark indicated that deep supervision was the main factor in performance gains [1]. In contrast, the autho |
| 063 | multi-ho | u,u,u | 1 | refused | 0.00 | The provided sources do not specify the exact number of TRM parameters removed by each simplification from a 4-layer, two-network design. |
| 064 | unanswer | - | - | flag: no verified quote from cited source(s) [ | - | TRM-Att obtains 7.8% accuracy on ARCAGI-2 [1, 5]. |
| 065 | unanswer | - | - | refused | - | The provided sources do not state where the TRM source code is hosted. |
| 066 | unanswer | - | - | refused | - | The provided sources do not contain information about how TRM performs on language reasoning benchmarks like GSM8K. |
| 067 | unanswer | - | - | pass | - | Experiments on ARC-AGI were run for around 3 days [1]. |
| 068 | unanswer | - | - | pass | - | The provided sources do not explicitly state how TRM accuracy scales above 19M parameters. However, one source shows that TRM-MLP(Ours) with 19M param |
| 069 | unanswer | - | - | pass | - | More recursions could be helpful for harder problems, but increasing either _T_ or _n_ incurs massive slowdowns [1]. |
