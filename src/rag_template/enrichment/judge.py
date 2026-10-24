"""
judge.py: an optional second opinion on pairs that already passed every deterministic gate.

The deterministic gates check provenance and support. They cannot tell that a grounded answer fails to
answer the question, or that one word flipped its meaning. A judge can, at the price of one more model
call per pair. It is OFF by default and only worth enabling with a model clearly stronger than the one
that wrote the pairs (a small model judging itself tends to accept everything).

A judge is anything with `check_many([(question, answer, chunk), ...]) -> [(ok, reason), ...]` that
raises `JudgeUnavailable` when it cannot give a verdict (bad key, outage). That says nothing about the
pair, so the enricher aborts the file and leaves it pending instead of recording a rejection.
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Sequence, Tuple

from rag_template.enrichment.llm import LLMClient, LLMUnavailable

logger = logging.getLogger("rag_template.judge")


class JudgeUnavailable(RuntimeError):
    """The judge cannot give a verdict right now."""


class LLMJudge:
    """Asks an OpenAI-compatible model two yes/no questions per pair, as JSON."""

    name = "llm"

    SYSTEM = (
        "You are a strict reviewer of question/answer pairs. You judge ONLY against the SOURCE. "
        'Reply with JSON only: {"supported": true|false, "answers_question": true|false}.'
    )
    USER = (
        "SOURCE:\n{source}\n\nQUESTION:\n{question}\n\nANSWER:\n{answer}\n\n"
        "supported: is every claim in the ANSWER stated in, or directly implied by, the SOURCE?\n"
        "answers_question: does the ANSWER directly give the specific thing the QUESTION asks for?"
    )

    def __init__(self, llm: LLMClient, workers: int = 2):
        self.llm = llm
        self.workers = workers

    def check(self, question: str, answer: str, source: str) -> Tuple[bool, str]:
        try:
            verdict = self.llm.chat_json(
                self.SYSTEM, self.USER.format(source=source, question=question, answer=answer), 200
            )
        except LLMUnavailable as e:
            raise JudgeUnavailable(str(e)) from e
        if not verdict:  # unparsable: keep the deterministic verdict rather than guess
            return True, ""
        if verdict.get("supported") is False:
            return False, "LLM judge: answer not supported by the source"
        if verdict.get("answers_question") is False:
            return False, "LLM judge: answer does not give what the question asks"
        return True, ""

    def check_many(self, items: Sequence[Tuple[str, str, str]]) -> List[Tuple[bool, str]]:
        with ThreadPoolExecutor(self.workers) as pool:
            return list(pool.map(lambda t: self.check(*t), items))


def make_judge(kind: str, llm: LLMClient) -> Optional[LLMJudge]:
    kind = (kind or "off").strip().lower()
    if kind in ("", "off", "none", "0", "false"):
        return None
    if kind == "llm":
        return LLMJudge(llm)
    raise ValueError(f"unknown judge '{kind}'; choose off or llm")
