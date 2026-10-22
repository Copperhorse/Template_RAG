"""
Enricher.py — Production-Grade Enrichment Pipeline (Optimized Two-Pass)

"""

import json
import logging
import os
import re
import sys
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Set, Tuple

import httpx
import numpy as np
import openai
from json_repair import repair_json
from openai import OpenAI
from rapidfuzz import fuzz
from rich.console import Console
from rich.logging import RichHandler
from sentence_transformers import util

from qp_core.env import load_dotenv

load_dotenv()  # settings (LLAMA_*, QP_VERIFY_JUDGE, LIQUID_API_KEY, ...) may live in a git-ignored .env

# ---------------- ROBUST PROJECT ROOT DETECTION ----------------
_env_root = os.environ.get("RAG_PROJECT_ROOT")
if _env_root:
    project_root = Path(_env_root).resolve()
else:
    project_root = Path(__file__).resolve().parents[4]

if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

DB_PATH = str(project_root / "data" / "rag_staging.db")
CHROMA_DIR = str(project_root / "data" / "chroma_store")

Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
Path(CHROMA_DIR).mkdir(parents=True, exist_ok=True)

from qp_core import models
from qp_core.DBManager import DBManager
from qp_pipeline import verify
from qp_pipeline.prompts import PromptSet, get_prompt_set

# ---------------- CONFIG ----------------
LLAMA_API_URL = os.environ.get(
    "LLAMA_API_URL",
    f"http://{os.environ.get('LLAMA_HOST', 'localhost')}:{os.environ.get('LLAMA_PORT', '8080')}/v1",
)
MODEL_NAME = os.environ.get("LLAMA_MODEL_NAME", "lfm-2.5-1.2b")  # llama-server ignores it

MAX_WORKERS = 1

# LLM client hardening. The openai library's defaults (10 min read timeout, 2 retries) let a
# hung llama server stall a run for half an hour per call.
LLM_TIMEOUT_S = float(os.environ.get("LLM_TIMEOUT_S", "120"))
LLM_MAX_RETRIES = 1
LLM_HEALTH_TIMEOUT_S = 5.0  # per-file health probe
# Same variable the API uses to start `llama serve --reasoning-budget`. llama-server counts
# thinking tokens against max_tokens, so every request must allow budget + the answer itself.
REASONING_BUDGET = int(os.environ.get("LLAMA_REASONING_BUDGET", "4096"))
UNLIMITED_REASONING_CAP = 8192  # max_tokens allowance for thinking when the budget is -1
METADATA_ANSWER_TOKENS = 800
QUESTIONS_ANSWER_TOKENS = 1000
REFERENCE_ANSWER_TOKENS = 500

QUOTE_MATCH_THRESHOLD = 60.0
DEDUP_SIMILARITY_THRESHOLD = 80
MIN_TOKENS_FOR_METADATA = 30
MIN_TOKENS_FOR_QA = 30
MIN_SUMMARY_TOKENS = 10
QUOTE_MIN_CHARS = 25  # Relaxed from 40

DIFFICULTY_TYPE = {
    "Easy": "Fact",
    "Medium": "Mechanism",
    "Hard": "Critical",
}

DEFLECTION_PATTERN = re.compile(
    r"the\s+text\s+does\s+not\s+"
    r"(specify|mention|state|provide|include|address|discuss|indicate|describe)"
    r"|the\s+(passage|chunk|document|context)\s+does\s+not"
    r"|no\s+(specific|numeric|direct)\s+(threshold|value|detail|information|mention)"
    r"|is\s+not\s+(mentioned|specified|discussed|provided|stated)\s+in\s+the\s+text"
    r"|cannot\s+be\s+(determined|inferred|found)\s+from",
    re.IGNORECASE,
)

console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True, markup=True)],
)
logger = logging.getLogger("Enricher")


def _quote_is_grounded(quote: str, content: str) -> tuple[bool, str]:
    # Superseded by verify.locate_quote; kept as the pre-verify baseline for evals/eval_verifier.py.
    quote = quote.strip()
    if len(quote) < QUOTE_MIN_CHARS:
        return False, f"Quote too short ({len(quote)} chars, min {QUOTE_MIN_CHARS})"

    if quote.lower() in content.lower():
        return True, "exact"

    score = fuzz.partial_ratio(quote.lower(), content.lower())
    if score >= QUOTE_MATCH_THRESHOLD:
        return True, f"fuzzy ({score:.0f}%)"

    return False, f"not found ({score:.0f}%)"


