"""
enricher.py: turn stored chunks into verified metadata and question/answer pairs.

For every usable chunk, in document order:

  1. metadata   summary + tags + triplets; tags and triplets must literally occur in the chunk
  2. Pass 1     the LLM proposes questions, each with a verbatim `source_quote`
  3. gates      a candidate pair must survive, in order:
                  invalid        a question and a quote of >= 25 characters
                  provenance     the quote is located in the chunk (and replaced by the exact chunk
                                 text); for maths it must be verbatim
                  Pass 2         a reference answer is written from the quote alone
                  refusal        NOT_ENOUGH_INFORMATION
                  deflection     "the text does not specify ..."
                  checker        by content type: prose/table -> PairVerifier (support, addresses the
                                 question, embedding similarity); code -> CodeVerifier (identifiers and
                                 numbers must exist in the code); maths -> AnswerValidator (lexical,
                                 bi-encoder, NLI)
                  judge          optional second opinion (judge.py)
  4. persist    survivors go to `chunk_qa`; every rejection goes to `chunk_rejections` with its reason

Failure model: an unreachable or overloaded LLM (`LLMUnavailable`) says nothing about the chunk, so
nothing is recorded for it; the run stops, the document stays pending and the next run resumes.
"""

import logging
import re
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Deque, Dict, List, Optional, Protocol, Set, Tuple

from rag_template.enrichment import verify
from rag_template.enrichment.judge import JudgeUnavailable
from rag_template.enrichment.llm import MIN_TOKENS_FOR_METADATA, LLMClient, LLMUnavailable
from rag_template.store.db import Database

logger = logging.getLogger("rag_template.enricher")

DIFFICULTY_TYPE = {"Easy": "Fact", "Medium": "Mechanism", "Hard": "Critical"}

DEFLECTION_PATTERN = re.compile(
    r"the\s+text\s+does\s+not\s+"
    r"(specify|mention|state|provide|include|address|discuss|indicate|describe)"
    r"|the\s+(passage|chunk|document|context|code|snippet)\s+does\s+not"
    r"|no\s+(specific|numeric|direct)\s+(threshold|value|detail|information|mention)"
    r"|is\s+not\s+(mentioned|specified|discussed|provided|stated|shown)\s+in\s+the\s+(text|code|passage)"
    r"|cannot\s+be\s+(determined|inferred|found)\s+from",
    re.IGNORECASE,
)


@dataclass
class EnrichConfig:
    min_tokens_for_metadata: int = MIN_TOKENS_FOR_METADATA
    min_tokens_for_qa: int = 30
    min_summary_words: int = 10  # a shorter summary is not added to the running context
    quote_min_chars: int = 25
    history: int = 3  # previous summaries given to the model as orientation (prose)
    neighbour_chars: int = 150  # PREV/NEXT excerpt for structured chunks
    batch_documents: int = 5
    max_workers: int = 1  # one local GPU server answers one request at a time anyway


class Checker(Protocol):
    def validate(self, question: str, answer: str, chunk: str, source_quote: str) -> Tuple[bool, str]: ...


class Gates:
    """Routes a chunk's content type to its quote locator and answer checker. Models are only loaded
    for content types that actually occur."""

    def __init__(self, prose: Optional[Checker] = None, code: Optional[Checker] = None, math: Optional[Checker] = None):
        self._checkers: Dict[str, Optional[Checker]] = {"prose": prose, "code": code, "math": math}

    @classmethod
    def uniform(cls, checker: Checker) -> "Gates":
        """One checker for every type (tests; or a custom domain checker)."""
        return cls(prose=checker, code=checker, math=checker)

    def checker(self, content_type: str) -> Checker:
        key = content_type if content_type in ("code", "math") else "prose"
        if self._checkers[key] is None:
            if key == "code":
                self._checkers[key] = verify.CodeVerifier()
            elif key == "math":
                from rag_template.enrichment.validator import AnswerValidator

                self._checkers[key] = AnswerValidator()
            else:
                self._checkers[key] = verify.PairVerifier()
        return self._checkers[key]  # type: ignore[return-value]

    @staticmethod
    def locate_quote(content_type: str, quote: str, content: str) -> Optional[str]:
        """The verbatim chunk text the model's quote refers to, or None."""
        if content_type == "math":  # formulas are copied exactly or not at all
            return quote.strip() if quote.strip() in content else None
        if content_type == "code":
            return verify.locate_code_quote(quote, content)
        return verify.locate_quote(quote, content)


