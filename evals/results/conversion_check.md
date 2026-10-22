# Conversion check

Each PDF converted by each backend, then compared with Poppler's `pdftotext` text (see `convcheck.py`).

| pdf | backend | verdict | fused # | novel # | dropped nums | word recall | 6-run recall | order gap | spaced runs | ragged tables | flat code | convert s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| code_mcp_handbook.pdf | pymupdf4llm | warn | 0 | 0 | 0.0 | 0.9903 | 0.9338 | 0.0565 | 0 | 3 | 0 | 0.6 |
| code_mcp_handbook.pdf | docling | bad | 0 | 0 | 0.0089 | 0.9716 | 0.9134 | 0.0582 | 0 | 0 | 72 | 0.3 |
| math_eslii_ch3_excerpt.pdf | pymupdf4llm | warn | 12 | 11 | 0.1296 | 0.9238 | 0.8064 | 0.1174 | 0 | 1 | 0 | 0.3 |
| math_eslii_ch3_excerpt.pdf | docling | warn | 8 | 2 | 0.2315 | 0.9433 | 0.8136 | 0.1297 | 15 | 1 | 0 | 0.2 |
| scan_islp_pages.pdf | pymupdf4llm | not-run | - | - | - | - | - | - | - | - | - | 0.0 |
| scan_islp_pages.pdf | docling | not-run | - | - | - | - | - | - | - | - | - | 0.0 |
| statute_banking_ordinance.pdf | pymupdf4llm | bad | 5 | 0 | 0.029 | 0.9974 | 0.9411 | 0.0563 | 0 | 23 | 0 | 0.3 |
| statute_banking_ordinance.pdf | docling | warn | 1 | 0 | 0.0528 | 0.9973 | 0.9487 | 0.0486 | 0 | 0 | 0 | 0.2 |
| tables_llm_reference.pdf | pymupdf4llm | warn | 0 | 0 | 0.0 | 0.9969 | 0.9444 | 0.0526 | 0 | 1 | 0 | 0.1 |
| tables_llm_reference.pdf | docling | warn | 1 | 3 | 0.0 | 0.9973 | 0.9348 | 0.0625 | 0 | 0 | 0 | 0.1 |
| ProtectionEconomicReformsAct-1992.pdf | pymupdf4llm | ok | 0 | 0 | 0.0 | 1.0 | 0.9637 | 0.0363 | 0 | 0 | 0 | 0.0 |
| ProtectionEconomicReformsAct-1992.pdf | docling | ok | 0 | 0 | 0.0 | 1.0 | 0.9853 | 0.0147 | 0 | 0 | 0 | 0.0 |
| 2510.04871v1.pdf | pymupdf4llm | warn | 1 | 4 | 0.0093 | 0.9415 | 0.7755 | 0.166 | 0 | 0 | 0 | 0.2 |
| 2510.04871v1.pdf | docling | warn | 1 | 0 | 0.014 | 0.9455 | 0.8101 | 0.1354 | 1 | 0 | 4 | 0.1 |

## Warnings and examples

- **code_mcp_handbook.pdf / pymupdf4llm**: 3 of 41 table(s) have rows with differing cell counts
- **code_mcp_handbook.pdf / docling**: 72 code block(s) collapsed onto one line
    - dropped: 32
- **math_eslii_ch3_excerpt.pdf / pymupdf4llm**: 11 replacement character(s), 0 leftover HTML tag(s); 1 of 3 table(s) have rows with differing cell counts
    - fused: oot or square; - basis expansions, such as X2 = X12, X3= X 13, leading to a polynomial representation; - numeric or “dum | ct of G by a set of level-dependent constants, since in �5j=1Xjβj,oneoftheXjsisone,andtheothersarezero. - interactions bet | st squares coefficient of x has the form where x¯ =^� ixi/N,and1=x0,thevectorofNones.Wecanviewthe estimate (3.27) as the res
    - novel: 6 8 Number of Directions 1.8 1.8 1.6 1.6 1.4 1.4 CV Error 1.21.0 CV Error 1.21.0 0.8 0.8 0.6 0.6 1.8 1.8 1.6 1.6 1.4 1.4 CV | ctive set at each step. The length are measured in units of L11 arc length. Least Angle Regression Lasso 0 5 10 15 0 5 10 1 | ffect of G by a set of level-dependent constants, since in �5j=1Xjβj,oneoftheXjsisone,andtheothersarezero. - interactions
    - dropped: 2xt | 2n | 0.03
