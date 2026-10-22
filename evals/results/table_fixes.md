# Table lookups and the table-cell answer gate

Two changes: (2) tables are chunked so each row says what it is a row of, and (5) the answer gate checks that a number the answer states sits in a table cell whose row and column fit the sentence.

## What changed
- Oversize tables split by rows; the caption and header go into every part; a row whose label only continues the one above ("+ SSD", "w/ ACT", "(ours)") is prefixed with it ("Qwen3-30B-Thinking / + SSD"). Separator rows are normalised.
- `tablecheck.py`: for each number in the answer that is a table cell of a cited chunk, some cell holding it must fit: the row label shares a word or number with the sentence, the previous sentence or the question (an inherited parent is required only when the row's own label is not unique in the table), and the column header must not contradict the sentence (`pass@1` vs `pass@5`, `v5` vs `v6`). Numbers that also occur in the evidence prose are exempt. Policy `lenient` turns it off.

## Measured (small n, one run each)
- Replay over 23 recorded answers (SSD, TRM, PERA) that cite a table: 1 flagged, SSD q022 ("41.5 before SSD and 59.7 after SSD"; 59.7 is the baseline's pass@5). That one is a real wrong-cell answer. No other flags; the TRM q027 false alarm from an earlier version is gone.
- 23 answers is too few to give a false-alarm rate. Two false alarms appeared and were fixed during development on the same data, so the clean count is fitted to it, not an independent test.
- Adversarial `evals gates`: table identical to the one before the check. Full test suite: 479 passed.
- Retrieval: SSD decoding-settings questions q041/q042 now rank the right table chunk first.
- Not settled: SSD unanswerable passes went 0 -> 2 (q066, q070) between runs; not checked whether that is run-to-run variance.

## Known blind spots (not caught)
- Before/after role of a cell (the q023 pattern), direction of change ("from A to B" vs "from B to A").
- Numbers stated in prose; only table cells are checked.
- A label like "no EMA" is not recognised as a continuation row (only `+`, `-`, `w/`, `with`, `(`, `...`), so such rows get no parent label.
- The row match is word overlap: an answer naming the right row words with the wrong number of that row is caught, one naming the wrong row with words the question also contains is not.
