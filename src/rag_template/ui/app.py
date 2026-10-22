"""
app.py: Streamlit front end.   rag ui      (or: streamlit run src/rag_template/ui/app.py)

Tabs: Ask (answer + the quotes that back it) · Search (what each retrieval stage did) · Library (ingest,
browse chunks and the quality gate's verdicts) · Evals (results written by `python -m rag_template.evals`) ·
Status. Settings come from the environment / .env exactly as for the CLI.
"""

import os
import tempfile
from pathlib import Path

import json

import pandas as pd
import streamlit as st

from rag_template.convcheck import ConversionReport
from rag_template.rag import RAG
from rag_template.rerankers import default_rerank_mode
from rag_template.retrieve import source_id
from rag_template.ui import logic

st.set_page_config(page_title="RAG template", page_icon="🔎", layout="wide")


@st.cache_resource(show_spinner="Loading models…")
def get_rag() -> RAG:
    return RAG()


def llm_status(rag: RAG) -> tuple:
    try:
        rag.llm.check_health()
        return True, rag.settings.llm.base_url
    except Exception as e:  # noqa: BLE001 - shown to the user
        return False, str(e)[:120]


rag = get_rag()
S = rag.settings

with st.sidebar:
    st.header("Retrieval")
    k = st.slider("Results (k)", 1, 20, 5)
    use_dense = st.toggle("Dense (bi-encoder)", True)
    use_lexical = st.toggle("BM25", True)
    can_rerank = rag.reranker is not None
    use_rerank = st.toggle("Rerank (second-stage reranker)", can_rerank, disabled=not can_rerank, help=None if can_rerank else "No reranker loaded (RAG_RERANK=off, or sentence-transformers missing).")
    _mode = default_rerank_mode(S.rerank_model) if S.rerank_mode == "auto" else S.rerank_mode
    rerank_mode = st.radio("Rerank mode", ["fuse", "replace"], index=0 if _mode == "fuse" else 1, horizontal=True, disabled=not (can_rerank and use_rerank), help="replace: order by the reranker alone. fuse: the reranker is a third voter next to dense and BM25. Default depends on the model (replace for Jina, fuse for others).")
    min_rerank = st.number_input("Min rerank score", value=None, placeholder="off", disabled=not (can_rerank and use_rerank))
    st.divider()
    st.header("Answer gate")
    policy = st.selectbox("Policy", ["balanced", "strict", "tolerant", "lenient"], index=["balanced", "strict", "tolerant", "lenient"].index(S.answer_policy) if S.answer_policy in ("balanced", "strict", "tolerant", "lenient") else 0,
                          help="strict: quotes verbatim, answer supported by the quotes. tolerant: also accepts a quote one word off. balanced: quotes verified, support checked against the cited chunk. lenient: a missing quote is replaced by the chunk's best-matching span (attribution is no longer verified).")
    st.divider()
    st.caption(f"Embedder: `{S.embed_model}`  \nStore: `{S.vector_store}`  \nReranker: `{S.rerank_model if can_rerank else 'off'}`")
    ok, info = llm_status(rag)
    st.caption(("🟢 LLM " if ok else "🔴 LLM unreachable ") + f"`{info}`")
    if st.button("Reload models / settings"):
        get_rag.clear()
        st.rerun()

search_kw = dict(dense=use_dense, lexical=use_lexical, rerank=use_rerank, rerank_mode=rerank_mode, min_rerank_score=min_rerank)
tab_ask, tab_search, tab_lib, tab_evals, tab_status = st.tabs(["Ask", "Search", "Library", "Evals", "Status"])

