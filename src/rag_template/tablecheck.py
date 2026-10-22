"""
tablecheck.py: is a number in an answer taken from the right cell of a table?

`verify.check_support` asks whether each number the answer states occurs somewhere in the evidence. On a table that is too weak: "after SSD
it is 59.7" passed because 59.7 is in the table (the baseline row's pass@5 column). This module asks the next question: for every number
the answer states that sits in a Markdown table of a cited chunk, is there a cell holding it whose *row* and *column* fit the sentence?

  row      the first cell of the row shares a distinctive word with the sentence or the question ("Qwen3-30B-Thinking")
  column   the column's header does not contradict the sentence: the same kind of token with another digit is a contradiction
           (`pass@5` in the header, `pass@1` in the sentence; `v5` against `v6`)

A number that is in no table cell is not this module's business (the set-level check handles it). It works only on tables, because that is
where the failure was measured (evals/results/golden_ssd_findings.md); prose sentences are not checked. It cannot judge the direction of a
change ("from A to B" against "from B to A"). It is a screen with known blind spots, not a proof.
"""

import collections
import re
from dataclasses import dataclass
from typing import Dict, List, Sequence, Set, Tuple

from rag_template.tables import LABEL_JOINER, inherit_row_labels

# a number as a reader sees it: 46.7, 1,000, 5.2%, +12.9pp; not the 30 of "30B" or the 3 of "Qwen3"
_NUMBER = re.compile(r"(?<![A-Za-z0-9.@])(?<![A-Za-z]-)[-+]?\d+(?:[.,]\d+)*(?:%|pp|x)?(?![A-Za-z0-9])")  # not the 1 of "ARC-AGI-1"
# a word-like token, keeping `pass@1`, `qwen3`, `30b`, `v6`
_TOKEN = re.compile(r"[a-z][a-z0-9]*(?:@\d+)?|\d+[a-z][a-z0-9]*")
_KIND = re.compile(r"^([a-z]+@?)(\d+)$")  # pass@1 -> ("pass@", "1"); v6 -> ("v", "6"); qwen3 -> ("qwen", "3")
_STOP = frozenset(
    "the a an of in on at to for from by with and or is are was were be as it its this that these those which what how does did do not no than then "
    "after before between each all per into over under about both more less most least value values result results table row column model models".split()
)


@dataclass
class Cell:
    number: str
    row_label: str
    column: str  # the header cell above it ("" when the header and the row disagree on the column count)
    row: str
    own_is_distinctive: bool = False  # the row's own label (after any inherited parent) has a word no other row's label has


def normalise_number(raw: str) -> str:
    return raw.lstrip("+-").rstrip("%x").removesuffix("pp").replace(",", "")


def numbers(text: str) -> List[str]:
    return [normalise_number(m.group()) for m in _NUMBER.finditer(text)]


def _stem(token: str) -> str:
    """Same crude stem as verify.py (first five letters: delete/deletes/deleted), for plain words only; `pass@1` and `qwen3` stay whole."""
    return token[:5] if token.isalpha() else token


def tokens(text: str) -> Set[str]:
    return {_stem(t) for t in _TOKEN.findall(text.lower()) if t not in _STOP}


def _bag(text: str) -> Set[str]:
    """Words and numbers: a row labelled `T=2, n=2` is identified by its numbers."""
    return tokens(text) | set(numbers(text))


def _cells(line: str) -> List[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_tables(text: str) -> List[List[Cell]]:
    """Every Markdown table in `text` as a list of number-bearing cells with their row label and column header."""
    tables: List[List[Cell]] = []
    block: List[str] = []
    for line in text.split("\n") + [""]:
        if line.lstrip().startswith("|"):
            block.append(line)
            continue
        if len(block) >= 3:
            header = _cells(block[0])
            out: List[Cell] = []
            rows = inherit_row_labels(block[2:])
            labels = [(_cells(r) or [""])[0] for r in rows]
            own = [_own_words(lb) for lb in labels]
            seen = collections.Counter(w for words in own for w in words)
            for row, label, words in zip(rows, labels, own):
                cells = _cells(row)
                aligned = len(cells) == len(header)
                distinctive = any(seen[w] == 1 for w in words)
                for i, cell in enumerate(cells[1:], 1):
                    for n in numbers(cell):
                        out.append(Cell(n, label, header[i] if aligned else "", row, distinctive))
            tables.append(out)
        block = []
    return tables


def _conflicts(sentence: Set[str], header: Set[str]) -> bool:
    """The header names a token of a kind the sentence also names, but with a different digit and not the sentence's own."""
    kinds_in_header: Dict[str, Set[str]] = {}
    for t in header:
        m = _KIND.match(t)
        if m:
            kinds_in_header.setdefault(m.group(1), set()).add(m.group(2))
    for t in sentence:
        m = _KIND.match(t)
        if m and m.group(1) in kinds_in_header and m.group(2) not in kinds_in_header[m.group(1)]:
            return True
    return False


def _label_words(part: str) -> Set[str]:
    return {t for t in _bag(part) if len(t) >= 2 or t.isdigit()}  # the "n" and "t" of `n=2, T=2` say nothing, its 2 and 2 do


def _own_words(label: str) -> Set[str]:
    return _label_words(label.split(LABEL_JOINER)[-1])


def _fits(cell: Cell, sentence: Set[str], context: Set[str]) -> bool:
    parts = cell.row_label.split(LABEL_JOINER)  # "parent / own"
    # the row's own label must be what the answer is about; the inherited parents too, unless the own label already identifies the row
    # ("+ SSD" occurs in every model's block and needs its parent; "w/ 1-step gradient" occurs once)
    for part in parts[-1:] if cell.own_is_distinctive else parts:
        label = _label_words(part)
        if label and not (label & context):
            return False  # the row is about something the sentence and the question never mention
    return not _conflicts(sentence, tokens(cell.column))


def _sentences(text: str) -> List[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]  # not on ";": "delete the file; 207 if one fails" is one statement


def check_table_numbers(answer: str, evidence: Sequence[str], question: str = "") -> Tuple[bool, str]:
    """(True, "") when every number of the answer that is a table cell in `evidence` fits a cell's row and column; otherwise
    (False, reason) naming the first number that does not."""
    tables = [t for text in evidence for t in parse_tables(text)]
    if not tables:
        return True, ""
    prose = {n for text in evidence for line in text.split("\n") if not line.lstrip().startswith("|") for n in numbers(line)}
    by_number: Dict[str, List[Cell]] = {}
    for table in tables:
        for cell in table:
            if cell.number not in prose:  # a number the prose also states may come from there
                by_number.setdefault(cell.number, []).append(cell)
    asked = _bag(question)
    previous: Set[str] = set()
    for sentence in _sentences(answer):
        toks = tokens(sentence)
        bag = _bag(sentence)
        context = bag | previous | asked  # the row may have been named a sentence earlier, or in the question
        previous = bag
        for n in [n for n in numbers(sentence) if n in by_number]:
            if not any(_fits(c, toks, context) for c in by_number[n]):
                seen = by_number[n][0]
                return False, f"Number {n} is in the sources, but not in a cell that fits this answer (found under row '{seen.row_label[:50]}', column '{seen.column[-50:]}')"
    return True, ""
