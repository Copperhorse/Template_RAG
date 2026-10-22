"""
golden.py: score an *already ingested* store against an external golden QA file.

The golden file is one JSON object per line:
    id, question, ground_truth, answerable, evidence [{chunk_id, quote}], optional facts / polarity (see below)
`evidence_verbatim` (a list of strings), when present, replaces `evidence` for relevance: use it where the original quote is an
annotated rendering no converter emits verbatim. `relevant_chunk_ids` in such a file belong to whatever chunking its author used, so they are ignored: a chunk is relevant
when it contains an `evidence` quote (compared on lower-cased alphanumerics, as in gold.py).

Three layers, so a failure is attributed to the stage that caused it:
  1. ingestion   is each evidence quote in a *usable* chunk? (rejected by the gate / split across chunks / not in the document)
  2. retrieval   rank of the first chunk holding evidence; recall of the evidence quotes in the top k
  3. answer      refused / flagged / delivered, whether a verified quote comes from an evidence chunk, and (answerable
                 questions) whether the answer contains the `facts` the ground truth needs. `facts` is a list of
                 alternative-lists: every inner list must have at least one alternative in the answer. `polarity: "no"`
                 additionally requires a negation near the start. This is a lower bound: a right answer worded differently
                 scores as wrong, so read the answers (the report lists them).
"""

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from rag_template.evals.gold import norm

_NEGATION = re.compile(r"\b(no|not|cannot|never|shall not|may not|isn't|doesn't|does not)\b", re.I)


@dataclass
class Row:
    id: str
    question: str
    ground_truth: str
    answerable: bool
    quotes: List[str]
    facts: List[List[str]] = field(default_factory=list)
    polarity: str = ""
    kind: str = ""
    difficulty: str = ""
    near_miss: List[str] = field(default_factory=list)
    status: str = "yes"  # yes | partial | no ("answerable" may be a bool or one of these strings)
    items: List[str] = field(default_factory=list)  # `answer_items` of a list question: what a complete answer names
    expected: str = ""  # `expected_behavior` of a partial or unanswerable question


def _status(value: Any) -> str:
    if isinstance(value, str) and value.strip().lower() in ("yes", "partial", "no"):
        return value.strip().lower()
    return "yes" if value in (True, None, "true", "True") else "no"


def load_golden(path: str | Path) -> List[Row]:
    rows = []
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        status = _status(d.get("answerable", True))
        rows.append(Row(
            d["id"], d["question"], d.get("ground_truth", ""), status != "no",
            d.get("evidence_verbatim") or [e["quote"] for e in d.get("evidence", []) if e.get("quote")], d.get("facts", []), d.get("polarity", ""),
            d.get("question_type", ""), d.get("difficulty", ""), d.get("near_miss_chunk_ids", []),
            status, [i["item"] for i in d.get("answer_items", []) if i.get("item")], d.get("expected_behavior", ""),
        ))
    return rows


FUZZY_COVERAGE = 0.8  # share of a quote's tokens (its digit-bearing tokens when it has three or more) a chunk must contain to count as holding it, when fuzzy matching is on
_TOKEN = re.compile(r"\d+(?:[.,]\d+)+|[a-z0-9]+")  # decimals stay whole: "66.1" is one token


def holds(quote: str, text: str, fuzzy: bool = False) -> bool:
    """Does `text` hold `quote`? Exact: the quote's letters and digits occur in order (as everywhere else in the evals). Fuzzy
    (opt-in): or at least FUZZY_COVERAGE of the quote's tokens occur in the text. For golden files whose evidence is a *rendering* of the
    source (a table row as `name: [66.1, 99.8]`, an equation in plain text) that no converter reproduces verbatim."""
    if norm(quote) in norm(text):
        return True
    if not fuzzy:
        return False
    qt = set(_TOKEN.findall(quote.lower()))
    numeric = {t for t in qt if len(t) >= 2 and any(c.isdigit() for c in t)}  # a lone digit ("pass@1") is rendering noise
    wanted = numeric if len(numeric) >= 3 else qt  # a rendered table row or equation: its numbers and names are what a converter keeps
    return len(wanted) >= 4 and len(wanted & set(_TOKEN.findall(text.lower()))) / len(wanted) >= FUZZY_COVERAGE


def audit_evidence(chunks: Sequence[Dict[str, Any]], rows: List[Row], fuzzy: bool = False) -> Dict[str, List[Dict[str, Any]]]:
    """Per question, per evidence quote: where it lives in the store. status = usable | rejected | split | absent (| fuzzy-usable when
    only the fuzzy match found it). `chunks`: dicts with content, should_use, reject_reason (`Database.iter_chunks()`)."""
    normed = [(norm(c["content"]), bool(c["should_use"]), c.get("reject_reason") or "") for c in chunks]
    joined = "".join(text for text, _, _ in normed)  # norm() only filters characters, so this is norm("".join(contents))
    out: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        items = []
        for q in r.quotes:
            n = norm(q)
            holders = [(use, why) for text, use, why in normed if n in text]
            if any(use for use, _ in holders):
                items.append({"quote": q, "status": "usable"})
            elif fuzzy and not holders and any(c["should_use"] and holds(q, c["content"], True) for c in chunks):
                items.append({"quote": q, "status": "fuzzy-usable"})
            elif holders:
                items.append({"quote": q, "status": "rejected", "why": holders[0][1]})
            else:
                items.append({"quote": q, "status": "split" if n in joined else "absent"})
        out[r.id] = items
    return out


