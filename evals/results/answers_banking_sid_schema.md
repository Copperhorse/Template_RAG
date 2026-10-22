# Answer-level evaluation

32 answerable and 12 unanswerable queries. Rates are Wilson 95% intervals. "Correct" = the answer contains a hand-written key phrase, so it is a lower bound.

## Answerable queries

- gold chunk was in the context the model saw: 94% (30/32; 95% CI 80-98)
- answered (did not refuse): 100% (32/32; 95% CI 89-100)
- answered and cites a chunk that holds the gold snippet: 78% (25/32; 95% CI 61-89)
- answered and contains the expected fact: 84% (27/32; 95% CI 68-93)
- answered and passed every gate: 78% (25/32; 95% CI 61-89)

## Do the gates discriminate?

- correct, among answers that **passed** the gates: 84% (21/25; 95% CI 65-94)
- correct, among answers the gates **flagged**: 86% (6/7; 95% CI 49-97)

## Unanswerable queries (the right behaviour is to refuse)

- refused: 58% (7/12; 95% CI 32-81)
- answered but flagged by the gates: 8% (1/12; 95% CI 1-35)
- answered and passed the gates (the dangerous case): 33% (4/12; 95% CI 14-61)

## If `strict=True` were used (flagged answers become refusals)

- answerable queries answered: 78% (25/32; 95% CI 61-89)
- answerable queries answered correctly: 66% (21/32; 95% CI 48-80)
- unanswerable queries refused: 67% (8/12; 95% CI 39-86)

Mean latency 4.9s per question. Why answers were flagged: {'Unsupported number in answer': 2, 'no verified quote from cited source(s) [S2]': 3, 'no verified quote from cited source(s) [S1]': 2, 'no verified quote from cited source(s) [S2, S5]': 1}

## Per-query record

