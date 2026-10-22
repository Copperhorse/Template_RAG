# Golden QA evaluation: ppc

Golden file `/home/copper/Downloads/ppc_golden_qa.jsonl` (207 questions: 185 answerable, 11 unanswerable, 11 partially answerable). Store: `/tmp/claude-1000/-home-copper-Git-Template-RAG/24d159d4-229a-4570-887a-d29472273e1a/scratchpad/blind_store` (992 chunks, 939 usable). LLM json_mode=`schema`, policy=`balanced`, k=5. 'Correct' = the answer contains the facts listed in the gold sidecar: a lower bound, read the answers below.

## 1. Ingestion: is the evidence in a usable chunk?

- usable: 86% (328/383)
- fuzzy-usable: 13% (51/383)
- rejected: 0% (0/383)
- split: 0% (0/383)
- absent: 1% (4/383)
- (fuzzy-usable: no exact match, but a chunk holds at least 80% of the quote's tokens; relevance below uses the same rule)
- questions with unreachable evidence: 183, 189

## 2. Retrieval (answerable questions and partially answerable ones)

- an evidence chunk in the top 5: 98% (193/196)
- evidence chunk ranked first: 92% (180/196)
- all of a question's evidence quotes covered by the top 5: 93% (183/196)

## 3. Answers

- answered (did not refuse): 98% (182/185)
- delivered (answered and passed the gates): 82% (152/185)
- contains every required fact: 0% (0/185)
- contains every required fact **and** delivered: 0% (0/185)
- mean share of required facts present: 0.00 (over the 0 questions that list facts)
- mean item recall over the 34 list questions that name their items: 0.57
- a verified quote comes from an evidence chunk: 96% (178/185)
- correct among flagged answers (false alarms): 0% (0/30)

## 4. Unanswerable questions (right behaviour: refuse)

- refused: 18% (2/11)
- answered but flagged: 18% (2/11)
- answered and passed the gates (the dangerous case): 64% (7/11)

## 4b. Partially answerable (the right reply cites what exists and says what the source does not give)

- refused outright (a fail: the part that exists should be given): 0% (0/11)
- answered and passed the gates: 91% (10/11)
- answered and flagged: 9% (1/11)
- whether a reply states what is missing needs reading; see section 6.

## 5. By question type (answerable)

| type | n | evidence in top-k | delivered | every fact | delivered and every fact |
|---|---:|---:|---:|---:|---:|
| conflict | 2 | 2 | 1 | 0 | 0 |
| factual | 143 | 142 | 122 | 0 | 0 |
| list | 34 | 34 | 26 | 0 | 0 |
| multi_hop | 6 | 6 | 3 | 0 | 0 |

## 6. Every question

| id | type | ev. | rank | outcome | facts | answer |
|---|---|---|---|---|---|---|
| 001 | factual | u,u | 1 | flag: no verified quote from cited source(s) [ | - | Yes. The Code applies to a Pakistani citizen who commits an offence abroad, and to offences on Pakistani ships or aircraft [S1]. Section 3 provides th |
| 002 | factual | u | 1 | pass | - | No. The Penal Code does not repeal such Acts. [S1] |
| 003 | factual | u | 1 | pass | - | Section 34 states that when a criminal act is done by several persons in furtherance of the common intention of all, each such person is liable for th |
| 004 | factual | u | 1 | pass | - | An effect is caused 'voluntarily' under section 39 when the person does so by means he intended to cause it, or by means which, at the time of employi |
| 005 | factual | u | 1 | pass | - | Under section 52, "good faith" requires due care and attention [S1]. |
| 006 | list | u,u,u,u,u,u,u,u | 1 | pass | - | Section 52A includes supplying a person with shelter, food, drink, money, clothes, arms, ammunition or means of conveyance, or assisting a person by a |
| 007 | factual | f | 1 | flag: no verified quote from cited source(s) [ | - | Yes, section 497 (adultery) is still listed in the Code text as an entry [S1]. |
| 008 | list | u,u,u,u,u,u,u,u,u,u | 1 | pass | - | Section 53 lists the following kinds of punishment: Qisas, Diyat, Arsh, Daman, Ta'zir, Death, Imprisonment for life, Imprisonment (rigorous or simple) |
| 009 | factual | u,u | 1 | pass | - | The Federal Government or the Provincial Government may commute a death sentence [S1]. However, for an offence of qatl, the sentence may not be commut |
| 010 | factual | u,u | 1 | pass | - | The Provincial Government may commute a sentence of imprisonment for life to a term not exceeding fourteen years [S1]. |
| 011 | factual | u | 1 | flag: Unsupported number in answer: [55] | - | No. According to Section 55 of the Pakistan Penal Code, the President's right to grant pardons, reprieves, respites, or remissions cannot be exercised |
| 012 | factual | u | 1 | pass | - | Imprisonment for life is reckoned as equivalent to imprisonment for twenty-five years when fractions of terms of punishment are calculated [S1]. |
| 013 | factual | u | 1 | pass | - | The cap is one-fourth of the maximum imprisonment term for the offence [S1]. |
| 014 | list | u,u,u | 1 | pass | - | For an offence punishable with fine only, default imprisonment may not exceed two months if the fine is not more than fifty rupees, four months if the |
| 015 | factual | u,f | 1 | pass | - | An unpaid fine may be levied within six years after the sentence passes [S1]. The offender's death does not discharge them from liability for property |
| 016 | multi_ho | u,u | 1 | flag: no verified quote from cited source(s) [ | - | For theft in a dwelling house under s.380, the offence is punishable with imprisonment and fine [S3]. The maximum default imprisonment for non-payment |
| 017 | list | u,u,u | 1 | pass | - | Under section 73, the maximum solitary confinement is three months in total, scaled by the sentence: up to one month if the term of imprisonment does  |
| 018 | factual | u | 1 | pass | - | At one stretch, solitary confinement may not exceed fourteen days at a time [S1]. Additionally, the total duration of solitary confinement for a convi |
| 019 | factual | u | 1 | pass | - | Under s.75, a repeat offender who has previously been convicted of an offence under Chapter XII or Chapter XVII with imprisonment for three years or u |
| 020 | factual | u | 1 | pass | - | The person is punished for the offence for which the lowest punishment is provided [S1]. |
| 021 | factual | u,u | 1 | pass | - | Section 82 provides that nothing is an offence done by a child under seven years of age [S1]. Section 83 provides that nothing is an offence done by a |
| 022 | factual | u | 1 | pass | - | Under section 84, an act is not an offence if, at the time of doing it, the person is by reason of unsoundness of mind incapable of knowing the nature |
| 023 | factual | u,u | 1 | pass | - | Yes, intoxication can be a defence to certain offences. Under Section 85 [S1], an act done by a person who is intoxicated and incapable of knowing the |
| 024 | factual | u | 1 | pass | - | Under section 87, a person above eighteen years of age who has given consent, whether express or implied, to suffer harm may validly consent to it [S1 |
| 025 | factual | u,u | 1 | pass | - | No. Section 94 only excuses an offence when the person was compelled by threats that, at the time of doing it, reasonably cause the apprehension that  |
| 026 | factual | u | 1 | pass | - | Section 95 uses the test that harm must be so slight that no person of ordinary sense and temper would complain of such harm [S1]. |
| 027 | factual | u | 1 | pass | - | Under section 97, a person has a right to defend the property of themselves or others against acts that are offenses under the definitions of theft, r |
| 028 | list | f,u,u,f | 5 | pass | - | Section 99 limits the right of private defence in two main ways. First, there is no right of private defence against an act that does not reasonably c |
| 029 | factual | u | 1 | flag: no verified quote from cited source(s) [ | - | Yes. According to Section 98 of the Pakistan Penal Code, every person has the right of private defence against an act committed by someone of unsound  |
| 030 | factual | u | 1 | pass | - | No. Under Section 99 of the Pakistan Penal Code, a person does not lose the right of private defence against an act by a public servant unless he know |
| 031 | list | u,u,u,u,u,u | 2 | flag: Unsupported number in answer: [3, 4, 5] | - | According to Section 100 of the Pakistan Penal Code, the right of private defence of the body extends to causing death in the following six situations |
| 032 | list | u,u,u,u | 1 | pass | - | Under Section 103 of the Pakistan Penal Code, the right of private defence of property extends to causing death when the offence that occasions the ex |
| 033 | factual | f | 1 | pass | - | The right of private defence of property against theft continues as long as the offender has effected his retreat with the property, or either the ass |
| 034 | factual | u | 1 | flag: no verified quote from cited source(s) [ | - | Yes. Under Section 106 of the Pakistan Penal Code, if a defender cannot effectively exercise the right of private defence against an assault that reas |
| 035 | factual | u | 1 | pass | - | The right of private defence of the body begins as soon as a reasonable apprehension of danger to the body arises from an attempt or threat to commit  |
| 036 | list | u,u,u | 1 | flag: Unsupported number in answer: [2] | - | Under section 107, a person abets the doing of a thing in three ways: [S1] (1) by instigating any person to do that thing; (2) by engaging with one or |
| 037 | factual | u | 1 | pass | - | No. According to Section 108 of the Pakistan Penal Code, the offence of abetment does not require that the act be committed or that the requisite effe |
| 038 | factual | u | 1 | flag: no verified quote from cited source(s) [ | - | Yes. Under the Pakistan Penal Code, a person in Pakistan who abets an act to be done abroad is guilty of abetment [S1]. The definition of abetment inc |
| 039 | factual | u,u | 1 | pass | - | Where the act abetted is committed in consequence of the abetment, the abettor is punished with the punishment provided for the offence itself [S1]. F |
| 040 | factual | u | 1 | pass | - | Misrepresentation can amount to instigation under the Pakistan Penal Code when a person, by wilful misrepresentation or wilful concealment of a materi |
| 041 | factual | u | 1 | pass | - | If an abettor is present when the offence is committed, he is deemed to have committed the act or offence [S1]. |
| 042 | factual | u,f | 1 | pass | - | Under section 115, if the offence is not committed, the abettor is punished with imprisonment for a term which may extend to seven years, and shall al |
| 043 | conflict | f,u,u | 1 | flag: Unsupported sentence in answer (8 of 12  | - | Based on the illustration in S1, if B had murdered Z, he would have been subject to the punishment of death or transportation for fife [S1]. The wordi |
| 044 | factual | u,f | 1 | pass | - | Under section 116, if the abettor is a public servant whose duty it is to prevent the commission of the offence, the abettor is punished with imprison |
| 045 | multi_ho | u,f,u | 1 | flag: no verified quote from cited source(s) [ | - | Under s.116, if the abettor is a public servant whose duty is to prevent theft, the abettor is punishable with imprisonment for a term which may exten |
| 046 | factual | u | 1 | pass | - | The punishment is imprisonment for a term which may extend to three years, or with fine, or with both [S1]. |
| 047 | factual | u | 1 | pass | - | Under section 120 of the Pakistan Penal Code, if the offence is committed, the person is punished with imprisonment for a term which may extend to one |
| 048 | factual | u | 1 | flag: Unsupported number in answer: [120] | - | Section 120 defines criminal conspiracy as an agreement between two or more persons to do or cause an illegal act, or an act that is not illegal by il |
| 049 | factual | u | 1 | flag: Unsupported number in answer: [120] | - | Yes. According to Section 120 of the Pakistan Penal Code, an agreement to commit an offence alone is not enough to constitute a criminal conspiracy un |
| 050 | factual | u,u | 1 | pass | - | Under section 120B of the Pakistan Penal Code, a party to a criminal conspiracy to commit an offence punishable with death, imprisonment for life, or  |
| 051 | factual | u | 1 | pass | - | Under section 121 of the Pakistan Penal Code, waging war against Pakistan, attempting to wage such war, or abetting it is punishable by death, or impr |
| 052 | factual | u | 1 | flag: no verified quote from cited source(s) [ | - | Based on the provided sources, the question about whether an act must be done for a conspiracy under section 121A is not addressed. The sources discus |
| 053 | factual | u,u | 1 | pass | - | Under section 124A of the Pakistan Penal Code, sedition is punishable with imprisonment for life, or imprisonment that may extend to three years, or f |
| 054 | factual | u,u | 1 | pass | - | Under section 123A of the Pakistan Penal Code, the punishment is rigorous imprisonment which may extend to ten years and a fine [S1]. The court has ex |
| 055 | factual | f | 1 | pass | - | Under section 123B of the Pakistan Penal Code, defiling or unauthorisedly removing the National Flag from Government property is punishable with impri |
| 056 | factual | u | 1 | pass | - | The maximum imprisonment is seven years [S1]. |
| 057 | factual | u,u | 1 | flag: Unsupported sentence in answer (5 of 9 w | - | Section 128 punishes a public servant who *voluntarily* allows a State prisoner to escape with imprisonment for life or up to ten years, and a fine [S |
| 058 | factual | u | 1 | pass | - | A paroled State prisoner is said to escape from lawful custody when he goes beyond the limits within which he is allowed to be at large [S1]. |
| 059 | factual | u | 1 | pass | - | Five or more persons [S1]. Being aware of facts that render an assembly unlawful, intentionally joining or continuing in it makes one a member of an u |
| 060 | list | u,u,u,u,u | 1 | pass | - | The five common objects are: [S1] First: to overawe by criminal force or show of criminal force the Federal or any Provincial Government or Legislatur |
| 061 | factual | u | 1 | pass | - | Yes. According to Section 141 of the Pakistan Penal Code, an assembly that was not unlawful when it gathered may later become an unlawful assembly [S1 |
| 062 | factual | u | 1 | pass | - | Members of an unlawful assembly are guilty of rioting whenever force or violence is used by the assembly, or by any member thereof, in prosecution of  |
| 063 | list | u,u,u,u,u | 1 | pass | - | The maximum imprisonment for the sections cited is life imprisonment or up to ten years, as stated in the Pakistan Penal Code [S1], [S3]. Section 365B |
| 064 | factual | u | 1 | pass | - | Every member of an unlawful assembly is guilty of an offence committed by another member only if the offence was committed in prosecution of the commo |
| 065 | multi_ho | u | 1 | pass | - | Section 145 [S2] |
| 066 | factual | u | 1 | pass | - | Under section 153A of the Pakistan Penal Code, promoting enmity between different groups on grounds of religion, race, language, caste, or community i |
| 067 | factual | f | 1 | pass | - | The maximum penalty is imprisonment for a term which may extend to two years, with fine or with both [S2]. |
| 068 | factual | f | 1 | pass | - | Section 153 provides for imprisonment of either description for a term which may extend to six months, or with fine, or with both, if rioting is not c |
| 069 | factual | f | 1 | pass | - | The maximum fine is not exceeding three thousand rupees [S1]. Note: The source text shows the amount as 'not exceeding40 ~~[~~ three thousand rupees]4 |
| 070 | list | u,u,u | 1 | refused | - | I don't know based on the provided sources. |
| 071 | factual | u | 1 | pass | - | Under Section 296 of the Pakistan Penal Code, disturbing a religious assembly lawfully engaged in worship is punishable with imprisonment of either de |
| 072 | factual | u | 1 | refused | - | I don't know based on the provided sources. |
| 073 | factual | f | 1 | flag: Unsupported sentence in answer (6 of 8 w | - | Section 298 carries a maximum imprisonment of three years [S2]. The question asks about sections 298B and 298C, but the provided sources only contain  |
| 074 | list | u,u,u,u,f | 1 | pass | - | Section 299 defines arsh as the compensation specified in the Chapter to be paid to the victim or his heirs [S1]; daman as the compensation determined |
| 075 | factual | u,u | 1 | pass | - | For Chapter XVI, an 'adult' is a person who has attained the age of eighteen years, and a 'minor' is a person who is not an adult [S1]. |
| 076 | factual | u | 3 | pass | - | The Code defines an offence committed 'in the name or on the pretext of honour' as an offence committed in the name or on the pretext of karo kari, si |
| 077 | factual | u,u | 2 | pass | - | Under section 300, qatl-i-amd is committed by doing an act which is likely to cause death or bodily injury, with the intention of causing death or bod |
| 078 | factual | u | 3 | pass | - | Section 301 applies: if a person intends to kill A but kills B instead, the act is liable for qatl-i-amd [S3]. |
| 079 | list | u,u,u | 1 | flag: Unsupported number in answer: [3] | - | Section 302 provides three possible punishments for qatl-i-amd: [S1] (a) death as qisas; (b) death or imprisonment for life as ta'zir if proof in Sect |
| 080 | factual | u,u | 1 | pass | - | Under ikrah-i-tam, the offender is punished with imprisonment from ten to twenty-five years, and the person causing the ikrah-i-tam is punished for th |
| 081 | factual | u,u | 1 | pass | - | Under Section 304, qatl-i-amd can be proved by either (a) the accused making a voluntary and true confession before a competent court, or (b) by evide |
| 082 | factual | f,u | 1 | pass | - | In case of qatl, the wali is the heirs of the victim, according to his personal law, or the Government if there is no heir [S1]. |
| 083 | list | u,u,u | 1 | pass | - | Qatl-i-amd is not liable to qisas under Section 306 when: (a) the offender is a minor or insane [S1]; (b) the offender causes the death of his child o |
| 084 | factual | u | 1 | flag: no verified quote from cited source(s) [ | - | A wali cannot waive the right of qisas when the Government is the wali [S1], or when the right of qisas vests in a minor or insane [S1]. Additionally, |
| 085 | factual | u,f | - | pass | - | Section 310 limits compounding qisas by allowing the court to punish the offender with death, life imprisonment, or up to fourteen years in prison as  |
| 086 | factual | u | 1 | pass | - | The punishment for giving a female in marriage or otherwise in badal-i-sulh is rigorous imprisonment that may extend to ten years but shall not be les |
| 087 | factual | u | 1 | pass | - | The court must take down the statement of the wali and such other persons as it may deem necessary on oath, and record an opinion that the waiver or c |
| 088 | factual | u | 1 | pass | - | Yes, an offender can still be punished after qisas has been waived or compounded [S1]. If the offence was committed in the name of honour, the minimum |
| 089 | list | u,u,u,u,u | 1 | pass | - | For purposes of section 311, 'fasad-fil-arz' includes the past conduct of the offender, any previous convictions, the brutal or shocking manner in whi |
| 090 | factual | f,u | 1 | pass | - | If a wali kills a convict whose qisas had been waived or compounded, the wali is punished with qisas if he himself waived or compounded the right of q |
| 091 | factual | u | 1 | pass | - | If the victim has no wali, the Government holds the right of qisas [S1]. |
| 092 | factual | u | 1 | pass | - | Yes. Under the Pakistan Penal Code, if the convict is a pregnant woman, the Court may postpone the execution of qisas for up to two years after the bi |
| 093 | factual | u,u | 1 | pass | - | Yes, all wali must be present for qisas to be executed, unless the Court authorises execution in the absence of a wali [S1], [S2]. |
| 094 | factual | u,f | 1 | flag: no verified quote from cited source(s) [ | - | qatl shibh-i-amd is an offence where, with intent to cause harm to the body or mind of any person, a person causes the death of that or any other pers |
| 095 | factual | u,u,u | 1 | pass | - | Under the Pakistan Penal Code, qatl-i-khata is punishable by diyat [S2]. If committed by rash or negligent driving, the offender is additionally punis |
| 096 | factual | f | 1 | pass | - | The punishment for qatl-bis-sabab is diyat [S1]. |
| 097 | factual | u,u | 1 | pass | - | The minimum value of diyat is not less than the value of thirty thousand six hundred and thirty grams of silver [S1]. The Federal Government announces |
| 098 | factual | u | 1 | pass | - | No. [S1] An heir who commits qatl-i-amd or Qatl shibh-i-amd is debarred from succeeding to the victim's estate as an heir or a beneficiary. |
| 099 | factual | f | 2 | pass | - | Under Section 324 of the Pakistan Penal Code, attempting to commit qatl-i-amd (qatl-e-amd) is punishable with imprisonment for either description for  |
| 100 | factual | u | 1 | pass | - | The punishment for attempting suicide is simple imprisonment for a term which may extend to one year, or with fine, or with both [S1]. |
| 101 | factual | u | 1 | pass | - | Under section 328 of the Pakistan Penal Code, a parent who exposes or leaves a child under twelve years of age with the intention of wholly abandoning |
| 102 | factual | u,u | 1 | pass | - | Diyat may be paid in lumpsum or in instalments spread over three years from the date of the final judgment [S1]. If the convict dies before paying diy |
| 103 | list | u,u,u,u,u | 1 | pass | - | Section 332 lists the kinds of hurt as Itlaf-i-udw, Itlaf-i-salahiyyat-i-udw, shajjah, jurh, and all kinds of other hurts [S1]. |
| 104 | list | u,u,u,u,u,u | 1 | pass | - | The six kinds of shajjah are: Shajjah-i-Khafifah, Shajjah-i-mudihah, Shajjah-i-hashimah, Shajjah-i-munaqqilah, Shajjah-i-ammah, and Shajjah-i-damighah |
| 105 | factual | u,f | 1 | pass | - | Shajjah-i-hashimah involves fracturing a bone without dislocating it [S1], whereas shajjah-i-munaqqilah involves fracturing the bone and thereby dislo |
| 106 | list | u,u,u,u,u | 1 | pass | - | Section 337A of the Pakistan Penal Code sets the following arsh for the higher kinds of shajjah as a share of diyat: shajjah-i-khafifah is punishable  |
| 107 | multi_ho | u,u | 1 | pass | - | At the minimum diyat value of thirty thousand six hundred and thirty grams of silver, the arsh for shajjah-i-hashimah is ten per cent of that value, i |
| 108 | factual | u | 1 | pass | - | The punishment for causing Itlaf-i-udw is qisas, and if qisas is not executable, the offender may be liable to arsh and imprisonment for a term which  |
| 109 | factual | u | 2 | pass | - | The punishment for jaifah is liability to arsh (one-third of the diyat) and may also be punished with imprisonment for a term which may extend to ten  |
| 110 | list | u,u,u,u,u,u | 1 | pass | - | Section 337F sets maximum ta'zir imprisonment of one year for damihah, three years for badi'ah and mutafahimah, five years for mudihah and hashimah, a |
| 111 | conflict | u,u,u,u | 1 | pass | - | Section 337F(iii) punishes mutafahimah [S2], which is named consistently with section 337E as mutalahimah [S1] [S1]. |
| 112 | factual | u,u,u | 1 | pass | - | The Code distinguishes between hurt caused by rash or negligent driving and other rash or negligent acts. For other acts, the punishment may include i |
| 113 | factual | u | 1 | pass | - | Under s.337J of the Pakistan Penal Code, administering poison or a stupefying drug with intent to cause hurt can result in the punishment of arsh or d |
| 114 | factual | u,u | 1 | pass | - | Section 337L treats other hurt that endangers life or lasts twenty days or more by making the person liable to daman and imprisonment of either descri |
| 115 | list | u,u,u,u | 1 | flag: no verified quote from cited source(s) [ | - | According to section 337M of the Pakistan Penal Code, hurt is not liable to qisas in four cases: [S1] (a) when the offender is a minor or insane; (b)  |
| 116 | factual | u | 1 | flag: no verified quote from cited source(s) [ | - | Qisas for hurt is executed in public by an authorised medical officer [S1]. In qatl-i-amd, it is executed by a functionary of the Government by causin |
| 117 | factual | u | 1 | pass | - | The minimum ta'zir is one-third of the maximum imprisonment provided for the hurt caused [S1]. |
| 118 | list | u,u,u,u,u,u | 1 | pass | - | For a single organ, the arsh is equivalent to the value of diyat [S1]. For one of a pair, the arsh is one-half of the diyat [S1]. For a finger, the ar |
| 119 | factual | u,u | 1 | pass | - | Under section 337U, if the injury is to a milk tooth, the accused is liable to daman and may also be punished with imprisonment for a term that may ex |
| 120 | factual | u | 1 | pass | - | Under s.337W, the amputated fingers and the hand are assessed separately because they are distinct hurts [S1]. The illustration in s.337W also states  |
| 121 | factual | u | 1 | pass | - | If the victim dies from the same hurt before healing, the arsh merges into the diyat [S1]. |
| 122 | list | u,u,u | 1 | pass | - | The court may consider the expenses incurred on the treatment of the victim, the loss or disability caused in the functioning or power of any organ, a |
| 123 | factual | u | 1 | pass | - | Arsh may be paid in a lump sum or in instalments spread over a period of three years from the date of the final judgment [S1]. |
| 124 | factual | f,f | 1 | pass | - | Under section 338A of the Pakistan Penal Code, causing isqat-i-hamal is punishable by ta'zir. If the woman consents, the punishment may be imprisonmen |
| 125 | factual | u,u | 1 | pass | - | Section 338C creates liability for isqat-i-janin that includes: (a) one-twentieth of the diyat if the child is born dead [S1], (b) full diyat if the c |
| 126 | factual | u | 1 | flag: Unsupported number in answer: [338] | - | Yes. According to Section 338 of the Pakistan Penal Code, a sentence of death awarded by way of qisas or ta'zir must be confirmed by the High Court be |
| 127 | factual | u | 1 | flag: no verified quote from cited source(s) [ | - | Yes. According to Section 309 of the Pakistan Penal Code, all offences under Chapter XVI may be waived or compounded [S1]. The same section provides t |
| 128 | factual | u,f | 1 | flag: Unsupported sentence in answer (5 of 7 w | - | The provided sources do not define 'wrongful restraint' as a distinct legal concept from 'wrongful confinement.' Section 340 of the Pakistan Penal Cod |
| 129 | list | u,f,u,u | 1 | pass | - | Wrongful restraint (s.341): maximum one month imprisonment [S5]. Confinement (s.342): maximum one year imprisonment [S2]. Confinement for three or mor |
| 130 | factual | u | 1 | pass | - | No. Under the Pakistan Penal Code, if a person in good faith believes they have a lawful right to obstruct a private way, that obstruction is not an o |
| 131 | factual | u,u | 1 | pass | - | Under s.346, the punishment is imprisonment of either description for a term which may extend to two years, in addition to any other punishment to whi |
| 132 | list | f,f,f,f,f | 1 | flag: Unsupported number in answer: [213] | - | Section 341 is not directly quoted in the sources, but Section 342 sets a fine of up to three thousand rupees [S3]. Section 352 is not directly quoted |
| 133 | list | u,u,u | 1 | pass | - | According to section 349, force can be used in three ways [S1]: First, by his own bodily power; Second, by disposing any substance in such a manner th |
| 134 | factual | u | 1 | pass | - | No, mere words do not amount to an assault [S1]. However, words may amount to an assault if they give a gesture or preparation the meaning that such g |
| 135 | factual | f | 1 | pass | - | Grave and sudden provocation will not mitigate the punishment under section 352 if the provocation is sought or voluntarily provoked by the offender a |
| 136 | factual | u,u | 1 | pass | - | Section 354 punishes assault on a woman with intent to outrage her modesty with imprisonment up to two years, fine, or both [S1]. Section 354A (strayi |
| 137 | factual | f | 1 | pass | - | Under section 358 of the Pakistan Penal Code, assault or criminal force on grave and sudden provocation is punishable with simple imprisonment for a t |
| 138 | factual | u | 1 | flag: Unsupported number in answer: [14, 16] | - | Under section 361, a victim of kidnapping from lawful guardianship includes a minor (male under 14, female under 16) or any person of unsound mind, pr |
| 139 | factual | u | 1 | pass | - | The Code defines abduction as compelling or inducing a person to go from any place by force or deceitful means [S1]. |
| 140 | factual | u | 1 | pass | - | Under section 364A of the Pakistan Penal Code, kidnapping or abducting a person under fourteen with intent to murder, enslave, or subject to lust is p |
| 141 | factual | u | 1 | pass | - | The punishment for kidnapping for ransom under s.365A is death or imprisonment for life, and also forfeiture of property [S1]. |
| 142 | factual | u | 1 | pass | - | The punishment is imprisonment for life and a fine [S1]. |
| 143 | list | u,u,u | 2 | flag: Unsupported sentence in answer (4 of 5 w | - | Section 361 (female minor) uses the age threshold of under sixteen years for a female minor [S3]. Sections 366A and 375(v) are not directly addressed  |
| 144 | factual | u | 1 | pass | - | Under Pakistan's Penal Code, selling or buying a person for prostitution is punishable by imprisonment that may extend to twenty-five years and a fine |
| 145 | factual | u | 1 | flag: Unsupported number in answer: [5, 367] | - | Under section 367 of the Pakistan Penal Code, kidnapping or abducting a person in order to subject them to unnatural lust is punishable with death or  |
| 146 | factual | u,u | 1 | pass | - | Habitual dealing in slaves carries a punishment of life imprisonment or up to ten years in prison, along with a fine [S1]. A single act of buying or s |
| 147 | factual | u | 1 | pass | - | The maximum imprisonment for unlawful compulsory labour under s.374(1) is 150 years [S1]. |
| 148 | list | u,u,u,u,u | 1 | pass | - | Under section 375, a man is said to commit rape in five circumstances: [S1] (i) against her will; (ii) without her consent; (iii) with her consent whe |
| 149 | factual | f,u | 1 | pass | - | Under section 376 of the Pakistan Penal Code, rape is punishable by death or imprisonment for a term not less than ten years or more than twenty-five  |
| 150 | factual | u | 2 | pass | - | Under section 377 of the Pakistan Penal Code, the punishment for unnatural offences includes imprisonment for life, or imprisonment of either descript |
| 151 | factual | u | 1 | pass | - | Under section 378, theft requires: (1) intent to take dishonestly any movable property [S1]; (2) taking the property out of the possession of another  |
| 152 | factual | u | 1 | pass | - | No. According to the provided illustration, taking a ring found lying on the high road, not in the possession of any person, does not constitute theft |
| 153 | list | u,u,u,u,u | 1 | pass | - | Theft in a dwelling (s.380) and theft by a clerk or servant (s.381) carry a maximum of seven years imprisonment [S1]. Theft of a motor vehicle (s.381A |
| 154 | factual | u | 1 | pass | - | Yes. Section 381A of the Pakistan Penal Code explicitly includes the theft of an electric motor of a tube-well or transformer within its scope [S1]. |
| 155 | factual | u | 2 | flag: no verified quote from cited source(s) [ | - | The Code defines extortion as intentionally putting a person in fear of any injury and dishonestly inducing that person to deliver property or valuabl |
| 156 | list | u,u,f,u,f | 1 | pass | - | Section 384: up to three years [S5]. Section 385: up to two years [S1]. Section 386: up to ten years [S1]. Section 387: up to seven years [S1]. Sectio |
| 157 | factual | f,u | 1 | pass | - | Theft becomes robbery when, in order to commit the theft, or in committing it, the offender voluntarily causes or attempts to cause death, hurt, wrong |
| 158 | factual | u | 1 | pass | - | Five or more persons [S1]. |
| 159 | list | f,f,u,f,u | 1 | flag: Unsupported sentence in answer (4 of 5 w | - | Section 397 sets a minimum seven-year imprisonment for robbery or dacoity involving a deadly weapon or grievous hurt [S1]. Section 395 sets imprisonme |
| 160 | factual | u,f | 1 | pass | - | Under the Pakistan Penal Code, hijacking is punishable by death or imprisonment for life, and the person may also be liable to forfeiture of property  |
| 161 | factual | u | 1 | pass | - | Criminal breach of trust under section 405 occurs when someone, being entrusted with property or dominion over property, dishonestly misappropriates,  |
| 162 | list | u,u,u,u | 1 | pass | - | The general maximum term for criminal breach of trust is imprisonment for a term which may extend to 160 years [S3]. For a carrier, the maximum is imp |
| 163 | factual | u | 1 | pass | - | Under section 415, dishonest concealment of facts amounts to cheating [S1]. |
| 164 | list | u,u,u,u | 1 | pass | - | For cheating (s.417), the maximum term is one year [S1]. For cheating a person whose interest one must protect (s.418), the maximum term is three year |
| 165 | factual | u | 1 | pass | - | The punishment is imprisonment up to three years, or a fine, or both [S1]. The burden of proof rests on the person who issued the cheque [S1]. |
| 166 | list | u,u,u,u,u | 1 | pass | - | s.426: up to three months [S4]. s.427: up to two years [S2]. s.428: up to two years [S1]. s.429: up to five years [S1]. s.430: up to five years [S1]. |
| 167 | factual | u | 1 | pass | - | Section 429 protects elephants, camels, horses, mules, buffaloes, bulls, cows, and oxen regardless of their value [S1]. |
| 168 | factual | u,u | 1 | pass | - | The exception to section 494 applies to a person whose marriage with the husband or wife has been declared void by a court of competent jurisdiction,  |
| 169 | factual | f | 1 | pass | - | Under section 493A of the Pakistan Penal Code, a man who deceitfully causes a woman not lawfully married to him to believe she is lawfully married and |
| 170 | factual | u,u | 1 | pass | - | Fornication is punishable by imprisonment up to five years and a fine not exceeding ten thousand rupees [S2]. A false charge of fornication is punisha |
| 171 | factual | u | 1 | pass | - | Under section 495 of the Pakistan Penal Code, if a bigamist conceals the former marriage from the new spouse, the punishment is imprisonment for a ter |
| 172 | factual | u,u | 1 | pass | - | Yes. Under the Pakistan Penal Code, imputing something to a deceased person can be defamation if it would harm the person's reputation if they were al |
| 173 | factual | u | 1 | pass | - | It depends on whether the imputation is made for the public good and whether it harms the person's reputation. Under the First Exception [S1], it is n |
| 174 | factual | u | 1 | pass | - | Defamation is punishable by simple imprisonment up to two years, or fine, or both [S3]. Printing or engraving defamatory matter is punishable by the s |
| 175 | factual | u | 1 | pass | - | No. Under the Second Exception of the Pakistan Penal Code, it is not defamation to express in good faith any opinion whatever respecting the conduct o |
| 176 | factual | f,f | 1 | pass | - | Under section 506, the punishment for criminal intimidation may extend to two years' imprisonment, or fine, or both [S1]. The text also states the pun |
| 177 | factual | u | 1 | pass | - | Section 507 adds imprisonment of either description for a term which may extend to two years, in addition to the punishment provided for the offence b |
| 178 | factual | u | 1 | pass | - | Under section 509, the punishment is simple imprisonment for a term which may extend to one year, or with fine, or with both [S1]. |
| 179 | factual | u | 1 | pass | - | Under s.510 of the Pakistan Penal Code, a person in a state of intoxication who appears in a public place and conducts themselves in a manner causing  |
| 180 | factual | u | 1 | pass | - | Under section 511 of the Pakistan Penal Code, where no express provision is made for the punishment of an attempt, the person is punished with impriso |
| 181 | multi_ho | u,u | 1 | pass | - | The longest term for an attempt under section 511 is one-half of the longest term of imprisonment provided for the offence [S1]. |
| 182 | factual | u | 1 | pass | - | According to the sources, the Workmen's Breach of Contract (Repealing) Act III of 1925 omitted two provisions from the Pakistan Penal Code: 490, 'Brea |
| 183 | list | f,f,a,a,f,a | 1 | pass | - | Based on the provided sources, the Protection of Women (Criminal Laws Amendment) Act, 2006 inserted the following provisions in the Pakistan Penal Cod |
| 184 | factual | u | 4 | pass | - | The age of fourteen was substituted in sections 364 and 364A by the Criminal Law (Amendment) Act, 2004 (I of 2005) [S1]. |
| 185 | multi_ho | u,f | 3 | refused | - | The sources do not contain information about an amendment raising the imprisonment ceiling in section 316. |
| 186 | partial | f,u,u | 1 | pass | - | Under the Pakistan Penal Code, murder is punishable with death or imprisonment for life, or imprisonment for a term which may extend to ten years, or  |
| 187 | partial | u,u | 2 | pass | - | The Code defines 'grievous hurt' as one of the kinds of hurt listed in section 332 of the Pakistan Penal Code [S2]. The listed kinds include Itlaf-i-u |
| 188 | partial | u,u | 1 | pass | - | Sections 58 and 59 dealt with transportation: 58 provided that offenders sentenced to transportation were dealt with until transported, and 59 provide |
| 189 | partial | a | - | flag: no verified quote from cited source(s) [ | - | Before the 2006 Act, section 375 defined rape as sexual intercourse with a woman under five descriptions [S3], and section 376 provided punishment of  |
| 190 | partial | f | - | pass | - | Clause (2) states that the provisions of the Code apply to offences committed beyond Pakistan by persons in the service of Pakistan, and clause (3) pr |
| 191 | partial | u,u | 1 | pass | - | The diyat is currently worth at least two hundred rupees, as per the Criminal Laws (Reforms) Ordinance (LXXXVI of 2002) [S3]. The value is also tied t |
| 192 | partial | u | 1 | pass | - | Article 17 of the Qanun-e-Shahadat, 1984 provides evidence as an alternative form of proof for qatl-i-amd [S1]. |
| 193 | partial | u | 1 | pass | - | Section 345 of the Code of Criminal Procedure, 1898 provides that all offences under the Pakistan Penal Code may be waived or compounded, and the prov |
| 194 | partial | u | 1 | pass | - | Section 338G allows the Government, in consultation with the Council of Islamic ideology, to make rules by notification in the official Gazette to car |
| 195 | partial | u,f | 1 | pass | - | Sections 372 and 373 provided for the offense of selling and buying a minor for the purpose of prostitution, etc. [S1] |
| 196 | partial | u | 1 | pass | - | Section 56 provided for the sentence of penal servitude for offenders who were Europeans or Americans [S1]. |
| 197 | unanswer | - | - | pass | - | The Pakistan Penal Code creates offences such as fraudulent cancellation or destruction of wills, authorities to adopt, or valuable security [S1], and |
| 198 | unanswer | - | - | flag: no verified quote from cited source(s) [ | - | The provided sources do not define terrorism or prescribe punishments for terrorist acts. The sections cited address specific criminal offenses such a |
| 199 | unanswer | - | - | pass | - | The Code does not specifically mention throwing acid on a person. Acid is described as a 'poison' or 'unwholesome drug' in [S3], so the relevant provi |
| 200 | unanswer | - | - | flag: no verified quote from cited source(s) [ | - | The Code defines "adult" as a person who has attained the age of eighteen years [S4], and "minor" as a person who is not an adult [S4]. The penalty fo |
| 201 | unanswer | - | - | pass | - | The sources do not specify the method by which a death sentence is carried out, such as hanging. [S2] |
| 202 | unanswer | - | - | refused | - | I don't know based on the provided sources. |
| 203 | unanswer | - | - | pass | - | The Code creates offences for stalking or harassment, such as insulting a woman's modesty [S1] and lurking house-trespass or house-breaking by night a |
| 204 | unanswer | - | - | pass | - | Under the Pakistan Penal Code, an act by a child under seven years of age is not an offence [S1, S5]. For children above seven and under twelve who ha |
| 205 | unanswer | - | - | refused | - | The sources do not provide information about the jurisdiction of the Federal Shariat Court over Chapter XVI offences. |
| 206 | unanswer | - | - | pass | - | The Code prescribes imprisonment for up to six months, a fine of up to 87 or 88 rupees, or both for selling or offering to sell drugs as different pre |
| 207 | unanswer | - | - | pass | - | The Code does not contain a specific provision titled 'money laundering.' However, Section 210 [S2] addresses fraudulently obtaining a decree or order |
