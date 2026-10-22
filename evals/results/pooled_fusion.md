# Pooled retrieval evaluation

One index over 48 files (questionprep, pdfs, banking, pera, trm, ssd), 388 answerable queries from every corpus's gold file. Relevance = the chunk is from the gold file and contains the gold snippet. Values are percentages with a 95% bootstrap half-width.

Golden-format questions dropped because no usable chunk holds their evidence verbatim: pera: 1 unreachable, ssd: 8 unreachable. Partial/unanswerable golden rows are not retrieval queries.

## Pooled

| system | recall@1 | recall@3 | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 | map@10 | ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pool/bm25 | 51.5 ±5.4 | 72.2 ±4.8 | 78.2 ±4.5 | 85.1 ±3.7 | 91.4 ±2.9 | 64.6 ±4.3 | 69.1 ±4.0 | 63.5 ±4.4 | 3 |
| pool/gemma RRF | 50.3 ±5.4 | 73.2 ±4.7 | 84.4 ±3.8 | 90.9 ±2.9 | 95.0 ±2.3 | 65.7 ±4.1 | 71.2 ±3.6 | 64.4 ±4.1 | 40 |
| pool/gemma RRF+rerank | 70.5 ±4.8 | 88.3 ±3.3 | 91.7 ±2.9 | 94.4 ±2.4 | 95.0 ±2.3 | 81.6 ±3.4 | 84.3 ±2.9 | 80.6 ±3.4 | 1391 |
| pool/gemma z(1,1) | 55.7 ±5.3 | 78.5 ±4.3 | 85.0 ±3.7 | 91.7 ±2.9 | 95.3 ±2.2 | 70.1 ±3.9 | 75.0 ±3.4 | 69.2 ±3.9 | 37 |
| pool/gemma z(1,1)+rerank | 70.2 ±4.7 | 88.2 ±3.4 | 92.3 ±2.6 | 94.1 ±2.4 | 95.3 ±2.2 | 81.6 ±3.3 | 84.2 ±2.9 | 80.5 ±3.3 | 1328 |
| pool/gemma z(dense x2) | 53.0 ±5.3 | 75.0 ±4.5 | 83.6 ±3.7 | 90.2 ±3.1 | 94.7 ±2.3 | 67.4 ±4.1 | 72.5 ±3.5 | 66.4 ±4.1 | 39 |
| pool/gemma z(dense x2)+rerank | 70.4 ±4.8 | 88.0 ±3.3 | 91.7 ±2.9 | 93.6 ±2.5 | 94.7 ±2.3 | 81.3 ±3.4 | 83.9 ±3.0 | 80.3 ±3.4 | 1264 |
| pool/gemma z(lexical x2) | 54.7 ±5.3 | 78.1 ±4.3 | 83.7 ±3.9 | 89.3 ±3.2 | 95.5 ±2.2 | 68.7 ±4.0 | 73.5 ±3.6 | 68.0 ±4.0 | 40 |
| pool/gemma z(lexical x2)+rerank | 72.9 ±4.6 | 87.6 ±3.3 | 92.9 ±2.6 | 94.5 ±2.3 | 95.5 ±2.2 | 83.0 ±3.3 | 85.4 ±2.8 | 82.0 ±3.2 | 1398 |

## questionprep (85 queries)