def fact_score(answer: str, facts: List[List[str]], polarity: str = "") -> Optional[float]:
    """Share of required facts present in the answer (None when the question has none)."""
    if not facts:
        return None
    a = norm(answer)
    hit = sum(1 for alts in facts if any(norm(x) in a for x in alts))
    total = len(facts)
    if polarity == "no":
        total += 1
        hit += 1 if _NEGATION.search(answer[:160]) else 0
    return hit / total


def item_recall(answer: str, items: Sequence[str]) -> Optional[float]:
    """Share of `items` an answer names: an item counts when every number and every word of 4+ letters in it occurs in the answer
    (so "Llama-3.1-8B +3.5" needs llama, 3.1, 8b and 3.5). None when the question lists no items. A lower bound, like fact_score."""
    if not items:
        return None
    a = norm(answer)

    def named(item: str) -> bool:
        tokens = [t for t in re.findall(r"[A-Za-z0-9.]+", item) if any(c.isdigit() for c in t) or len(t) >= 4]
        return bool(tokens) and all(norm(t) in a for t in tokens)

    return sum(1 for i in items if named(i)) / len(items)


def evidence_hit(text: str, quotes: List[str], fuzzy: bool = False) -> bool:
    return any(holds(q, text, fuzzy) for q in quotes)


def run(rag, rows: List[Row], audit: Dict[str, List[Dict[str, Any]]], k: int = 5, policy: Optional[str] = None, fuzzy: bool = False, max_context_tokens: Optional[int] = None, expand_section: int = 0) -> List[Dict[str, Any]]:
    out = []
    answerer = rag.answerer(policy)
    if max_context_tokens:
        answerer.max_context_tokens = max_context_tokens  # the prompt budget for sources (Answerer default 3000)
    answerer.expand_section = expand_section
    for i, r in enumerate(rows, 1):
        t = time.time()
        hits = rag.search(r.question, k=k)
        rank = next((j + 1 for j, h in enumerate(hits) if evidence_hit(h.content, r.quotes, fuzzy)), None)
        covered = sum(1 for q in r.quotes if any(holds(q, h.content, fuzzy) for h in hits))
        ans = answerer.ask(r.question, k=k, hits=hits)  # the answer is built from the hits just scored
        verified_from_evidence = any(evidence_hit(q.hit.content, r.quotes, fuzzy) for q in ans.quotes)
        cites_evidence = any(1 <= n <= len(ans.sources) and evidence_hit(ans.sources[n - 1].content, r.quotes, fuzzy) for n in ans.citations)
        out.append({
            "id": r.id, "question": r.question, "kind": r.kind, "difficulty": r.difficulty, "answerable": r.status == "yes", "status": r.status,
            "ground_truth": r.ground_truth, "evidence_status": [e["status"] for e in audit[r.id]],
            "rank": rank, "covered": covered, "n_quotes": len(r.quotes),
            "answer": ans.text, "refused": ans.refused, "grounded": ans.grounded, "reason": ans.reason,
            "citations": ans.citations, "n_verified": len(ans.quotes), "verified_from_evidence": verified_from_evidence,
            "cites_evidence": cites_evidence, "fact_score": fact_score(ans.text, r.facts, r.polarity) if r.answerable else None, "item_recall": item_recall(ans.text, r.items),
            "sources": [h.breadcrumb for h in ans.sources], "source_content": [h.content for h in ans.sources], "seconds": round(time.time() - t, 1),
        })
        print(f"[{i}/{len(rows)}] {r.id} rank={rank} refused={ans.refused} grounded={ans.grounded}", flush=True)
    return out


def _pct(n: int, d: int) -> str:
    return f"{100 * n / d:.0f}% ({n}/{d})" if d else "n/a"


