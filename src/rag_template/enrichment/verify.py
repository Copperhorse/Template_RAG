"""
verify.py: decide whether a generated question/answer pair is grounded in its chunk.

The checks run cheapest first and every rejection carries a reason that ends up in
`chunk_rejections`, so you can see which gate is doing the work:

  1. provenance   the model's quote must be found in the chunk. The stored quote is replaced by the
                  exact chunk text (snapped to whole sentences, or whole lines for code), so what we
                  keep is verbatim even when the model paraphrased or dropped punctuation.
  2. support      every number in the answer must occur in the chunk; no answer sentence may be mostly
                  made of words the source and question do not contain (an invented sentence); and at
                  most one unfamiliar technical word may appear (a swapped term).
  3. question     an answer that only repeats the question adds nothing; a "how many" question needs a
                  quantity; a "why"/"purpose" question needs a reason; and an answer whose embedding is
                  far from its quote does not follow from it.

Layers that need an embedding model (rare-word and similarity checks) are skipped when none is
available, so the function stays usable and testable without any model.

These are cheap checks of provenance and support. They cannot tell whether a grounded answer really
answers the question ("what is the purpose of X?" answered with a description of X). Small NLI models
call correct, restated quotes "neutral" or even "contradiction", so NLI is not a gate here (the
lexical -> bi-encoder -> NLI chain in validator.py is kept for maths, where wording is rigid).

The thresholds in `VerifyConfig` were tuned on English technical prose with a small local model.
Treat them as a starting point and re-tune on your own gold set: `Database.rejection_summary()` shows
which gate rejects the most.
"""

import builtins
import keyword
import logging
import re
from dataclasses import dataclass, replace
from typing import Callable, List, Optional, Sequence, Set, Tuple

from rapidfuzz import fuzz

logger = logging.getLogger("rag_template.verify")