| system | recall@1 | recall@3 | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 | map@10 | ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pool/bm25 | 32.9 ±11.4 | 62.9 ±11.4 | 71.4 ±10.0 | 78.6 ±10.0 | 88.6 ±7.9 | 49.4 ±9.2 | 56.5 ±8.8 | 49.4 ±9.2 | 3 |
| pool/gemma RRF | 40.0 ±11.4 | 68.6 ±11.4 | 77.1 ±10.0 | 88.6 ±7.9 | 92.9 ±6.4 | 55.9 ±9.2 | 63.8 ±8.2 | 55.9 ±9.2 | 34 |
| pool/gemma RRF+rerank | 57.1 ±11.4 | 78.6 ±10.0 | 88.6 ±7.9 | 92.9 ±6.4 | 92.9 ±6.4 | 69.5 ±8.8 | 75.2 ±7.6 | 69.5 ±8.8 | 918 |
| pool/gemma z(1,1) | 40.0 ±10.7 | 71.4 ±10.7 | 78.6 ±10.0 | 88.6 ±7.1 | 95.7 ±5.0 | 57.1 ±9.1 | 64.8 ±8.1 | 57.1 ±9.1 | 33 |
| pool/gemma z(1,1)+rerank | 57.1 ±11.4 | 78.6 ±10.0 | 88.6 ±7.9 | 92.9 ±6.4 | 95.7 ±5.0 | 70.0 ±8.7 | 75.7 ±7.5 | 70.0 ±8.7 | 901 |
| pool/gemma z(dense x2) | 40.0 ±10.7 | 71.4 ±10.0 | 78.6 ±10.0 | 90.0 ±7.1 | 92.9 ±6.4 | 57.7 ±8.7 | 65.5 ±7.9 | 57.7 ±8.7 | 39 |
| pool/gemma z(dense x2)+rerank | 58.6 ±11.4 | 80.0 ±9.3 | 88.6 ±7.9 | 91.4 ±6.4 | 92.9 ±6.4 | 70.6 ±8.6 | 75.7 ±7.8 | 70.6 ±8.6 | 833 |
| pool/gemma z(lexical x2) | 42.9 ±10.7 | 71.4 ±11.4 | 74.3 ±10.7 | 84.3 ±8.6 | 95.7 ±5.0 | 57.2 ±9.3 | 63.8 ±8.6 | 57.2 ±9.3 | 38 |
| pool/gemma z(lexical x2)+rerank | 61.4 ±11.4 | 78.6 ±10.0 | 90.0 ±7.1 | 92.9 ±5.7 | 95.7 ±5.0 | 71.9 ±8.7 | 77.1 ±7.5 | 71.9 ±8.7 | 973 |

## pdfs (106 queries)

| system | recall@1 | recall@3 | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 | map@10 | ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pool/bm25 | 67.1 ±10.4 | 85.4 ±7.9 | 89.0 ±6.7 | 91.5 ±6.1 | 96.3 ±4.3 | 76.1 ±7.9 | 79.9 ±7.0 | 76.1 ±7.9 | 3 |
| pool/gemma RRF | 59.8 ±11.0 | 80.5 ±8.5 | 91.5 ±5.5 | 93.9 ±4.9 | 97.6 ±3.0 | 71.6 ±8.0 | 77.1 ±6.8 | 71.6 ±8.0 | 38 |
| pool/gemma RRF+rerank | 80.5 ±9.1 | 96.3 ±4.3 | 96.3 ±4.3 | 97.6 ±3.0 | 97.6 ±3.0 | 88.3 ±5.6 | 90.7 ±4.7 | 88.3 ±5.6 | 1362 |
| pool/gemma z(1,1) | 68.3 ±10.4 | 87.8 ±6.7 | 93.9 ±5.5 | 96.3 ±4.3 | 97.6 ±3.0 | 79.2 ±7.1 | 83.5 ±5.9 | 79.2 ±7.1 | 38 |
| pool/gemma z(1,1)+rerank | 81.7 ±9.1 | 96.3 ±4.3 | 96.3 ±4.3 | 97.6 ±3.0 | 97.6 ±3.0 | 89.2 ±5.6 | 91.3 ±4.6 | 89.2 ±5.6 | 1303 |
| pool/gemma z(dense x2) | 63.4 ±11.0 | 81.7 ±8.5 | 91.5 ±5.5 | 92.7 ±5.5 | 97.6 ±3.0 | 74.3 ±7.9 | 78.8 ±6.7 | 74.3 ±7.9 | 39 |
| pool/gemma z(dense x2)+rerank | 80.5 ±9.1 | 96.3 ±4.3 | 96.3 ±4.3 | 97.6 ±3.0 | 97.6 ±3.0 | 88.2 ±5.6 | 90.6 ±4.7 | 88.2 ±5.6 | 1240 |
| pool/gemma z(lexical x2) | 65.9 ±11.0 | 89.0 ±6.7 | 92.7 ±5.5 | 95.1 ±4.3 | 98.8 ±1.8 | 77.6 ±7.3 | 82.0 ±6.2 | 77.6 ±7.3 | 38 |
| pool/gemma z(lexical x2)+rerank | 84.1 ±7.9 | 97.6 ±3.0 | 97.6 ±3.0 | 98.8 ±1.8 | 98.8 ±1.8 | 90.8 ±4.9 | 92.9 ±4.0 | 90.8 ±4.9 | 1381 |