- **math_eslii_ch3_excerpt.pdf / docling**: 15 run(s) of spaced-out single letters (garbled formula text); 1 of 4 table(s) have rows with differing cell counts
    - fused: ^ { T } y ,$$ where ˆ yi = ˆ f(xi). The matrix H = X(XT X)-1XT appearing in equation (3.7) is sometimes called the "hat" m | by Andrew Ng.] - 42 2. Overview of Supervised Learning ## 3Linear Methods for Regression ## 3.1 Introduction A linear regre | ere are in fact also the multiple regression coefficients. 1The inner-product notation is suggestive of generalizations of
    - novel: ffect of G by a set of level-dependent constants, since in ∑5j=1 Xjβj, one of the Xjs is one, and the others are zero. - i | ach xij gets replaced by xij - ¯xj. We estimate β0 by ¯ y = 1N ∑N1 yi. The remaining coefficients get estimated by a ridge
    - dropped: 43 | 2xt | 2n
    - spaced_letters: l e f t h e r s u m e s | a s t a t i s t a l p o i f w e r | h i s c r i t i o n i s
- **statute_banking_ordinance.pdf / pymupdf4llm**: 5 numeric token(s) fused from two words of the PDF, e.g. '3provided' (a footnote marker or label glued to a value); 23 of 45 table(s) have rows with differing cell counts
    - fused: ction 42 of the Companies Ordinance 1984(XLVII of 1984):^2 3Provided further that the State Bank may, subject to such conditions | nk, be liable to a penalty of an amount which may extend to 2twenty thousand rupees and, where the default is a continuing one, | Government on any inspection made under this section. (7) 2Omitted > 3 40A. Responsibility of State Bank — (1) Without prejud
    - dropped: 7.1 | 1985.2 | 1of
- **statute_banking_ordinance.pdf / docling**: 1 numeric token(s) fused from two words of the PDF, e.g. '1981page' (a footnote marker or label glued to a value)
    - fused: tte of Pakistan, Extraordinary, Part III dated December 19, 1981Page 446 and ERRATA in Gazette of Pakistan, Extraordinary, Part
    - dropped: 101972 | 7.1 | 1985.2
- **tables_llm_reference.pdf / pymupdf4llm**: 1 of 31 table(s) have rows with differing cell counts
- **tables_llm_reference.pdf / docling**: 1 numeric token(s) fused from two words of the PDF, e.g. 'v32' (a footnote marker or label glued to a value)
    - fused: https://huggingface.co/docs/transformers/model_doc/deepseek_v32) - [Kimi Linear and KDA, arXiv 2510.26692](https://arxiv.or
    - novel: scalable-ai.eecs.berkeley.edu/assets/lecture_slides/lecture_15.pdf) - [Reasoning RL in 2026, Turing Post](https://www.turi | v1 | om/grpo-in-production-the-failure-modes-nobody-writes-about-5d59c3fc9c3b) - [Agent-RL algorithm list, arXiv 2606.12384](https://ar
- **2510.04871v1.pdf / pymupdf4llm**: 1 numeric token(s) fused from two words of the PDF, e.g. '15m' (a footnote marker or label glued to a value)
    - fused: ocess, removing the need for the extra forward pass. Over- 15M on Sudoku and 19M on Maze 8 Recursive Reasoning with Tiny
    - novel: xt --> Cross-entropy loss: Reverse Embedding Add & Norm MLP 4x Add & Norm Self-Attention 个 Input (x) Prediction (y) Latent | any way, and it made the approach more complicated. Back- 11 Recursive Reasoning with Tiny Networks ## Algorithms with | returnz ``` ``` defdeeprecursion(x,z,n=6,T=3): #recursingT−1timestoimprovez(nogradientsneeded) withtorch.nograd(): forjinrange(T−1
    - dropped: 2510.04871 | 3d
- **2510.04871v1.pdf / docling**: 1 numeric token(s) fused from two words of the PDF, e.g. '94309440' (a footnote marker or label glued to a value); 1 run(s) of spaced-out single letters (garbled formula text); 4 code block(s) collapsed onto one line
    - fused: Conference on Computer Vision and Pattern Recognition, pp. 94309440, 2024. Brock, A., Donahue, J., and Simonyan, K. Large scal
    - dropped: 2510.04871 | 9430 | 9440
    - spaced_letters: f o r w a r d p a s s o f H R M i s d o n e a s f l o w s
