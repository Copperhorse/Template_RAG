# Golden QA evaluation: PERA, table-aware chunking + table-cell gate, schema mode

Golden file `evals/gold/pera.jsonl` (44 questions: 39 answerable, 5 unanswerable). Store: `/tmp/claude-1000/-home-copper-Git-Template-RAG/24d159d4-229a-4570-887a-d29472273e1a/scratchpad/pera_t` (6 chunks, 6 usable). LLM json_mode=`schema`, policy=`balanced`, k=5. 'Correct' = the answer contains the facts listed in the gold sidecar: a lower bound, read the answers below.

## 1. Ingestion: is the evidence in a usable chunk?

- usable: 98% (47/48)
- rejected: 0% (0/48)
- split: 0% (0/48)
- absent: 2% (1/48)
- questions with unreachable evidence: 002

## 2. Retrieval (answerable questions)

- an evidence chunk in the top 5: 95% (37/39)
- evidence chunk ranked first: 87% (34/39)
- all of a question's evidence quotes covered by the top 5: 95% (37/39)
- note: the store has only 6 usable chunks, so the top 5 is most of the store; retrieval is easy here by construction.

## 3. Answers

- answered (did not refuse): 100% (39/39)
- delivered (answered and passed the gates): 95% (37/39)
- contains every required fact: 64% (25/39)
- contains every required fact **and** delivered: 64% (25/39)
- mean share of required facts present: 0.71
- a verified quote comes from an evidence chunk: 92% (36/39)
- correct among flagged answers (false alarms): 0% (0/2)

## 4. Unanswerable questions (right behaviour: refuse)

- refused: 0% (0/5)
- answered but flagged: 20% (1/5)
- answered and passed the gates (the dangerous case): 80% (4/5)

## 5. By question type (answerable)

| type | n | evidence in top-k | delivered | every fact | delivered and every fact |
|---|---:|---:|---:|---:|---:|
| amendment | 4 | 3 | 4 | 1 | 1 |
| conditional | 2 | 2 | 2 | 1 | 1 |
| definition | 4 | 4 | 4 | 3 | 3 |
| exception | 3 | 3 | 3 | 3 | 3 |
| factual | 16 | 15 | 16 | 16 | 16 |
| list | 2 | 2 | 1 | 0 | 0 |
| multi-hop | 6 | 6 | 5 | 0 | 0 |
| numeric | 1 | 1 | 1 | 1 | 1 |
| temporal | 1 | 1 | 1 | 0 | 0 |

## 6. Every question

