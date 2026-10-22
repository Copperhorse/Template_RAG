# Answer-level evaluation

32 answerable and 12 unanswerable queries. Rates are Wilson 95% intervals. "Correct" = the answer contains a hand-written key phrase, so it is a lower bound.

## Answerable queries

- gold chunk was in the context the model saw: 97% (31/32; 95% CI 84-99)
- answered (did not refuse): 100% (32/32; 95% CI 89-100)
- answered and cites a chunk that holds the gold snippet: 81% (26/32; 95% CI 65-91)
- answered and contains the expected fact: 97% (31/32; 95% CI 84-99)
- answered and passed every gate: 81% (26/32; 95% CI 65-91)

## Do the gates discriminate?

- correct, among answers that **passed** the gates: 100% (26/26; 95% CI 87-100)
- correct, among answers the gates **flagged**: 83% (5/6; 95% CI 44-97)

## Unanswerable queries (the right behaviour is to refuse)

- refused: 67% (8/12; 95% CI 39-86)
- answered but flagged by the gates: 17% (2/12; 95% CI 5-45)
- answered and passed the gates (the dangerous case): 17% (2/12; 95% CI 5-45)

## If `strict=True` were used (flagged answers become refusals)

- answerable queries answered: 81% (26/32; 95% CI 65-91)
- answerable queries answered correctly: 81% (26/32; 95% CI 65-91)
- unanswerable queries refused: 83% (10/12; 95% CI 55-95)

Mean latency 4.8s per question. Why answers were flagged: {'Unsupported sentence in answer (16 of 23 words not in the so': 1, 'the answer cites no source': 1, 'no verified quote from cited source(s) [1]': 1, 'no verified quote from cited source(s) [2]': 3, 'no verified quote from cited source(s) [2, 4, 5]': 1, 'Unsupported number in answer': 1}

## Per-query record

