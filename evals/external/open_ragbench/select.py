"""Pick the evaluation slice of Open RAG Benchmark by a fixed hash, before any run: 80 positive + 40 hard-negative papers."""

import hashlib, json, sys

meta = sys.argv[1]
q = json.load(open(f"{meta}/queries.json"))
r = json.load(open(f"{meta}/qrels.json"))
urls = json.load(open(f"{meta}/pdf_urls.json"))
pos = sorted({v["doc_id"] for v in r.values()})
neg = sorted(set(urls) - set(pos))
h = lambda d: hashlib.sha256(("orb-slice-v1|" + d).encode()).hexdigest()
P = sorted(pos, key=h)[:80]
N = sorted(neg, key=h)[:40]
Q = {k: {**q[k], **r[k]} for k in q if r[k]["doc_id"] in set(P)}
json.dump({"positive": P, "negative": N, "queries": Q}, open(f"{meta}/slice.json", "w"), indent=1)
print(len(P), len(N), len(Q), "queries")
