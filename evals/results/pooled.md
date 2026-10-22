# Pooled retrieval evaluation

One index over 48 files (questionprep, pdfs, banking, pera, trm, ssd), 388 answerable queries from every corpus's gold file. Relevance = the chunk is from the gold file and contains the gold snippet. Values are percentages with a 95% bootstrap half-width.

Golden-format questions dropped because no usable chunk holds their evidence verbatim: pera: 1 unreachable, ssd: 8 unreachable. Partial/unanswerable golden rows are not retrieval queries.

## Pooled

| system | recall@1 | recall@3 | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 | map@10 | ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pool/bm25 | 51.5 ±5.4 | 72.2 ±4.8 | 78.2 ±4.5 | 85.1 ±3.7 | 91.4 ±2.9 | 64.6 ±4.3 | 69.1 ±4.0 | 63.5 ±4.4 | 3 |
| pool/gemma RRF | 50.6 ±5.4 | 73.2 ±4.7 | 84.4 ±3.8 | 90.9 ±2.9 | 95.0 ±2.3 | 65.7 ±4.2 | 71.3 ±3.6 | 64.5 ±4.2 | 52 |
| pool/gemma RRF+rerank | 70.5 ±4.8 | 88.3 ±3.3 | 91.7 ±2.9 | 94.4 ±2.4 | 95.0 ±2.3 | 81.7 ±3.4 | 84.4 ±2.9 | 80.7 ±3.4 | 1411 |

## questionprep (85 queries)

| system | recall@1 | recall@3 | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 | map@10 | ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pool/bm25 | 32.9 ±11.4 | 62.9 ±11.4 | 71.4 ±10.0 | 78.6 ±10.0 | 88.6 ±7.9 | 49.4 ±9.2 | 56.5 ±8.8 | 49.4 ±9.2 | 3 |
| pool/gemma RRF | 40.0 ±11.4 | 68.6 ±11.4 | 77.1 ±10.0 | 88.6 ±7.9 | 92.9 ±6.4 | 55.9 ±9.2 | 63.8 ±8.2 | 55.9 ±9.2 | 45 |
| pool/gemma RRF+rerank | 57.1 ±11.4 | 78.6 ±10.0 | 88.6 ±7.9 | 92.9 ±6.4 | 92.9 ±6.4 | 69.5 ±8.8 | 75.2 ±7.6 | 69.5 ±8.8 | 935 |

## pdfs (106 queries)

| system | recall@1 | recall@3 | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 | map@10 | ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pool/bm25 | 67.1 ±10.4 | 85.4 ±7.9 | 89.0 ±6.7 | 91.5 ±6.1 | 96.3 ±4.3 | 76.1 ±7.9 | 79.9 ±7.0 | 76.1 ±7.9 | 3 |
| pool/gemma RRF | 59.8 ±11.0 | 80.5 ±8.5 | 91.5 ±5.5 | 93.9 ±4.9 | 97.6 ±3.0 | 71.4 ±8.1 | 76.9 ±6.8 | 71.4 ±8.1 | 42 |
| pool/gemma RRF+rerank | 80.5 ±9.1 | 96.3 ±4.3 | 96.3 ±4.3 | 97.6 ±3.0 | 97.6 ±3.0 | 88.3 ±5.6 | 90.7 ±4.7 | 88.3 ±5.6 | 1379 |

## banking (44 queries)

| system | recall@1 | recall@3 | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 | map@10 | ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pool/bm25 | 75.0 ±15.6 | 81.2 ±14.1 | 81.2 ±14.1 | 87.5 ±10.9 | 93.8 ±7.8 | 78.8 ±12.8 | 80.8 ±12.0 | 78.8 ±12.8 | 3 |
| pool/gemma RRF | 65.6 ±15.6 | 84.4 ±12.5 | 93.8 ±7.8 | 96.9 ±4.7 | 100.0 ±0.0 | 76.5 ±11.4 | 81.5 ±9.4 | 76.5 ±11.4 | 50 |
| pool/gemma RRF+rerank | 84.4 ±10.9 | 96.9 ±4.7 | 96.9 ±4.7 | 100.0 ±0.0 | 100.0 ±0.0 | 91.0 ±6.7 | 93.2 ±5.1 | 91.0 ±6.7 | 2165 |

## pera (38 queries)

| system | recall@1 | recall@3 | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 | map@10 | ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pool/bm25 | 59.2 ±15.1 | 72.4 ±13.8 | 75.9 ±13.6 | 88.2 ±9.9 | 88.2 ±9.9 | 69.2 ±12.7 | 73.0 ±11.2 | 67.8 ±12.5 | 3 |
| pool/gemma RRF | 59.6 ±15.4 | 79.4 ±12.5 | 87.3 ±10.1 | 90.8 ±8.6 | 93.4 ±7.2 | 73.1 ±12.1 | 76.2 ±10.3 | 70.8 ±11.9 | 63 |
| pool/gemma RRF+rerank | 79.8 ±12.1 | 90.8 ±8.6 | 90.8 ±8.6 | 90.8 ±8.6 | 93.4 ±7.2 | 88.2 ±9.2 | 88.2 ±8.9 | 86.8 ±9.9 | 1956 |

