"""
pooled.py: retrieval over ALL evaluation corpora in one index.

Every other eval indexes one corpus at a time, so a retriever that only works when the library holds a single document passes. A real
library has many: this pools the QuestionPrep snapshot and every PDF, asks every gold question of every corpus, and reports per corpus
and pooled, plus the one number a single-corpus eval cannot give: how often the top hit comes from the wrong document.

Two gold formats are read: `{file, snippet}` (gold.py) and the external golden format (golden.py: evidence quotes, one PDF per file).
For the second, a quote becomes a gold item only if it occurs verbatim (lower-cased alphanumerics) in a usable chunk of that PDF; the
rest are counted as `unreachable` and left out, so the pooled numbers measure retrieval and not the converter's rendering of a table.
"""

import hashlib
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from rag_template.evals.gold import GoldItem, Query, load_gold, norm
from rag_template.evals.golden import load_golden

# label -> (corpus dir, gold file, pdf the golden file is about; "" for the {file, snippet} format)
CORPORA: Dict[str, Tuple[str, str, str]] = {
    "questionprep": ("evals/corpus/questionprep", "evals/gold/handwritten.jsonl", ""),
    "pdfs": ("evals/corpus/pdfs", "evals/gold/pdfs.jsonl", ""),
    "banking": ("evals/corpus/banking", "evals/gold/banking.jsonl", ""),
    "pera": ("evals/corpus/pera", "evals/gold/pera.jsonl", "ProtectionEconomicReformsAct-1992.pdf"),
    "trm": ("evals/corpus/trm", "evals/gold/trm.jsonl", "2510.04871v1.pdf"),
    "ssd": ("evals/corpus/ssd", "evals/gold/ssd.jsonl", "2604.01193v2.pdf"),
}


@dataclass
class Pool:
    queries: List[Query] = field(default_factory=list)
    corpus_of: Dict[str, str] = field(default_factory=dict)  # query id -> corpus label
    unreachable: Dict[str, int] = field(
        default_factory=dict
    )  # corpus -> golden questions dropped (no verbatim evidence in a usable chunk)
    unanswerable: Dict[str, int] = field(default_factory=dict)


def build_pool_dir(labels: Sequence[str], root: Path, dest: Path) -> Tuple[Path, Dict[str, str], Dict[str, str]]:
    """Symlink every corpus file into `dest`, keeping each file's path relative to its corpus (the gold files name them that way).
    A file with the same bytes as one already linked is skipped (the library's own exact-duplicate rule would drop it too) and
    `alias` maps its name to the kept one. Returns (dest, alias, corpus_of_file)."""
    seen: Dict[str, str] = {}
    alias: Dict[str, str] = {}
    corpus_of_file: Dict[str, str] = {}
    for label in labels:
        src = root / CORPORA[label][0]
        for p in sorted(src.rglob("*")):
            if not p.is_file():
                continue
            rel = str(p.relative_to(src))
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            if digest in seen:
                alias[rel] = seen[digest]
                continue
            target = dest / rel
            if target.exists() or target.is_symlink():
                raise ValueError(f"{label}: '{rel}' is also in another corpus; the pooled gold would be ambiguous")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.symlink_to(p.resolve())
            seen[digest], corpus_of_file[rel] = rel, label
    return dest, alias, corpus_of_file


def load_pool(
    labels: Sequence[str], root: Path, chunks: Optional[Sequence[Dict]] = None, alias: Optional[Dict[str, str]] = None
) -> Pool:
    """All gold queries of `labels`, ids prefixed with the corpus. `chunks` (Database.iter_chunks of the pooled index) is needed to
    resolve the quotes of golden-format files; without it only {file, snippet} golds are loaded."""
    pool = Pool()
    alias = alias or {}
    usable = [(c["source"], norm(c["content"])) for c in chunks or [] if c["should_use"]]
    for label in labels:
        _, gold_path, pdf = CORPORA[label]
        path = root / gold_path
        if not pdf:
            for q in load_gold(path):
                q.id = f"{label}:{q.id}"
                for g in q.gold:
                    g.file = alias.get(g.file, g.file)
                pool.queries.append(q)
                pool.corpus_of[q.id] = label
            continue
        if chunks is None:
            continue
        pdf = alias.get(pdf, pdf)
        for row in load_golden(path):
            qid = f"{label}:{row.id}"
            if row.status != "yes":  # partial and unanswerable questions have no single gold passage
                pool.unanswerable[label] = pool.unanswerable.get(label, 0) + 1
                continue
            items = [
                GoldItem(pdf, q) for q in row.quotes if any(src == pdf and norm(q) in text for src, text in usable)
            ]
            if not items:
                pool.unreachable[label] = pool.unreachable.get(label, 0) + 1
                continue
            pool.queries.append(Query(qid, row.question, type=label, answerable=True, gold=items, origin=label))
            pool.corpus_of[qid] = label
    return pool


def wrong_document(ranked: Sequence[Dict], gold_files: set, k: int = 1) -> bool:
    """No hit in the top k comes from a document that holds the answer."""
    return not any(r["source"] in gold_files for r in ranked[:k])


def temp_pool(
    labels: Sequence[str], root: Path
) -> Tuple[tempfile.TemporaryDirectory, Path, Dict[str, str], Dict[str, str]]:
    tmp = tempfile.TemporaryDirectory(prefix="rag-pool-")
    dest, alias, corpus_of_file = build_pool_dir(labels, root, Path(tmp.name))
    return tmp, dest, alias, corpus_of_file
