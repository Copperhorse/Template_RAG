"""
retrieve.py: hybrid retrieval with explicit stages, then an answer that must quote its sources.

Retriever.search
  1 dense      bi-encoder: the query is embedded and matched against the chunk vectors (and the
               generated-question vectors, if the optional enrichment stage ran)
  2 lexical    BM25 (SQLite FTS5) over chunk text + breadcrumb: finds the exact identifiers, error
               strings and acronyms that embeddings blur
  3 fusion     reciprocal rank fusion of the two rankings: score = sum 1 / (k + rank). No score
               calibration needed, so cosine and BM25 can be combined directly
  4 rerank     cross-encoder reads (query, chunk) pairs jointly and re-orders the fused candidates; this
               is the precision step, and the only stage that sees query and chunk together
  5 gates      min_dense_score / min_rerank_score drop weak candidates; chunks the evaluator rejected at
               ingest were never indexed in the first place
  6 evidence   optional (`quotes=True`): the best-matching sentence/lines of each hit, extracted
               verbatim, so a result shows *why* it matched

Answerer.ask
  retrieve -> sources labelled S1, S2, ... -> the LLM answers as JSON {answer, quotes[{source, quote}]} -> gates:
    - every [n] the answer cites must exist and be a source the model was shown
    - every cited source needs at least one quote that is found in that chunk (the stored quote is the
      exact chunk text, never the model's paraphrase; unfound quotes are reported and dropped)
    - the answer must be supported by those verified quotes: numbers occur in them, no sentence is
      mostly made of unseen words (prose) / every `identifier` occurs in them (code)
  If nothing relevant is retrieved the LLM is not called.
"""

import logging
import re
from dataclasses import dataclass, field, replace
from typing import Any, Dict, List, Optional, Sequence, Tuple

from rag_template import evidence
from rag_template.enrichment import verify
from rag_template.enrichment.llm import LLMClient
from rag_template.rerankers import CrossEncoderReranker, Reranker  # noqa: F401  (re-exported: they used to live here)
from rag_template.pages import page_label
from rag_template.store.db import Database
from rag_template.store.embedders import Embedder
from rag_template.store.vector import VectorStore
from rag_template.tablecheck import check_table_numbers
from rag_template.tokens import count_tokens

logger = logging.getLogger("rag_template.retrieve")

RRF_K = 60
REFUSAL = "I don't know based on the provided sources."


@dataclass
class Hit:
    chunk_id: str
    doc_id: str
    source: str
    score: float  # final ranking score: the rerank score if a reranker ran, else the fused RRF score
    content: str
    breadcrumb: str = ""
    content_type: str = "prose"
    metadata: Dict[str, Any] = field(default_factory=dict)
    rrf_score: float = 0.0
    rerank_score: Optional[float] = None
    dense_rank: Optional[int] = None  # 1-based position in the bi-encoder ranking
    lexical_rank: Optional[int] = None  # 1-based position in the BM25 ranking
    dense_score: Optional[float] = None  # best cosine similarity among this chunk's vectors
    matched_question: Optional[str] = None  # set when a generated-question vector was the best match
    quote: Optional[evidence.Quote] = None  # best supporting span (search(quotes=True))
    section_of: Optional[str] = None  # set on a chunk added by `section_neighbors`: the chunk id of the retrieved hit it continues

    @property
    def label(self) -> str:
        return self.breadcrumb or self.source

    @property
    def located(self) -> str:
        """The label plus the PDF page(s) when known: "Ablation > Table 3 (p. 7)". For display; the prompt uses `label`."""
        page = page_label(self.metadata or {})
        return f"{self.label} ({page})" if page else self.label

    @property
    def via(self) -> List[str]:
        out = [n for n, r in (("dense", self.dense_rank), ("lexical", self.lexical_rank)) if r]
        if self.rerank_score is not None:
            out.append("rerank")
        if self.matched_question:
            out.append("qa")
        if self.section_of:
            out.append("section")
        return out


