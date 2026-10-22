# Open RAG Benchmark (arXiv), retrieval only

Slice frozen before any run (`freeze_open_ragbench.txt`): 119 stored papers (80 positive + 39 hard-negative; 1 positive refused as a near-duplicate, its 10 questions dropped), 17,096 chunks, 596 questions. Production defaults, k=10, one run per variant, nothing tuned on it. Dataset: vectara/open_ragbench, CC-BY-NC-4.0.

"Document" = a top-k chunk comes from the gold paper. "Section" = such a chunk whose words are mostly (>=60% / >=80%) found in the gold section's text. The benchmark's section ids refer to its own parse, not our chunks, so the section level is my proxy. Control (random other section of the same paper, BM25 top 5): the proxy accepts the wrong section 27.1% of the time at 60% and 15.2% at 80%, against 91.2% / 87.6% for the gold section. Read the 80% rows, and treat them as slightly optimistic.

| variant | level | R@1 | R@3 | R@5 | R@10 | MRR@10 |
|---|---|---:|---:|---:|---:|---:|
| full (n=596) | document | 99.5 | 99.7 | 99.7 | 99.7 | 99.6  R@5 CI 99.2-100.0
| full (n=596) | section>=60% | 78.4 | 90.9 | 93.8 | 96.1 | 85.1  R@5 CI 91.8-95.5
| full (n=596) | section>=80% | 73.5 | 86.7 | 90.3 | 93.5 | 80.8  R@5 CI 87.8-92.6
| no_routing (n=596) | document | 99.5 | 99.8 | 99.8 | 99.8 | 99.6  R@5 CI 99.5-100.0
| no_routing (n=596) | section>=60% | 78.4 | 91.1 | 94.0 | 96.3 | 85.1  R@5 CI 91.9-95.6
| no_routing (n=596) | section>=80% | 73.5 | 86.7 | 90.3 | 93.5 | 80.8  R@5 CI 87.8-92.6
| rrf (n=596) | document | 97.5 | 99.0 | 99.8 | 100.0 | 98.4  R@5 CI 99.5-100.0
| rrf (n=596) | section>=60% | 68.6 | 85.4 | 91.8 | 95.5 | 78.2  R@5 CI 89.4-93.8
| rrf (n=596) | section>=80% | 62.9 | 81.7 | 87.4 | 92.4 | 73.3  R@5 CI 84.6-89.9
| bm25 (n=596) | document | 97.7 | 98.8 | 99.2 | 99.7 | 98.3  R@5 CI 98.3-99.8
| bm25 (n=596) | section>=60% | 70.5 | 87.1 | 91.3 | 94.8 | 79.4  R@5 CI 88.9-93.5
| bm25 (n=596) | section>=80% | 66.1 | 82.9 | 87.8 | 91.9 | 75.4  R@5 CI 85.1-90.4

full, section>=60%, by source and type
source=text n=385: doc R@5 99.7 | section R@5 93.8 MRR 85.4
source=text-image n=156: doc R@5 99.4 | section R@5 92.3 MRR 82.3
source=text-table n=13: doc R@5 100.0 | section R@5 100.0 MRR 94.9
source=text-table-image n=42: doc R@5 100.0 | section R@5 97.6 MRR 89.8
type=abstractive n=358: doc R@5 99.7 | section R@5 95.3 MRR 83.8
type=extractive n=238: doc R@5 99.6 | section R@5 91.6 MRR 87.0
full share of top-5 chunks from another paper: 1.4%
no_routing share of top-5 chunks from another paper: 5.8%

No published retrieval baseline for this dataset was found (the open-rag-eval repository lists none), so the only comparison is among the four variants above.