## banking (44 queries)

| system | recall@1 | recall@3 | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 | map@10 | ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pool/bm25 | 75.0 ±15.6 | 81.2 ±14.1 | 81.2 ±14.1 | 87.5 ±10.9 | 93.8 ±7.8 | 78.8 ±12.8 | 80.8 ±12.0 | 78.8 ±12.8 | 3 |
| pool/gemma RRF | 65.6 ±15.6 | 84.4 ±12.5 | 93.8 ±7.8 | 96.9 ±4.7 | 100.0 ±0.0 | 77.0 ±11.1 | 81.9 ±9.2 | 77.0 ±11.1 | 38 |
| pool/gemma RRF+rerank | 84.4 ±10.9 | 96.9 ±4.7 | 96.9 ±4.7 | 100.0 ±0.0 | 100.0 ±0.0 | 91.0 ±6.7 | 93.2 ±5.1 | 91.0 ±6.7 | 2136 |
| pool/gemma z(1,1) | 75.0 ±14.1 | 87.5 ±10.9 | 90.6 ±9.4 | 96.9 ±4.7 | 100.0 ±0.0 | 83.0 ±10.7 | 86.4 ±8.9 | 83.0 ±10.7 | 39 |
| pool/gemma z(1,1)+rerank | 84.4 ±10.9 | 96.9 ±4.7 | 96.9 ±4.7 | 100.0 ±0.0 | 100.0 ±0.0 | 91.0 ±6.6 | 93.2 ±5.0 | 91.0 ±6.6 | 2082 |
| pool/gemma z(dense x2) | 68.8 ±15.6 | 84.4 ±12.5 | 96.9 ±4.7 | 96.9 ±4.7 | 100.0 ±0.0 | 79.5 ±10.7 | 83.9 ±9.0 | 79.5 ±10.7 | 39 |
| pool/gemma z(dense x2)+rerank | 84.4 ±10.9 | 96.9 ±4.7 | 96.9 ±4.7 | 100.0 ±0.0 | 100.0 ±0.0 | 90.0 ±7.6 | 92.5 ±5.7 | 90.0 ±7.6 | 2047 |
| pool/gemma z(lexical x2) | 71.9 ±15.6 | 87.5 ±10.9 | 87.5 ±10.9 | 93.8 ±7.8 | 100.0 ±0.0 | 80.1 ±11.3 | 83.4 ±10.2 | 80.1 ±11.3 | 39 |
| pool/gemma z(lexical x2)+rerank | 87.5 ±10.9 | 96.9 ±4.7 | 96.9 ±4.7 | 100.0 ±0.0 | 100.0 ±0.0 | 92.6 ±6.4 | 94.5 ±4.9 | 92.6 ±6.4 | 2059 |

## pera (38 queries)