def _content_words(t: str):
    return {w.lower() for w in re.findall(r"[a-zA-Z]{4,}", t)}


def _ensure_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, list) and len(value) == 1 and isinstance(value[0], dict):
        logger.warning("JSON parsed as single-element list — unwrapping to dict")
        return value[0]
    if isinstance(value, list) and value:
        logger.warning(
            f"JSON parsed as list with {len(value)} elements — expected a dict. Returning empty."
        )
    return {}


def get_questions_per_difficulty(estimated_tokens: int) -> int:
    if estimated_tokens < 80:
        return 1
    elif estimated_tokens < 200:
        return 2
    else:
        return 3


class AnswerValidator:
    SIMILARITY_THRESHOLD = 0.50
    LEXICAL_OVERLAP_THRESHOLD = (
        0.30  # Baseline gate: must have at least 30% word overlap
    )
    ENTAILMENT_THRESHOLD = 0.60
    CONTRADICTION_THRESHOLD = 0.60
    MIN_SENTENCES = 1
    MAX_SENTENCES = 5

    def __init__(
        self,
        bi_model_name: str = "BAAI/bge-small-en-v1.5",
        ce_model_name: str = "cross-encoder/nli-deberta-v3-xsmall",
    ):
        # Shared, process-wide instances (see qp_core.models); no per-run reload.
        self.bi_encoder = models.get_bi_encoder(bi_model_name)
        self.cross_encoder = models.get_cross_encoder(ce_model_name)

    def validate(
        self, question: str, answer: str, chunk: str, source_quote: str
    ) -> Tuple[bool, str]:
        if not answer or not answer.strip():
            return False, "Empty answer"

        struct_ok, sent_count = self._structural_check(answer)
        if not struct_ok:
            return False, f"Structural fail: {sent_count} sentences"

        # GATE 1: Lexical (Always run)
        c_words = self._content_words(chunk)
        a_words = self._content_words(answer)
        if not a_words:
            return False, "No content words in answer"

        overlap = len(c_words & a_words) / len(a_words)
        if overlap < self.LEXICAL_OVERLAP_THRESHOLD:
            return (
                False,
                f"Lexical fail: overlap={overlap:.2f} (gate is {self.LEXICAL_OVERLAP_THRESHOLD})",
            )

        # GATE 2: Bi-Encoder Similarity (Answer vs Quote & Answer vs Chunk)
        embeddings = self.bi_encoder.encode(
            [answer, source_quote, chunk], convert_to_tensor=True
        )
        ans_emb, quote_emb, chunk_emb = embeddings[0], embeddings[1], embeddings[2]

        # Use .item() to safely extract the scalar value and avoid PyTorch ValueError
        sim_ans_quote = util.cos_sim(ans_emb, quote_emb).item()
        sim_ans_chunk = util.cos_sim(ans_emb, chunk_emb).item()

        bi_score = max(sim_ans_quote, sim_ans_chunk)

        # GATE 3: Cross-Encoder NLI (Answer vs Source Quote)
        logits = self.cross_encoder.predict([[source_quote, answer]])
        e = np.exp(np.array(logits[0], dtype=np.float64) - np.max(logits[0]))
        probs = e / e.sum()

        p_contra = probs[0]
        p_entail = probs[1]
        p_neutral = probs[2]

        if p_contra > self.CONTRADICTION_THRESHOLD:
            return (
                False,
                f"NLI Contradiction ({p_contra:.2f} > {self.CONTRADICTION_THRESHOLD})",
            )

        if p_entail > self.ENTAILMENT_THRESHOLD:
            if bi_score < 0.40:  # Extremely lenient bi-encoder floor
                return (
                    False,
                    f"Entailed ({p_entail:.2f}), but bi-score too low ({bi_score:.2f})",
                )

        else:
            adjusted_bi_score = bi_score * (0.50 + 0.50 * p_entail)
            if adjusted_bi_score < self.SIMILARITY_THRESHOLD:
                return (
                    False,
                    f"Neutral NLI ({p_neutral:.2f}) dragged down bi-score: {adjusted_bi_score:.2f} < {self.SIMILARITY_THRESHOLD}",
                )

        # GATE 4: Question Heuristics
        if question.strip().lower().startswith(("why", "how")):
            causal = {
                "because",
                "due to",
                "as a result",
                "therefore",
                "leads to",
                "causes",
                "through",
                "allows",
                "enables",
                "since",
            }
            answer_words_set = set(answer.lower().split())
            if not any(
                w in answer.lower() if " " in w else w in answer_words_set
                for w in causal
            ):
                return False, "Why/How-question lacks causal/mechanism phrase"

        return True, ""

    def _sentence_count(self, text: str) -> int:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        return len([s for s in sentences if len(s) > 5])

    def _content_words(self, text: str) -> Set[str]:
        return _content_words(text)

    def _structural_check(self, text: str) -> Tuple[bool, int]:
        count = self._sentence_count(text)
        return (self.MIN_SENTENCES <= count <= self.MAX_SENTENCES), count


