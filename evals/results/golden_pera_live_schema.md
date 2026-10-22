# Golden QA evaluation: live store, json_mode schema

Golden file `evals/gold/pera.jsonl` (44 questions: 39 answerable, 5 unanswerable). Store: `/tmp/claude-1000/-home-copper-Git-Template-RAG/24d159d4-229a-4570-887a-d29472273e1a/scratchpad/pera_live_copy` (6 chunks, 5 usable). LLM json_mode=`schema`, policy=`balanced`, k=5. 'Correct' = the answer contains the facts listed in the gold sidecar: a lower bound, read the answers below.

## 1. Ingestion: is the evidence in a usable chunk?

- usable: 84% (43/51)
- rejected: 2% (1/51)
- split: 0% (0/51)
- absent: 14% (7/51)
- questions with unreachable evidence: 002, 004, 030, 031, 032, 033

## 2. Retrieval (answerable questions)

- an evidence chunk in the top 5: 87% (34/39)
- evidence chunk ranked first: 82% (32/39)
- all of a question's evidence quotes covered by the top 5: 85% (33/39)
- note: the store has only 5 usable chunks, so the top 5 is most of the store; retrieval is easy here by construction.

## 3. Answers

- answered (did not refuse): 97% (38/39)
- delivered (answered and passed the gates): 87% (34/39)
- contains every required fact: 62% (24/39)
- contains every required fact **and** delivered: 59% (23/39)
- mean share of required facts present: 0.70
- a verified quote comes from an evidence chunk: 82% (32/39)
- correct among flagged answers (false alarms): 25% (1/4)

## 4. Unanswerable questions (right behaviour: refuse)

- refused: 0% (0/5)
- answered but flagged: 40% (2/5)
- answered and passed the gates (the dangerous case): 60% (3/5)

## 5. By question type (answerable)

| type | n | evidence in top-k | delivered | every fact | delivered and every fact |
|---|---:|---:|---:|---:|---:|
| amendment | 4 | 1 | 3 | 1 | 1 |
| conditional | 2 | 2 | 2 | 1 | 1 |
| definition | 4 | 4 | 4 | 3 | 3 |
| exception | 3 | 3 | 3 | 3 | 3 |
| factual | 16 | 14 | 15 | 15 | 14 |
| list | 2 | 2 | 1 | 0 | 0 |
| multi-hop | 6 | 6 | 4 | 0 | 0 |
| numeric | 1 | 1 | 1 | 1 | 1 |
| temporal | 1 | 1 | 1 | 0 | 0 |

## 6. Every question

