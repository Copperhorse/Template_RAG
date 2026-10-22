"""
gates.py: adversarial test of the answer gates, no model needed.

For each answerable gold query we build a *clean* scenario (three sources: the chunk that holds the gold
snippet plus two distractors of the same kind; an answer and quote copied from the gold snippet) and check
that the gate accepts it. Then we corrupt it in one specific way and check the gate's verdict:

    expect "flag"    the corruption is a defect the gates are supposed to catch
    expect "accept"  the change is legitimate (a lightly re-typed quote) and must NOT be flagged
    informational    behaviour we want to know, whichever way it goes (a paraphrase, a negation)

The whole path is exercised (`Answerer.ask` with a fake LLM that returns the crafted JSON), so quote
location, citation parsing and the support checks are all in play. Clean answers here are easy by
construction; the false-reject rate on *real* model answers is measured by `evals answers`.
"""

import builtins
import json
import keyword
import random
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from rag_template.enrichment.llm import LLMClient
from rag_template.evals.gold import Query, norm
from rag_template.retrieve import Answerer, Hit, source_id

IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]{3,}")
_BUILTIN_NAMES = frozenset(dir(builtins)) | frozenset(keyword.kwlist)  # the gate allows these without evidence


@dataclass
class Scenario:
    query: Query
    hits: List[Hit]  # hits[0] holds the gold snippet
    snippet: str
    answer: str  # clean, ends with the [S1] citation
    kind: str  # code | doc


class _Retriever:
    def __init__(self, hits):
        self.hits = hits

    def search(self, *a, **kw):
        return self.hits

    def span_scorer(self):
        """Word overlap with the query: a deterministic stand-in for the cross-encoder (used by the extraction fallback)."""
        def score(query, texts):
            q = set(re.findall(r"\w+", query.lower()))
            return [float(len(q & set(re.findall(r"\w+", t.lower())))) for t in texts]
        return score


class _LLM:
    def __init__(self, reply):
        self.reply = reply

    def chat_json(self, system, user, tokens, schema=None):
        return LLMClient.extract_json(self.reply)


def _hit(row: Dict) -> Hit:
    return Hit(row["chunk_id"], row.get("doc_id", ""), row["source"], 1.0, row["content"], row.get("breadcrumb") or row["source"],
               row["content_type"], row.get("metadata", {}))


def _clean_answer(snippet: str, kind: str) -> str:
    if kind == "code":
        idents = [i for i in dict.fromkeys(IDENT.findall(snippet)) if i not in ("self", "return", "else", "elif", "None", "True", "False", "import", "from", "class")]
        picked = " and ".join(f"`{i}`" for i in idents[:2]) or "`value`"
        return f"The code defines {picked} [S1]."
    text = re.sub(r"[`*|]+", " ", snippet)
    text = re.sub(r"\s+", " ", text).strip()
    return f"{text} [S1]" if text.endswith((".", "!", "?")) else f"{text}. [S1]"


def build_scenarios(queries: Sequence[Query], chunks: Sequence[Dict], seed: int = 0) -> List[Scenario]:
    rng = random.Random(seed)
    usable = [c for c in chunks if c["should_use"]]
    out = []
    for q in queries:
        if not q.answerable or not q.gold:
            continue
        g = q.gold[0]
        gn = norm(g.snippet)
        home = next((c for c in usable if c["source"] == g.file and gn in norm(c["content"])), None)
        if home is None:
            continue
        kind = "code" if q.type == "code" else "doc"
        others = [c for c in usable if c["source"] != g.file]
        same_kind = [c for c in others if (c["content_type"] == "code") == (kind == "code")]
        # prefer same-kind, substantial chunks; fall back to looser pools so a small corpus still works
        pool = next((p for p in ([c for c in same_kind if len(c["content"]) > 120], same_kind, others) if len(p) >= 2), None)
        if pool is None:
            continue
        distractors = rng.sample(pool, 2)
        out.append(Scenario(q, [_hit(home), *map(_hit, distractors)], g.snippet, _clean_answer(g.snippet, kind), kind))
    return out