def route_to_document(order: List[str], rows: Dict[str, Dict[str, Any]], scores: Dict[str, float], margin: float) -> List[str]:
    """Automatic document routing. A document's score is the best reranker score among its chunks; when the leading document beats the
    runner-up by `margin` or more, only its chunks stay (in their current order), so answers are not built from a neighbouring
    document that merely looks similar. With one document, or a close call, `order` is returned unchanged. Measured: other-document
    chunks in the top 5 fell from 18.7% to 3.9% at margin 0.10 with evidence recall unchanged (evals/results/architecture_review.md)."""
    best: Dict[str, float] = {}
    for cid, score in scores.items():
        doc = rows[cid]["doc_id"]
        best[doc] = max(best.get(doc, score), score)
    if len(best) < 2:
        return order
    ranked = sorted(best.values(), reverse=True)
    if ranked[0] - ranked[1] < margin:
        return order
    leader = max(best, key=best.get)  # type: ignore[arg-type]
    return [c for c in order if rows[c]["doc_id"] == leader]


def zscore_fusion(signals: Sequence[Tuple[Dict[str, float], float]]) -> Dict[str, float]:
    """Per-query score fusion. Each signal is ({chunk_id: score, higher is better}, weight). A signal's scores are standardised over its
    own candidates for this query ((x - mean) / std), so a cosine that sits near 0.6 for every chunk and a BM25 value on another scale
    become comparable, and a strong match counts more than a weak one at the same rank. A chunk the signal did not return gets that
    signal's lowest z. A signal with no spread (one candidate, or all equal) contributes 0."""
    fused: Dict[str, float] = {}
    chunks = {c for scores, _ in signals for c in scores}
    for scores, weight in signals:
        if not scores:
            continue
        vals = list(scores.values())
        mean = sum(vals) / len(vals)
        std = (sum((v - mean) ** 2 for v in vals) / len(vals)) ** 0.5
        z = {c: ((v - mean) / std if std else 0.0) for c, v in scores.items()}
        floor = min(z.values())
        for c in chunks:
            fused[c] = fused.get(c, 0.0) + weight * z.get(c, floor)
    return fused


