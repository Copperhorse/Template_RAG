"""
quotes.py: how tolerant should quote matching be? Measured, not guessed.

Every answerable gold snippet is a real quote. We damage it the way a small model does (one word inserted,
swapped, dropped or replaced) and the way a fabrication would (30% or 50% of the words replaced by other words
from the corpus, or text lifted from a different chunk), then ask the two locators whether they find it in its
chunk:

    strict   verify.locate_quote      exact alphanumeric match, or fuzzy >= 85
    loose    + verify._locate_loose   fuzzy >= 75 and >= 80% of the quote's words present

A good tolerance accepts the slips ("accept" high) and rejects the fabrications ("accept" low). The two groups
overlap at the edges (a quote with half its words replaced can still look like a slip), which is why the answer
gate stores the chunk's real text and checks the answer's support against it.
"""

import random
import re
from typing import Dict, List, Sequence

from rapidfuzz import fuzz

from rag_template.enrichment import verify
from rag_template.evals.gold import Query, norm

MIN_QUOTE_ALNUM = 25  # shorter snippets are skipped: a 12-character "quote" is mostly the identifier itself


def _words(text: str) -> List[str]:
    return text.split()


def mutations(vocab: Sequence[str], rng: random.Random) -> Dict[str, Dict]:
    """name -> {"kind": "slip" | "fabrication", "fn": words -> words}"""

    def swap(w):
        i = len(w) // 2
        return w[:i] + [w[i + 1], w[i]] + w[i + 2 :] if len(w) > 3 else w

    def replace_fraction(frac):
        return lambda w: [rng.choice(vocab) if rng.random() < frac else x for x in w]

    return {
        "one word inserted": {"kind": "slip", "fn": lambda w: w[: len(w) // 2] + ["default"] + w[len(w) // 2 :]},
        "two words swapped": {"kind": "slip", "fn": swap},
        "last 25% cut off": {"kind": "slip", "fn": lambda w: w[: max(3, int(len(w) * 0.75))]},
        "one word dropped": {"kind": "slip", "fn": lambda w: w[: len(w) // 2] + w[len(w) // 2 + 1 :]},
        "one word replaced": {"kind": "slip", "fn": lambda w: w[: len(w) // 2] + [rng.choice(vocab)] + w[len(w) // 2 + 1 :]},
        "30% of words replaced": {"kind": "fabrication", "fn": replace_fraction(0.3)},
        "50% of words replaced": {"kind": "fabrication", "fn": replace_fraction(0.5)},
        "text of another chunk": {"kind": "fabrication", "fn": None},
    }


def run_quote_tolerance(queries: Sequence[Query], chunks: Sequence[Dict], seed: int = 0) -> List[Dict]:
    rng = random.Random(seed)
    usable = [c for c in chunks if c["should_use"]]
    vocab = [w for c in usable for w in re.findall(r"[A-Za-z]{5,}", c["content"])]
    cases = []
    for q in queries:
        if not q.answerable or not q.gold or len(norm(q.gold[0].snippet)) < MIN_QUOTE_ALNUM:
            continue
        g = q.gold[0]
        home = next((c for c in usable if c["source"] == g.file and norm(g.snippet) in norm(c["content"])), None)
        if home:
            cases.append((g.snippet, home))
    rows = []
    for name, m in mutations(vocab, rng).items():
        scores, accepted_strict, accepted_loose, n = [], 0, 0, 0
        for snippet, home in cases:
            code = home["content_type"] == "code"
            if m["fn"] is None:
                other = rng.choice([c for c in usable if c["source"] != home["source"] and len(c["content"]) > 200])
                text = other["content"][: len(snippet) + 10]
            else:
                text = " ".join(m["fn"](_words(snippet)))
                if norm(text) == norm(snippet):
                    continue  # the damage was a no-op (a very short snippet): not a test case
            n += 1
            scores.append(fuzz.partial_ratio(norm(text), norm(home["content"])))
            accepted_strict += verify.locate_quote_ex(text, home["content"], code=code) is not None
            accepted_loose += verify.locate_quote_ex(text, home["content"], code=code, loose=True) is not None
        scores.sort()
        rows.append({
            "damage": name, "kind": m["kind"], "n": n,
            "median_score": scores[len(scores) // 2] if scores else 0.0, "max_score": scores[-1] if scores else 0.0,
            "strict_accepts": accepted_strict / n if n else 0.0, "loose_accepts": accepted_loose / n if n else 0.0,
        })
    return rows


def markdown(rows: Sequence[Dict]) -> str:
    out = ["| damage | kind | n | median match score | max | strict accepts | loose accepts |", "|---|---|---:|---:|---:|---:|---:|"]
    for r in rows:
        out.append(f"| {r['damage']} | {r['kind']} | {r['n']} | {r['median_score']:.0f} | {r['max_score']:.0f} | {100 * r['strict_accepts']:.0f}% | {100 * r['loose_accepts']:.0f}% |")
    return "\n".join(out)