def render(records: List[Dict[str, Any]], meta: Dict[str, Any]) -> str:
    status = lambda r: r.get("status") or ("yes" if r["answerable"] else "no")  # noqa: E731  (older result files have only the bool)
    ans = [r for r in records if status(r) == "yes"]
    una = [r for r in records if status(r) == "no"]
    part = [r for r in records if status(r) == "partial"]
    scored = ans + part  # these have evidence to find
    delivered = lambda r: not r["refused"] and r["grounded"]  # noqa: E731
    flagged = lambda r: not r["refused"] and not r["grounded"]  # noqa: E731
    full = lambda r: r["fact_score"] is not None and r["fact_score"] >= 0.999  # noqa: E731
    count = lambda rows, pred: sum(1 for r in rows if pred(r))  # noqa: E731
    share = lambda rows, pred: _pct(count(rows, pred), len(rows))  # noqa: E731
    listed = [r for r in ans if r.get("item_recall") is not None]
    with_facts = [r for r in ans if r["fact_score"] is not None]
    k = meta["k"]
    evidence = [s for r in scored for s in r["evidence_status"]]
    unreachable = [r["id"][-3:] for r in scored if any(s not in ("usable", "fuzzy-usable") for s in r["evidence_status"])]
    p = [f"# Golden QA evaluation: {meta['label']}", "",
         f"Golden file `{meta['golden']}` ({len(records)} questions: {len(ans)} answerable, {len(una)} unanswerable"
         + (f", {len(part)} partially answerable" if part else "") + f"). Store: `{meta['store']}` "
         f"({meta['chunks']} chunks, {meta['usable']} usable). LLM json_mode=`{meta['json_mode']}`, policy=`{meta['policy']}`, k={k}. "
         "'Correct' = the answer contains the facts listed in the gold sidecar: a lower bound, read the answers below.", "",
         "## 1. Ingestion: is the evidence in a usable chunk?", ""]
    p += [f"- {s}: {_pct(evidence.count(s), len(evidence))}" for s in ("usable", "fuzzy-usable", "rejected", "split", "absent") if s != "fuzzy-usable" or evidence.count(s)]
    if "fuzzy-usable" in evidence:
        p.append(f"- (fuzzy-usable: no exact match, but a chunk holds at least {int(FUZZY_COVERAGE * 100)}% of the quote's tokens; relevance below uses the same rule)")
    if unreachable:
        p.append(f"- questions with unreachable evidence: {', '.join(unreachable)}")
    p += ["", "## 2. Retrieval (answerable questions" + (" and partially answerable ones)" if part else ")"), "",
          f"- an evidence chunk in the top {k}: {share(scored, lambda r: r['rank'])}",
          f"- evidence chunk ranked first: {share(scored, lambda r: r['rank'] == 1)}",
          f"- all of a question's evidence quotes covered by the top {k}: {share(scored, lambda r: r['covered'] == r['n_quotes'])}",
          *([f"- note: the store has only {meta['usable']} usable chunks, so the top {k} is most of the store; retrieval is easy here by construction."] if meta["usable"] <= 2 * k else []),
          "", "## 3. Answers", "",
          f"- answered (did not refuse): {share(ans, lambda r: not r['refused'])}",
          f"- delivered (answered and passed the gates): {share(ans, delivered)}",
          f"- contains every required fact: {share(ans, full)}",
          f"- contains every required fact **and** delivered: {share(ans, lambda r: full(r) and delivered(r))}",
          f"- mean share of required facts present: {sum(r['fact_score'] for r in with_facts) / max(len(with_facts), 1):.2f}"
          + (f" (over the {len(with_facts)} questions that list facts)" if len(with_facts) != len(ans) else ""),
          *([f"- mean item recall over the {len(listed)} list questions that name their items: {sum(r['item_recall'] for r in listed) / len(listed):.2f}"] if listed else []),
          f"- a verified quote comes from an evidence chunk: {share(ans, lambda r: r['verified_from_evidence'])}",
          f"- correct among flagged answers (false alarms): {_pct(count(ans, lambda r: flagged(r) and full(r)), count(ans, flagged))}",
          "", "## 4. Unanswerable questions (right behaviour: refuse)", "",
          f"- refused: {share(una, lambda r: r['refused'])}",
          f"- answered but flagged: {share(una, flagged)}",
          f"- answered and passed the gates (the dangerous case): {share(una, delivered)}",
          *(["", "## 4b. Partially answerable (the right reply cites what exists and says what the source does not give)", "",
             f"- refused outright (a fail: the part that exists should be given): {share(part, lambda r: r['refused'])}",
             f"- answered and passed the gates: {share(part, delivered)}",
             f"- answered and flagged: {share(part, flagged)}",
             "- whether a reply states what is missing needs reading; see section 6."] if part else []),
          "", "## 5. By question type (answerable)", "", "| type | n | evidence in top-k | delivered | every fact | delivered and every fact |", "|---|---:|---:|---:|---:|---:|"]
    for kind in sorted({r["kind"] for r in ans}):
        g = [r for r in ans if r["kind"] == kind]
        p.append(f"| {kind} | {len(g)} | {count(g, lambda r: r['rank'])} | {count(g, delivered)} | {count(g, full)} | {count(g, lambda r: full(r) and delivered(r))} |")
    p += ["", "## 6. Every question", "", "| id | type | ev. | rank | outcome | facts | answer |", "|---|---|---|---|---|---|---|"]
    for r in records:
        outcome = "refused" if r["refused"] else ("pass" if r["grounded"] else "flag: " + r["reason"][:40])
        facts = "-" if r["fact_score"] is None else f"{r['fact_score']:.2f}"
        p.append(f"| {r['id'][-3:]} | {r['kind'][:8]} | {','.join(s[0] for s in r['evidence_status']) or '-'} | {r['rank'] or '-'} | {outcome} | {facts} | "
                 f"{r['answer'][:150].replace('|', '/').replace(chr(10), ' ')} |")
    return "\n".join(p) + "\n"
