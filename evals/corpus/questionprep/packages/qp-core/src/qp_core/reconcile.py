"""
reconcile.py — compare the SQLite store with the Chroma collection.

Two kinds of drift are reported:
  * orphan embeddings: Chroma documents whose `file_id` metadata is not in the `files` table
    (left behind by a failed or interrupted delete; they still hold the deleted user's text)
  * unindexed files: files that have questions but no embeddings in Chroma
    (indexing failed or was switched off with QP_INDEX_EMBEDDINGS=0)

Only orphans can be fixed here (deleted). Re-indexing is `VectorIndexer.index_file(file_id)`.
"""

import sqlite3
from dataclasses import dataclass, field
from typing import Dict, List, Set

COLLECTION_NAME = "qa_pairs"
_PAGE = 1000


@dataclass
class Report:
    orphan_ids: List[str] = field(default_factory=list)  # Chroma ids to delete
    orphan_file_ids: Set[str] = field(default_factory=set)  # file_ids (or "" if metadata is missing)
    unindexed_file_ids: List[str] = field(default_factory=list)
    chroma_total: int = 0
    pending_deletions: List[str] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.orphan_ids and not self.unindexed_file_ids


def sqlite_state(db_path: str):
    """(all file ids, file ids that have at least one question, pending-deletion file ids)."""
    con = sqlite3.connect(db_path)
    try:
        all_files = {r[0] for r in con.execute("SELECT file_id FROM files")}
        with_questions = {
            r[0]
            for r in con.execute(
                "SELECT DISTINCT c.file_id FROM chunk_questions q JOIN chunks c ON c.chunk_id = q.chunk_id"
            )
        }
        try:
            pending = [r[0] for r in con.execute("SELECT file_id FROM pending_deletions")]
        except sqlite3.OperationalError:  # DB from before task 2.3
            pending = []
    finally:
        con.close()
    return all_files, with_questions, pending


def chroma_file_ids(collection) -> Dict[str, str]:
    """{chroma id: file_id ('' when the metadata has none)} for every document."""
    out: Dict[str, str] = {}
    offset = 0
    while True:
        page = collection.get(include=["metadatas"], limit=_PAGE, offset=offset)
        ids = page.get("ids") or []
        if not ids:
            return out
        for cid, meta in zip(ids, page.get("metadatas") or [{}] * len(ids)):
            out[cid] = str((meta or {}).get("file_id") or "")
        offset += len(ids)


def compare(collection, db_path: str) -> Report:
    all_files, with_questions, pending = sqlite_state(db_path)
    docs = chroma_file_ids(collection)

    report = Report(chroma_total=len(docs), pending_deletions=sorted(pending))
    for cid, fid in sorted(docs.items()):
        if fid not in all_files:
            report.orphan_ids.append(cid)
            report.orphan_file_ids.add(fid)
    indexed = {fid for fid in docs.values() if fid}
    report.unindexed_file_ids = sorted(with_questions - indexed)
    return report


def delete_orphans(collection, report: Report) -> int:
    for i in range(0, len(report.orphan_ids), _PAGE):
        collection.delete(ids=report.orphan_ids[i : i + _PAGE])
    return len(report.orphan_ids)