| id | type | ev. | rank | outcome | facts | answer |
|---|---|---|---|---|---|---|
| 001 | factual | u | 1 | pass | 1.00 | The short title of Act No. XII of 1992 is the Protection of Economic Reforms Act, 1992 [S1]. |
| 002 | factual | a | - | pass | 1.00 | The act number of the Protection of Economic Reforms Act is Act No. XII of 1992 [S1]. |
| 003 | factual | u | 3 | pass | 1.00 | The Protection of Economic Reforms Act received the President's assent on July 23, 1992 [S3]. |
| 004 | factual | u | 3 | pass | 1.00 | The Act was published in the Gazette of Pakistan on Tuesday, July 28, 1992 [S3]. |
| 005 | factual | u | 1 | pass | 1.00 | The Protection of Economic Reforms Act, 1992 extends to the whole of Pakistan [S1]. |
| 006 | factual | u | 1 | pass | 1.00 | The Protection of Economic Reforms Act, 1992 shall come into force at once [S1]. |
| 007 | definiti | u | 1 | pass | 1.00 | The term "Government" in this Act includes both the Federal Government and any Provincial Government [S1]. |
| 008 | definiti | u | 1 | pass | 0.00 | Economic reforms are defined as economic policies and programmes, laws and regulations announced, promulgated or implemented by the Government on and  |
| 009 | definiti | u | 1 | pass | 1.00 | Economic reforms include economic policies and programmes, laws and regulations announced, promulgated or implemented by the Government on and after t |
| 010 | definiti | u | 1 | pass | 1.00 | All other expressions used in the Act shall have the meaning assigned to them under the relevant laws [S1]. |
| 011 | factual | u | 1 | pass | 1.00 | The Protection of Economic Reforms Act overrides the Foreign Currency Accounts (Protection) Ordinance, 2001 (L of 2001) under section 3 [S1]. |
| 012 | factual | u | 1 | pass | 1.00 | All citizens of Pakistan resident in Pakistan or outside Pakistan and all other persons are entitled and free to bring, hold, sell, transfer and take  |
| 013 | numeric | u | 1 | pass | 1.00 | The cash threshold for cross border or inland movement of foreign currencies is US$ 10,000 or its equivalent, subject to an annual ceiling as may be p |
| 014 | exceptio | u | 1 | pass | 1.00 | No, the freedom to bring, hold, sell, transfer and take out foreign exchange as stated in section 4(1) does not apply to any payment from abroad for g |
| 015 | exceptio | u | 1 | pass | 1.00 | The provided sources do not explicitly state whether foreign exchange earned by the overseas branch of a Pakistani bank is covered by the freedom ment |
| 016 | list | u | 2 | pass | 0.29 | The freedom to bring, hold, sell, transfer, and take out foreign exchange within or out of Pakistan in any form, as stated in section 4(1) of ACT NO.  |
| 017 | factual | u | 1 | pass | 1.00 | All citizens of Pakistan resident in Pakistan or outside Pakistan who hold foreign currency accounts in Pakistan, and all other persons who hold such  |
| 018 | temporal | u | 1 | pass | 0.00 | The immunity against inquiry from the Income Tax Department or any other taxation authority as to the source of financing of foreign currency accounts |
| 019 | factual | u | 1 | pass | 1.00 | The balances in the foreign currency accounts and income therefrom are exempt from the levy of wealth tax, income tax, and compulsory deduction of Zak |
| 020 | exceptio | u | 1 | pass | 1.00 | Banks may depart from complete secrecy in respect of transactions in the foreign currency accounts if otherwise required under the Foreign Exchange Re |
| 021 | conditio | u | 1 | pass | 1.00 | No, cash shall not be deposited in the account of a citizen of Pakistan resident in Pakistan unless the account holder is a filer as defined in the In |
| 022 | conditio | u,u | 1 | pass | 0.00 | The State Bank of Pakistan or other banks shall not impose any restrictions on deposits in and withdrawals from the foreign currency accounts, and any |
| 023 | factual | u | 1 | pass | 1.00 | Section 6 protects the fiscal incentives for investment provided by the Government through the statutory orders listed in the Schedule or otherwise no |
| 024 | factual | u | 1 | pass | 1.00 | No, the ownership, management and control of any banking, commercial, manufacturing or other company, establishment or enterprise transferred by the G |
| 025 | list | u | 1 | flag: the answer cites no source | 0.67 | Section 8 protects no foreign, industrial or commercial enterprise established or owned in any form by a foreign or Pakistani investor for private gai |
| 026 | factual | u | 1 | pass | 1.00 | The secrecy of bonafide banking transactions must be strictly observed by all banks and financial institutions, by whosoever owned, controlled or mana |
| 027 | factual | u | 1 | pass | 1.00 | Section 10 states that all financial obligations incurred, including those under any instrument, or any financial and contractual commitment made by o |
| 028 | factual | u | 1 | pass | 1.00 | The Federal Government has the power to make rules for carrying out the purposes of the Protection of Economic Reforms Act [S1]. |
| 029 | factual | u,u | 1 | pass | 1.00 | The stated objectives of the Act in its preamble are to create a liberal environment for savings and investments and other matters relating thereto [S |
| 030 | amendmen | u | 1 | pass | 1.00 | Section 4(2)(f) was omitted by the Finance Act, 2018, and clause (g) was inserted by the Finance Act, 2018 [S1]. |
| 031 | amendmen | u | - | pass | 0.00 | The 1992 Act refers to the 2001 Ordinance in section 3 because it states that the Act shall have effect notwithstanding anything contained in the Fore |
| 032 | amendmen | u | 1 | pass | 0.00 | The provisions of section 5 were inserted by the Finance Act, 2018, as indicated by the note '5. Inserted vide Finance Act, 2018' in [S1]. |
| 033 | amendmen | u | 1 | pass | 0.00 | The Finance Act, 2018 substituted section 4(1) of ACT NO. XII OF 1992 [S1]. |
| 034 | multi-ho | u,u | 1 | pass | 0.50 | The immunity against any inquiry from the Income Tax Department or any other taxation authority as to the source of financing of the foreign currency  |
| 035 | multi-ho | u,u | 1 | pass | 0.00 | Yes, the immunity against inquiry from the Income Tax Department or any other taxation authority as to the source of financing of the foreign currency |
| 036 | multi-ho | u,u,u | 1 | pass | 0.33 | No, the ownership, management and control of any banking, commercial, manufacturing or other company, establishment or enterprise transferred by the G |
| 037 | multi-ho | u,u | 1 | flag: the answer cites no source | 0.00 | The provisions restrict the resident Pakistani non-filer from depositing cash in a foreign currency account. Specifically, no cash shall be deposited  |
| 038 | multi-ho | u,u | 1 | pass | 0.50 | The Act imposes banking secrecy in two ways: first, under section (3) of Act No. XII of 1992, banks must maintain complete secrecy regarding transacti |
| 039 | multi-ho | u,u | 1 | pass | 0.50 | The Federal Government may make rules governing deposits in and withdrawals from the foreign currency accounts [S1]. Generally, the Federal Government |
| 040 | unanswer | - | - | pass | - | The provided sources state that the secrecy of bonafide banking transactions shall be strictly observed by all banks and financial institutions, by wh |
| 041 | unanswer | - | - | pass | - | The annual ceiling on cross border or inland movement of foreign currencies in cash exceeding US$ 10,000 or its equivalent is subject to being prescri |
| 042 | unanswer | - | - | pass | - | The statutory orders listed in the Schedule referred to in section 6 are those through which the Government provides fiscal incentives for investment  |
| 043 | unanswer | - | - | pass | - | The Act defines a 'filer' as defined in the Income Tax Ordinance, 2001 (XLIX of 2001) [S1]. |
| 044 | unanswer | - | - | flag: the answer cites no source | - | The exact words omitted from section 4(1) by the Finance Act, 2018 are not provided in the sources. |
