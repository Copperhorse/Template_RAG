"""
split.py: a fixed dev / test split of every gold question, so changes are tuned on one part and judged on the other.

A question is dev when the hash of its normalised text falls below `DEV_PERCENT`, test otherwise. Hashing the text (not the id or the row
number) means the same question in two gold files (the banking statute questions occur in both banking.jsonl and pdfs.jsonl) lands on
the same side, and nobody can move a question by renaming it or re-rolling a seed. The rule is the whole split: there is no file to edit.

Use: tune and read per-question output on `dev` only; report `test` as aggregate numbers, once per change.
"""

import hashlib
import re
from typing import Iterable, List, TypeVar

DEV_PERCENT = 60
T = TypeVar("T")


def _key(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def bucket(question: str) -> int:
    return int(hashlib.sha256(_key(question).encode()).hexdigest(), 16) % 100


def is_dev(question: str) -> bool:
    return bucket(question) < DEV_PERCENT


def select(items: Iterable[T], question_of, part: str) -> List[T]:
    """`part`: dev | test | all."""
    if part not in ("dev", "test", "all"):
        raise ValueError("split must be dev, test or all")
    return [x for x in items if part == "all" or (part == "dev") == is_dev(question_of(x))]
