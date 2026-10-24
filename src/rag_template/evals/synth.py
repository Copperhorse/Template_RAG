"""
synth.py: extra gold queries written by the LLM, for volume.

For a sample of chunks the model writes one question the chunk answers plus the exact sentence/lines that
answer it. Every generated pair must survive filters before it becomes gold:

    evidence       must be located in the chunk (and is replaced by the exact chunk text), >= 40 chars
    question       5-30 words, no file name, no copied phrase: it may not share any run of
                   `max_shared_words` consecutive words with the passage (this limits the lexical overlap
                   that makes synthetic queries too easy for BM25)
    uniqueness     no near-duplicate question, no duplicate evidence

Caveats worth stating next to any number computed on this set: the question was written *from* the chunk,
so the chunk it came from is the only one labelled relevant even when another also answers it (recall is
underestimated), and the generator shares blind spots with the models being evaluated (it is a small LLM
reading the same text). Report it separately from the hand-written set.
"""

import random
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from rapidfuzz import fuzz

from rag_template import evidence
from rag_template.evals.gold import GoldItem, Query, norm
from rag_template.tokens import count_tokens

WORD = re.compile(r"[a-z0-9_]+")

SYSTEM = "You write realistic search queries. Output ONLY valid JSON."
USER = """\
Below is a passage from a software project ({kind}). Imagine a developer who has NOT seen it and wants to find it.

### PASSAGE
{passage}

### TASK
Write ONE question that this passage answers, and copy the single sentence (or 1-3 consecutive lines of code) that answers it.

### RULES
1. Describe the idea in your own words. Do NOT reuse any phrase of {n} or more consecutive words from the passage.
2. 5 to 30 words. Do not mention file names.
3. "evidence" is copied exactly from the passage, at least 40 characters.

### OUTPUT (JSON only)
{{"question": "...", "evidence": "..."}}
"""


def shared_run(question: str, passage: str, n: int) -> Optional[str]:
    """The first run of `n` consecutive words that appears in both texts, or None."""
    q = WORD.findall(question.lower())
    grams = {" ".join(w[i : i + n]) for w in [WORD.findall(passage.lower())] for i in range(len(w) - n + 1)}
    for i in range(len(q) - n + 1):
        g = " ".join(q[i : i + n])
        if g in grams:
            return g
    return None


@dataclass
class SynthStats:
    attempted: int = 0
    kept: int = 0
    rejected: Dict[str, int] = field(default_factory=dict)

    def reject(self, why: str) -> None:
        self.rejected[why] = self.rejected.get(why, 0) + 1


def sample_chunks(
    chunks: Sequence[Dict], n: int, seed: int = 0, min_tokens: int = 80, max_tokens: int = 400
) -> List[Dict]:
    """Usable chunks of a useful size, half code and half documentation when both exist."""
    pool = [c for c in chunks if c["should_use"] and min_tokens <= count_tokens(c["content"]) <= max_tokens]
    rng = random.Random(seed)
    code = [c for c in pool if c["content_type"] == "code"]
    docs = [c for c in pool if c["content_type"] != "code"]
    rng.shuffle(code), rng.shuffle(docs)
    half = n // 2
    picked = code[:half] + docs[: n - min(half, len(code))]
    picked += [c for c in (code[half:] + docs[n - min(half, len(code)) :]) if c not in picked][
        : max(0, n - len(picked))
    ]
    rng.shuffle(picked)
    return picked[:n]


def accept(
    raw: dict, chunk: Dict, seen_q: List[str], seen_ev: set, stats: SynthStats, max_shared_words: int = 4
) -> Optional[Query]:
    q = str(raw.get("question") or "").strip()
    ev = str(raw.get("evidence") or "").strip()
    if not q or not ev:
        stats.reject("missing question or evidence")
        return None
    exact = evidence.locate(ev, chunk["content"], chunk["content_type"])
    if exact is None or len(exact) < 40:
        stats.reject("evidence not found in the chunk" if exact is None else "evidence too short")
        return None
    words = len(q.split())
    if not 5 <= words <= 30:
        stats.reject("question length")
        return None
    if chunk["source"].split("/")[-1].lower() in q.lower():
        stats.reject("question names the file")
        return None
    if shared_run(q, chunk["content"], max_shared_words):
        stats.reject(f"question copies a {max_shared_words}-word phrase")
        return None
    if any(fuzz.token_sort_ratio(q.lower(), s) > 85 for s in seen_q):
        stats.reject("near-duplicate question")
        return None
    if norm(exact) in seen_ev:
        stats.reject("duplicate evidence")
        return None
    seen_q.append(q.lower())
    seen_ev.add(norm(exact))
    stats.kept += 1
    return Query(
        "",
        q,
        "code" if chunk["content_type"] == "code" else "doc",
        "synthetic",
        True,
        [GoldItem(chunk["source"], exact)],
        [],
        "synthetic",
    )


def generate_queries(
    chunks: Sequence[Dict], llm, n: int = 150, seed: int = 0, max_shared_words: int = 4, on_progress=None
) -> tuple:
    """Returns (queries, stats). `llm` needs `.chat_json(system, user, tokens)`."""
    stats, seen_q, seen_ev, out = SynthStats(), [], set(), []
    for i, chunk in enumerate(sample_chunks(chunks, int(n * 1.6), seed)):
        if len(out) >= n:
            break
        stats.attempted += 1
        kind = "source code" if chunk["content_type"] == "code" else "documentation"
        raw = llm.chat_json(SYSTEM, USER.format(kind=kind, passage=chunk["content"][:3000], n=max_shared_words), 400)
        q = (
            accept(raw, chunk, seen_q, seen_ev, stats, max_shared_words)
            if raw
            else (stats.reject("no parsable JSON") or None)
        )
        if q:
            q.id = f"s{len(out) + 1:03d}"
            out.append(q)
        if on_progress:
            on_progress(i + 1, len(out), stats)
    return out, stats
