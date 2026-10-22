"""Validity check for the section proxy (added after the frozen runs, disclosed): score the BM25 top 10 against the gold section and against a
random OTHER section of the same paper. If the other-section rate is high, the proxy cannot tell sections apart."""
import json, os, random, re, sys
from pathlib import Path
orb, store = Path(sys.argv[1]), Path(sys.argv[2]); os.environ["RAG_DATA_DIR"] = str(store)
from rag_template.config import Settings
from rag_template.rag import RAG
rag = RAG(Settings.from_env()); s = json.load(open(orb / "meta" / "slice.json"))
W = lambda t: re.findall(r"[a-z0-9]+", t.lower()); rnd = random.Random(0)
secs = {d: [set(W(x.get("text", "") + " " + " ".join((x.get("tables") or {}).values()))) for x in json.load(open(orb / "corpus" / f"{d}.json"))["sections"]] for d in s["positive"]}
res = {t: [0, 0] for t in (0.6, 0.8)}; n = 0
for q in s["queries"].values():
    g = q["doc_id"]
    if g == "2411.18627v2" or q["section_id"] >= len(secs[g]) or len(secs[g]) < 2: continue
    other = rnd.choice([i for i in range(len(secs[g])) if i != q["section_id"]]); n += 1
    hits = [h for h in rag.search(q["query"], k=5, rerank=False, dense=False) if h.source == f"{g}.pdf"]
    for t in res:
        for j, sec in enumerate((q["section_id"], other)):
            res[t][j] += any(len(set(W(h.content))) >= 15 and len(set(W(h.content)) & secs[g][sec]) / len(set(W(h.content))) >= t for h in hits)
for t, (a, b) in res.items(): print(f"thr {t}: gold section {100*a/n:.1f}%  random other section {100*b/n:.1f}%  (n={n})")
