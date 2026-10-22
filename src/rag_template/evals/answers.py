"""
answers.py: answer-level evaluation against a running LLM.

Retrieval quality says nothing about whether the answer step behaves. For every gold query we run the full
`Answerer` and record what the gates decided, then relate that to ground truth:

  answerable queries     answered? gate verdict? does the answer contain the expected fact (`answer_contains`)?
                         does it cite a chunk that really holds the gold snippet (attribution)? was the gold
                         chunk in the context at all (context recall)?
  unanswerable queries   did it refuse? if it answered anyway, did the gates flag it?

and the question the gates exist for: among answers that passed the gates, how often is the fact right,
compared with answers the gates flagged? "Correct" is a substring check on a hand-written key phrase, a
coarse proxy that misses correct answers worded differently, so read the rates as lower bounds.
"""

import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from rapidfuzz import fuzz

from rag_template.evals.gold import Query, covered_items, norm
from rag_template.evals.metrics import wilson_interval
from rag_template.retrieve import REFUSAL, Answer, Answerer, answer_schema


@dataclass
class AnswerRecord:
    id: str
    query: str
    answerable: bool
    type: str
    refused: bool
    grounded: bool
    reason: str
    text: str
    citations: List[int]
    n_quotes: int
    n_unverified: int
    context_has_gold: Optional[bool]
    cites_gold: Optional[bool]
    correct: Optional[bool]
    latency_s: float
    sources: List[str] = field(default_factory=list)
    dropped: List[Dict[str, Any]] = field(default_factory=list)  # quotes the gate could not locate: claimed text + best fuzzy score
    reply: Dict[str, Any] = field(default_factory=dict)  # the model's parsed JSON reply, so any policy can be replayed offline
    context: List[Dict[str, Any]] = field(default_factory=list)  # the sources it saw: label, content, content_type, metadata
    how: List[str] = field(default_factory=list)  # how each verified quote matched: exact | fuzzy | loose | extracted


def is_correct(text: str, keys: Sequence[str]) -> Optional[bool]:
    if not keys:
        return None
    t = norm(text)
    return any(norm(k) in t for k in keys if norm(k))


def _snapshot(hits) -> List[Dict[str, Any]]:
    return [{"label": h.label, "source": h.source, "content": h.content, "content_type": h.content_type, "metadata": h.metadata,
             "rerank_score": h.rerank_score, "dense_score": h.dense_score} for h in hits]


def run_answer_eval(retriever, llm, queries: Sequence[Query], k: int = 5, on_record=None, policy: str = "strict", quotes_first: bool = False, **search_kw) -> List[AnswerRecord]:
    """Retrieve, ask the model, gate the reply. The raw reply and the sources are stored in each record."""
    answerer = Answerer(retriever, llm, policy=policy, quotes_first=quotes_first)
    out: List[AnswerRecord] = []
    for q in queries:
        started = time.monotonic()
        hits = retriever.search(q.query, k=k, **search_kw)
        reply: Dict[str, Any] = {}
        if hits:
            prompt, shown = answerer.build_prompt(q.query, hits)
            hits = hits[:shown]
            reply = llm.chat_json(answerer.system, prompt, answerer.answer_tokens, schema=answer_schema(quotes_first, shown))
            a = answerer.judge(reply, hits, q.query)
        else:
            a = Answer(REFUSAL, [], reason="nothing relevant was retrieved", refused=True)
        latency = time.monotonic() - started
        rec = _record(q, a, latency, reply)
        out.append(rec)
        if on_record:
            on_record(rec)
    return out


def _record(q: Query, a: Answer, latency: float, reply: Dict[str, Any]) -> AnswerRecord:
    ctx_gold = cites_gold = None
    if q.answerable:
        ctx_gold = any(covered_items(q, h.source, h.content) for h in a.sources)
        cited = [a.sources[n - 1] for n in a.citations if 1 <= n <= len(a.sources)]
        cites_gold = any(covered_items(q, h.source, h.content) for h in cited)
    dropped = []
    for n, claimed in a.unverified_quotes:
        src = a.sources[n - 1].content if 1 <= n <= len(a.sources) else ""
        score = fuzz.partial_ratio(norm(claimed), norm(src)) if src else 0.0
        dropped.append({"source": n, "claimed": claimed[:240], "best_match_score": round(score, 1)})
    return AnswerRecord(
        q.id, q.query, q.answerable, q.type, a.refused, a.grounded, a.reason, a.text, a.citations,
        len(a.quotes), len(a.unverified_quotes), ctx_gold, cites_gold,
        None if a.refused or not q.answerable else is_correct(a.text, q.answer_contains), 0.0 if latency is None else latency,
        [h.label for h in a.sources], dropped, reply, _snapshot(a.sources), [x.how for x in a.quotes],
    )