def _sentence_or_line(hit: Hit) -> str:
    """A verbatim, quotable span of a distractor chunk (>= 40 chars)."""
    lines = [ln.strip() for ln in hit.content.splitlines() if len(ln.strip()) >= 40 and not ln.strip().startswith(("#", "```", "|--"))]
    if lines:
        return lines[len(lines) // 2]
    return hit.content.strip()[:120]


def _reply(answer: str, quotes: Sequence[Tuple[int, str]]) -> str:
    return json.dumps({"answer": answer, "quotes": [{"source": source_id(n), "quote": q} for n, q in quotes]})


def _bump_number(answer: str) -> Optional[str]:
    """Change the first number in the answer's text (not in its [S1] citation) by +7; None if it has none."""
    body, cite = re.match(r"^(.*?)(\s*\[S\d+\]\.?)?$", answer, re.S).groups()
    m = re.search(r"(?<![\w.])\d+(?![\w])", body)
    if not m:
        return None
    return body[: m.start()] + str(int(m.group()) + 7) + body[m.end():] + (cite or "")


def _negate(answer: str) -> Optional[str]:
    for a, b in ((" is ", " is not "), (" are ", " are not "), (" uses ", " does not use "), (" returns ", " never returns "), (" must ", " must never ")):
        if a in answer:
            return answer.replace(a, b, 1)
    return None


def _swap_word(snippet: str) -> str:
    words = IDENT.findall(snippet)
    return snippet.replace(max(words, key=len), "banana", 1) if words else snippet


def _foreign_identifier(s: "Scenario") -> str:
    """A real, non-builtin identifier from a distractor chunk that does not occur in the gold snippet."""
    for h in s.hits[1:]:
        for ident in IDENT.findall(h.content):
            if ident not in _BUILTIN_NAMES and ident not in s.snippet:
                return ident
    return "other_helper"


@dataclass
class Corruption:
    name: str
    expect: str  # flag | accept | info
    describe: str
    make: Callable[[Scenario], Optional[Tuple[str, List[Tuple[int, str]]]]]  # -> (answer, quotes) or None if not applicable


def _lenient(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", s.lower())).strip()


CORRUPTIONS: List[Corruption] = [
    Corruption("clean", "accept", "answer and quote copied from the gold snippet", lambda s: (s.answer, [(1, s.snippet)])),
    Corruption("quote_retyped", "accept", "the real quote, lower-cased with punctuation and spacing dropped", lambda s: (s.answer, [(1, _lenient(s.snippet))])),
    Corruption("fabricated_quote", "flag", "quote replaced by text from an unrelated chunk", lambda s: (s.answer, [(1, _sentence_or_line(s.hits[1]))])),
    Corruption("quote_from_wrong_source", "flag", "real text, but taken from source 2 while citing source 1", lambda s: (s.answer, [(1, _sentence_or_line(s.hits[1]))])),
    Corruption("no_quotes", "flag", "answer cites [S1] but gives no quotes", lambda s: (s.answer, [])),
    Corruption("no_citation", "flag", "good quote, but the answer cites nothing", lambda s: (s.answer.replace(" [S1]", ""), [(1, s.snippet)])),
    Corruption("nonexistent_citation", "flag", "answer cites [S9]", lambda s: (s.answer.replace("[S1]", "[S9]"), [(1, s.snippet)])),
    Corruption("wrong_number", "flag", "a number in the answer changed (+7)", lambda s: (lambda a: (a, [(1, s.snippet)]) if a else None)(_bump_number(s.answer))),
    Corruption("invented_identifier", "flag", "answer adds a `backticked` name that exists nowhere", lambda s: (s.answer.replace(" [S1]", " It also calls `legacy_sync_worker`. [S1]"), [(1, s.snippet)])),
    Corruption("answer_from_other_source", "flag", "answer is text from an unrelated chunk, with a real quote for the right one",
               lambda s: (re.sub(r"\s+", " ", re.sub(r"[`*|]+", " ", _sentence_or_line(s.hits[1]))).strip() + " [S1]" if s.kind == "doc" else f"The code defines `{_foreign_identifier(s)}` [S1].", [(1, s.snippet)])),
    Corruption("paraphrased_quote", "info", "the real quote with its longest word replaced by 'banana' (fuzzy match tolerance)", lambda s: (s.answer, [(1, _swap_word(s.snippet))])),
    Corruption("negation", "info", "the answer asserts the opposite (is -> is not); the quote is unchanged", lambda s: (lambda a: (a, [(1, s.snippet)]) if a else None)(_negate(s.answer))),
    Corruption("fluent_unsupported_claim", "info", "a plausible extra sentence with no numbers or names", lambda s: (s.answer.replace(" [S1]", " This approach is widely considered best practice in modern production systems. [S1]"), [(1, s.snippet)])),
]


@dataclass
class GateReport:
    rows: List[Dict] = field(default_factory=list)  # one per corruption; "by_policy" maps policy -> {n, flagged, flag_rate}
    examples: Dict[str, List[str]] = field(default_factory=dict)
    policies: List[str] = field(default_factory=list)

    def markdown(self) -> str:
        lines = ["| corruption | n | expected | " + " | ".join(f"{p}: flagged" for p in self.policies) + " | what it is |", "|---|---:|---|" + "---:|" * len(self.policies) + "---|"]
        for r in self.rows:
            exp = {"flag": "flag", "accept": "accept", "info": "info"}[r["expect"]]
            cells = []
            for p in self.policies:
                d = r["by_policy"][p]
                rate = f"{100 * d['flag_rate']:.0f}%"
                bad = (r["expect"] == "flag" and d["flag_rate"] < 1.0) or (r["expect"] == "accept" and d["flag_rate"] > 0.0)
                cells.append(f"**{rate}**" if bad else rate)
            lines.append(f"| {r['name']} | {r['n']} | {exp} | " + " | ".join(cells) + f" | {r['describe']} |")
        return "\n".join(lines) + "\n\nBold = the gate did not do what that row expects (a `flag` row below 100%, an `accept` row above 0%)."


def run_gate_eval(scenarios: Sequence[Scenario], policies: Sequence[str] = ("strict", "tolerant", "balanced", "lenient"), **answerer_kw) -> GateReport:
    report = GateReport(policies=list(policies))
    for c in CORRUPTIONS:
        by_policy, n = {}, 0
        missed: List[str] = []
        for policy in policies:
            flagged, n = 0, 0
            for s in scenarios:
                made = c.make(s)
                if made is None:
                    continue
                answer, quotes = made
                ans = Answerer(_Retriever(s.hits), _LLM(_reply(answer, quotes)), policy=policy, **answerer_kw).ask(s.query.query)
                n += 1
                is_flagged = not ans.grounded
                flagged += is_flagged
                wrong = is_flagged if c.expect == "accept" else (not is_flagged if c.expect == "flag" else False)
                if wrong and len(missed) < 4:
                    missed.append(f"[{policy}] {s.query.id}: {ans.reason or 'accepted'} | answer={answer[:90]!r}")
            by_policy[policy] = {"n": n, "flagged": flagged, "flag_rate": flagged / n if n else 0.0}
        first = by_policy[policies[0]]
        report.rows.append({"name": c.name, "expect": c.expect, "describe": c.describe, "n": n, "flagged": first["flagged"], "flag_rate": first["flag_rate"], "by_policy": by_policy})
        report.examples[c.name] = missed
    return report