| id | type | refused | gates | correct | cites gold | answer |
|---|---|---|---|---|---|---|
| b01 | doc | no | pass | True | True | A banking company that is not a schedule bank must maintain a cash res |
| b02 | doc | no | pass | True | True | No, a banking company is generally not allowed to directly or indirect |
| b03 | doc | no | pass | True | True | Whoever wilfully makes a statement which is false in any material part |
| b04 | doc | no | pass | True | True | The Federal Government may suspend the operation of the Ordinance for  |
| b05 | doc | no | pass | True | True | The total period of suspension, even when extended, shall not exceed o |
| b06 | doc | no | pass | True | True | The Banking Mohtasib shall be appointed by the President in consultati |
| b07 | doc | no | pass | True | True | The Banking Mohtasib holds office for a period of three years and is n |
| b08 | doc | no | pass | True | True | Every company carrying on the business of banking in Pakistan shall us |
| b09 | doc | no | pass | True | True | A deposit counts as unclaimed if no transaction has taken place at the |
| b10 | doc | no | pass | True | True | A bank is barred from paying dividends on its shares until all its cap |
| b11 | doc | no | pass | True | True | Loans and advances made by a banking company for agricultural and othe |
| b12 | doc | no | flag: Unsupported sentence in answer (16 of 23 | True | True | No, a banking company incorporated in Pakistan shall not have a person |
| b13 | doc | no | pass | True | True | A director of a banking company, who is not its chief executive or a d |
| b14 | doc | no | pass | True | True | Any break of less than three years in the continuity of office shall b |
| b15 | doc | no | pass | True | True | Banking is defined as the accepting, for the purpose of lending or inv |
| b16 | doc | no | pass | True | True | No, a company engaged in the manufacture of goods or trade that accept |
| b17 | doc | no | pass | True | True | The official liquidator submits lists of debtors to the High Court fro |
| b18 | doc | no | pass | True | True | No banking company shall employ or be managed by a managing agent [1]. |
| b19 | doc | no | pass | True | True | Yes, banking companies are bound to comply with the directions issued  |
| b20 | doc | no | pass | True | False | A company needs to apply in writing to the State Bank for a licence un |
| b21 | doc | no | pass | True | False | Every banking company "and every financial institution specified in se |
| b22 | doc | no | pass | True | True | With effect on and from September 1, 1967, the amount which a banking  |
| b23 | doc | no | pass | True | True | The minimum paid-up capital a banking company must have is determined  |
| b24 | doc | no | flag: the answer cites no source | True | False | No company, firm, or person who is not a banking company, a corporatio |
| b25 | doc | no | pass | True | True | Section 3A of the Ordinance applies to certain financial institutions  |
| b26 | doc | no | flag: no verified quote from cited source(s) [ | False | False | The Ordinance substituted certain provisions of the Companies Act, 191 |
| b27 | doc | no | flag: no verified quote from cited source(s) [ | True | False | The State Bank may supersede the Board of Directors of a banking compa |
| b28 | doc | no | flag: no verified quote from cited source(s) [ | True | True | Approved securities are defined as the securities in which a trustee m |
| b29 | doc | no | pass | True | True | The Banking Mohtasib shall not hold any other office of profit in the  |
| b30 | doc | no | pass | True | False | The statement of cash reserve must be submitted to the State Bank befo |
| b31 | doc | no | flag: no verified quote from cited source(s) [ | True | True | The Banking Mohtasib may be removed from office on the ground that he  |
| b32 | doc | no | pass | True | True | A list of debtors must contain the rate of interest, if any, and the d |
| n01 | none | yes | pass | None | None | The provided sources do not contain information on how to apply for a  |
| n02 | none | yes | pass | None | None | I don't know based on the provided sources. |
| n03 | none | yes | pass | None | None | I don't know based on the provided sources. |
| n04 | none | yes | pass | None | None | I don't know based on the provided sources. |
| n05 | none | no | flag: no verified quote from cited source(s) [ | None | None | The provided sources list 'Rates proposed to be charged on various typ |
| n06 | none | no | flag: Unsupported number in answer: [2001] | None | None | In a proceeding for the winding-up of a banking company, within ninety |
| n07 | none | yes | pass | None | None | The provided sources do not mention Basel III capital buffers. |
| n08 | none | yes | pass | None | None | The provided sources do not contain information about the penalty for  |
| n09 | none | yes | pass | None | None | The provided sources do not specify a fine that can be imposed on the  |
| n10 | none | no | pass | None | None | The balance-sheet and profit and loss account prepared in terms of Sec |
| n11 | none | yes | pass | None | None | The provided sources do not state the retirement age of the Governor o |
| n12 | none | no | pass | None | None | The complainant must intimate in writing to the concerned bank their i |

## Gate policies, same replies re-judged

| policy | answered | flagged | false alarms (correct answers flagged) | errors missed (wrong answers passed) | usable (correct and accepted) | accepted and citing the gold chunk | unanswerable that passed |
|---|---:|---:|---:|---:|---:|---:|---:|
| strict | 32 | 19% (6/32) | 16% (5/31) | 0% (0/1) | 81% (26/32) | 72% (23/32) | 17% (2/12) |
| tolerant | 32 | 16% (5/32) | 13% (4/31) | 0% (0/1) | 84% (27/32) | 75% (24/32) | 17% (2/12) |
| balanced | 32 | 12% (4/32) | 10% (3/31) | 0% (0/1) | 88% (28/32) | 78% (25/32) | 25% (3/12) |
| lenient | 32 | 3% (1/32) | 3% (1/31) | 100% (1/1) | 94% (30/32) | 81% (26/32) | 33% (4/12) |
| balanced + relevance gate 0.183 | 32 | 12% (4/32) | 10% (3/31) | 0% (0/1) | 88% (28/32) | 78% (25/32) | 17% (2/12) |
| balanced + relevance gate 0.211 | 32 | 12% (4/32) | 10% (3/31) | 0% (0/1) | 88% (28/32) | 78% (25/32) | 17% (2/12) |
| balanced + relevance gate 0.304 | 32 | 12% (4/32) | 10% (3/31) | 0% (0/1) | 88% (28/32) | 78% (25/32) | 17% (2/12) |