# ------------------------------------------------------------------------------------------- Ask
with tab_ask:
    q = st.text_input("Question", key="ask_q", placeholder="How does retry decide how long to wait?")
    strict = st.checkbox("Strict: replace a flagged answer with a refusal", False)
    if st.button("Ask", type="primary", disabled=not q) and q:
        if not ok:
            st.error(f"The LLM server is not reachable ({info}). Start it with scripts/serve_llm.sh.")
        else:
            with st.spinner("Retrieving and answering…"):
                ans = rag.ask(q, k=k, strict=strict, policy=policy, **search_kw)
            level, text = logic.verdict(ans)
            st.markdown(f"### {ans.text}")
            getattr(st, level)(text)
            if ans.missing_terms:
                st.caption("Words from your question that appear in none of the sources: " + ", ".join(f"`{t}`" for t in ans.missing_terms))
            if ans.quotes:
                st.subheader("Verified quotes")
                for qs in ans.quotes:
                    with st.container(border=True):
                        badge = {"loose": " · approximate match", "extracted": " · extracted (the model gave no quote)"}.get(qs.how, "")
                        st.markdown(f"**[{source_id(qs.source)}] {qs.hit.located}**{badge}")
                        if qs.hit.content_type == "code":
                            st.code(qs.text, language=qs.hit.metadata.get("language") or None)
                        elif logic.looks_tabular(qs.text):
                            st.code(qs.text, language=None)  # a Markdown blockquote would mangle table syntax
                        else:
                            st.markdown(f"> {qs.text}")
            for n, claimed in ans.unverified_quotes:
                st.error(f"Dropped quote for [{source_id(n)}]: not found in that source.  \n`{claimed[:200]}`")
            st.subheader("Sources")
            for i, h in enumerate(ans.sources, 1):
                with st.expander(f"[{source_id(i)}] {h.located}", expanded=False):
                    quotes = [x.text for x in ans.quotes if x.source == i]
                    if h.content_type == "code":
                        st.code(h.content, language=h.metadata.get("language") or None, line_numbers=True)
                        for t in quotes:
                            rng = logic.quote_lines(h.content, t)
                            st.caption(f"quoted lines {rng[0]}–{rng[1]} of this chunk" if rng else "quote not located")
                    else:
                        st.markdown(logic.highlight_html(h.content, quotes, h.content_type), unsafe_allow_html=True)

# ---------------------------------------------------------------------------------------- Search
with tab_search:
    sq = st.text_input("Query", key="search_q", placeholder="retry backoff")
    show_quotes = st.checkbox("Show the best supporting span of each hit", True)
    if sq:
        hits = rag.search(sq, k=k, quotes=show_quotes, **search_kw)
        if not hits:
            st.info("Nothing retrieved. Has anything been ingested and indexed (Library tab)?")
        else:
            st.dataframe(pd.DataFrame(logic.hit_rows(hits)), hide_index=True, width="stretch")
            for i, h in enumerate(hits, 1):
                with st.expander(f"[{i}] {h.located}"):
                    if h.matched_question:
                        st.caption(f"matched the generated question: {h.matched_question}")
                    if h.quote:
                        st.markdown("**Best span**")
                        st.code(h.quote.text, language=h.metadata.get("language") or None) if (h.content_type == "code" or logic.looks_tabular(h.quote.text)) else st.markdown(f"> {h.quote.text}")
                    st.code(h.content, language=h.metadata.get("language") or None, line_numbers=h.content_type == "code")