| id | type | ev. | rank | outcome | facts | answer |
|---|---|---|---|---|---|---|
| 001 | factual | u | 1 | pass | 1.00 | The short title of Act No. XII of 1992 is the Protection of Economic Reforms Act, 1992 [1]. |
| 002 | factual | a | - | pass | 1.00 | The act number of the Protection of Economic Reforms Act is ACT NO. XII OF 1992 [1]. |
| 003 | factual | u | 2 | flag: Unsupported number in answer: [23] | 1.00 | The Protection of Economic Reforms Act received the President's assent on July 23, 1992 [2]. |
| 004 | factual | r | - | pass | 0.00 | The Act was published for general information on the 28th of July, 1992 [2]. |
| 005 | factual | u | 1 | pass | 1.00 | The Protection of Economic Reforms Act, 1992 extends to the whole of Pakistan [1]. |
| 006 | factual | u | 1 | pass | 1.00 | The Protection of Economic Reforms Act, 1992, shall come into force at once [1]. |
| 007 | definiti | u | 1 | pass | 1.00 | The Act defines "Government" to include both the Federal Government and any Provincial Government [1]. |
| 008 | definiti | u | 1 | pass | 0.00 | Economic reforms are defined as economic policies and programmes, laws and regulations announced, promulgated or implemented by the Government on and  |
| 009 | definiti | u | 1 | pass | 1.00 | Economic reforms include economic policies and programmes, laws and regulations announced, promulgated or implemented by the Government on and after t |
| 010 | definiti | u | 1 | pass | 1.00 | All other expressions used in the Act shall have the meaning assigned to them under the relevant laws [1]. |
| 011 | factual | u | 1 | pass | 1.00 | The Protection of Economic Reforms Act overrides the Foreign Currency Accounts (Protection) Ordinance, 2001 (L of 2001) under section 3 [1]. |
| 012 | factual | u | 1 | pass | 1.00 | All citizens of Pakistan resident in Pakistan or outside Pakistan and all other persons are entitled and free to bring, hold, sell, transfer and take  |
| 013 | numeric | u | 1 | pass | 1.00 | The cash threshold for cross border or inland movement of foreign currencies is US$ 10,000 or its equivalent, subject to an annual ceiling that may be |
| 014 | exceptio | u | 1 | pass | 1.00 | No, the freedom to bring, hold, sell, transfer, and take out foreign exchange as stated in section 4(1) does not apply to any payment from abroad for  |
| 015 | exceptio | u | 1 | pass | 1.00 | The provided sources do not explicitly state whether foreign exchange earned by the overseas branch of a Pakistani bank is covered by the freedom ment |
| 016 | list | u | 2 | pass | 0.29 | The categories excluded from the freedom to bring, hold, sell, transfer, and take out foreign exchange within or out of Pakistan in any form under sec |
| 017 | factual | u | 1 | pass | 1.00 | All citizens of Pakistan resident in Pakistan or outside Pakistan who hold foreign currency accounts in Pakistan, and all other persons who hold such  |
| 018 | temporal | u | 1 | pass | 0.00 | The immunity against inquiry from the Income Tax Department or any other taxation authority as to the source of financing of foreign currency accounts |
| 019 | factual | u | 1 | pass | 1.00 | The balances in the foreign currency accounts and income therefrom are exempt from the levy of wealth tax and income tax and compulsory deduction of Z |
| 020 | exceptio | u | 1 | pass | 1.00 | Banks may depart from complete secrecy in respect of transactions in the foreign currency accounts if otherwise required under the Foreign Exchange Re |
| 021 | conditio | u | 1 | pass | 1.00 | No, cash shall not be deposited in the account of a citizen of Pakistan resident in Pakistan unless the account holder is a filer as defined in the In |
| 022 | conditio | u,u | 1 | pass | 0.00 | The State Bank of Pakistan or other banks shall not impose any restrictions on deposits in and withdrawals from the foreign currency accounts, and any |
| 023 | factual | u | 1 | pass | 1.00 | Section 6 protects the fiscal incentives for investment provided by the Government through the statutory orders listed in the Schedule or otherwise no |
| 024 | factual | u | 1 | pass | 1.00 | No, the ownership, management and control of any banking, commercial, manufacturing or other company, establishment or enterprise transferred by the G |
| 025 | list | u | 1 | flag: the answer cites no source | 0.67 | Section 8 protects no foreign, industrial or commercial enterprise established or owned in any form by a foreign or Pakistani investor for private gai |
| 026 | factual | u | 1 | pass | 1.00 | The secrecy of bonafide banking transactions must be strictly observed by all banks and financial institutions, by whosoever owned, controlled or mana |
| 027 | factual | u | 1 | pass | 1.00 | Section 10 states that all financial obligations incurred, including those under any instrument, or any financial and contractual commitment made by o |
| 028 | factual | u | 1 | pass | 1.00 | The Federal Government has the power to make rules for carrying out the purposes of the Protection of Economic Reforms Act [1]. |
| 029 | factual | u,u | 1 | pass | 1.00 | The stated objectives of the Act in its preamble are to create a liberal environment for savings and investments [1], to provide legal protection to e |
| 030 | amendmen | a,a | - | pass | 1.00 | Section 4(2)(f) and clause (g) were inserted vide Finance Act, 2018 [1]. |
| 031 | amendmen | u,a | 1 | pass | 0.00 | The 1992 Act, specifically in section 3, refers to the Foreign Currency Accounts (Protection) Ordinance, 2001 (L of 2001) because the 1992 Act is an ' |
| 032 | amendmen | a,a | - | pass | 0.00 | The provisions of section 5 were inserted by the Finance Act, 2018 [1]. |
| 033 | amendmen | a | - | flag: Unsupported number in answer: [1992] | 0.00 | The Finance Act, 2018 substituted section 4(1) of ACT NO. XII OF 1992 [1]. |
| 034 | multi-ho | u,u | 1 | pass | 0.50 | The account is immune from inquiry from the Income Tax Department or any other taxation authority as to the source of financing of the foreign currenc |
| 035 | multi-ho | u,u | 1 | pass | 0.50 | The immunity against inquiry from the Income Tax Department or any other taxation authority as to the source of financing of the foreign currency acco |
| 036 | multi-ho | u,u,u | 1 | refused | 0.33 | The provided sources do not contain information regarding whether the Government could re-nationalize a bank that it privatized in 1995. |
| 037 | multi-ho | u,u | 1 | pass | 0.00 | The provision regarding the cross border or inland movement of foreign currencies in cash restricts movement exceeding US$ 10,000 or its equivalent, s |
| 038 | multi-ho | u,u | 1 | flag: Unsupported number in answer: [2, 1992] | 0.50 | Two different sections impose banking secrecy: section (3) of ACT NO. XII OF 1992, which states that banks must maintain complete secrecy regarding tr |
| 039 | multi-ho | u,u | 1 | pass | 0.50 | The Federal Government may make rules governing deposits in and withdrawals from the foreign currency accounts [1], and the Federal Government may mak |
| 040 | unanswer | - | - | pass | - | The provided sources state that the secrecy of bonafide banking transactions shall be strictly observed by all banks and financial institutions, by wh |
| 041 | unanswer | - | - | pass | - | The annual ceiling on cross border or inland movement of foreign currencies in cash exceeding US$ 10,000 or its equivalent is subject to a ceiling tha |
| 042 | unanswer | - | - | flag: no verified quote from cited source(s) [ | - | The statutory orders listed in the Schedule referred to in section 6 are those through which the Government provides fiscal incentives for investment  |
| 043 | unanswer | - | - | pass | - | The Act defines a 'filer' as defined in the Income Tax Ordinance, 2001 (XLIX of 2001) [1]. |
| 044 | unanswer | - | - | flag: the answer cites no source | - | The exact words omitted from section 4(1) by the Finance Act, 2018 are not provided in the sources. |