class Retriever:
    def __init__(
        self, db: Database, store: VectorStore, embedder: Embedder, reranker: Optional[Reranker] = None,
        query_task: Optional[str] = None, rerank_mode: str = "replace", rerank_top: Optional[int] = None, scope: str = "default",
        route_margin: Optional[float] = None,
    ):
        """`query_task` is passed to task-aware embedders ("search result", "code retrieval", ...).
        `rerank_mode` is the default for `search` (see there); RAG passes "fuse" (Settings.rerank_mode).
        `rerank_top` is how many fused candidates the reranker reads (Settings.rerank_top).
        `route_margin`: (RAG passes Settings.route_margin, default 0.10; a Retriever built directly defaults to off) when several documents are indexed, keep only the best-scoring document's chunks if its best reranker score
        leads the next document's by at least this much (None = off); with a close call the mix is kept. Needs the reranker."""
        self.db, self.store, self.embedder, self.reranker, self.query_task, self.rerank_mode = db, store, embedder, reranker, query_task, rerank_mode
        self.rerank_top = rerank_top
        self.route_margin = route_margin
        if hasattr(db, "get_meta"):
            from rag_template.index import verify_embedder

            verify_embedder(db, embedder, scope)  # raises when the store was built by another embedder

    def section_neighbors(self, hits: Sequence[Hit], limit: int = 3, window: int = 2) -> List[Hit]:
        """Chunks that continue a retrieved one: same document, same section (breadcrumb), within `window` positions, usable and not
        already retrieved; following chunks before preceding ones, best hit first, at most `limit` in all. A list or an explanation that
        runs past a chunk boundary (a page break, a table in between) keeps its tail in such a neighbour, which a question-to-chunk
        match does not see. Returned after the retrieved hits, so their source ids do not move."""
        have = {h.chunk_id for h in hits}
        extra: List[Hit] = []
        for h in hits:
            if len(extra) >= limit:
                break
            ids = self.db.get_chunk_ids_for_document(h.doc_id, usable_only=True)
            if h.chunk_id not in ids:
                continue
            i = ids.index(h.chunk_id)
            near = [ids[j] for j in [*range(i + 1, i + window + 1), *range(i - 1, i - window - 1, -1)] if 0 <= j < len(ids)]
            rows = self.db.get_chunks(near)
            for cid in near:
                r = rows.get(cid)
                if r is None or cid in have or (r.get("breadcrumb") or "") != h.breadcrumb or len(extra) >= limit:
                    continue
                have.add(cid)
                extra.append(Hit(chunk_id=cid, doc_id=r["doc_id"], source=r.get("source", ""), score=0.0, content=r["content"],
                                 breadcrumb=r.get("breadcrumb") or "", content_type=r["content_type"], metadata=r["metadata"], section_of=h.chunk_id))
        return extra

    def span_scorer(self) -> evidence.Scorer:
        """What ranks sentences/lines inside a chunk: the cross-encoder if there is one, else bi-encoder similarity."""
        return self.reranker.rerank if self.reranker is not None else evidence.embedding_scorer(self.embedder)

    def search(
        self,
        query: str,
        k: int = 5,
        doc_id: Optional[str] = None,
        candidates: Optional[int] = None,
        dense: bool = True,
        lexical: bool = True,
        rerank: bool = True,
        query_task: Optional[str] = None,
        rerank_top: Optional[int] = None,
        rerank_mode: Optional[str] = None,
        rrf_k: int = RRF_K,
        weights: Tuple[float, float] = (1.0, 1.0),
        fusion: str = "rrf",
        min_dense_score: Optional[float] = None,
        min_rerank_score: Optional[float] = None,
        quotes: bool = False,
    ) -> List[Hit]:
        """`weights` scales (dense, lexical) in the fusion. `rerank_top` is how many fused candidates
        the cross-encoder reads (default max(3k, 20)); chunks beyond it keep their fused order below
        the reranked ones. `rerank_mode`: "replace" orders the candidates by the cross-encoder alone;
        "fuse" treats the cross-encoder as a third voter in the rank fusion, so a reranker that is weak
        on your domain cannot overrule both first-stage rankers. `fusion`: "rrf" (default) adds weight/(k+rank) over the two rankings;
        "zscore" standardises each signal's scores within this query (cosine, and the negated BM25 value) and adds them with `weights`,
        so a strong match counts more than a weak one at the same rank (`zscore_fusion`). Measured on source code with a web-passage
        cross-encoder, "replace" lost 14 points of recall@5 and "fuse" lost none (evals/results/ablations.md)."""
        n = candidates or max(k * 4, 20)
        rerank_mode = rerank_mode or self.rerank_mode

        # 1. dense
        dense_rank: Dict[str, int] = {}
        dense_score: Dict[str, float] = {}
        matched_q: Dict[str, str] = {}
        if dense:
            where = {"doc_id": doc_id} if doc_id else None
            for vh in self.store.query(self.embedder.embed_query(query, query_task or self.query_task), n_results=n, where=where):
                cid = vh.metadata.get("chunk_id")
                if not cid or cid in dense_rank:
                    continue  # hits come best-first, so the first vector of a chunk is its best
                dense_rank[cid] = len(dense_rank) + 1
                dense_score[cid] = vh.score
                if vh.metadata.get("kind") == "qa":
                    matched_q[cid] = vh.document.split("\nAnswer:", 1)[0].removeprefix("Question: ").strip()

        # 2. lexical (BM25)
        lexical_rank: Dict[str, int] = {}
        lexical_value: Dict[str, float] = {}
        if lexical:
            for pos, r in enumerate(self.db.search_lexical(query, limit=n, doc_id=doc_id), 1):
                lexical_rank[r["chunk_id"]] = pos
                lexical_value[r["chunk_id"]] = -float(r["rank"])  # SQLite's bm25() is lower-is-better (negative)

        # 3. reciprocal rank fusion
        fused: Dict[str, float] = {}
        if fusion == "zscore":
            fused = zscore_fusion([(dense_score, weights[0]), (lexical_value, weights[1])])
        elif fusion == "rrf":
            for ranking, weight in ((dense_rank, weights[0]), (lexical_rank, weights[1])):
                for cid, pos in ranking.items():
                    fused[cid] = fused.get(cid, 0.0) + weight / (rrf_k + pos)
        else:
            raise ValueError(f"unknown fusion '{fusion}'; choose rrf or zscore")
        order = sorted(fused, key=fused.get, reverse=True)  # type: ignore[arg-type]
        rows = self.db.get_chunks(order)
        order = [c for c in order if c in rows and rows[c]["should_use"]]

        # 4. cross-encoder rerank
        rerank_scores: Dict[str, float] = {}
        final: Dict[str, float] = dict(fused)
        if rerank and self.reranker is not None and order:
            head = order[: rerank_top or self.rerank_top or max(k * 3, 20)]
            rerank_scores = dict(zip(head, self.reranker.rerank(query, [rows[c]["content"] for c in head])))
            by_rerank = sorted(head, key=lambda c: rerank_scores[c], reverse=True)
            if rerank_mode == "fuse":
                first_stage = {c: i + 1 for i, c in enumerate(head)}
                second_stage = {c: i + 1 for i, c in enumerate(by_rerank)}
                final.update({c: 1.0 / (rrf_k + first_stage[c]) + 1.0 / (rrf_k + second_stage[c]) for c in head})
                order = sorted(head, key=lambda c: final[c], reverse=True) + order[len(head):]
            elif rerank_mode == "replace":
                final.update(rerank_scores)
                order = by_rerank + order[len(head):]
            else:
                raise ValueError(f"unknown rerank_mode '{rerank_mode}'; choose replace or fuse")

        if self.route_margin is not None and rerank_scores:
            order = route_to_document(order, rows, rerank_scores, self.route_margin)

        # 5. gates
        if min_dense_score is not None:  # a chunk BM25 also found is kept; a weak dense match alone is not
            order = [c for c in order if c in lexical_rank or dense_score.get(c, 0.0) >= min_dense_score]
        if min_rerank_score is not None and rerank_scores:
            order = [c for c in order if c in rerank_scores and rerank_scores[c] >= min_rerank_score]  # the unscored tail ranks below scored chunks and cannot be judged

        hits = []
        for cid in order[:k]:
            r = rows[cid]
            hits.append(
                Hit(
                    chunk_id=cid, doc_id=r["doc_id"], source=r.get("source", ""),
                    score=final[cid], content=r["content"],
                    breadcrumb=r.get("breadcrumb") or "", content_type=r["content_type"], metadata=r["metadata"],
                    rrf_score=fused[cid], rerank_score=rerank_scores.get(cid),
                    dense_rank=dense_rank.get(cid), lexical_rank=lexical_rank.get(cid),
                    dense_score=dense_score.get(cid), matched_question=matched_q.get(cid),
                )
            )

        # 6. evidence
        if quotes and hits:
            scorer = self.span_scorer()
            for h in hits:
                h.quote = evidence.extract_quote(query, h.content, h.content_type, scorer)
        return hits


