"""
verify.py: decide whether a generated question/answer pair is grounded in its chunk.

The checks run cheapest first and every rejection carries a reason that ends up in
`chunk_rejections`:

  1. provenance   the model's quote must be found in the chunk. The stored quote is replaced by
                  the exact chunk text (snapped to whole sentences), so what we keep is verbatim
                  even when the model paraphrased or dropped punctuation.
  2. support      every number in the answer must occur in the chunk; no answer sentence may be
                  mostly made of words the source and question do not contain (an invented
                  sentence); and at most one unfamiliar technical word may appear (a swapped term).
  3. question     an answer that only repeats the question adds nothing; a "how many" question needs
                  a quantity; a "why"/"purpose" question needs a reason; and an answer whose
                  embedding is far from its quote does not follow from it.
  Small NLI models call correct, restated quotes "neutral" or even "contradiction" (see
  evals/report.md), so NLI is not used as a gate.

These are cheap checks of provenance and support. They cannot tell whether a grounded answer
really answers the question ("what is the purpose of X?" answered with a description of X, or a
circular "because it is defined that way"); on the gold set that is about 1 accepted pair in 50.
Judges were tried for it. Local ones did not help: LFM2.5 accepted every pair; Sharp-MiniCPM5 rejected 43%
of good pairs for "not supported" and its "answers the question" verdict caught none of the pairs the
checks above let through; HHEM-2.1-Open and an extractive QA model added almost nothing. The one that did is
Liquid AI's D1 decision model (`D1Judge`, optional and OFF by default): run after these checks it accepted none
of the real or synthetic bad pairs on the gold set. It is an external API, so enabling it sends chunk, question
and answer text to api.liquid.ai. See evals/report.md. Thresholds were tuned on evals/corpus/gold_qa.json with
evals/eval_verifier.py.
"""

import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Set, Tuple

import httpx
from rapidfuzz import fuzz

logger = logging.getLogger("verify")

_NUMBER_WORDS = {
    "first": 1, "two": 2, "second": 2, "three": 3, "third": 3, "four": 4, "fourth": 4,
    "five": 5, "fifth": 5, "six": 6, "sixth": 6, "seven": 7, "seventh": 7, "eight": 8, "eighth": 8,
    "nine": 9, "ninth": 9, "ten": 10, "tenth": 10, "twelve": 12, "twelfth": 12,
}
# Words that talk about the source rather than about its content, plus LaTeX debris from PDF extraction.
_META = frozenset(
    "source text passage chunk section stated states state explicitly specifically mentioned mentions described "
    "describes according specified specifies indicates sqrt frac mathrm text".split()
)
_QUANTITY_Q = re.compile(r"^\s*(how\s+(many|much)\b|what\s+is\s+the\s+(number|count|value)\b)", re.I)
_CARDINALS = frozenset("two three four five six seven eight nine ten twelve".split())
_PURPOSE_Q = re.compile(r"^\s*why\b|\b(purpose|reason|motivation)\b", re.I)
_PURPOSE_MARK = re.compile(
    r"\b(because|so that|in order to|since|therefore|thus|hence|due to|as a result|allow\w*|enabl\w*|ensur\w*|"
    r"prevent\w*|preserv\w*|facilitat\w*|help\w*|lets?|need\w*|must|can|so as to)\b|^\s*to\s+\w+|,\s*so\b|\bto\s+(make|use|inject|obtain|provide)\b",
    re.I,
)
_STOP = frozenset(
    "what which whom whose when where while does did doing done that this these those with from into onto "
    "over than then them they their there here have has had having been being were was will would could "
    "should also each every both such more most some only very just about after before between during "
    "through without within against upon under above below".split()
)


@dataclass(frozen=True)
class VerifyConfig:
    fuzzy_quote_min: float = 85.0  # partial_ratio needed when the quote is not an exact match
    max_quote_sentences: int = 3  # a snapped quote longer than this keeps its exact span instead
    support_scope: str = "chunk"  # "chunk" or "quote": where the answer's words must be found
    novel_ratio_max: float = 0.50  # per answer sentence: share of words in neither source nor question
    min_sentence_words: int = 4  # shorter sentences give a noisy novelty ratio and are not judged by it
    rare_novel_max: int = 1  # unfamiliar technical words (split by the tokenizer) allowed in an answer
    min_quote_similarity: float = 0.70  # cosine(answer, quote) below this means the answer is not from the quote
    min_words_for_similarity: int = 4  # shorter answers embed poorly; they are covered by the support checks


@dataclass
class Verdict:
    ok: bool
    reason: str = ""
    quote: str = ""  # the verbatim chunk text that replaces the model's quote