@dataclass
class EnrichReport:
    documents: int = 0
    server_down: bool = False


def _reject(level: str, question: str, answer: str, reason: str) -> Dict[str, str]:
    return {"level": level, "question": question, "answer": answer, "reason": reason}


class EnrichmentManager:
    def __init__(
        self,
        db: Database,
        llm: LLMClient,
        gates: Optional[Gates] = None,
        judge: Any = None,
        config: Optional[EnrichConfig] = None,
    ):
        """`judge` is anything with `.check_many([(question, answer, chunk), ...]) -> [(ok, reason)]`
        (see judge.py); None disables it."""
        self.db = db
        self.llm = llm
        self.gates = gates or Gates()
        self.judge = judge
        self.config = config or EnrichConfig()
        if judge is not None:
            logger.warning(
                "Judge '%s' is enabled: the text of each chunk, question and answer is sent to that model.",
                getattr(judge, "name", type(judge).__name__),
            )

    # ------------------------------------------------------------------ one chunk

    def process_chunk(self, chunk: Dict[str, Any], context: str) -> Tuple[bool, str]:
        """Enrich one chunk. Raises LLMUnavailable if the server fails; nothing is left behind for
        the chunk then (no rejection rows, no enrichment row), so it stays pending."""
        self.llm.reset_stats()
        try:
            return self._process_chunk(chunk, context)
        except LLMUnavailable:
            self.db.delete_enrichment(chunk["chunk_id"])  # an enrichment row would mean "attempted"
            raise
        finally:
            st = self.llm.stats
            if st["calls"]:
                logger.info(
                    f"Chunk {chunk['chunk_id'][:8]}: {st['calls']} LLM call(s), {st['seconds']:.1f}s, "
                    f"tokens in/out {st['prompt_tokens']}/{st['completion_tokens']}"
                )

    def _process_chunk(self, chunk: Dict[str, Any], context: str) -> Tuple[bool, str]:
        cfg = self.config
        chunk_id, content = chunk["chunk_id"], chunk["content"]
        tokens = chunk.get("estimated_tokens", 0)
        ctype = chunk.get("content_type", "prose")
        logger.info(f"Chunk {chunk_id[:8]} | {tokens} tokens | type={ctype} | {chunk.get('section_header', '')[:60]}")

        meta = self.llm.generate_metadata(content, context, estimated_tokens=tokens, content_type=ctype)
        if not meta:
            reason = "Too short for metadata" if tokens < cfg.min_tokens_for_metadata else "Metadata generation failed"
            self.db.save_rejections(chunk_id, [{"reason": reason}])
            return tokens < cfg.min_tokens_for_metadata, ""

        meta["tags"] = self.llm.verify_tags_grounded(self.llm.normalize_tags(meta.get("tags", [])), content)
        meta["triplets"] = self.llm.verify_triplets_grounded(meta.get("triplets", []), content)
        self.db.save_enrichment(chunk_id, meta)

        if tokens < cfg.min_tokens_for_qa:
            return True, meta.get("summary", "")

        valid: List[Dict] = []
        rejected: List[Dict] = []
        for cand in self.llm.generate_question_candidates(chunk, context):
            ok, reason = self._gate_candidate(cand, content, ctype)
            if ok:
                valid.append(cand)
            else:
                rejected.append(reason)  # type: ignore[arg-type]

        if valid and self.judge is not None and ctype != "math":
            valid, judged_out = self._apply_judge(valid, content)
            rejected += judged_out

        if valid:
            self.db.save_qa(chunk_id, valid)
        if rejected:
            self.db.save_rejections(chunk_id, rejected)
        return True, meta.get("summary", "")

    def _gate_candidate(self, cand: Dict, content: str, ctype: str):
        """(True, '') and `cand` completed with answer/type, or (False, rejection record)."""
        question = str(cand.get("question", "")).strip()
        quote = str(cand.get("source_quote", "")).strip()
        level = cand.get("difficulty", "Medium")

        if not question or len(quote) < self.config.quote_min_chars:
            return False, _reject(level, question, "", "Invalid Pass 1")

        located = self.gates.locate_quote(ctype, quote, content)
        if located is None:
            why = "Math quote not verbatim" if ctype == "math" else "Weak quote: not found in chunk"
            return False, _reject(level, question, "", why)
        quote = cand["source_quote"] = located  # the stored quote is chunk text, never the paraphrase

        # combined prompt sets already return the answer with the question
        answer = (cand.get("answer") or "").strip() or self.llm.generate_reference_answer(
            question, content, quote, ctype
        )
        if not answer or "NOT ENOUGH INFORMATION" in answer.replace("_", " ").upper():
            return False, _reject(level, question, answer, "Pass 2 refused")
        if DEFLECTION_PATTERN.search(answer):
            return False, _reject(level, question, answer, "Deflection")

        is_valid, reason = self.gates.checker(ctype).validate(question, answer, content, quote)
        if not is_valid:
            return False, _reject(level, question, answer, reason)
        cand["question"], cand["answer"], cand["type"] = question, answer, DIFFICULTY_TYPE.get(level, "Fact")
        return True, ""

    def _apply_judge(self, valid: List[Dict], content: str) -> Tuple[List[Dict], List[Dict]]:
        try:
            verdicts = self.judge.check_many([(c["question"], c["answer"], content) for c in valid])
        except JudgeUnavailable as e:
            raise LLMUnavailable(str(e)) from e
        kept, dropped = [], []
        for cand, (ok, reason) in zip(valid, verdicts):
            if ok:
                kept.append(cand)
            else:
                dropped.append(_reject(cand.get("difficulty", "Medium"), cand["question"], cand["answer"], reason))
        return kept, dropped

    # ------------------------------------------------------------------ one document

    def _neighbour(self, chunk_id: Optional[str], known: Dict[str, str]) -> Optional[str]:
        if not chunk_id:
            return None
        if chunk_id in known:
            return known[chunk_id]
        row = self.db.get_chunk(chunk_id)
        return row["content"] if row else None

    def build_context(self, chunk: Dict[str, Any], history: Deque[str], known: Dict[str, str]) -> str:
        """Orientation for the model: where the chunk sits, plus its neighbours. Never a source."""
        lines: List[str] = []
        crumb = chunk.get("breadcrumb")
        if crumb:
            lines.append(f"Location: {crumb}")
        meta = chunk.get("metadata", {})
        if meta.get("signature"):
            lines.append(f"Signature: {meta['signature']}")
        ctype = chunk.get("content_type", "prose")
        if ctype in ("table", "math", "code"):
            n = self.config.neighbour_chars
            for label, cid in (("PREV", chunk.get("prev_chunk_id")), ("NEXT", chunk.get("next_chunk_id"))):
                text = self._neighbour(cid, known)
                if text:
                    lines.append(f"{label}: {text[:n]}")
            if not any(ln.startswith(("PREV", "NEXT")) for ln in lines):
                lines.append("No adjacent structural chunks")
        else:
            lines.append("History:\n" + "\n".join(f"- {s}" for s in history))
        return "\n".join(lines)

    def enrich_document(self, doc_id: str) -> None:
        """Raises LLMUnavailable (document left pending) if the server is down or stops answering."""
        chunks = self.db.get_chunks_to_enrich(doc_id)
        if not chunks:
            return
        self.llm.check_health()  # fail fast, before touching any chunk

        known = {c["chunk_id"]: c["content"] for c in chunks}
        history: Deque[str] = deque(maxlen=self.config.history)
        for chunk in chunks:
            success, summary = self.process_chunk(chunk, self.build_context(chunk, history, known))
            if (
                success
                and summary
                and not DEFLECTION_PATTERN.search(summary)
                and len(summary.split()) >= self.config.min_summary_words
            ):
                history.append(summary)

    def run(self) -> EnrichReport:
        """Enrich every pending document. Stops at the first LLM outage; unfinished work stays pending."""
        report = EnrichReport()
        done: Set[str] = set()
        while True:
            docs = self.db.get_pending_documents(limit=self.config.batch_documents, exclude=list(done))
            if not docs:
                return report
            done.update(docs)
            with ThreadPoolExecutor(self.config.max_workers) as pool:
                futures = {pool.submit(self.enrich_document, d): d for d in docs}
                for future in as_completed(futures):
                    try:
                        future.result()
                        report.documents += 1
                    except LLMUnavailable as e:
                        logger.error(f"{e}. Stopping; unfinished documents stay pending.")
                        report.server_down = True
                    except Exception:
                        logger.exception(f"Enrichment of {futures[future]} crashed")
            if report.server_down:
                return report