# ----------------------------------------------------------------------------------- answers


@dataclass
class QuotedSource:
    source: int  # 1-based number the model saw
    hit: Hit
    text: str  # exact chunk text, never the model's wording
    how: str = "exact"  # exact | fuzzy | loose (the model's quote was approximate) | extracted (the model gave none)


@dataclass
class Answer:
    text: str
    sources: List[Hit]
    grounded: bool = True
    reason: str = ""  # why the grounding gate failed, or "" when it passed
    refused: bool = False
    citations: List[int] = field(default_factory=list)
    quotes: List[QuotedSource] = field(default_factory=list)  # verified, verbatim
    unverified_quotes: List[Tuple[int, str]] = field(default_factory=list)  # claimed but not found in their chunk (source 0: no usable number)
    missing_terms: List[str] = field(default_factory=list)  # question words found in none of the sources (a hint, not a verdict)


@dataclass(frozen=True)
class AnswerPolicy:
    """How strict the answer gate is. Every setting trades false alarms against missed errors; the trade-off is
    measured in evals/results/answer_policies.md, and the adversarial test (evals/results/gates.md) shows what each
    still catches.

    support_against   "quotes": the answer must be supported by the verified quotes alone. "sources": by the whole
                      cited chunks (a small model that quotes badly cannot cause a false alarm).
    loose_quotes      accept a quote that is almost, not exactly, in the cited chunk (one word off) and store the
                      chunk's real text for it. Needs score >= 75 and 80% of the quote's words (verify.py).
    extract_missing   when a cited source has no verified quote (the model forgot, or it was invented), take the
                      span of that source that best matches the answer instead, labelled how="extracted". The
                      citation is then checked for support but the model's attribution is not verified.
    check_table_cells every number the answer states that sits in a table of a cited chunk must come from a cell whose row and
                      column fit the answer (tablecheck.py). Off for "lenient" so that loosening a policy only accepts more.
    """

    support_against: str = "quotes"
    loose_quotes: bool = False
    extract_missing: bool = False
    check_table_cells: bool = True