# ----------------------------------------------------------------------------- text helpers


def _canon(text: str) -> Tuple[str, List[int]]:
    """Lower-case alphanumerics only, with the index of each kept character in `text`."""
    chars, index = [], []
    for i, ch in enumerate(text):
        if ch.isalnum():
            chars.append(ch.lower())
            index.append(i)
    return "".join(chars), index


def _sentence_spans(text: str) -> List[Tuple[int, int]]:
    spans, start = [], 0
    for m in re.finditer(r"(?<=[.!?])\s+", text):
        spans.append((start, m.start()))
        start = m.end()
    spans.append((start, len(text)))
    return [(a, b) for a, b in spans if b > a]


def _snap(chunk: str, start: int, end: int, max_sentences: int) -> str:
    """Widen [start, end) to whole sentences unless that would exceed `max_sentences`."""
    covered = [(a, b) for a, b in _sentence_spans(chunk) if a < end and b > start]
    if covered and len(covered) <= max_sentences:
        return chunk[covered[0][0] : covered[-1][1]].strip()
    return chunk[start:end].strip()


def locate_quote(quote: str, chunk: str, cfg: VerifyConfig = VerifyConfig()) -> Optional[str]:
    """The verbatim chunk text the quote refers to, or None when the quote is not in the chunk."""
    q, _ = _canon(quote)
    c, idx = _canon(chunk)
    if len(q) < 12:
        return None
    pos = c.find(q)
    if pos >= 0:
        return _snap(chunk, idx[pos], idx[pos + len(q) - 1] + 1, cfg.max_quote_sentences)
    align = fuzz.partial_ratio_alignment(q, c)
    if align is not None and align.score >= cfg.fuzzy_quote_min and align.dest_end > align.dest_start:
        return _snap(chunk, idx[align.dest_start], idx[align.dest_end - 1] + 1, cfg.max_quote_sentences)
    return None


def _stem(word: str) -> str:
    return word[:5]


def _content_stems(text: str) -> Set[str]:
    """Stems of words of 4+ letters (stop and meta words removed): the words that carry meaning."""
    return {_stem(w) for w in _content_words(text)}


def _content_words(text: str) -> List[str]:
    text = re.sub(r"\\[A-Za-z]+", " ", text)  # LaTeX commands such as \\sqrt, \\text
    return [w for w in re.findall(r"[a-z]{4,}", text.lower()) if w not in _STOP and w not in _META]


def _numbers(text: str) -> Set[int]:
    nums = {int(n) for n in re.findall(r"(?<![\w.])\d+(?![\w])", text)}
    nums |= {_NUMBER_WORDS[w] for w in re.findall(r"[a-z]+", text.lower()) if w in _NUMBER_WORDS}
    return nums


_SHORT_STOP = frozenset("the and for are was has had not but can its who how why did does you our out any all may per via too her him his she".split())


def _tokens(text: str) -> Set[str]:
    """Every token that could be new information: words (also 3-letter ones such as "two"),
    numbers and single-letter symbols."""
    return {
        _stem(w)
        for w in re.findall(r"[a-z0-9]+", text.lower())
        if w not in _STOP and w not in _SHORT_STOP and w not in _META and (len(w) >= 3 or len(w) == 1 or w.isdigit())
    }


# --------------------------------------------------------------------------------- checks


def check_support(
    answer: str,
    chunk: str,
    quote: str,
    question: str,
    cfg: VerifyConfig,
    is_rare: Optional[Callable[[str], bool]] = None,
) -> Tuple[bool, str]:
    source = quote if cfg.support_scope == "quote" else chunk
    missing = _numbers(answer) - _numbers(chunk)
    if missing:
        return False, f"Unsupported number in answer: {sorted(missing)}"
    known = _content_stems(source) | _content_stems(question)
    if not _content_stems(answer):  # "N = 6.", "d k": judged on numbers and symbols only
        if _tokens(answer) - _tokens(chunk) - _tokens(question):
            return False, "Unsupported symbol in answer"
        return True, ""
    novel_words: List[str] = []
    for sentence in re.split(r"(?<=[.!?])\s+", answer):
        words = _content_words(sentence)
        novel = [w for w in words if _stem(w) not in known]
        if len(words) >= cfg.min_sentence_words and len(novel) / len(words) > cfg.novel_ratio_max:
            return False, f"Unsupported sentence in answer ({len(novel)} of {len(words)} words not in the source)"
        novel_words += novel
    if is_rare is not None:
        rare = [w for w in novel_words if is_rare(w)]
        if len(rare) > cfg.rare_novel_max:
            return False, f"Unsupported terms in answer: {rare[:3]}"
    return True, ""