## trm (63 queries)

| system | recall@1 | recall@3 | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 | map@10 | ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pool/bm25 | 47.1 ±11.4 | 72.0 ±10.7 | 80.2 ±9.1 | 88.6 ±7.1 | 90.2 ±7.1 | 66.4 ±9.4 | 70.5 ±8.0 | 63.4 ±8.9 | 3 |
| pool/gemma RRF | 46.0 ±11.5 | 70.1 ±11.1 | 86.0 ±8.1 | 95.0 ±4.9 | 96.6 ±4.0 | 67.4 ±9.0 | 73.1 ±7.2 | 65.0 ±8.8 | 62 |
| pool/gemma RRF+rerank | 73.0 ±9.8 | 89.7 ±6.3 | 91.8 ±5.7 | 95.0 ±4.9 | 96.6 ±4.0 | 87.6 ±6.3 | 87.9 ±5.6 | 84.3 ±6.7 | 1111 |

## ssd (52 queries)

| system | recall@1 | recall@3 | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 | map@10 | ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pool/bm25 | 37.2 ±13.0 | 58.3 ±13.3 | 67.6 ±12.2 | 76.0 ±10.9 | 89.7 ±8.0 | 52.9 ±11.5 | 57.0 ±10.2 | 49.9 ±11.0 | 3 |
| pool/gemma RRF | 40.1 ±13.1 | 60.3 ±13.0 | 73.1 ±11.2 | 81.1 ±10.3 | 89.7 ±7.7 | 56.0 ±11.3 | 60.3 ±9.9 | 52.5 ±10.6 | 60 |
| pool/gemma RRF+rerank | 54.5 ±13.3 | 79.8 ±10.4 | 86.2 ±8.7 | 89.7 ±7.7 | 89.7 ±7.7 | 70.2 ±10.0 | 74.5 ±8.7 | 68.8 ±9.9 | 1604 |
Byte-identical files indexed once (gold names mapped to the kept copy): `packages/qp-pipeline/src/qp_pipeline/py.typed` = `packages/qp-core/src/qp_core/py.typed`; `packages/qp-voice/src/qp_voice/py.typed` = `packages/qp-core/src/qp_core/py.typed`; `Banking-Companies-Ordinance-1962.pdf` = `statute_banking_ordinance.pdf`.


## Wrong-document rates (`pool/gemma RRF+rerank`; inside one corpus another file is often a legitimate neighbour topic, another corpus never is)

| corpus | queries | top-1 from another corpus | top-1 not from a gold file | no gold-file hit in the top 5 |
|---|---:|---:|---:|---:|
| questionprep | 70 | 0 (0.0%) | 25 (35.7%) | 5 (7.1%) |
| pdfs | 82 | 2 (2.4%) | 2 (2.4%) | 0 (0.0%) |
| banking | 32 | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| pera | 38 | 3 (7.9%) | 3 (7.9%) | 2 (5.3%) |
| trm | 63 | 1 (1.6%) | 1 (1.6%) | 1 (1.6%) |
| ssd | 52 | 1 (1.9%) | 1 (1.9%) | 0 (0.0%) |
| all | 337 | 7 (2.1%) | 32 (9.5%) | 8 (2.4%) |

## Cost of sharing the index (same queries, same system, one corpus alone vs all together)

| corpus | isolated recall@5 | pooled recall@5 | difference |
|---|---:|---:|---:|
| questionprep | 88.6 | 88.6 | +0.0 |
| pdfs | 95.1 | 96.3 | +1.2 |
| banking | 96.9 | 96.9 | +0.0 |
| pera | 97.4 | 90.8 | -6.6 |
| trm | 93.4 | 91.8 | -1.6 |
| ssd | 91.0 | 86.2 | -4.8 |

## Misses (`pool/gemma RRF+rerank`, no relevant chunk in the top 10)

17 queries without a relevant chunk in the top 10:

- `questionprep:d02` (doc, natural) **What password hashing does the app use and how many iterations?**  
  gold: `docs/architecture.md`; found at rank >20; top-3: QuestionPrep — next phases (plan for Claude Code) ; packages/qp-core/src/qp_core/DBManager.py > DBMana; packages/qp-core/src/qp_core/DBManager.py > DBMana
- `questionprep:d18` (doc, natural) **What does the reasoning budget setting control?**  
  gold: `docs/configuration.md`; found at rank >20; top-3: packages/qp-pipeline/src/qp_pipeline/Enricher.py >; QuestionPrep — next phases (plan for Claude Code) ; packages/qp-pipeline/src/qp_pipeline/Enricher.py >
- `questionprep:d28` (doc, natural) **How is spoken audio turned into a transcript?**  
  gold: `docs/architecture.md`; found at rank >20; top-3: packages/qp-voice/src/qp_voice/speech_to_text.py >; HTTP API > Voice; apps/orchestrator/main.py > analyze_speech