class LLMUnavailable(RuntimeError):
    """The LLM server could not be reached, timed out, or answered with a 5xx.

    This says nothing about the chunk being processed, so callers must NOT record a rejection for
    it: they abort the file and leave its chunks pending so a later run retries them.
    """


_THINK_BLOCK = re.compile(r"<think>.*?(?:</think>|$)", re.DOTALL | re.IGNORECASE)


def _strip_thinking(content: str) -> str:
    """Drop inline <think> blocks (servers started with --reasoning-format none leave them in
    `content`; an unterminated block means the budget ran out mid-thought)."""
    return _THINK_BLOCK.sub("", content).strip()


class LLMClient:
    def __init__(
        self,
        base_url: str,
        api_key: str = "no-key",
        timeout: float = LLM_TIMEOUT_S,
        max_retries: int = LLM_MAX_RETRIES,
        prompts: Optional[PromptSet] = None,
    ):
        self.prompts = prompts or get_prompt_set()  # QP_PROMPT_SET, see prompts.py
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=httpx.Timeout(timeout, connect=5.0),
            max_retries=max_retries,
        )
        self.stats = self._empty_stats()

    # ---------------- transport ----------------

    @staticmethod
    def _empty_stats() -> Dict[str, float]:
        return {"calls": 0, "seconds": 0.0, "prompt_tokens": 0, "completion_tokens": 0}

    def reset_stats(self) -> None:
        self.stats = self._empty_stats()

    @staticmethod
    def _max_tokens(answer_tokens: int) -> int:
        budget = REASONING_BUDGET if REASONING_BUDGET >= 0 else UNLIMITED_REASONING_CAP
        return budget + answer_tokens

    def check_health(self) -> None:
        """Raise LLMUnavailable unless the server answers /v1/models right now."""
        try:
            self.client.with_options(timeout=LLM_HEALTH_TIMEOUT_S, max_retries=0).models.list()
        except openai.APIError as e:
            raise LLMUnavailable(f"LLM server is not responding: {e}") from e

    def _chat(self, sys_prompt: str, user_prompt: str, answer_tokens: int) -> str:
        """
        One chat completion. Returns the text of `message.content` only (`reasoning_content` is
        never parsed); "" when the model produced no usable content.
        Raises LLMUnavailable for transport failures, timeouts and 5xx; any other error
        (e.g. a 400 for one oversized request) is the request's problem and yields "".
        """
        started = time.monotonic()
        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=self._max_tokens(answer_tokens),
                extra_body={"top_k": 50, "repetition_penalty": 1.05},
            )
        except (openai.APIConnectionError, openai.RateLimitError) as e:
            # APITimeoutError is a subclass of APIConnectionError
            raise LLMUnavailable(f"LLM server unreachable or too slow: {e}") from e
        except openai.APIStatusError as e:
            if e.status_code >= 500:
                raise LLMUnavailable(f"LLM server error {e.status_code}: {e}") from e
            logger.error(f"LLM rejected the request ({e.status_code}): {e}")
            return ""
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            return ""

        elapsed = time.monotonic() - started
        usage = getattr(response, "usage", None)
        self.stats["calls"] += 1
        self.stats["seconds"] += elapsed
        self.stats["prompt_tokens"] += getattr(usage, "prompt_tokens", 0) or 0
        self.stats["completion_tokens"] += getattr(usage, "completion_tokens", 0) or 0

        choice = response.choices[0]
        if choice.finish_reason == "length":
            logger.warning(
                f"LLM hit max_tokens ({self._max_tokens(answer_tokens)}) after {elapsed:.1f}s; "
                "output may be empty or cut off"
            )
        return _strip_thinking(choice.message.content or "")

    def _extract_json(self, text: str) -> Dict[str, Any]:
        fenced = re.search(r"```json\s*(\{.*\})\s*```", text, re.DOTALL)
        raw = fenced.group(1) if fenced else text

        try:
            parsed = json.loads(raw)
            result = _ensure_dict(parsed)
            if result:
                return result
        except json.JSONDecodeError:
            pass

        try:
            repaired = repair_json(raw, return_objects=True)
            result = _ensure_dict(repaired)
            if result:
                return result
        except Exception as e:
            logger.debug(f"repair_json failed: {e}")

        logger.error(f"JSON Parse Error: unrecoverable | Raw: {text[:100]}...")
        return {}

    def _call_model(
        self, sys_prompt: str, user_prompt: str, answer_tokens: int = METADATA_ANSWER_TOKENS
    ) -> Dict[str, Any]:
        return self._extract_json(self._chat(sys_prompt, user_prompt, answer_tokens))

    def _deduplicate_candidates(self, candidates: List[Dict]) -> List[Dict]:
        seen_qs: List[str] = []
        seen_quotes: List[str] = []
        unique: List[Dict] = []

        for cand in candidates:
            if not isinstance(cand, dict):
                continue
            q = cand.get("question", "").lower().strip()
            quote = cand.get("source_quote", "").lower().strip()
            if not q:
                continue

            if any(
                fuzz.token_sort_ratio(q, s) > DEDUP_SIMILARITY_THRESHOLD
                for s in seen_qs
            ):
                continue

            if quote and any(fuzz.partial_ratio(quote, sq) > 90 for sq in seen_quotes):
                continue

            seen_qs.append(q)
            if quote:
                seen_quotes.append(quote)
            unique.append(cand)

        return unique

    @staticmethod
    def _normalize_tags(tags: List[str]) -> List[str]:
        GENERIC_BLOCKLIST = {" "}

        def _to_snake(tag: str) -> str:
            s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", tag.strip())
            s = re.sub(r"[\s\-]+", "_", s)
            return s.lower()

        seen: set = set()
        result: List[str] = []
        for raw in tags:
            if not isinstance(raw, str) or not raw.strip():
                continue
            normalised = _to_snake(raw)
            if normalised in GENERIC_BLOCKLIST or normalised in seen:
                continue
            seen.add(normalised)
            result.append(normalised)

        return result

    @staticmethod
    def _verify_tags_grounded(tags: List[str], text: str) -> List[str]:
        text_lower = text.lower()
        grounded = []
        for tag in tags:
            surface = tag.replace("_", " ")
            if surface in text_lower or tag in text_lower:
                grounded.append(tag)
        return grounded

    @staticmethod
    def _verify_triplets_grounded(triplets: List[Dict], text: str) -> List[Dict]:
        text_lower = text.lower()
        grounded = []
        for t in triplets:
            if not isinstance(t, dict):
                continue
            subj = t.get("subject", "").lower().strip()
            obj = t.get("object", "").lower().strip()
            if subj and obj and subj in text_lower and obj in text_lower:
                grounded.append(t)
        return grounded

    def generate_metadata(
        self,
        text: str,
        context: str,
        estimated_tokens: int = 150,
        content_type: str = "prose",
    ) -> Dict[str, Any]:
        if estimated_tokens < MIN_TOKENS_FOR_METADATA:
            return {}

        prompt = self.prompts.metadata(text, context)
        sys_prompt, user_prompt = prompt.system, prompt.user
        return self._call_model(sys_prompt, user_prompt, METADATA_ANSWER_TOKENS)

    def generate_question_candidates(self, chunk: Dict, context_str: str) -> List[Dict]:
        estimated_tokens = chunk.get("estimated_tokens", 150)
        per_diff = get_questions_per_difficulty(estimated_tokens)
        content_type = chunk.get("content_type", "prose")

        if self.prompts.combined:
            return self._generate_combined(chunk, context_str, per_diff, content_type)

        difficulty_instructions = self.prompts.difficulty_instructions(content_type)
        all_candidates: List[Dict] = []

        for difficulty, instruction in difficulty_instructions.items():
            prompt = self.prompts.questions(
                chunk["content"], context_str, difficulty, instruction, per_diff
            )
            sys_prompt, user_prompt = prompt.system, prompt.user
            result = self._call_model(sys_prompt, user_prompt, QUESTIONS_ANSWER_TOKENS)
            raw = result.get("qa_pairs", [])

            if not raw and result:
                from collections import defaultdict

                groups: dict = defaultdict(dict)
                for k, v in result.items():
                    m = re.match(r"^(question|source_quote)(\d*)$", k)
                    if m:
                        groups[m.group(2)][m.group(1)] = v
                flat_items = [g for g in groups.values() if "question" in g]
                if flat_items:
                    raw = flat_items

            count = 0
            for item in raw:
                if count >= per_diff:
                    break
                if not isinstance(item, dict):
                    continue
                item["difficulty"] = difficulty
                all_candidates.append(item)
                count += 1

        return self._deduplicate_candidates(all_candidates)

    def _generate_combined(
        self, chunk: Dict, context_str: str, per_diff: int, content_type: str
    ) -> List[Dict]:
        """One call returns questions AND answers (prompt sets with combined=True)."""
        prompt = self.prompts.combined_qa(chunk["content"], context_str, per_diff, content_type)
        result = self._call_model(prompt.system, prompt.user, 600 + 350 * per_diff * 3)
        raw = result.get("qa_pairs", [])
        levels = list(self.prompts.difficulty_instructions(content_type))
        candidates: List[Dict] = []
        counts: Dict[str, int] = {}
        for item in raw if isinstance(raw, list) else []:
            if not isinstance(item, dict):
                continue
            level = str(item.get("difficulty", "")).strip().capitalize()
            if level not in levels:
                continue
            if counts.get(level, 0) >= per_diff:
                continue
            counts[level] = counts.get(level, 0) + 1
            item["difficulty"] = level
            candidates.append(item)
        return self._deduplicate_candidates(candidates)

    def generate_reference_answer(
        self, question: str, chunk_content: str, source_quote: str = ""
    ) -> str:
        prompt = self.prompts.answer(question, chunk_content, source_quote)
        sys_prompt, user_prompt = prompt.system, prompt.user
        return self._chat(sys_prompt, user_prompt, REFERENCE_ANSWER_TOKENS)


