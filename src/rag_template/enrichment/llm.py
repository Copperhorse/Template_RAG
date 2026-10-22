"""
llm.py: a hardened client for any OpenAI-compatible chat server, plus the enrichment calls built on it.

Hardening (the openai defaults are a 10 minute read timeout and 2 retries, which lets one hung
server stall a run for half an hour per call):
  * short timeouts and one retry, configurable in LLMSettings
  * `LLMUnavailable` for anything that says nothing about the chunk being processed: connection
    errors, timeouts, 429, 5xx. Callers must NOT record a rejection for it; they stop and leave the
    work pending so a later run retries. Any other error (a 400 for one oversized request) is the
    request's problem and yields "".
  * reasoning models: every request allows `reasoning_budget + answer tokens`; <think> blocks that
    leak into `content` are stripped (an unterminated one means the budget ran out mid-thought)
  * JSON from small models is parsed strictly, then repaired, then given up on (returns {})
"""

import json
import logging
import re
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

import httpx
import openai
from json_repair import repair_json
from openai import OpenAI
from rapidfuzz import fuzz

from rag_template.config import LLMSettings
from rag_template.enrichment.prompts import PromptSet, get_prompt_set

logger = logging.getLogger("rag_template.llm")

MIN_TOKENS_FOR_METADATA = 30
DEDUP_SIMILARITY_THRESHOLD = 80  # token_sort_ratio above this = the same question
DEDUP_QUOTE_THRESHOLD = 90  # partial_ratio above this = the same evidence


class LLMUnavailable(RuntimeError):
    """The LLM server could not be reached, timed out, or answered with a 5xx / 429."""


_THINK_BLOCK = re.compile(r"<think>.*?(?:</think>|$)", re.DOTALL | re.IGNORECASE)


def strip_thinking(content: str) -> str:
    return _THINK_BLOCK.sub("", content).strip()


def ensure_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, list) and len(value) == 1 and isinstance(value[0], dict):
        logger.warning("JSON parsed as single-element list: unwrapping to dict")
        return value[0]
    if isinstance(value, list) and value:
        logger.warning(f"JSON parsed as list with {len(value)} elements, expected a dict. Returning empty.")
    return {}


def questions_per_level(estimated_tokens: int) -> int:
    """How many questions to ask for at each difficulty: small chunks hold fewer distinct facts."""
    if estimated_tokens < 80:
        return 1
    if estimated_tokens < 200:
        return 2
    return 3