# --------------------------------------------------------------------------------------- Library
with tab_lib:
    left, right = st.columns(2)
    with left:
        st.subheader("Add documents")
        path = st.text_input("File or folder path", placeholder="/path/to/repo")
        replace = st.checkbox("Replace a document with the same source", False)
        if st.button("Ingest path", disabled=not path):
            p = Path(path).expanduser()
            if not p.exists():
                st.error("No such path.")
            else:
                results = rag.ingest_directory(p, replace=replace) if p.is_dir() else {str(p): rag.ingest_path(p, replace=replace)}
                st.dataframe(pd.DataFrame([{"file": n, "status": r.status, "usable/total": f"{r.usable_chunks}/{r.chunks}" if r.ok else "", "conversion": (r.conversion or {}).get("verdict", ""), "message": r.message} for n, r in results.items()]), hide_index=True)
        up = st.file_uploader("…or upload files", accept_multiple_files=True)
        if up and st.button("Ingest uploads"):
            with tempfile.TemporaryDirectory() as tmp:
                for f in up:
                    dest = Path(tmp) / f.name
                    dest.write_bytes(f.getvalue())
                    r = rag.ingest_path(dest, source=f.name, replace=replace)
                    st.write(f"`{f.name}`: {r.status}" + (f" ({r.usable_chunks}/{r.chunks} chunks usable)" if r.ok else f" – {r.message}"))
        if st.button("Index new documents"):
            with st.spinner("Embedding…"):
                st.success(f"{rag.index()} new vectors")
    with right:
        st.subheader("Documents")
        docs = rag.db.list_documents()
        if docs:
            st.dataframe(pd.DataFrame([{"source": d["source"], "chunks": d["chunks"], "usable": d["usable_chunks"], "doc_id": d["doc_id"][:8]} for d in docs]), hide_index=True, width="stretch")
        else:
            st.info("The library is empty.")
    if docs:
        st.divider()
        chosen = st.selectbox("Inspect a document", docs, format_func=lambda d: d["source"])
        if chosen.get("conversion_json"):
            rep = ConversionReport.from_dict(json.loads(chosen["conversion_json"]))
            icon = {"ok": "✅", "warn": "⚠️", "bad": "❌", "not-run": "➖"}[rep.verdict]
            with st.expander(f"{icon} How this file was converted: {rep.verdict}", expanded=rep.flagged):
                st.caption("Compared with the PDF's own text (Poppler `pdftotext`). It reports; it does not change what is indexed.")
                if rep.reason:
                    st.write(rep.reason)
                for w in rep.warnings:
                    st.warning(w)
                for kind in ("fused", "spaced_letters", "novel"):
                    for e in rep.examples.get(kind, [])[:3]:
                        st.caption(kind)
                        st.code(str(e), language=None)
                st.json({k: v for k, v in rep.metrics.items() if k in ("word_recall", "run6_recall", "fused_numeric", "dropped_numeric_ratio", "tables", "ragged_tables", "flattened_code_blocks")}, expanded=False)
        only_rejected = st.checkbox("Only chunks the quality gate rejected", False)
        full = rag.db.get_chunks(rag.db.get_chunk_ids_for_document(chosen["doc_id"]))
        table = logic.chunk_rows(sorted(full.values(), key=lambda c: c["chunk_index"]), only_rejected)
        st.dataframe(pd.DataFrame(table).drop(columns=["chunk_id"]) if table else pd.DataFrame(), hide_index=True, width="stretch")
        if table:
            pick = st.selectbox("Show chunk", table, format_func=lambda r: f"#{r['#']} {r['section']}")
            c = full[pick["chunk_id"]]
            st.code(c["content"], language=c["metadata"].get("language") or None)
        if st.button("Delete this document", type="secondary"):
            rag.delete(chosen["doc_id"])
            st.rerun()

# ------------------------------------------------------------------------------------------ Evals
with tab_evals:
    results_dir = Path(os.environ.get("RAG_RESULTS_DIR", "evals/results"))
    files = logic.result_files(results_dir)
    if not files:
        st.info(f"No results in `{results_dir}`. Run `python -m rag_template.evals retrieval` (and `ablations`, `gates`, `answers`).")
    else:
        pick = st.selectbox("Report", files, format_func=lambda p: p.stem)
        js = pick.with_suffix(".json")
        frame = logic.recall_frame(js) if pick.stem == "retrieval" else None
        if frame:
            st.caption("Recall@k (%) per system")
            st.bar_chart(pd.DataFrame(frame).set_index("system"))
        st.markdown(pick.read_text())

# ----------------------------------------------------------------------------------------- Status
with tab_status:
    st.subheader("Index")
    st.json(rag.status())
    c1, c2 = st.columns(2)
    c1.metric("Vectors in the store", rag.store.count())
    rec = rag.reconcile()
    c2.metric("Drift (orphan vectors / unindexed docs)", f"{len(rec['orphan_vectors'])} / {len(rec['unindexed_docs'])}")
    try:
        from rag_template import models

        st.subheader("Models in memory")
        st.table(pd.DataFrame(models.loaded_models()))
        import torch

        if torch.cuda.is_available():
            st.caption(f"GPU {torch.cuda.get_device_name(0)}: {torch.cuda.memory_allocated() // 2**20} MB allocated by this process")
    except ImportError:
        pass