POLICIES = {
    "strict": AnswerPolicy("quotes", False, False),  # quotes verbatim, answer supported by the quotes alone
    "tolerant": AnswerPolicy("quotes", True, False),  # + accepts a quote that is one word off
    "balanced": AnswerPolicy("sources", True, False),  # quotes still required and verified; support checked against the cited chunk
    "lenient": AnswerPolicy("sources", True, True, check_table_cells=False),  # + a missing/invalid quote is replaced by the chunk's best-matching span
}


# Sources are labelled S1, S2, ... in the prompt and cited as [S1] or [S1, S3]. A bare number is deliberately NOT an id: documents are full of
# numbers (section 22, "[3]" bibliography references, years) and a model that writes one where a source id belongs must not be taken for citing.
_CITATION = re.compile(r"\[(S\d+(?:\s*,\s*S\d+)*)\]")


def source_id(n: int) -> str:
    """The label of source number n: 3 -> "S3"."""
    return f"S{n}"


def _cite_numbers(group: str) -> List[int]:
    """The source numbers inside one citation: "S1, S3" -> [1, 3]."""
    return [int(n) for n in re.findall(r"\d+", group)]


def _ids(numbers: Sequence[int]) -> str:
    """For messages: [22, 3] -> "[S22, S3]"."""
    return "[" + ", ".join(source_id(n) for n in numbers) + "]"

def answer_schema(quotes_first: bool = False, n_sources: Optional[int] = None) -> dict:
    """JSON schema of the reply. In "quotes_first" order the model must write its evidence before its answer. With `n_sources` the
    `source` of a quote can only be one of the ids shown (S1..Sn), so a server that enforces the schema cannot produce a source that does not exist."""
    source = {"type": "string", "enum": [source_id(i) for i in range(1, n_sources + 1)]} if n_sources else {"type": "string", "pattern": "^S[0-9]+$"}
    quote = {"type": "object", "properties": {"source": source, "quote": {"type": "string"}}, "required": ["source", "quote"], "additionalProperties": False}
    props = {"answer": {"type": "string"}, "quotes": {"type": "array", "items": quote}}
    order = ["quotes", "answer"] if quotes_first else ["answer", "quotes"]
    return {"type": "object", "properties": {k: props[k] for k in order}, "required": order, "additionalProperties": False}