class LLMClient:
    def __init__(self, settings: Optional[LLMSettings] = None, prompts: Optional[PromptSet] = None):
        self.settings = settings or LLMSettings()
        s = self.settings
        self.prompts = prompts or get_prompt_set()
        self.client = OpenAI(
            base_url=s.base_url,
            api_key=s.api_key,
            timeout=httpx.Timeout(s.timeout_s, connect=5.0),
            max_retries=s.max_retries,
        )
        self.stats = self._empty_stats()

    # ------------------------------------------------------------------ transport

    @staticmethod
    def _empty_stats() -> Dict[str, float]:
        return {"calls": 0, "seconds": 0.0, "prompt_tokens": 0, "completion_tokens": 0}

    def reset_stats(self) -> None:
        self.stats = self._empty_stats()

    def _max_tokens(self, answer_tokens: int) -> int:
        s = self.settings
        budget = s.reasoning_budget if s.reasoning_budget >= 0 else s.unlimited_reasoning_cap
        return budget + answer_tokens

    def check_health(self) -> None:
        """Raise LLMUnavailable unless the server answers /models right now."""
        try:
            self.client.with_options(timeout=self.settings.health_timeout_s, max_retries=0).models.list()
        except openai.APIError as e:
            raise LLMUnavailable(f"LLM server is not responding: {e}") from e

    def chat(self, system: str, user: str, answer_tokens: int, json_mode: bool = False, response_format: Optional[Dict[str, Any]] = None) -> str:
        """One chat completion; the text of `message.content` only (`reasoning_content` is never
        parsed); "" when the model produced no usable content."""
        s = self.settings
        started = time.monotonic()
        try:
            response = self.client.chat.completions.create(
                model=s.model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=s.temperature,
                max_tokens=self._max_tokens(answer_tokens),
                **({"extra_body": s.extra_body} if s.extra_body else {}),
                **({"response_format": response_format} if response_format else ({"response_format": {"type": "json_object"}} if json_mode else {})),
            )
        except (openai.APIConnectionError, openai.RateLimitError) as e:  # APITimeoutError is a subclass
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
            logger.warning(f"LLM hit max_tokens ({self._max_tokens(answer_tokens)}) after {elapsed:.1f}s; output may be empty or cut off")
        return strip_thinking(choice.message.content or "")

    def response_format_for(self, schema: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """The response_format to send, from LLMSettings.json_mode: the caller's schema in "schema" mode, plain JSON
        in "json_object" mode (and in "schema" mode when the caller has no schema), nothing when "off"."""
        mode = self.settings.json_mode
        mode = "json_object" if mode is True else ("off" if mode is False else str(mode))
        if mode == "schema" and schema:
            return {"type": "json_schema", "json_schema": {"name": "reply", "strict": True, "schema": schema}}
        if mode in ("json_object", "schema"):
            return {"type": "json_object"}
        return None

    def chat_json(self, system: str, user: str, answer_tokens: int, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.extract_json(self.chat(system, user, answer_tokens, response_format=self.response_format_for(schema)))

    @staticmethod
    def extract_json(text: str) -> Dict[str, Any]:
        fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
        raw = fenced.group(1) if fenced else text
        try:
            result = ensure_dict(json.loads(raw))
            if result:
                return result
        except json.JSONDecodeError:
            pass
        try:
            result = ensure_dict(repair_json(raw, return_objects=True))
            if result:
                return result
        except Exception as e:
            logger.debug(f"repair_json failed: {e}")
        logger.error(f"JSON Parse Error: unrecoverable | Raw: {text[:100]}...")
        return {}

    # ------------------------------------------------------------------ post-processing

    @staticmethod
    def deduplicate_candidates(candidates: List[Dict]) -> List[Dict]:
        seen_qs: List[str] = []
        seen_quotes: List[str] = []
        unique: List[Dict] = []
        for cand in candidates:
            if not isinstance(cand, dict):
                continue
            q = str(cand.get("question", "")).lower().strip()
            quote = str(cand.get("source_quote", "")).lower().strip()
            if not q:
                continue
            if any(fuzz.token_sort_ratio(q, s) > DEDUP_SIMILARITY_THRESHOLD for s in seen_qs):
                continue
            if quote and any(fuzz.partial_ratio(quote, sq) > DEDUP_QUOTE_THRESHOLD for sq in seen_quotes):
                continue
            seen_qs.append(q)
            if quote:
                seen_quotes.append(quote)
            unique.append(cand)
        return unique

    @staticmethod
    def normalize_tags(tags: List[str]) -> List[str]:
        def to_snake(tag: str) -> str:
            s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", tag.strip())
            return re.sub(r"[\s\-]+", "_", s).lower()

        seen, result = set(), []
        for raw in tags if isinstance(tags, list) else []:
            if not isinstance(raw, str) or not raw.strip():
                continue
            tag = to_snake(raw)
            if tag not in seen:
                seen.add(tag)
                result.append(tag)
        return result

    @staticmethod
    def verify_tags_grounded(tags: List[str], text: str) -> List[str]:
        """Keep tags whose words appear in the text (a tag the model invented is noise in retrieval)."""
        low = text.lower()
        return [t for t in tags if t.replace("_", " ") in low or t in low]

    @staticmethod
    def verify_triplets_grounded(triplets: List[Dict], text: str) -> List[Dict]:
        low = text.lower()
        out = []
        for t in triplets if isinstance(triplets, list) else []:
            if not isinstance(t, dict):
                continue
            subj = str(t.get("subject", "")).lower().strip()
            obj = str(t.get("object", "")).lower().strip()
            if subj and obj and subj in low and obj in low:
                out.append(t)
        return out

    # ------------------------------------------------------------------ enrichment calls

    def generate_metadata(self, text: str, context: str, estimated_tokens: int = 150, content_type: str = "prose") -> Dict[str, Any]:
        if estimated_tokens < MIN_TOKENS_FOR_METADATA:
            return {}
        p = self.prompts.metadata(text, context, content_type)
        return self.chat_json(p.system, p.user, self.settings.metadata_answer_tokens)

    def generate_question_candidates(self, chunk: Dict, context: str) -> List[Dict]:
        per_level = questions_per_level(chunk.get("estimated_tokens", 150))
        ctype = chunk.get("content_type", "prose")
        if self.prompts.combined:
            return self._generate_combined(chunk, context, per_level, ctype)

        candidates: List[Dict] = []
        for difficulty, instruction in self.prompts.difficulty_instructions(ctype).items():
            p = self.prompts.questions(chunk["content"], context, difficulty, instruction, per_level, ctype)
            result = self.chat_json(p.system, p.user, self.settings.questions_answer_tokens)
            raw = result.get("qa_pairs", [])
            if not raw and result:  # flat {"question1": ..., "source_quote1": ...} from a confused model
                groups: Dict[str, Dict] = defaultdict(dict)
                for k, v in result.items():
                    m = re.match(r"^(question|source_quote)(\d*)$", k)
                    if m:
                        groups[m.group(2)][m.group(1)] = v
                raw = [g for g in groups.values() if "question" in g]
            count = 0
            for item in raw if isinstance(raw, list) else []:
                if count >= per_level:
                    break
                if isinstance(item, dict):
                    item["difficulty"] = difficulty
                    candidates.append(item)
                    count += 1
        return self.deduplicate_candidates(candidates)

    def _generate_combined(self, chunk: Dict, context: str, per_level: int, ctype: str) -> List[Dict]:
        p = self.prompts.combined_qa(chunk["content"], context, per_level, ctype)
        result = self.chat_json(p.system, p.user, 600 + 350 * per_level * 3)
        raw = result.get("qa_pairs", [])
        levels = list(self.prompts.difficulty_instructions(ctype))
        counts: Dict[str, int] = {}
        out: List[Dict] = []
        for item in raw if isinstance(raw, list) else []:
            if not isinstance(item, dict):
                continue
            level = str(item.get("difficulty", "")).strip().capitalize()
            if level not in levels or counts.get(level, 0) >= per_level:
                continue
            counts[level] = counts.get(level, 0) + 1
            item["difficulty"] = level
            out.append(item)
        return self.deduplicate_candidates(out)

    def generate_reference_answer(self, question: str, chunk_content: str, source_quote: str = "", content_type: str = "prose") -> str:
        p = self.prompts.answer(question, chunk_content, source_quote, content_type)
        return self.chat(p.system, p.user, self.settings.reference_answer_tokens)
