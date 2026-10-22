"""Retrieval-only evaluation on the Open RAG Benchmark slice. Document level (any top-k chunk from the gold paper) and a section-level
proxy (a chunk from the gold paper whose words are >= THRESH covered by the gold section's text; the benchmark's section ids refer to
its own parse, not to our chunks)."""
import json, os, re, sys, time
from pathlib import Path
orb, store, out, variant = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]
os.environ["RAG_DATA_DIR"] = str(store)
if variant == "no_routing": os.environ["RAG_ROUTE_MARGIN"] = "off"
from rag_template.config import Settings
from rag_template.rag import RAG
rag = RAG(Settings.from_env())
s = json.load(open(orb / "meta" / "slice.json"))
W = lambda t: re.findall(r"[a-z0-9]+", t.lower())
sections = {}
for d in s["positive"]:
    c = json.load(open(orb / "corpus" / f"{d}.json"))
    sections[d] = [set(W(x.get("text", "") + " " + " ".join((x.get("tables") or {}).values()))) for x in c["sections"]]
kw = {"full": {}, "no_routing": {}, "rrf": {"rerank": False}, "bm25": {"rerank": False, "dense": False}}[variant]
rows = []
t0 = time.time()
SKIP = {"2411.18627v2"}  # not stored: the near-duplicate check matched it to 2410.20267v2 (decided before any run)
for n, (qid, q) in enumerate((k, v) for k, v in s["queries"].items() if v["doc_id"] not in SKIP):
    hits = rag.search(q["query"], k=10, **kw)
    gold, sec = q["doc_id"], q["section_id"]
    doc = [h.source == f"{gold}.pdf" for h in hits]
    cov = []
    for h in hits:
        w = set(W(h.content))
        cov.append(len(w & sections[gold][sec]) / len(w) if h.source == f"{gold}.pdf" and len(w) >= 15 and sec < len(sections[gold]) else 0.0)
    rows.append({"id": qid, "type": q["type"], "source": q["source"], "doc": doc, "cov": cov, "sources": [h.source for h in hits]})
    if n % 50 == 0: print(n, f"{time.time()-t0:.0f}s", flush=True)
json.dump(rows, open(out, "w"))
print("done", len(rows), f"{time.time()-t0:.0f}s")
