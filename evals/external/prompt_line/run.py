"""Experiment C (decided before the run): production pipeline on the MiniCPM4 dev answerable questions with one extra sentence appended to the
system prompt. Nothing else changes. Usage: run.py STORE GOLDEN OUT_STEM"""
import json, os, sys
os.environ["RAG_DATA_DIR"] = sys.argv[1]; os.environ["RAG_ROUTE_MARGIN"] = "off"
from rag_template.config import Settings
from rag_template.rag import RAG
from rag_template.evals import golden as G
from rag_template.evals.split import select
LINE = (" If the sources give different values for the same thing, state each value with its source id and say that they differ."
        " List every item or number the question asks for; do not stop after the first.")
rag = RAG(Settings.from_env())
make = rag.answerer
def patched(policy=None):
    a = make(policy); a.system = a.system + LINE; return a
rag.answerer = patched
rows = [r for r in select(G.load_golden(sys.argv[2]), lambda r: r.question, "dev")]
audit = G.audit_evidence(rag.db.iter_chunks(), rows, fuzzy=True)
rec = G.run(rag, rows, audit, k=5, fuzzy=True)
json.dump({"line": LINE, "records": rec}, open(sys.argv[3] + ".json", "w"), indent=1, ensure_ascii=False)
