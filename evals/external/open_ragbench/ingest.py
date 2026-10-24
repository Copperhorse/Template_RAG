"""Ingest the slice into a fresh store with production defaults (backend auto, formulas as configured) and index it."""

import json, os, sys, time
from pathlib import Path

orb, store = Path(sys.argv[1]), Path(sys.argv[2])
os.environ["RAG_DATA_DIR"] = str(store)
from rag_template.config import Settings
from rag_template.rag import RAG

rag = RAG(Settings.from_env())
s = json.load(open(orb / "meta" / "slice.json"))
t0 = time.time()
for i, d in enumerate(s["positive"] + s["negative"]):
    p = orb / "pdfs" / f"{d}.pdf"
    if not p.exists():
        print("MISSING", d, flush=True)
        continue
    t = time.time()
    res = rag.ingest_path(p, replace=True, source=f"{d}.pdf")
    print(
        f"[{i + 1}/120] {d} {res.status} {res.chunks} chunks {res.usable_chunks} usable {time.time() - t:.0f}s",
        flush=True,
    )
print("indexing", flush=True)
print(rag.index(), "chunks embedded", f"{time.time() - t0:.0f}s total", flush=True)