def system_prompt(quotes_first: bool = False) -> str:
    shape = (
        '{"quotes": [{"source": "<id such as S1>", "quote": "<text copied word for word from that source>"}], '
        '"answer": "<your answer, citing sources inline as [S1], [S2]>"}'
        if quotes_first
        else '{"answer": "<your answer, citing sources inline as [S1], [S2]>", '
        '"quotes": [{"source": "<id such as S1>", "quote": "<text copied word for word from that source>"}]}'
    )
    return (
        "You answer questions using ONLY the SOURCES provided, each labelled with an id (S1, S2, ...). "
        "Cite a source by its id only; section, clause and reference numbers inside a source are not ids. "
        f"Reply with JSON only: {shape}. "
        "Every source you cite must have at least one quote that supports your answer. "
        "Use the sources' own terms, names and numbers; add no outside knowledge. "
        f'If the sources do not contain the answer, reply {{"answer": "{REFUSAL}", "quotes": []}}.'
    )


SYSTEM_PROMPT = system_prompt()  # answer-first (the default)

# A model told to refuse usually does so in its own words ("The provided sources do not contain ..."). That is the
# correct behaviour and must not be reported as an answer that "cites no source".
_REFUSAL_WORDING = re.compile(
    r"^\W*(?:i\s+(?:do\s*n['o]t|don['’]t|cannot|can['’]t)\s+(?:know|find|answer)"
    r"|(?:the\s+)?(?:provided\s+|given\s+)?(?:sources?|documents?|context|passages?|text)\s+(?:do(?:es)?\s+not|don['’]t|doesn['’]t|(?:is|are)\s+not|contains?\s+no)\b"
    r"|there\s+is\s+no\s+(?:information|mention|answer)"
    r"|no\s+(?:information|answer|mention)\s+(?:is|was|can\s+be)?\s*(?:found|provided|available)"
    r"|(?:not\s+enough|insufficient)\s+information)",
    re.IGNORECASE,
)


def is_refusal(text: str) -> bool:
    """True for the exact sentinel and for the ways a model words "the sources do not say". Only the opening of
    the reply is inspected, and only when the reply cites no source (a cited answer is an answer)."""
    t = text.strip()
    return t.rstrip(".").strip().lower() == REFUSAL.rstrip(".").lower() or (not _CITATION.search(t) and bool(_REFUSAL_WORDING.match(t)))