# "first" and "second" are left out on purpose: in ordinary prose they are sequencing words ("Chroma first, then
# SQLite"), or a unit of time, not claims about a quantity. Higher ordinals ("third phase") still count.
_NUMBER_WORDS = {
    "two": 2,
    "three": 3,
    "third": 3,
    "four": 4,
    "fourth": 4,
    "five": 5,
    "fifth": 5,
    "six": 6,
    "sixth": 6,
    "seven": 7,
    "seventh": 7,
    "eight": 8,
    "eighth": 8,
    "nine": 9,
    "ninth": 9,
    "ten": 10,
    "tenth": 10,
    "twelve": 12,
    "twelfth": 12,
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
_SHORT_STOP = frozenset(
    "the and for are was has had not but can its who how why did does you our out any all may per via too her him his she".split()
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
    min_quote_chars: int = 12  # alphanumeric characters a quote needs before it can be located


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


def _snap_lines(chunk: str, start: int, end: int) -> str:
    """Widen [start, end) to whole lines (code is quoted line by line, not sentence by sentence)."""
    a = chunk.rfind("\n", 0, start) + 1
    b = chunk.find("\n", end)
    return chunk[a : b if b >= 0 else len(chunk)].strip("\n").rstrip()


def _in_table_row(chunk: str, start: int) -> bool:
    """True when `start` lies on a Markdown table row (a line that begins with a pipe)."""
    line_start = chunk.rfind("\n", 0, start) + 1
    return chunk[line_start : line_start + 1] == "|"


def _snap_best(chunk: str, start: int, end: int, max_sentences: int) -> str:
    """Sentences for prose, whole lines for table rows (a row's cells contain ". |", which would cut it into junk)."""
    if _in_table_row(chunk, start):
        return _snap_lines(chunk, start, end)
    return _snap(chunk, start, end, max_sentences)


def _align(quote: str, chunk: str, cfg: VerifyConfig) -> Optional[Tuple[int, int]]:
    """Character span in `chunk` that `quote` refers to, comparing alphanumerics only."""
    q, _ = _canon(quote)
    c, idx = _canon(chunk)
    if len(q) < cfg.min_quote_chars:
        return None
    pos = c.find(q)
    if pos >= 0:
        return idx[pos], idx[pos + len(q) - 1] + 1
    align = fuzz.partial_ratio_alignment(q, c)
    if align is not None and align.score >= cfg.fuzzy_quote_min and align.dest_end > align.dest_start:
        return idx[align.dest_start], idx[align.dest_end - 1] + 1
    return None


def locate_quote(quote: str, chunk: str, cfg: VerifyConfig = VerifyConfig()) -> Optional[str]:
    """The verbatim chunk text (whole sentences) the quote refers to, or None if it is not in the chunk."""
    span = _align(quote, chunk, cfg)
    return None if span is None else _snap_best(chunk, span[0], span[1], cfg.max_quote_sentences)


def locate_code_quote(quote: str, chunk: str, cfg: VerifyConfig = VerifyConfig()) -> Optional[str]:
    """Like locate_quote, but the result is whole lines of code. Code is symbol-heavy (`return y + 1`
    has 8 alphanumerics), so a quote needs fewer of them than prose does."""
    span = _align(quote, chunk, replace(cfg, min_quote_chars=min(cfg.min_quote_chars, 8)))
    return None if span is None else _snap_lines(chunk, span[0], span[1])


# ---- tolerant location: for quotes a small model copied almost, but not exactly
#
# Measured on the 70 gold snippets of evals/gold/handwritten.jsonl (evals/results/quote_tolerance.md): quotes with one
# word inserted, swapped, dropped or replaced score 76-100 (partial_ratio on alphanumerics); a quote lifted from a
# different chunk scores at most 55 with at most 67% of its words present. 75 / 80% sits between the two. It cannot
# tell "one word slightly off" from "one word invented", so callers must store the *located chunk text* (never the
# model's wording) and check the answer's support against that text.
LOOSE_MIN_SCORE = 75.0
LOOSE_MIN_WORD_COVERAGE = 0.80
LOOSE_MIN_CHARS = 20  # alphanumeric characters; shorter quotes are too easy to match by accident


def _quote_words(text: str) -> List[str]:
    return [w for w in re.findall(r"[a-z0-9_]+", text.lower()) if len(w) > 1 or w.isdigit()]


def _locate_loose(quote: str, chunk: str, cfg: VerifyConfig, code: bool) -> Optional[str]:
    span = _align(
        quote,
        chunk,
        replace(cfg, fuzzy_quote_min=LOOSE_MIN_SCORE, min_quote_chars=max(cfg.min_quote_chars, LOOSE_MIN_CHARS)),
    )
    if span is None:
        return None
    text = (
        _snap_lines(chunk, span[0], span[1]) if code else _snap_best(chunk, span[0], span[1], cfg.max_quote_sentences)
    )
    words = _quote_words(quote)
    have = set(_quote_words(text))
    if not words or sum(w in have for w in words) / len(words) < LOOSE_MIN_WORD_COVERAGE:
        return None
    return text


def locate_quote_ex(
    quote: str, chunk: str, cfg: VerifyConfig = VerifyConfig(), code: bool = False, loose: bool = False
) -> Optional[Tuple[str, str]]:
    """(chunk text, how) where how is "exact" (alphanumeric match), "fuzzy" (>= 85) or "loose" (>= 75 with word
    coverage; only when `loose`). None if the quote is not in the chunk."""
    text = locate_code_quote(quote, chunk, cfg) if code else locate_quote(quote, chunk, cfg)
    if text is not None:
        canon_q, _ = _canon(quote)
        canon_c, _ = _canon(chunk)
        return text, ("exact" if canon_q and canon_q in canon_c else "fuzzy")
    if loose:
        text = _locate_loose(quote, chunk, cfg, code)
        if text is not None:
            return text, "loose"
    return None


def _stem(word: str) -> str:
    return word[:5]


def _content_words(text: str) -> List[str]:
    text = re.sub(r"\\[A-Za-z]+", " ", text)  # LaTeX commands such as \sqrt, \text
    return [w for w in re.findall(r"[a-z]{4,}", text.lower()) if w not in _STOP and w not in _META]


def _content_stems(text: str) -> Set[str]:
    return {_stem(w) for w in _content_words(text)}


# A number glued to a name by a hyphen is part of that name (SHA-256, UTF-8, ISO-8601, GPT-4, HS256), not a quantity
# the answer asserts. "3-5" and "-5" are unaffected: only a *letter* before the hyphen exempts a number.
# An ordinal suffix belongs to the number ("23rd July", "the 7th day"): without it "23rd" in the source is not read as 23,
# so an answer saying "July 23" would be called unsupported. Dates in statutes and gazettes are written this way.
_STANDALONE_NUMBER = re.compile(r"(?<![\w.])(?<![A-Za-z]-)(\d+)(?:st|nd|rd|th)?(?![\w])")
# "260 000", "1,000,000" and "12 345 678" are single numbers written with a thousands separator.
_GROUPED_NUMBER = re.compile(r"(?<![\d.,])\d{1,3}(?:[ \u00a0\u202f,]\d{3})+(?![\d])")


def _collapse_thousands(text: str) -> str:
    return _GROUPED_NUMBER.sub(lambda m: re.sub(r"[ \u00a0\u202f,]", "", m.group()), text)


def _numbers(text: str) -> Set[int]:
    text = _collapse_thousands(text)
    nums = {int(n) for n in _STANDALONE_NUMBER.findall(text)}
    nums |= {_NUMBER_WORDS[w] for w in re.findall(r"[a-z]+", text.lower()) if w in _NUMBER_WORDS}
    return nums


def _tokens(text: str) -> Set[str]:
    """Every token that could be new information: words (also 3-letter ones such as "two"),
    numbers and single-letter symbols."""
    return {
        _stem(w)
        for w in re.findall(r"[a-z0-9]+", text.lower())
        if w not in _STOP and w not in _SHORT_STOP and w not in _META and (len(w) >= 3 or len(w) == 1 or w.isdigit())
    }


# Words that carry no topic in a question ("which function does this application use ..."). Used only for the
# informational "not found in the sources" hint, never for a verdict (see missing_question_terms).
_QUESTION_FILLER = frozenset(
    "what which where when does this that with from into have used uses using application system function method class code "
    "file files data value values approach handle handles default order work works make makes takes take need needs name names "
    "given kind type types list lists create creates created return returns returned write writes written check checks checked "
    "find finds found provide provides support supports many much long happen happens ever there their these those".split()
)


def question_terms(question: str) -> List[str]:
    """The distinctive words of a question (each once): no stop words, source-talk or filler like "which" or "function"."""
    seen: List[str] = []
    for w in re.findall(r"[a-z0-9]{4,}", question.lower()):
        if w not in _STOP and w not in _META and w not in _QUESTION_FILLER and w not in seen:
            seen.append(w)
    return seen


def missing_question_terms(question: str, texts: Sequence[str]) -> List[str]:
    """Distinctive words of the question that occur in none of `texts` (compared by their first five letters).

    This is a hint for the reader ("your question mentions slack and redis; no source does"), not a gate: measured on
    the hand-written gold set it flagged 17 of 70 answerable questions to catch 12 of 15 unanswerable ones, because
    natural questions paraphrase (evals/README.md)."""
    hay = {w[:5] for t in texts for w in re.findall(r"[a-z0-9]{4,}", t.lower())}
    return [w for w in question_terms(question) if w[:5] not in hay]


# --------------------------------------------------------------------------------- checks


def check_support(
    answer: str,
    chunk: str,
    quote: str,
    question: str,
    cfg: VerifyConfig,
    is_rare: Optional[Callable[[str], bool]] = None,
    trusted_question: bool = False,
) -> Tuple[bool, str]:
    """`trusted_question=True` (the question was typed by the user): a number the question itself states, repeated by the
    answer, is not invented. Leave it False for generated question/answer pairs, where the same LLM wrote both."""
    source = quote if cfg.support_scope == "quote" else chunk
    missing = _numbers(answer) - _numbers(chunk) - (_numbers(question) if trusted_question else set())
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
        has_quantity = (
            re.search(r"\d", answer)
            or words & _CARDINALS
            or re.search(r"(?<![A-Za-z])[b-hj-zB-HJ-Z](?![A-Za-z])", answer)
        )
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
    """Run every layer for prose. `is_rare(word)` and `similarity(a, b)` are optional; a layer whose
    helper is missing is skipped."""
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
            return Verdict(
                False,
                f"Answer does not follow from the quote (similarity {sim:.2f} < {cfg.min_quote_similarity})",
                span,
            )
    return Verdict(True, "", span)


# ------------------------------------------------------------------------------- code

_BACKTICKED = re.compile(r"`([^`\n]{1,80})`")
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
# Names an answer may use without them appearing in the chunk ("returns `None`", "raises `ValueError`").
_ALWAYS_OK = (
    frozenset(dir(builtins))
    | frozenset(keyword.kwlist)
    | {"null", "undefined", "true", "false", "this", "void", "string", "number", "boolean"}
)


_PUNCT_ONLY = re.compile(r"^[^\w]+$")


def _is_identifier_claim(span: str) -> bool:
    """A backticked span that names something (a function, a path, a flag, a constant), as opposed to a regex, a
    one-character literal, or a stray fragment where the model's own markdown got tangled."""
    if _PUNCT_ONLY.match(span) or len(span) > 80:
        return False
    if span[0] in ".,;:" or re.search(r"[.!?]\s+\w", span):  # starts mid-sentence, or contains a sentence break
        return False
    if len(re.findall(r"[\\^$()?*+\[\]{}|]", span)) >= 3:  # a regular expression or other expression, not a name
        return False
    return bool(_IDENT.search(span))


def check_code_support(answer: str, chunk: str, context: str = "") -> Tuple[bool, str]:
    """Grounding for answers about code, where wording is irrelevant and names are everything:
    every number must occur in the evidence, and every identifier the answer puts in backticks must too
    (`retry_count`, `Foo.bar()`, `--flag`). English prose around them is not judged.

    `context` is text that is true of the evidence without being in it: for a retrieved chunk, its breadcrumb
    ("pkg/db.py > DBManager.get_pending_files"). A method's chunk does not repeat its class name, so without this
    `DBManager.get_pending_files()` would be called unsupported. Numbers are checked against `chunk` alone."""
    missing = _numbers(answer) - _numbers(chunk)
    if missing:
        return False, f"Unsupported number in answer: {sorted(missing)}"
    haystack = f"{chunk}\n{context}" if context else chunk
    for span in _BACKTICKED.findall(answer):
        span = span.strip()
        if not _is_identifier_claim(span) or span in haystack:
            continue
        absent = [i for i in _IDENT.findall(span) if i not in haystack and i not in _ALWAYS_OK]
        if absent:
            return False, f"Unsupported identifier in answer: `{span}`"
    return True, ""


def verify_code(question: str, answer: str, chunk: str, quote: str, cfg: VerifyConfig = VerifyConfig()) -> Verdict:
    if not answer or not answer.strip():
        return Verdict(False, "Empty answer")
    span = locate_code_quote(quote, chunk, cfg)
    if span is None:
        return Verdict(False, "Weak quote: not found in chunk")
    ok, reason = check_code_support(answer, chunk)
    if not ok:
        return Verdict(False, reason, span)
    ok, reason = check_addresses_question(question, answer)
    if not ok:
        return Verdict(False, reason, span)
    return Verdict(True, "", span)


# ------------------------------------------------------------------------------ checkers
# A "checker" is anything with `.validate(question, answer, chunk, source_quote) -> (ok, reason)`.


class EmbeddingHelpers:
    """`is_rare` and `similarity` from the shared bi-encoder (loaded on first use)."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        from rag_template import models

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
    """`verify()` for prose, with the embedding layers loaded on first use. Without the `local`
    extra it degrades to the text-only layers (and says so once)."""

    def __init__(
        self,
        cfg: VerifyConfig = VerifyConfig(),
        helpers: Optional[EmbeddingHelpers] = None,
        use_embeddings: bool = True,
    ):
        self.cfg = cfg
        self._helpers = helpers
        self._use_embeddings = use_embeddings

    def _get_helpers(self) -> Optional[EmbeddingHelpers]:
        if self._helpers is None and self._use_embeddings:
            try:
                self._helpers = EmbeddingHelpers()
            except ImportError:
                logger.warning(
                    "sentence-transformers is not installed: PairVerifier runs without its similarity and rare-word layers"
                )
                self._use_embeddings = False
        return self._helpers

    def validate(self, question: str, answer: str, chunk: str, source_quote: str) -> Tuple[bool, str]:
        h = self._get_helpers()
        v = verify(
            question, answer, chunk, source_quote, self.cfg, h.is_rare if h else None, h.similarity if h else None
        )
        return v.ok, v.reason


class CodeVerifier:
    def __init__(self, cfg: VerifyConfig = VerifyConfig()):
        self.cfg = cfg

    def validate(self, question: str, answer: str, chunk: str, source_quote: str) -> Tuple[bool, str]:
        v = verify_code(question, answer, chunk, source_quote, self.cfg)
        return v.ok, v.reason