- `questionprep:c07` (code, natural) **how are code blocks math and tables protected from being split in markdown chunking**  
  gold: `packages/qp-pipeline/src/qp_pipeline/MarkdownChunker.py`; found at rank >20; top-3: packages/qp-pipeline/src/qp_pipeline/MarkdownChunk; Architecture > 1. Ingestion (upload → chunks); packages/qp-pipeline/src/qp_pipeline/MarkdownChunk
- `questionprep:c24` (code, natural) **how are near-identical generated questions removed**  
  gold: `packages/qp-pipeline/src/qp_pipeline/Enricher.py`; found at rank >20; top-3: packages/qp-pipeline/src/qp_pipeline/verify.py > <; Architecture > 2. Enrichment (chunks → questions); packages/qp-pipeline/src/qp_pipeline/Enricher.py >
- `pdfs:s08` (scan, natural) **How are most statistical learning methods characterized?**  
  gold: `scan_islp_pages.pdf`; found at rank >20; top-3: 2.1.2 How Do We Estimate f?; 2.2 Assessing Model Accuracy; 2.1.4 Supervised Versus Unsupervised Learning
- `pdfs:c06` (code, natural) **When should an MCP server be made stateless?**  
  gold: `code_mcp_handbook.pdf`; found at rank >20; top-3: From Python to a Deployed AI Application > 04 MCP ; From Python to a Deployed AI Application > 10 Dock; From Python to a Deployed AI Application > 04 MCP 
- `pera:pera-q004` (pera, natural) **When was the Act published in the Gazette of Pakistan?**  
  gold: `ProtectionEconomicReformsAct-1992.pdf`; found at rank >20; top-3: ORDINANCE No. LVII OF 1962 > 7 . Form of business ; SUSPENSION OF BUSINESS AND WINDING UP OF BANKING C; SUSPENSION OF BUSINESS AND WINDING UP OF BANKING C
- `pera:pera-q030` (pera, natural) **Which amending law changed section 4(2)(f) and added clause (g)?**  
  gold: `ProtectionEconomicReformsAct-1992.pdf`; found at rank >20; top-3: ORDINANCE No. LVII OF 1962 > 3. Limited applicatio; ORDINANCE No. LVII OF 1962 > 7 . Form of business ; ORDINANCE No. LVII OF 1962 > 7 . Form of business 
- `pera:pera-q031` (pera, natural) **Why does a 1992 Act refer to a 2001 Ordinance in section 3?**  
  gold: `ProtectionEconomicReformsAct-1992.pdf`; found at rank 16; top-3: ACT NO. XII OF 1992; ACT NO. XII OF 1992; RP—I/82 > RECORD OF AMENDMENTS
- `trm:trm-q001` (trm, natural) **Who wrote 'Less is More: Recursive Reasoning with Tiny Networks' and where is the author affiliated?**  
  gold: `2510.04871v1.pdf`; found at rank 11; top-3: Less is More: Recursive Reasoning with Tiny Networ; Less is More: Recursive Reasoning with Tiny Networ; Less is More: Recursive Reasoning with Tiny Networ
- `trm:trm-q056` (trm, natural) **What limitations and future directions does the conclusion name?**  
  gold: `2510.04871v1.pdf`; found at rank >20; top-3: From Python to a Deployed AI Application > 14 The ; packages/qp-pipeline/src/qp_pipeline/prompts.py > ; B.3 HowSSDReshapes Locks andForks
- `ssd:ssd-q005` (ssd, natural) **What does SSD not require? List everything the paper rules out.**  
  gold: `2604.01193v2.pdf`; found at rank >20; top-3: B.2 Understanding theSSDObjective and Its Learning; 3.2 SSD ImprovesCodeGenerationAcross theBoard; B.5 WhyDecode-OnlyTuningCannotMatchSSD
- `ssd:ssd-q006` (ssd, natural) **How much does hard-problem pass@5 improve for Qwen3-30B-Instruct on LCB v6?**  
  gold: `2604.01193v2.pdf`; found at rank >20; top-3: 3.2 SSD ImprovesCodeGenerationAcross theBoard; 3.1 Experimental Setup; 3.2 SSD ImprovesCodeGenerationAcross theBoard
- `ssd:ssd-q026` (ssd, natural) **What is effective temperature T_eff and what does it predict?**  
  gold: `2604.01193v2.pdf`; found at rank >20; top-3: B.3 HowSSDReshapes Locks andForks; C.2 HowSSDHyperparameters Interact: Full Sweeps; 3.3 Global DecodingPoliciesCannotMatchSSD
- `ssd:ssd-q043` (ssd, natural) **How are thinking models prompted differently from instruct models?**  
  gold: `2604.01193v2.pdf`; found at rank >20; top-3: C.2 HowSSDHyperparameters Interact: Full Sweeps; From Python to a Deployed AI Application > 17 Ques; 3.3 Global DecodingPoliciesCannotMatchSSD
- `ssd:ssd-q060` (ssd, natural) **Is the base-model pass@5 baseline used in the stress test the same as in Table 2?**  
  gold: `2604.01193v2.pdf`; found at rank >20; top-3: C.5 High-TemperatureCaseStudy: Full Details andAdd; 3.1 Experimental Setup; 3.3 Global DecodingPoliciesCannotMatchSSD