def regate(records: Sequence[AnswerRecord], queries: Sequence[Query], retriever, policy, min_relevance: Optional[float] = None) -> List[AnswerRecord]:
    """Re-judge every recorded reply under `policy` (no LLM call): same model output, different gate. With `min_relevance`
    the pre-LLM relevance gate is applied first, exactly as `Answerer.ask` would: a query whose best reranker score is
    below it is refused and the recorded reply is ignored."""
    from rag_template.retrieve import Hit

    by_id = {q.id: q for q in queries}
    answerer = Answerer(retriever, llm=None, policy=policy, min_relevance=min_relevance)
    out = []
    for r in records:
        if not r.context:  # nothing was retrieved: the verdict does not depend on the policy
            out.append(r)
            continue
        hits = [Hit("", "", c["source"], 1.0, c["content"], c["label"], c["content_type"], c["metadata"], rerank_score=c.get("rerank_score"),
                    dense_score=c.get("dense_score")) for c in r.context]
        a = answerer.relevance_refusal(hits) or answerer.judge(r.reply, hits, r.query)
        out.append(_record(by_id[r.id], a, r.latency_s, r.reply))
    return out


def policy_table(runs: Dict[str, Sequence[AnswerRecord]]) -> List[Dict[str, Any]]:
    """One row per policy. "False alarm" = the gate flagged an answer that contains the expected fact; "missed" = the
    gate passed an answer that does not (both need a hand-written key phrase, so they are lower bounds)."""
    rows = []
    for name, recs in runs.items():
        ans = [r for r in recs if r.answerable and not r.refused]
        labelled = [r for r in ans if r.correct is not None]
        right, wrong = [r for r in labelled if r.correct], [r for r in labelled if not r.correct]
        una = [r for r in recs if not r.answerable]
        total = [r for r in recs if r.answerable]
        rows.append({
            "policy": name, "answered": len(ans),
            "flag_rate": _rate(sum(not r.grounded for r in ans), len(ans)),
            "false_alarm": _rate(sum(not r.grounded for r in right), len(right)),
            "missed_error": _rate(sum(r.grounded for r in wrong), len(wrong)),
            "usable": _rate(sum(bool(r.correct) and r.grounded for r in labelled), len(total)),  # correct AND accepted, of all answerable
            "cites_gold_of_passed": _rate(sum(bool(r.cites_gold) for r in ans if r.grounded), sum(r.grounded for r in ans)),
            # needs no key phrase: accepted AND citing a chunk that holds the gold evidence, of all answerable queries
            "attributed": _rate(sum(bool(r.cites_gold) and r.grounded for r in ans), len(total)),
            "unanswerable_passed": _rate(sum((not r.refused) and r.grounded for r in una), len(una)),
        })
    return rows


def load_records(path: str) -> List["AnswerRecord"]:
    import json

    return [AnswerRecord(**r) for r in json.load(open(path))["records"]]


def policy_markdown(rows: Sequence[Dict[str, Any]]) -> str:
    def c(d):
        return f"{100 * d['rate']:.0f}% ({d['k']}/{d['n']})"

    head = "| policy | answered | flagged | false alarms (correct answers flagged) | errors missed (wrong answers passed) | usable (correct and accepted) | accepted and citing the gold chunk | unanswerable that passed |\n|---|---:|---:|---:|---:|---:|---:|---:|"
    return head + "\n" + "\n".join(f"| {r['policy']} | {r['answered']} | {c(r['flag_rate'])} | {c(r['false_alarm'])} | {c(r['missed_error'])} | {c(r['usable'])} | {c(r['attributed'])} | {c(r['unanswerable_passed'])} |" for r in rows)


def _rate(num: int, den: int) -> Dict[str, float]:
    p, lo, hi = wilson_interval(num, den)
    return {"n": den, "k": num, "rate": p, "lo": lo, "hi": hi}