class EnrichmentManager:
    def __init__(
        self,
        db_path: Optional[str] = None,
        llm: Optional[LLMClient] = None,
        validator: Optional["AnswerValidator"] = None,
        verifier: Optional[Any] = None,
        judge: Any = None,
    ):
        """`validator` / `verifier` are anything with `.validate(question, answer, chunk, quote)`.
        The validator checks math chunks; the verifier (verify.PairVerifier) checks prose. Injecting
        only a validator replaces both, which keeps tests free of models.

        `judge` is an optional second opinion on prose pairs that passed the verifier (anything with
        `.check_many([(question, answer, chunk), ...]) -> [(ok, reason), ...]`). None reads QP_VERIFY_JUDGE
        (off unless set to "d1"); False forces it off."""
        logger.info("🚀 Starting Optimized Two-Pass Pipeline...")
        self.db = DBManager(db_path or DB_PATH)
        self.llm = llm or LLMClient(LLAMA_API_URL)
        self._validator = validator  # built on first use: prose chunks never need it
        self.verifier = verifier or (validator if validator is not None else verify.PairVerifier())
        self.judge = verify.judge_from_env() if judge is None else (judge or None)
        if self.judge is not None:
            logger.warning(
                "Judge '%s' is enabled: the text of each chunk, question and answer is sent to an external service.",
                getattr(self.judge, "name", type(self.judge).__name__),
            )

    @property
    def validator(self) -> "AnswerValidator":
        """The lexical → bge → NLI validator, used for math chunks. Loading its models is deferred so a
        run over prose only never pays for it."""
        if self._validator is None:
            self._validator = AnswerValidator()
        return self._validator

    def _process_chunk(self, chunk: Dict, context_str: str) -> Tuple[bool, str]:
        """
        Enrich one chunk. Raises LLMUnavailable if the server fails; in that case nothing is
        left behind for the chunk (no rejection rows, no enrichment row), so it stays pending.
        """
        self.llm.reset_stats()
        try:
            return self._process_chunk_impl(chunk, context_str)
        except LLMUnavailable:
            # get_pending_files() treats an enrichment row as "attempted"; drop it.
            self.db.delete_enrichment(chunk["chunk_id"])
            raise
        finally:
            st = self.llm.stats
            if st["calls"]:
                logger.info(
                    f"Chunk {chunk['chunk_id'][:8]}: {st['calls']} LLM call(s), "
                    f"{st['seconds']:.1f}s, tokens in/out "
                    f"{st['prompt_tokens']}/{st['completion_tokens']}"
                )

    def _process_chunk_impl(self, chunk: Dict, context_str: str) -> Tuple[bool, str]:
        chunk_id = chunk["chunk_id"]
        content = chunk["content"]
        tokens = chunk.get("estimated_tokens", 0)
        ctype = chunk.get("content_type", "prose")

        if chunk.get("should_use") != 1:
            return True, chunk.get("existing_summary", "")

        if chunk.get("existing_summary") and self.db.get_questions_for_chunk(chunk_id):
            return True, chunk.get("existing_summary", "")

        console.rule(
            f"[bold cyan]Chunk {chunk_id[:8]}[/] | {tokens} tokens | type={ctype}"
        )

        meta = self.llm.generate_metadata(
            content, context_str, estimated_tokens=tokens, content_type=ctype
        )
        if not meta:
            if tokens < MIN_TOKENS_FOR_METADATA:
                self.db.save_rejections(
                    chunk_id, [{"reason": "Too short for metadata"}]
                )
                return True, ""
            self.db.save_rejections(
                chunk_id, [{"reason": "Metadata generation failed"}]
            )
            return False, ""

        meta["tags"] = self.llm._normalize_tags(meta.get("tags", []))
        meta["tags"] = self.llm._verify_tags_grounded(meta["tags"], content)
        meta["triplets"] = self.llm._verify_triplets_grounded(
            meta.get("triplets", []), content
        )
        self.db.save_enrichment(chunk_id, meta)

        if tokens < MIN_TOKENS_FOR_QA:
            return True, meta.get("summary", "")

        candidates = self.llm.generate_question_candidates(chunk, context_str)
        all_valid_qa: List[Dict] = []
        rejected_qa: List[Dict] = []

        for i, cand in enumerate(candidates):
            question = cand.get("question", "").strip()
            source_quote = cand.get("source_quote", "").strip()
            level = cand.get("difficulty", "Medium")

            if not question or len(source_quote) < 25:
                rejected_qa.append(
                    {
                        "level": level,
                        "question": question,
                        "answer": "",
                        "reason": "Invalid Pass 1",
                    }
                )
                continue

            if ctype == "math":
                if source_quote.strip() not in content:
                    rejected_qa.append(
                        {
                            "level": level,
                            "question": question,
                            "answer": "",
                            "reason": "Math quote not verbatim",
                        }
                    )
                    continue
            else:
                # The stored quote becomes the exact chunk text, never the model's paraphrase.
                span = verify.locate_quote(source_quote, content)
                if span is None:
                    rejected_qa.append(
                        {
                            "level": level,
                            "question": question,
                            "answer": "",
                            "reason": "Weak quote: not found in chunk",
                        }
                    )
                    continue
                source_quote = cand["source_quote"] = span

            # Combined prompt sets already return the answer with the question.
            answer = (cand.get("answer") or "").strip() or self.llm.generate_reference_answer(
                question, content, source_quote
            )

            if (
                not answer
                or "NOT ENOUGH INFORMATION" in answer.replace("_", " ").upper()
            ):
                rejected_qa.append(
                    {
                        "level": level,
                        "question": question,
                        "answer": answer,
                        "reason": "Pass 2 refused",
                    }
                )
                continue

            if DEFLECTION_PATTERN.search(answer):
                rejected_qa.append(
                    {
                        "level": level,
                        "question": question,
                        "answer": answer,
                        "reason": "Deflection",
                    }
                )
                continue

            checker = self.validator if ctype == "math" else self.verifier
            is_valid, reason = checker.validate(question, answer, content, source_quote)
            if is_valid:
                cand["answer"] = answer
                cand["type"] = DIFFICULTY_TYPE.get(level, "Fact")
                all_valid_qa.append(cand)
            else:
                rejected_qa.append(
                    {
                        "level": level,
                        "question": question,
                        "answer": answer,
                        "reason": reason,
                    }
                )

        if all_valid_qa and self.judge is not None and ctype != "math":
            # Second opinion on the pairs that passed every check. A judge outage is not the pair's fault, so it
            # aborts the file like an LLM outage (nothing recorded, chunks stay pending).
            try:
                verdicts = self.judge.check_many([(c["question"].strip(), c["answer"], content) for c in all_valid_qa])
            except verify.JudgeUnavailable as e:
                raise LLMUnavailable(str(e)) from e
            kept: List[Dict] = []
            for cand, (ok, reason) in zip(all_valid_qa, verdicts):
                if ok:
                    kept.append(cand)
                else:
                    rejected_qa.append(
                        {
                            "level": cand.get("difficulty", "Medium"),
                            "question": cand["question"].strip(),
                            "answer": cand["answer"],
                            "reason": reason,
                        }
                    )
            all_valid_qa = kept

        if all_valid_qa:
            self.db.save_questions(chunk_id, all_valid_qa)
        if rejected_qa:
            self.db.save_rejections(chunk_id, rejected_qa)

        return True, meta.get("summary", "")

    def enrich_single_file(self, file_id: str) -> None:
        """Raises LLMUnavailable (file left pending) if the server is down or stops answering."""
        chunks = self.db.get_chunks_for_file_ordered(file_id)
        if not chunks:
            return
        self.llm.check_health()  # fail fast, before touching any chunk

        chunk_map = {c["chunk_id"]: c["content"] for c in chunks}
        history: Deque[str] = deque(maxlen=3)

        for chunk in chunks:
            ctype = chunk.get("content_type", "prose")
            if ctype in ["table", "math", "code"]:
                parts = []
                prev_id = chunk.get("prev_chunk_id")
                if prev_id and prev_id in chunk_map:
                    parts.append(f"PREV: {chunk_map[prev_id][:150]}")
                next_id = chunk.get("next_chunk_id")
                if next_id and next_id in chunk_map:
                    parts.append(f"NEXT: {chunk_map[next_id][:150]}")
                context_str = (
                    "\n".join(parts) if parts else "No adjacent structural chunks"
                )
            else:
                context_str = "History:\n" + "\n".join([f"- {s}" for s in history])

            success, summary = self._process_chunk(chunk, context_str)

            if (
                success
                and summary
                and not DEFLECTION_PATTERN.search(summary)
                and len(summary.split()) >= MIN_SUMMARY_TOKENS
            ):
                history.append(summary)

    def run(self) -> None:
        done: Set[str] = set()
        while True:
            files = self.db.get_pending_files(limit=5, exclude=list(done))
            if not files:
                break
            done.update(files)
            server_down = False
            with ThreadPoolExecutor(MAX_WORKERS) as ex:
                futures = {
                    ex.submit(self.enrich_single_file, fid): fid for fid in files
                }
                for future in as_completed(futures):
                    try:
                        future.result()
                    except LLMUnavailable as e:
                        logger.error(f"{e}. Stopping; unfinished files stay pending.")
                        server_down = True
                    except Exception as e:
                        logger.error(f"Thread crash: {e}")
            if server_down:
                return


if __name__ == "__main__":
    EnrichmentManager().run()
