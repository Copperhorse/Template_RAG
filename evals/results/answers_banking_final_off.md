# Answer-level evaluation

32 answerable and 12 unanswerable queries. Rates are Wilson 95% intervals. "Correct" = the answer contains a hand-written key phrase, so it is a lower bound.

## Answerable queries

- gold chunk was in the context the model saw: 94% (30/32; 95% CI 80-98)
- answered (did not refuse): 100% (32/32; 95% CI 89-100)
- answered and cites a chunk that holds the gold snippet: 75% (24/32; 95% CI 58-87)
- answered and contains the expected fact: 88% (28/32; 95% CI 72-95)
- answered and passed every gate: 75% (24/32; 95% CI 58-87)

## Do the gates discriminate?

- correct, among answers that **passed** the gates: 88% (21/24; 95% CI 69-96)
- correct, among answers the gates **flagged**: 88% (7/8; 95% CI 53-98)

## Unanswerable queries (the right behaviour is to refuse)

- refused: 50% (6/12; 95% CI 25-75)
- answered but flagged by the gates: 0% (0/12; 95% CI 0-24)
- answered and passed the gates (the dangerous case): 50% (6/12; 95% CI 25-75)

## If `strict=True` were used (flagged answers become refusals)

- answerable queries answered: 75% (24/32; 95% CI 58-87)
- answerable queries answered correctly: 66% (21/32; 95% CI 48-80)
- unanswerable queries refused: 50% (6/12; 95% CI 25-75)

Mean latency 4.8s per question. Why answers were flagged: {'Unsupported number in answer': 1, 'no verified quote from cited source(s) [S2]': 4, 'no verified quote from cited source(s) [S1]': 2, 'the answer cites no source': 1}

## Per-query record