class Answerer:
    def __init__(
        self,
        retriever: Retriever,
        llm: LLMClient,
        max_context_tokens: int = 3000,
        answer_tokens: int = 800,
        verify_config: verify.VerifyConfig = verify.VerifyConfig(),
        policy: AnswerPolicy | str = "strict",
        support_against: Optional[str] = None,
        quotes_first: bool = False,
        min_relevance: Optional[float] = None,
        expand_section: int = 0,
    ):
        """`expand_section`: add up to this many chunks that continue a retrieved one in the same section (`Retriever.section_neighbors`)
        after the retrieved sources; 0 (default) is off.
        `quotes_first`: ask for the evidence before the answer (and, in LLM_JSON_MODE=schema, enforce that order).
        `min_relevance`: refuse, without calling the LLM, when the best reranker score among the retrieved sources is below
        this. The number is specific to the reranker (jina-reranker-v3.5 scores are cosines: see evals/results/answerability.md
        for operating points); None switches the gate off."""
        self.min_relevance = min_relevance
        self.expand_section = expand_section
        self.retriever, self.llm = retriever, llm
        self.quotes_first = quotes_first
        self.system = system_prompt(quotes_first)
        self.max_context_tokens, self.answer_tokens, self.cfg = max_context_tokens, answer_tokens, verify_config
        self.policy = POLICIES[policy] if isinstance(policy, str) else policy
        if support_against is not None:  # kept for callers that predate AnswerPolicy
            self.policy = replace(self.policy, support_against=support_against)

    def build_prompt(self, question: str, hits: Sequence[Hit]) -> Tuple[str, int]:
        """(prompt, number of sources that fit the context budget)."""
        blocks, used = [], 0
        for i, h in enumerate(hits, 1):
            body = h.content if h.content_type != "code" else f"```{h.metadata.get('language', '')}\n{h.content}\n```"
            block = f"[{source_id(i)}] {h.label}\n{body}"
            used += count_tokens(block)
            if blocks and used > self.max_context_tokens:
                break
            blocks.append(block)
        return "SOURCES:\n\n" + "\n\n".join(blocks) + f"\n\nQUESTION: {question}\n\nJSON:", len(blocks)

    def ask(self, question: str, k: int = 5, doc_id: Optional[str] = None, strict: bool = False, hits: Optional[Sequence[Hit]] = None, **search_kwargs) -> Answer:
        """`hits`: already retrieved sources for this question (skips the search; a caller that needs the hits too searches once)."""
        hits = list(hits) if hits is not None else self.retriever.search(question, k=k, doc_id=doc_id, **search_kwargs)
        if not hits:
            return Answer(REFUSAL, [], reason="nothing relevant was retrieved", refused=True)
        weak = self.relevance_refusal(hits)
        if weak is not None:
            return weak
        if self.expand_section and hasattr(self.retriever, "section_neighbors"):
            hits = hits + self.retriever.section_neighbors(hits, limit=self.expand_section)
        prompt, shown = self.build_prompt(question, hits)
        hits = hits[:shown]
        parsed = self.llm.chat_json(self.system, prompt, self.answer_tokens, schema=answer_schema(self.quotes_first, shown))
        return self.judge(parsed, hits, question, strict=strict)

    def relevance_refusal(self, hits: Sequence[Hit]) -> Optional[Answer]:
        """The refusal to return (no LLM call) when the best reranker score is below `min_relevance`, else None. Inactive when the
        gate is off or the hits carry no reranker scores (reranking disabled): the threshold would mean nothing then."""
        if self.min_relevance is None:
            return None
        scores = [h.rerank_score for h in hits if h.rerank_score is not None]
        if not scores:
            logger.warning("min_relevance is set but the retrieved hits have no reranker scores (is reranking off?): the relevance gate is inactive")
            return None
        best = max(scores)
        if best >= self.min_relevance:
            return None
        return Answer(REFUSAL, list(hits), reason=f"no retrieved source looks relevant (best reranker score {best:.3f} < {self.min_relevance:g})", refused=True)

    def judge(self, parsed: dict, hits: Sequence[Hit], question: str, strict: bool = False, policy: Optional[AnswerPolicy] = None) -> Answer:
        """Gate a model reply. Pure (no LLM call), so a recorded reply can be re-judged under another policy."""
        policy = policy or self.policy
        hits = list(hits)
        text = str(parsed.get("answer") or "").strip()
        if not text:
            return Answer(REFUSAL, hits, False, "the model returned no parsable answer", True)
        if is_refusal(text):
            return Answer(REFUSAL if text.rstrip(".").strip().lower() == REFUSAL.rstrip(".").lower() else text, hits, refused=True)

        raw_quotes = parsed.get("quotes") if isinstance(parsed.get("quotes"), list) else []
        claimed = [  # source 0 = the model gave no usable source id: located by its text below, else reported as dropped
            (evidence.parse_source(q.get("source")) or 0, str(q.get("quote", ""))) if isinstance(q, dict) else (0, q)
            for q in raw_quotes if isinstance(q, (dict, str))
        ]
        claimed, remap = self._reattribute(claimed, hits, policy.loose_quotes)
        if remap:
            text = _CITATION.sub(lambda m: _ids([remap.get(n, n) for n in _cite_numbers(m.group(1))]), text)
        cited = sorted({n for group in _CITATION.findall(text) for n in _cite_numbers(group)})
        ok, bad = evidence.verify_quotes(claimed, [(h.content, h.content_type) for h in hits], loose=policy.loose_quotes)
        quotes = [QuotedSource(n, hits[n - 1], t, how) for n, t, how in ok]
        if policy.extract_missing:
            quotes += self._extract_missing(text, hits, cited, quotes)
        ans = Answer(text, hits, citations=cited, quotes=quotes, unverified_quotes=bad,
                     missing_terms=verify.missing_question_terms(question, [f"{h.label}\n{h.content}" for h in hits]))

        reason = self._gate(text, question, hits, cited, quotes, policy)
        if reason:
            ans.grounded, ans.reason = False, reason
            if strict:
                return Answer(REFUSAL, hits, False, reason, True, cited, quotes, bad, ans.missing_terms)
        return ans

    @staticmethod
    def _reattribute(claimed: List[Tuple[int, str]], hits: Sequence[Hit], loose: bool) -> Tuple[List[Tuple[int, str]], Dict[int, int]]:
        """The id a model writes is a hint; the quote's text is the evidence. A quote with no usable id (missing, unparseable, or an id
        that names no source) is attributed to the retrieved chunk that holds it verbatim when exactly one does. Returns the corrected
        claims and {nonexistent id: the id it was resolved to}, used to rewrite the matching citations in the answer. An id that names
        a real source is NEVER corrected: a real quote filed under the wrong source is the fabrication the gate must still catch."""
        fixed: List[Tuple[int, str]] = []
        targets: Dict[int, set] = {}
        for n, quote in claimed:
            if 1 <= n <= len(hits) or not quote.strip():  # a real id (right or wrong), or nothing to locate
                where: List[int] = []
            else:
                where = [i + 1 for i, h in enumerate(hits) if evidence.verify_quotes([(1, quote)], [(h.content, h.content_type)], loose=loose)[0]]
            if len(where) == 1:
                if n:
                    targets.setdefault(n, set()).add(where[0])
                fixed.append((where[0], quote))
            else:
                fixed.append((n, quote))
        return fixed, {n: next(iter(t)) for n, t in targets.items() if len(t) == 1}

    def _extract_missing(self, text: str, hits: Sequence[Hit], cited: List[int], quotes: List[QuotedSource]) -> List[QuotedSource]:
        """For each cited source without a verified quote: its span that best matches the answer (verbatim by construction)."""
        scorer = self.retriever.span_scorer() if hasattr(self.retriever, "span_scorer") else None
        if scorer is None:
            return []
        body = _CITATION.sub("", text).strip()
        out = []
        for n in cited:
            if not 1 <= n <= len(hits) or any(q.source == n for q in quotes):
                continue
            span = evidence.extract_quote(body, hits[n - 1].content, hits[n - 1].content_type, scorer)
            if span:
                out.append(QuotedSource(n, hits[n - 1], span.text, "extracted"))
        return out

    def _gate(self, text: str, question: str, hits: Sequence[Hit], cited: List[int], quotes: List[QuotedSource], policy: AnswerPolicy) -> str:
        if not cited:
            return "the answer cites no source"
        bad = [n for n in cited if not 1 <= n <= len(hits)]
        if bad:
            return f"cites sources that do not exist: {_ids(bad)}"
        unquoted = [n for n in cited if not any(q.source == n for q in quotes)]
        if unquoted:
            return f"no verified quote from cited source(s) {_ids(unquoted)}"

        body = _CITATION.sub("", text)
        used = [q for q in quotes if q.source in cited]
        evidence_text = "\n\n".join(q.text for q in used)
        if policy.support_against == "sources":
            evidence_text = "\n\n".join(hits[n - 1].content for n in cited)
        if any(q.hit.content_type == "code" for q in used):
            labels = "\n".join(q.hit.label for q in used)  # breadcrumbs: "pkg/db.py > DBManager.get_pending_files"
            ok, why = verify.check_code_support(body, evidence_text, context=labels)
        else:
            cfg = verify.VerifyConfig(**{**self.cfg.__dict__, "support_scope": "chunk"})
            labels = "\n".join(q.hit.breadcrumb for q in used if q.hit.breadcrumb)  # the heading the model was shown ("ACT NO. XII OF 1992") is evidence too
            ok, why = verify.check_support(body, f"{evidence_text}\n{labels}" if labels else evidence_text, evidence_text, question, cfg, trusted_question=True)
        if ok and policy.check_table_cells:
            tables = [hits[n - 1].content for n in cited if hits[n - 1].content_type == "table"]
            ok, why = check_table_numbers(body, tables, question)
        return "" if ok else why