def check_addresses_question(question: str, answer: str) -> Tuple[bool, str]:
    if not (_tokens(answer) - _tokens(question)):
        return False, "Answer only restates the question"
    if _QUANTITY_Q.search(question):
        words = set(re.findall(r"[a-z]+", answer.lower()))
        has_quantity = re.search(r"\d", answer) or words & _CARDINALS or re.search(r"(?<![A-Za-z])[b-hj-zB-HJ-Z](?![A-Za-z])", answer)
        if not has_quantity:
            return False, "Question asks for a number; the answer gives none"
    if _PURPOSE_Q.search(question) and not _PURPOSE_MARK.search(answer):
        return False, "Why/purpose question: the answer states no reason or purpose"
    return True, ""


def verify(
    question: str,
    answer: str,
    chunk: str,
    quote: str,
    cfg: VerifyConfig = VerifyConfig(),
    is_rare: Optional[Callable[[str], bool]] = None,
    similarity: Optional[Callable[[str, str], float]] = None,
) -> Verdict:
    """Run every layer. `is_rare(word)` and `similarity(a, b)` are optional; a layer whose helper is
    missing is skipped, which keeps the function usable (and testable) without any model."""
    if not answer or not answer.strip():
        return Verdict(False, "Empty answer")
    span = locate_quote(quote, chunk, cfg)
    if span is None:
        return Verdict(False, "Weak quote: not found in chunk")
    ok, reason = check_support(answer, chunk, span, question, cfg, is_rare)
    if not ok:
        return Verdict(False, reason, span)
    ok, reason = check_addresses_question(question, answer)
    if not ok:
        return Verdict(False, reason, span)
    if similarity is not None and len(_content_words(answer)) >= cfg.min_words_for_similarity:
        sim = similarity(answer, span)
        if sim < cfg.min_quote_similarity:
            return Verdict(False, f"Answer does not follow from the quote (similarity {sim:.2f} < {cfg.min_quote_similarity})", span)
    return Verdict(True, "", span)