def summarize(records: Sequence[AnswerRecord]) -> Dict[str, Any]:
    ans = [r for r in records if r.answerable]
    una = [r for r in records if not r.answerable]
    answered = [r for r in ans if not r.refused]
    labelled = [r for r in answered if r.correct is not None]
    passed = [r for r in labelled if r.grounded]
    flagged = [r for r in labelled if not r.grounded]
    out: Dict[str, Any] = {
        "answerable": {
            "n": len(ans),
            "context_recall": _rate(sum(bool(r.context_has_gold) for r in ans), len(ans)),
            "answered": _rate(len(answered), len(ans)),
            "refused": _rate(len(ans) - len(answered), len(ans)),
            "grounded_given_answered": _rate(sum(r.grounded for r in answered), len(answered)),
            "correct_given_answered": _rate(sum(bool(r.correct) for r in labelled), len(labelled)),
            "cites_gold_given_answered": _rate(sum(bool(r.cites_gold) for r in answered), len(answered)),
            "correct_given_gates_passed": _rate(sum(bool(r.correct) for r in passed), len(passed)),
            "correct_given_gates_flagged": _rate(sum(bool(r.correct) for r in flagged), len(flagged)),
        },
        "unanswerable": {
            "n": len(una),
            "refused": _rate(sum(r.refused for r in una), len(una)),
            "answered_and_flagged": _rate(sum((not r.refused) and not r.grounded for r in una), len(una)),
            "answered_and_passed_gates": _rate(sum((not r.refused) and r.grounded for r in una), len(una)),
        },
        "strict_mode": {  # what `ask(strict=True)` would have returned: a flagged answer becomes a refusal
            "answerable_answered": _rate(sum((not r.refused) and r.grounded for r in ans), len(ans)),
            "answerable_correct": _rate(sum(bool(r.correct) and r.grounded for r in labelled), len(labelled)),
            "unanswerable_refused": _rate(sum(r.refused or not r.grounded for r in una), len(una)),
        },
        "latency_s": {"mean": sum(r.latency_s for r in records) / max(1, len(records)), "max": max((r.latency_s for r in records), default=0.0)},
        "flag_reasons": {},
    }
    for r in records:
        if not r.grounded and not r.refused:
            key = r.reason.split(":")[0][:60]
            out["flag_reasons"][key] = out["flag_reasons"].get(key, 0) + 1
    return out


def markdown(summary: Dict[str, Any], records: Sequence[AnswerRecord]) -> str:
    def r(d):
        return f"{100 * d['rate']:.0f}% ({d['k']}/{d['n']}; 95% CI {100 * d['lo']:.0f}-{100 * d['hi']:.0f})"

    a, u, s = summary["answerable"], summary["unanswerable"], summary["strict_mode"]
    lines = [
        "# Answer-level evaluation", "",
        f"{a['n']} answerable and {u['n']} unanswerable queries. Rates are Wilson 95% intervals. "
        f"\"Correct\" = the answer contains a hand-written key phrase, so it is a lower bound.", "",
        "## Answerable queries", "",
        f"- gold chunk was in the context the model saw: {r(a['context_recall'])}",
        f"- answered (did not refuse): {r(a['answered'])}",
        f"- answered and cites a chunk that holds the gold snippet: {r(a['cites_gold_given_answered'])}",
        f"- answered and contains the expected fact: {r(a['correct_given_answered'])}",
        f"- answered and passed every gate: {r(a['grounded_given_answered'])}", "",
        "## Do the gates discriminate?", "",
        f"- correct, among answers that **passed** the gates: {r(a['correct_given_gates_passed'])}",
        f"- correct, among answers the gates **flagged**: {r(a['correct_given_gates_flagged'])}", "",
        "## Unanswerable queries (the right behaviour is to refuse)", "",
        f"- refused: {r(u['refused'])}",
        f"- answered but flagged by the gates: {r(u['answered_and_flagged'])}",
        f"- answered and passed the gates (the dangerous case): {r(u['answered_and_passed_gates'])}", "",
        "## If `strict=True` were used (flagged answers become refusals)", "",
        f"- answerable queries answered: {r(s['answerable_answered'])}",
        f"- answerable queries answered correctly: {r(s['answerable_correct'])}",
        f"- unanswerable queries refused: {r(s['unanswerable_refused'])}", "",
        f"Mean latency {summary['latency_s']['mean']:.1f}s per question. Why answers were flagged: {summary['flag_reasons'] or 'none'}", "",
        "## Per-query record", "", "| id | type | refused | gates | correct | cites gold | answer |", "|---|---|---|---|---|---|---|",
    ]
    for x in records:
        verdict = "pass" if x.grounded else f"flag: {x.reason[:40]}"
        lines.append(f"| {x.id} | {x.type} | {'yes' if x.refused else 'no'} | {verdict} | {x.correct} | {x.cites_gold} | {x.text[:70].replace('|', '/').replace(chr(10), ' ')} |")
    return "\n".join(lines) + "\n"


def to_json(summary, records) -> Dict[str, Any]:
    return {"summary": summary, "records": [asdict(x) for x in records]}
