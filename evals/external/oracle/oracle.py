"""Oracle-context diagnostic: answer each MiniCPM4 dev question from ONLY the stored chunks that hold its gold evidence quotes (fuzzy
match, MiniCPM4 paper only, at most 5, in document order). Same model, prompt and gates as production; retrieval is bypassed."""

import json, os, sys, time

os.environ["RAG_DATA_DIR"] = sys.argv[1]
os.environ["RAG_ROUTE_MARGIN"] = "off"
from rag_template.config import Settings
from rag_template.rag import RAG
from rag_template.retrieve import Hit
from rag_template.evals import golden as G
from rag_template.evals.split import select

rag = RAG(Settings.from_env())
rows = [r for r in select(G.load_golden(sys.argv[2]), lambda r: r.question, "dev") if r.status == "yes"]
chunks = [c for c in rag.db.iter_chunks() if c["should_use"] and c["source"] == "2506.07900v2.pdf"]
ans = rag.answerer(None)
out = []
for r in rows:
    held = [c for c in chunks if any(G.holds(q, c["content"], True) for q in r.quotes)][:5]
    if not held:
        out.append({"id": r.id, "skipped": "no stored chunk holds the evidence"})
        continue
    hits = [
        Hit(
            chunk_id=c["chunk_id"],
            doc_id="",
            source=c["source"],
            score=1.0,
            content=c["content"],
            breadcrumb=c["section_header"] or "",
            content_type=c["content_type"],
        )
        for c in held
    ]
    t = time.time()
    a = ans.ask(r.question, hits=hits)
    out.append(
        {
            "id": r.id,
            "question": r.question,
            "ground_truth": r.ground_truth,
            "kind": r.kind,
            "n_chunks": len(hits),
            "answer": a.text,
            "refused": a.refused,
            "reason": a.reason,
            "grounded": a.grounded,
            "seconds": round(time.time() - t, 1),
        }
    )
    print(r.id, len(hits), a.refused, flush=True)
json.dump(out, open(sys.argv[3], "w"), indent=1, ensure_ascii=False)
print("done", sum(1 for o in out if "skipped" in o), "skipped of", len(out))