class EmbeddingHelpers:
    """`is_rare` and `similarity` from the shared bge encoder (loaded on first use)."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        from qp_core import models

        self._encoder = models.get_bi_encoder(model_name)
        self._rare: dict = {}

    def is_rare(self, word: str) -> bool:
        """True when the tokenizer has to split the word: technical terms, names, jargon."""
        if word not in self._rare:
            self._rare[word] = len(self._encoder.tokenizer.tokenize(word)) > 1
        return self._rare[word]

    def similarity(self, a: str, b: str) -> float:
        from sentence_transformers import util

        ea, eb = self._encoder.encode([a, b], convert_to_tensor=True, show_progress_bar=False)
        return float(util.cos_sim(ea, eb).item())


class PairVerifier:
    """`verify()` with the bge helpers loaded on first use, exposing the same
    `.validate(question, answer, chunk, source_quote) -> (ok, reason)` shape as AnswerValidator."""

    def __init__(self, cfg: VerifyConfig = VerifyConfig()):
        self.cfg = cfg
        self._helpers: Optional[EmbeddingHelpers] = None

    def validate(self, question: str, answer: str, chunk: str, source_quote: str) -> Tuple[bool, str]:
        if self._helpers is None:
            self._helpers = EmbeddingHelpers()
        v = verify(question, answer, chunk, source_quote, self.cfg, self._helpers.is_rare, self._helpers.similarity)
        return v.ok, v.reason


def default_verifier(cfg: VerifyConfig = VerifyConfig()):
    """(pair, chunk_text) -> (ok, reason), the shape evals/eval_verifier.py scores."""
    verifier = PairVerifier(cfg)
    return lambda pair, chunk: verifier.validate(pair["question"], pair["answer"], chunk, pair["quote"])


# ------------------------------------------------------------------ optional judge: Liquid AI D1
#
# D1 is a decision model: it answers yes/no questions about a piece of text with a calibrated probability and
# generates no tokens. Used here as a second opinion on pairs that already passed the checks above; it catches
# what they cannot (an answer that is grounded but does not answer the question, a one-word meaning change, a
# conflation of two facts) and accepts correct paraphrases. Off unless QP_VERIFY_JUDGE=d1 and LIQUID_API_KEY is set.

D1_URL = "https://api.liquid.ai/decisions/v1/systemone"
D1_QUESTIONS = {  # phrasings fixed before the first evaluation run and never tuned on the gold set
    "supported": "Is every claim made in the ANSWER stated in or directly implied by the SOURCE?",
    "answers_question": "Does the ANSWER directly give the specific thing the QUESTION asks for?",
}
D1_DEFAULT_THRESHOLD = 0.867  # min(both probabilities) cut-off that kept 97% of the good gold pairs (evals/report.md)
_D1_REASONS = {
    "supported": "answer not supported by the source",
    "answers_question": "answer does not give what the question asks",
}


class JudgeUnavailable(RuntimeError):
    """The judge cannot give a verdict right now (bad key, network failure, repeated rate limiting). Says nothing
    about the pair, so callers must not record a rejection for it; Enricher turns it into LLMUnavailable."""


class D1Judge:
    """Yes/no judge backed by Liquid AI's `d1:free` model. `check` returns (ok, reason) like the other checkers."""

    name = "d1"

    def __init__(
        self,
        api_key: str,
        *,
        url: str = D1_URL,
        threshold: float = D1_DEFAULT_THRESHOLD,
        workers: int = 4,
        timeout: float = 60.0,
        retries: int = 5,
        transport: Optional[httpx.BaseTransport] = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        if not api_key:
            raise ValueError("D1Judge needs an API key")
        self.url, self.threshold, self.workers, self.retries, self._sleep = url, threshold, workers, retries, sleep
        self._headers = {"Authorization": f"Bearer {api_key}"}  # never logged
        self._client = httpx.Client(timeout=timeout, transport=transport)

    def probabilities(self, question: str, answer: str, source: str) -> Optional[Dict[str, float]]:
        """P(yes) for each D1 question, or None when the request itself is unusable (for example too large)."""
        body = {
            "model": "d1:free",
            "state": f"SOURCE:\n{source}\n\nQUESTION:\n{question}\n\nANSWER:\n{answer}",
            "questions": {k: {"type": "noul", "instructions": v} for k, v in D1_QUESTIONS.items()},
        }
        last = "no attempt made"
        for attempt in range(self.retries):
            try:
                r = self._client.post(self.url, json=body, headers=self._headers)
            except httpx.TransportError as e:
                last = f"network error: {type(e).__name__}"
            else:
                if r.status_code == 200:
                    answers = r.json()["answers"]
                    return {k: float(answers[k]["noul"]) for k in D1_QUESTIONS}
                if r.status_code in (401, 403):
                    raise JudgeUnavailable(f"D1 rejected the API key (HTTP {r.status_code}); check LIQUID_API_KEY")
                if r.status_code not in (408, 409, 425, 429) and r.status_code < 500:
                    logger.warning(f"D1 could not judge one pair (HTTP {r.status_code}); keeping the deterministic verdict")
                    return None
                last = f"HTTP {r.status_code}"
            self._sleep(min(2 ** attempt, 30))
        raise JudgeUnavailable(f"D1 is not responding after {self.retries} attempts ({last})")

    def check(self, question: str, answer: str, source: str) -> Tuple[bool, str]:
        probs = self.probabilities(question, answer, source)
        if probs is None:
            return True, ""
        worst = min(probs, key=probs.get)
        if probs[worst] >= self.threshold:
            return True, ""
        return False, f"D1 judge: {_D1_REASONS[worst]} (p={probs[worst]:.2f})"

    def check_many(self, items: Sequence[Tuple[str, str, str]]) -> List[Tuple[bool, str]]:
        """`check` for several (question, answer, source) triples, a few requests at a time, in order."""
        with ThreadPoolExecutor(self.workers) as pool:
            return list(pool.map(lambda t: self.check(*t), items))


def judge_from_env(env: Optional[Mapping[str, str]] = None) -> Optional[D1Judge]:
    """The optional judge chosen by QP_VERIFY_JUDGE (unset, "off" or "none": no judge). Only "d1" exists; it needs
    LIQUID_API_KEY and reads QP_D1_THRESHOLD (default D1_DEFAULT_THRESHOLD). Raises ValueError for a bad setting."""
    env = os.environ if env is None else env
    name = env.get("QP_VERIFY_JUDGE", "").strip().lower()
    if name in ("", "off", "none", "0", "false"):
        return None
    if name != "d1":
        raise ValueError(f"unknown QP_VERIFY_JUDGE '{name}'; the only judge is 'd1'")
    key = env.get("LIQUID_API_KEY", "").strip()
    if not key:
        raise ValueError("QP_VERIFY_JUDGE=d1 needs LIQUID_API_KEY in the environment")
    return D1Judge(key, threshold=float(env.get("QP_D1_THRESHOLD", D1_DEFAULT_THRESHOLD)))
