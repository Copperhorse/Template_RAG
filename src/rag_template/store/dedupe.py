"""
dedupe.py: near-duplicate detection with SimHash (stdlib only).

Two documents whose 64-bit SimHashes differ in at most `k` bits are treated as near-duplicates (a
re-export of the same PDF, a copy with a new header). Exact byte duplicates are caught earlier by
the SHA-256 stored on each document. The index is a linear scan over integers, which is
instantaneous up to hundreds of thousands of documents; swap in banded buckets beyond that.
"""

import hashlib
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Mapping

EMPTY_HASH = "0" * 16


def _hash64(feature: str) -> int:
    return int.from_bytes(hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest(), "big")


def simhash(text: str, width: int = 3) -> str:
    """64-bit SimHash of character n-grams, as 16 hex digits."""
    norm = re.sub(r"\W+", "", text.lower())
    if not norm:
        return EMPTY_HASH
    grams = Counter(norm[i : i + width] for i in range(max(len(norm) - width + 1, 1)))
    acc = [0] * 64
    for gram, weight in grams.items():
        h = _hash64(gram)
        for bit in range(64):
            acc[bit] += weight if (h >> bit) & 1 else -weight
    value = sum(1 << bit for bit in range(64) if acc[bit] > 0)
    return format(value, "016x")


def hamming(a_hex: str, b_hex: str) -> int:
    return (int(a_hex, 16) ^ int(b_hex, 16)).bit_count()


@dataclass
class DuplicateCheck:
    is_duplicate: bool
    duplicate_ids: List[str] = field(default_factory=list)
    simhash: str = EMPTY_HASH


class SimHashIndex:
    def __init__(self, k: int = 3):
        self.k = k
        self._hashes: Dict[str, str] = {}

    def add(self, doc_id: str, simhash_hex: str) -> None:
        self._hashes[doc_id] = simhash_hex

    def remove(self, doc_id: str) -> None:
        self._hashes.pop(doc_id, None)

    def load(self, hashes: Mapping[str, str]) -> None:
        """Replace the index with {doc_id: simhash_hex}."""
        self._hashes = dict(hashes)

    def check(self, text: str) -> DuplicateCheck:
        h = simhash(text)
        if h == EMPTY_HASH:
            return DuplicateCheck(False, [], h)
        near = sorted(
            (hamming(h, other), doc_id) for doc_id, other in self._hashes.items() if hamming(h, other) <= self.k
        )
        return DuplicateCheck(bool(near), [doc_id for _, doc_id in near], h)

    def __len__(self) -> int:
        return len(self._hashes)