| system | recall@1 | recall@3 | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 | map@10 | ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pool/bm25 | 59.2 ±15.1 | 72.4 ±13.8 | 75.9 ±13.6 | 88.2 ±9.9 | 88.2 ±9.9 | 69.2 ±12.7 | 73.0 ±11.2 | 67.8 ±12.5 | 3 |
| pool/gemma RRF | 57.0 ±15.6 | 79.4 ±12.5 | 87.3 ±10.1 | 90.8 ±8.6 | 93.4 ±7.2 | 71.9 ±12.0 | 75.4 ±10.3 | 69.6 ±11.9 | 39 |
| pool/gemma RRF+rerank | 79.8 ±12.1 | 90.8 ±8.6 | 90.8 ±8.6 | 90.8 ±8.6 | 93.4 ±7.2 | 87.7 ±9.2 | 87.8 ±9.0 | 86.4 ±9.6 | 1932 |
| pool/gemma z(1,1) | 63.2 ±14.5 | 87.3 ±10.1 | 87.3 ±10.1 | 88.2 ±9.9 | 90.8 ±8.6 | 75.9 ±11.4 | 78.3 ±10.4 | 74.5 ±11.3 | 39 |
| pool/gemma z(1,1)+rerank | 79.8 ±12.1 | 90.8 ±8.6 | 90.8 ±8.6 | 90.8 ±8.6 | 90.8 ±8.6 | 87.7 ±9.2 | 87.8 ±9.0 | 86.4 ±9.6 | 1697 |
| pool/gemma z(dense x2) | 60.5 ±15.1 | 82.0 ±11.6 | 87.3 ±10.1 | 89.9 ±8.6 | 93.4 ±7.9 | 73.5 ±11.7 | 76.4 ±10.5 | 71.5 ±11.8 | 39 |
| pool/gemma z(dense x2)+rerank | 79.8 ±12.1 | 90.8 ±8.6 | 90.8 ±8.6 | 90.8 ±8.6 | 93.4 ±7.9 | 87.3 ±9.6 | 87.5 ±9.2 | 86.0 ±9.9 | 1621 |
| pool/gemma z(lexical x2) | 60.5 ±14.5 | 87.3 ±10.1 | 88.2 ±9.9 | 88.2 ±9.9 | 90.8 ±8.6 | 75.0 ±11.4 | 77.8 ±10.3 | 73.8 ±11.2 | 39 |
| pool/gemma z(lexical x2)+rerank | 79.8 ±12.1 | 90.8 ±8.6 | 90.8 ±8.6 | 90.8 ±8.6 | 90.8 ±8.6 | 88.2 ±9.2 | 88.2 ±8.9 | 86.8 ±9.9 | 1823 |

## trm (63 queries)

| system | recall@1 | recall@3 | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 | map@10 | ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pool/bm25 | 47.1 ±11.4 | 72.0 ±10.7 | 80.2 ±9.1 | 88.6 ±7.1 | 90.2 ±7.1 | 66.4 ±9.4 | 70.5 ±8.0 | 63.4 ±8.9 | 2 |
| pool/gemma RRF | 46.0 ±11.5 | 70.1 ±11.1 | 86.0 ±8.1 | 95.0 ±4.9 | 96.6 ±4.0 | 67.4 ±9.0 | 73.1 ±7.2 | 65.0 ±8.8 | 41 |
| pool/gemma RRF+rerank | 73.0 ±9.8 | 89.7 ±6.3 | 91.8 ±5.7 | 95.0 ±4.9 | 96.6 ±4.0 | 87.6 ±6.3 | 87.9 ±5.6 | 84.3 ±6.7 | 1092 |
| pool/gemma z(1,1) | 54.0 ±11.5 | 76.2 ±9.9 | 88.6 ±7.3 | 95.0 ±4.9 | 95.0 ±4.9 | 72.6 ±8.7 | 76.9 ±7.2 | 70.1 ±8.8 | 39 |
| pool/gemma z(1,1)+rerank | 69.8 ±10.3 | 87.6 ±6.7 | 91.8 ±6.2 | 91.8 ±6.2 | 95.0 ±4.9 | 85.0 ±6.8 | 85.0 ±6.4 | 81.4 ±7.3 | 1059 |
| pool/gemma z(dense x2) | 54.0 ±11.4 | 73.3 ±10.4 | 80.2 ±9.5 | 92.6 ±5.8 | 95.0 ±4.9 | 71.2 ±9.2 | 75.1 ±7.7 | 68.6 ±9.1 | 39 |
| pool/gemma z(dense x2)+rerank | 72.2 ±10.3 | 88.1 ±6.9 | 91.0 ±6.5 | 92.6 ±5.8 | 95.0 ±4.9 | 85.9 ±6.7 | 86.2 ±6.4 | 82.9 ±7.3 | 1021 |
| pool/gemma z(lexical x2) | 54.2 ±11.9 | 72.8 ±10.6 | 87.0 ±7.9 | 91.8 ±6.3 | 95.0 ±4.9 | 71.1 ±9.2 | 75.4 ±7.8 | 69.2 ±9.1 | 39 |
| pool/gemma z(lexical x2)+rerank | 71.4 ±10.3 | 88.4 ±6.7 | 91.8 ±6.2 | 92.6 ±5.8 | 95.0 ±4.9 | 86.1 ±6.5 | 86.1 ±6.3 | 82.7 ±7.1 | 1132 |