| id | type | refused | gates | correct | cites gold | answer |
|---|---|---|---|---|---|---|
| b01 | doc | no | flag: Unsupported number in answer: [5] | True | False | Every banking company, not being a schedule bank, shall maintain by wa |
| b02 | doc | no | pass | True | True | No, except as authorized under section 7, a banking company is prohibi |
| b03 | doc | no | pass | True | True | Whoever wilfully makes a statement which is false in any material part |
| b04 | doc | no | pass | True | True | The Federal Government may suspend the operation of the Ordinance for  |
| b05 | doc | no | pass | False | False | The total period of super session, after extension, does not exceed th |
| b06 | doc | no | pass | True | True | The Banking Mohtasib shall be appointed by the President in consultati |
| b07 | doc | no | pass | True | True | The Banking Mohtasib holds office for a period of three years and is n |
| b08 | doc | no | pass | True | True | Every company carrying on the business of banking in Pakistan shall us |
| b09 | doc | no | pass | True | True | A deposit is considered unclaimed if no transaction has taken place at |
| b10 | doc | no | pass | False | False | A banking company may be restricted or prohibited from paying dividend |
| b11 | doc | no | flag: no verified quote from cited source(s) [ | True | False | Loans and advances made by a banking company for agricultural and othe |
| b12 | doc | no | pass | False | False | A person holding the office of a director of a banking company may als |
| b13 | doc | no | pass | True | True | A director of a banking company, who is not its chief executive or a d |
| b14 | doc | no | pass | True | True | Any break of less than three years in the continuity of office shall b |
| b15 | doc | no | pass | True | True | Banking means the accepting, for the purpose of lending or investment, |
| b16 | doc | no | pass | True | True | No, a company engaged in the manufacture of goods or carrying on any t |
| b17 | doc | no | pass | True | True | The official liquidator is responsible for submitting lists of debtors |
| b18 | doc | no | flag: no verified quote from cited source(s) [ | False | True | Banking companies may be managed by a managing agent [S1]. |
| b19 | doc | no | pass | True | True | Yes, banking companies are bound to comply with the directions issued  |
| b20 | doc | no | flag: no verified quote from cited source(s) [ | True | True | Before a company can carry on banking business in Pakistan, it must ho |
| b21 | doc | no | flag: no verified quote from cited source(s) [ | True | True | Every banking company “and every financial institution specified in se |
| b22 | doc | no | pass | True | True | With effect on and from the 1st September, 1967, the amount which a ba |
| b23 | doc | no | pass | True | True | The minimum paid-up capital a banking company must have is determined  |
| b24 | doc | no | pass | True | True | No company, firm, or person that is not a banking company, a corporati |
| b25 | doc | no | pass | True | True | Section 3A applies the Ordinance to certain financial institutions bes |
| b26 | doc | no | pass | False | False | The Ordinance substituted the 'Companies Act, 1913 (VII of 1913)' with |
| b27 | doc | no | flag: no verified quote from cited source(s) [ | True | True | The State Bank may supersede the Board of Directors of a banking compa |
| b28 | doc | no | pass | True | True | Approved securities are defined in the Ordinance, and for the purpose  |
| b29 | doc | no | pass | True | True | The Banking Mohtasib shall not hold any other office of profit in the  |
| b30 | doc | no | pass | True | False | The statement of cash reserve must be submitted to the State Bank befo |
| b31 | doc | no | flag: no verified quote from cited source(s) [ | True | True | The Banking Mohtasib can be removed from office on the ground that the |
| b32 | doc | no | pass | True | True | A list of debtors must contain the rate of interest, if any, and the d |
| n01 | none | yes | pass | None | None | The provided sources do not contain information on how to apply for a  |
| n02 | none | yes | pass | None | None | I don't know based on the provided sources. |
| n03 | none | yes | pass | None | None | I don't know based on the provided sources. |
| n04 | none | yes | pass | None | None | I don't know based on the provided sources. |
| n05 | none | no | pass | None | None | The provided sources mention that there are 'Rates proposed to be char |
| n06 | none | no | flag: Unsupported number in answer: [2001] | None | None | In every proceeding for the winding-up of a banking company, within ni |
| n07 | none | no | pass | None | None | The provided sources do not mention Basel III capital buffers. However |
| n08 | none | no | pass | None | None | The penalty for wilfully making a false statement in any return, balan |
| n09 | none | yes | pass | None | None | The provided sources do not specify a fine that can be imposed on the  |
| n10 | none | yes | pass | None | None | The provided sources do not contain information about a section that r |
| n11 | none | yes | pass | None | None | The provided sources do not state the retirement age of the Governor o |
| n12 | none | no | pass | None | None | The complainant must intimate in writing to the concerned bank their i |

## Gate policies, same replies re-judged

| policy | answered | flagged | false alarms (correct answers flagged) | errors missed (wrong answers passed) | usable (correct and accepted) | accepted and citing the gold chunk | unanswerable that passed |
|---|---:|---:|---:|---:|---:|---:|---:|
| strict | 32 | 22% (7/32) | 22% (6/27) | 80% (4/5) | 66% (21/32) | 62% (20/32) | 33% (4/12) |
| tolerant | 32 | 22% (7/32) | 22% (6/27) | 80% (4/5) | 66% (21/32) | 62% (20/32) | 33% (4/12) |
| balanced | 32 | 19% (6/32) | 19% (5/27) | 80% (4/5) | 69% (22/32) | 62% (20/32) | 42% (5/12) |
| lenient | 32 | 3% (1/32) | 4% (1/27) | 100% (5/5) | 81% (26/32) | 78% (25/32) | 42% (5/12) |
| balanced + relevance gate 0.183 | 32 | 19% (6/32) | 19% (5/27) | 80% (4/5) | 69% (22/32) | 62% (20/32) | 33% (4/12) |
| balanced + relevance gate 0.211 | 32 | 19% (6/32) | 19% (5/27) | 80% (4/5) | 69% (22/32) | 62% (20/32) | 33% (4/12) |
| balanced + relevance gate 0.304 | 31 | 19% (6/31) | 19% (5/27) | 75% (3/4) | 69% (22/32) | 62% (20/32) | 8% (1/12) |