| id | type | refused | gates | correct | cites gold | answer |
|---|---|---|---|---|---|---|
| b01 | doc | no | flag: Unsupported number in answer: [5] | True | False | Every banking company, not being a schedule bank, shall maintain by wa |
| b02 | doc | no | pass | True | True | No, except as authorized under section 7, a banking company is not all |
| b03 | doc | no | pass | True | True | Whoever wilfully makes a statement which is false in any material part |
| b04 | doc | no | pass | True | True | The Federal Government may suspend the operation of the Ordinance for  |
| b05 | doc | no | pass | False | False | The total period of super session, after extension, does not exceed th |
| b06 | doc | no | pass | True | True | The Banking Mohtasib shall be appointed by the President in consultati |
| b07 | doc | no | pass | True | True | The Banking Mohtasib holds office for a period of three years and is n |
| b08 | doc | no | pass | True | True | Every company carrying on the business of banking in Pakistan shall us |
| b09 | doc | no | pass | True | True | A deposit is considered unclaimed if there has been no transaction at  |
| b10 | doc | no | pass | False | True | A bank may be barred from paying dividends on its shares if the State  |
| b11 | doc | no | flag: no verified quote from cited source(s) [ | True | False | Loans and advances made by a banking company for agricultural and othe |
| b12 | doc | no | pass | False | False | A person holding the office of a director of a banking company may als |
| b13 | doc | no | pass | True | True | A director of a banking company, who is not its chief executive or a d |
| b14 | doc | no | pass | True | True | Any break of less than three years in the continuity of office is disr |
| b15 | doc | no | pass | True | True | Banking means the accepting, for the purpose of lending or investment, |
| b16 | doc | no | pass | True | True | No, a company engaged in the manufacture of goods or carrying on any t |
| b17 | doc | no | pass | True | True | The official liquidator is responsible for submitting lists of debtors |
| b18 | doc | no | flag: no verified quote from cited source(s) [ | False | True | Banking companies may be managed by a managing agent [S1]. |
| b19 | doc | no | pass | True | True | Yes, banking companies are bound to comply with the directions issued  |
| b20 | doc | no | flag: no verified quote from cited source(s) [ | True | True | Before a company can carry on banking business in Pakistan, it must ho |
| b21 | doc | no | flag: no verified quote from cited source(s) [ | True | True | Every banking company “and every financial institution specified in se |
| b22 | doc | no | pass | True | True | With effect on and from the 1st September, 1967, the amount which a ba |
| b23 | doc | no | pass | True | True | The minimum paid-up capital a banking company must have may be determi |
| b24 | doc | no | flag: the answer cites no source | True | False | No company, firm, or person that is not a banking company, a corporati |
| b25 | doc | no | pass | True | True | Section 3A applies the Ordinance to certain financial institutions, in |
| b26 | doc | no | pass | True | False | The Ordinance does not replace the Companies Ordinance, 1984; rather,  |
| b27 | doc | no | flag: no verified quote from cited source(s) [ | True | False | The State Bank may supersede the Board of Directors of a banking compa |
| b28 | doc | no | pass | True | True | Approved securities mean the securities in which a trustee may invest  |
| b29 | doc | no | pass | True | True | The Banking Mohtasib shall not hold any other office of profit in the  |
| b30 | doc | no | pass | True | False | The statement of cash reserve must be submitted to the State Bank befo |
| b31 | doc | no | flag: no verified quote from cited source(s) [ | True | True | The Banking Mohtasib can be removed from office on the ground that the |
| b32 | doc | no | pass | True | True | A list of debtors must contain the rate of interest, if any, and the d |
| n01 | none | yes | pass | None | None | The provided sources do not contain information on how to apply for a  |
| n02 | none | yes | pass | None | None | I don't know based on the provided sources. |
| n03 | none | yes | pass | None | None | I don't know based on the provided sources. |
| n04 | none | yes | pass | None | None | I don't know based on the provided sources. |
| n05 | none | no | pass | None | None | The provided sources mention that there are 'Rates proposed to be char |
| n06 | none | no | pass | None | None | In every proceeding for the winding-up of a banking company where a wi |
| n07 | none | no | pass | None | None | The provided sources do not mention the Basel III capital buffers a ba |
| n08 | none | no | pass | None | None | The penalty for wilfully making a false statement in any return, balan |
| n09 | none | no | pass | None | None | The provided sources do not specify a fine that can be imposed on the  |
| n10 | none | yes | pass | None | None | The provided sources do not contain information about a section that r |
| n11 | none | yes | pass | None | None | The provided sources do not state the retirement age of the Governor o |
| n12 | none | no | pass | None | None | The complainant must intimate in writing to the concerned bank their i |

## Gate policies, same replies re-judged

| policy | answered | flagged | false alarms (correct answers flagged) | errors missed (wrong answers passed) | usable (correct and accepted) | accepted and citing the gold chunk | unanswerable that passed |
|---|---:|---:|---:|---:|---:|---:|---:|
| strict | 32 | 25% (8/32) | 25% (7/28) | 75% (3/4) | 66% (21/32) | 62% (20/32) | 50% (6/12) |
| tolerant | 32 | 25% (8/32) | 25% (7/28) | 75% (3/4) | 66% (21/32) | 62% (20/32) | 50% (6/12) |
| balanced | 32 | 22% (7/32) | 21% (6/28) | 75% (3/4) | 69% (22/32) | 62% (20/32) | 50% (6/12) |
| lenient | 32 | 6% (2/32) | 7% (2/28) | 100% (4/4) | 81% (26/32) | 75% (24/32) | 50% (6/12) |
| balanced + relevance gate 0.183 | 32 | 22% (7/32) | 21% (6/28) | 75% (3/4) | 69% (22/32) | 62% (20/32) | 42% (5/12) |
| balanced + relevance gate 0.211 | 32 | 22% (7/32) | 21% (6/28) | 75% (3/4) | 69% (22/32) | 62% (20/32) | 42% (5/12) |
| balanced + relevance gate 0.304 | 31 | 23% (7/31) | 22% (6/27) | 75% (3/4) | 66% (21/32) | 62% (20/32) | 17% (2/12) |