## ssd (52 queries)

| system | recall@1 | recall@3 | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 | map@10 | ms/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pool/bm25 | 37.2 ±13.0 | 58.3 ±13.3 | 67.6 ±12.2 | 76.0 ±10.9 | 89.7 ±8.0 | 52.9 ±11.5 | 57.0 ±10.2 | 49.9 ±11.0 | 2 |
| pool/gemma RRF | 40.1 ±13.1 | 60.3 ±13.0 | 73.1 ±11.2 | 81.1 ±10.3 | 89.7 ±7.7 | 56.0 ±11.3 | 60.3 ±9.9 | 52.5 ±10.6 | 53 |
| pool/gemma RRF+rerank | 54.5 ±13.3 | 79.8 ±10.4 | 86.2 ±8.7 | 89.7 ±7.7 | 89.7 ±7.7 | 69.8 ±10.0 | 74.3 ±8.9 | 68.5 ±9.9 | 1582 |
| pool/gemma z(1,1) | 42.0 ±13.0 | 64.1 ±12.7 | 70.2 ±11.9 | 84.0 ±9.9 | 91.7 ±7.4 | 58.2 ±11.1 | 63.7 ±9.8 | 56.4 ±10.9 | 38 |
| pool/gemma z(1,1)+rerank | 54.5 ±13.1 | 81.7 ±10.3 | 90.1 ±7.5 | 91.7 ±7.4 | 91.7 ±7.4 | 70.6 ±9.8 | 75.2 ±8.2 | 69.0 ±9.6 | 1532 |
| pool/gemma z(dense x2) | 37.5 ±13.5 | 60.3 ±13.1 | 71.5 ±11.7 | 79.5 ±11.2 | 89.7 ±7.7 | 53.3 ±11.3 | 58.9 ±10.4 | 51.4 ±11.0 | 38 |
| pool/gemma z(dense x2)+rerank | 52.6 ±13.5 | 77.9 ±10.4 | 87.2 ±8.7 | 89.7 ±7.7 | 89.7 ±7.7 | 69.3 ±10.0 | 73.6 ±8.8 | 67.4 ±9.8 | 1435 |
| pool/gemma z(lexical x2) | 39.1 ±13.1 | 64.1 ±12.3 | 72.8 ±11.2 | 82.1 ±10.3 | 91.7 ±7.4 | 55.9 ±11.1 | 61.7 ±9.8 | 54.3 ±10.8 | 45 |
| pool/gemma z(lexical x2)+rerank | 58.3 ±12.8 | 75.0 ±11.4 | 90.1 ±7.5 | 91.7 ±7.4 | 91.7 ±7.4 | 72.3 ±9.9 | 76.4 ±8.6 | 70.7 ±9.7 | 1600 |
Byte-identical files indexed once (gold names mapped to the kept copy): `packages/qp-pipeline/src/qp_pipeline/py.typed` = `packages/qp-core/src/qp_core/py.typed`; `packages/qp-voice/src/qp_voice/py.typed` = `packages/qp-core/src/qp_core/py.typed`; `Banking-Companies-Ordinance-1962.pdf` = `statute_banking_ordinance.pdf`.


## Score fusion against RRF (paired bootstrap, A - B, points; bold = interval excludes 0)

| comparison (A − B) | Δ recall@20 | Δ recall@5 | Δ mrr@10 |
|---|---:|---:|---:|
| z(1,1) vs RRF | +0.3 [-1.5, +2.1] p=0.435 | +0.6 [-1.7, +2.9] p=0.299 | **+4.4** [+2.3, +6.7] p=0.000 |
| z(dense x2) vs RRF | -0.3 [-2.1, +1.5] p=0.703 | -0.7 [-3.6, +2.0] p=0.708 | +1.7 [-0.3, +3.8] p=0.051 |
| z(lexical x2) vs RRF | +0.6 [-1.2, +2.4] p=0.321 | -0.6 [-3.3, +1.9] p=0.688 | **+3.0** [+0.5, +5.6] p=0.008 |
| z(1,1)+rerank vs RRF+rerank | +0.3 [-1.5, +2.1] p=0.435 | +0.6 [-1.2, +2.4] p=0.319 | -0.0 [-1.4, +1.3] p=0.522 |
| z(dense x2)+rerank vs RRF+rerank | -0.3 [-2.1, +1.5] p=0.703 | +0.0 [-1.6, +1.6] p=0.535 | -0.3 [-1.7, +0.9] p=0.699 |
| z(lexical x2)+rerank vs RRF+rerank | +0.6 [-1.2, +2.4] p=0.321 | +1.2 [-0.6, +3.0] p=0.128 | +1.4 [-0.2, +3.0] p=0.045 |
- z(1,1)+rerank vs RRF+rerank, questionprep: recall@5 +0.0 [-7.1, +7.1]
- z(1,1)+rerank vs RRF+rerank, pdfs: recall@5 +0.0 [+0.0, +0.0]
- z(1,1)+rerank vs RRF+rerank, banking: recall@5 +0.0 [+0.0, +0.0]
- z(1,1)+rerank vs RRF+rerank, pera: recall@5 +0.0 [+0.0, +0.0]
- z(1,1)+rerank vs RRF+rerank, trm: recall@5 +0.0 [-4.8, +4.8]
- z(1,1)+rerank vs RRF+rerank, ssd: recall@5 +3.8 [+0.0, +9.6]
- z(dense x2)+rerank vs RRF+rerank, questionprep: recall@5 +0.0 [-5.7, +5.7]
- z(dense x2)+rerank vs RRF+rerank, pdfs: recall@5 +0.0 [+0.0, +0.0]
- z(dense x2)+rerank vs RRF+rerank, banking: recall@5 +0.0 [+0.0, +0.0]
- z(dense x2)+rerank vs RRF+rerank, pera: recall@5 +0.0 [+0.0, +0.0]
- z(dense x2)+rerank vs RRF+rerank, trm: recall@5 -0.8 [-4.8, +2.4]
- z(dense x2)+rerank vs RRF+rerank, ssd: recall@5 +1.0 [-4.8, +6.7]
- z(lexical x2)+rerank vs RRF+rerank, questionprep: recall@5 +1.4 [-4.3, +7.1]
- z(lexical x2)+rerank vs RRF+rerank, pdfs: recall@5 +1.2 [+0.0, +3.7]
- z(lexical x2)+rerank vs RRF+rerank, banking: recall@5 +0.0 [+0.0, +0.0]
- z(lexical x2)+rerank vs RRF+rerank, pera: recall@5 +0.0 [+0.0, +0.0]
- z(lexical x2)+rerank vs RRF+rerank, trm: recall@5 +0.0 [-4.8, +4.8]
- z(lexical x2)+rerank vs RRF+rerank, ssd: recall@5 +3.8 [+0.0, +9.6]

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
  gold: `ProtectionEconomicReformsAct-1992.pdf`; found at rank >20; top-3: SUSPENSION OF BUSINESS AND WINDING UP OF BANKING C; ORDINANCE No. LVII OF 1962 > 7 . Form of business ; SUSPENSION OF BUSINESS AND WINDING UP OF BANKING C
- `pera:pera-q030` (pera, natural) **Which amending law changed section 4(2)(f) and added clause (g)?**  
  gold: `ProtectionEconomicReformsAct-1992.pdf`; found at rank >20; top-3: ORDINANCE No. LVII OF 1962 > 3. Limited applicatio; ORDINANCE No. LVII OF 1962 > 7 . Form of business ; ORDINANCE No. LVII OF 1962 > 7 . Form of business 
- `pera:pera-q031` (pera, natural) **Why does a 1992 Act refer to a 2001 Ordinance in section 3?**  
  gold: `ProtectionEconomicReformsAct-1992.pdf`; found at rank 20; top-3: ACT NO. XII OF 1992; ACT NO. XII OF 1992; RP—I/82 > RECORD OF AMENDMENTS
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
