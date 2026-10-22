"""
db.py: every SQLite operation (stdlib only).

    documents            one row per ingested file
    chunks               chunk text + position + the evaluator's verdict (`should_use`) + metadata_json
    chunk_enrichments    summary / tags / triplets per chunk
    chunk_qa             verified question/answer pairs per chunk (they are indexed as extra vectors)
    chunk_rejections     every candidate pair a gate rejected, with the reason, so gates can be tuned
    chunks_fts           FTS5 mirror of chunk text + breadcrumb, for lexical search (if SQLite has FTS5)

"Pending" work is derived, not flagged: a usable chunk with no enrichment, no QA and no rejection row
has not been attempted. That makes the enrichment run resumable and safe to interrupt.

Schema changes: add an `ALTER TABLE` to MIGRATIONS (additive only) and bump nothing else.
"""

import json
import logging
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence

logger = logging.getLogger("rag_template.db")

SCHEMA = [
    """CREATE TABLE IF NOT EXISTS documents (
        doc_id TEXT PRIMARY KEY,
        source TEXT,
        name TEXT,
        kind TEXT,
        title TEXT,
        simhash TEXT,
        sha256 TEXT,
        content_length INTEGER,
        processed_at TEXT,
        conversion_json TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS chunks (
        chunk_id TEXT PRIMARY KEY,
        doc_id TEXT NOT NULL,
        chunk_index INTEGER,
        content TEXT,
        content_type TEXT,
        estimated_tokens INTEGER,
        section_header TEXT,
        parent_section TEXT,
        top_header TEXT,
        breadcrumb TEXT,
        metadata_json TEXT,
        prev_chunk_id TEXT,
        next_chunk_id TEXT,
        quality_score REAL,
        should_use INTEGER DEFAULT 1,
        reject_reason TEXT,
        FOREIGN KEY(doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE
    )""",
    """CREATE TABLE IF NOT EXISTS chunk_enrichments (
        chunk_id TEXT PRIMARY KEY,
        tags TEXT,
        triplets TEXT,
        summary TEXT,
        processed_at TEXT,
        FOREIGN KEY(chunk_id) REFERENCES chunks(chunk_id) ON DELETE CASCADE
    )""",
    """CREATE TABLE IF NOT EXISTS chunk_qa (
        qa_id TEXT PRIMARY KEY,
        chunk_id TEXT NOT NULL,
        question_text TEXT NOT NULL,
        answer_text TEXT NOT NULL,
        source_quote TEXT,
        difficulty TEXT CHECK(difficulty IN ('Easy','Medium','Hard')),
        question_type TEXT,
        FOREIGN KEY(chunk_id) REFERENCES chunks(chunk_id) ON DELETE CASCADE
    )""",
    """CREATE TABLE IF NOT EXISTS chunk_rejections (
        rejection_id TEXT PRIMARY KEY,
        chunk_id TEXT NOT NULL,
        level TEXT,
        question_text TEXT,
        answer_text TEXT,
        reason TEXT NOT NULL,
        rejected_at TEXT,
        FOREIGN KEY(chunk_id) REFERENCES chunks(chunk_id) ON DELETE CASCADE
    )""",
    "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)",  # store-level facts, e.g. which embedder built the vectors
    "CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id)",
    "CREATE INDEX IF NOT EXISTS idx_chunks_use ON chunks(should_use)",
    "CREATE INDEX IF NOT EXISTS idx_qa_chunk ON chunk_qa(chunk_id)",
    "CREATE INDEX IF NOT EXISTS idx_rej_chunk ON chunk_rejections(chunk_id)",
    "CREATE INDEX IF NOT EXISTS idx_rej_reason ON chunk_rejections(reason)",
    "CREATE INDEX IF NOT EXISTS idx_docs_sha256 ON documents(sha256)",
]

# Additive migrations for databases created by an earlier version of this template. Append only.
MIGRATIONS: List[str] = [
    "ALTER TABLE documents ADD COLUMN conversion_json TEXT",  # the PDF conversion check (convcheck.py); NULL for other formats
]


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _fts_query(text: str) -> str:
    """Turn free text into a safe FTS5 query: quoted tokens OR-ed together."""
    import re

    tokens = re.findall(r"[A-Za-z0-9_]{2,}", text)
    return " OR ".join(f'"{t}"' for t in dict.fromkeys(tokens))


class Database:
    def __init__(self, db_path: str | Path = "data/rag.db"):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.has_fts = False
        self._init_db()

    # ------------------------------------------------------------------ connection + schema

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self.db_path, timeout=30)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON;")
        con.execute("PRAGMA journal_mode = WAL;")
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def get_meta(self, key: str) -> Optional[str]:
        with self._connection() as con:
            row = con.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None

    def set_meta(self, key: str, value: str) -> None:
        with self._connection() as con:
            con.execute("INSERT INTO meta(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))

    def _init_db(self) -> None:
        with self._connection() as con:
            for stmt in SCHEMA:
                con.execute(stmt)
            for migration in MIGRATIONS:
                try:
                    con.execute(migration)
                except sqlite3.OperationalError:
                    pass  # already applied
            try:
                con.execute(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5("
                    "chunk_id UNINDEXED, doc_id UNINDEXED, text, tokenize='porter unicode61')"
                )
                self.has_fts = True
            except sqlite3.OperationalError:
                logger.info("SQLite was built without FTS5; lexical search is disabled")

    # ------------------------------------------------------------------ documents

    def save_document(
        self,
        doc_id: str,
        source: str,
        simhash: Optional[str],
        content_length: int,
        sha256: Optional[str] = None,
        kind: str = "",
        title: str = "",
        conversion_json: Optional[str] = None,
    ) -> None:
        with self._connection() as con:
            con.execute(
                "INSERT OR REPLACE INTO documents (doc_id, source, name, kind, title, simhash, sha256, content_length, processed_at, conversion_json)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                (doc_id, source, Path(source).name, kind, title, simhash, sha256, content_length, _now(), conversion_json),
            )

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        with self._connection() as con:
            row = con.execute("SELECT * FROM documents WHERE doc_id = ?", (doc_id,)).fetchone()
        return dict(row) if row else None

    def list_documents(self) -> List[Dict[str, Any]]:
        sql = """
            SELECT d.*, COUNT(c.chunk_id) AS chunks,
                   COALESCE(SUM(c.should_use), 0) AS usable_chunks
            FROM documents d LEFT JOIN chunks c ON c.doc_id = d.doc_id
            GROUP BY d.doc_id ORDER BY d.processed_at
        """
        with self._connection() as con:
            return [dict(r) for r in con.execute(sql).fetchall()]

    def get_all_simhashes(self) -> Dict[str, str]:
        """{doc_id: simhash} for every document that has one."""
        with self._connection() as con:
            rows = con.execute("SELECT doc_id, simhash FROM documents WHERE simhash IS NOT NULL").fetchall()
        return {r["doc_id"]: r["simhash"] for r in rows}

    def get_document_by_sha256(self, sha256: str) -> Optional[Dict[str, Any]]:
        with self._connection() as con:
            row = con.execute("SELECT doc_id, name FROM documents WHERE sha256 = ? LIMIT 1", (sha256,)).fetchone()
        return dict(row) if row else None

    def get_document_by_source(self, source: str) -> Optional[Dict[str, Any]]:
        with self._connection() as con:
            row = con.execute("SELECT * FROM documents WHERE source = ? LIMIT 1", (source,)).fetchone()
        return dict(row) if row else None

    def delete_document(self, doc_id: str) -> bool:
        """Remove a document and everything under it. Delete its vectors FIRST (VectorStore
        .delete_document) and call this only if that succeeded, so the two stores never diverge."""
        with self._connection() as con:
            if self.has_fts:
                con.execute("DELETE FROM chunks_fts WHERE doc_id = ?", (doc_id,))
            return con.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,)).rowcount > 0

    # ------------------------------------------------------------------ chunks

    def save_chunks(self, doc_id: str, chunks: Sequence[Dict[str, Any]]) -> int:
        """Store evaluated chunks (each carries an `evaluation` dict from ChunkEvaluator)."""
        rows, fts_rows = [], []
        for c in chunks:
            ev = c.get("evaluation", {})
            meta = c.get("metadata", {})
            usable = 1 if ev.get("should_use", True) else 0
            rows.append(
                (
                    c["chunk_id"], doc_id, c["chunk_index"], c["content"],
                    meta.get("content_type", "prose"), c.get("estimated_tokens", 0),
                    meta.get("section_header", ""), meta.get("parent_section") or "", meta.get("top_header", ""),
                    meta.get("breadcrumb", ""), json.dumps(meta, default=str),
                    c.get("prev_chunk_id"), c.get("next_chunk_id"),
                    ev.get("quality_score", 0.0), usable, None if usable else ev.get("reason"),
                )
            )
            if usable:
                fts_rows.append((c["chunk_id"], doc_id, f"{meta.get('breadcrumb', '')}\n{c['content']}"))
        with self._connection() as con:
            con.executemany(
                """INSERT OR REPLACE INTO chunks
                   (chunk_id, doc_id, chunk_index, content, content_type, estimated_tokens, section_header,
                    parent_section, top_header, breadcrumb, metadata_json, prev_chunk_id, next_chunk_id,
                    quality_score, should_use, reject_reason)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                rows,
            )
            if self.has_fts and fts_rows:
                con.executemany("INSERT INTO chunks_fts (chunk_id, doc_id, text) VALUES (?,?,?)", fts_rows)
        return len(rows)

    @staticmethod
    def _chunk_row(row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        try:
            d["metadata"] = json.loads(d.pop("metadata_json") or "{}")
        except json.JSONDecodeError:
            d["metadata"] = {}
        return d

    def get_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        with self._connection() as con:
            row = con.execute("SELECT * FROM chunks WHERE chunk_id = ?", (chunk_id,)).fetchone()
        return self._chunk_row(row) if row else None

    def get_chunks(self, chunk_ids: Sequence[str]) -> Dict[str, Dict[str, Any]]:
        if not chunk_ids:
            return {}
        out: Dict[str, Dict[str, Any]] = {}
        with self._connection() as con:
            for i in range(0, len(chunk_ids), 500):  # stay under SQLite's variable limit
                batch = list(chunk_ids[i : i + 500])
                q = f"SELECT c.*, d.source AS source, d.name AS doc_name FROM chunks c JOIN documents d ON d.doc_id = c.doc_id WHERE c.chunk_id IN ({','.join('?' * len(batch))})"
                for row in con.execute(q, batch).fetchall():
                    out[row["chunk_id"]] = self._chunk_row(row)
        return out

    def iter_chunks(self) -> List[Dict[str, Any]]:
        """Every chunk with its source path and quality verdict (used by the evals)."""
        sql = "SELECT c.chunk_id, c.content, c.content_type, c.should_use, c.reject_reason, c.section_header, d.source FROM chunks c JOIN documents d ON d.doc_id = c.doc_id ORDER BY d.source, c.chunk_index"
        with self._connection() as con:
            return [dict(r) for r in con.execute(sql).fetchall()]

    def get_chunk_ids_for_document(self, doc_id: str, usable_only: bool = False) -> List[str]:
        sql = "SELECT chunk_id FROM chunks WHERE doc_id = ?" + (" AND should_use = 1" if usable_only else "") + " ORDER BY chunk_index"
        with self._connection() as con:
            return [r["chunk_id"] for r in con.execute(sql, (doc_id,)).fetchall()]

    def get_indexable_chunks(self, doc_id: str) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM chunks WHERE doc_id = ? AND should_use = 1 ORDER BY chunk_index"
        with self._connection() as con:
            return [self._chunk_row(r) for r in con.execute(sql, (doc_id,)).fetchall()]

    def get_rejected_chunks(self, doc_id: str) -> List[Dict[str, Any]]:
        sql = "SELECT chunk_id, chunk_index, section_header, reject_reason, substr(content,1,120) AS preview FROM chunks WHERE doc_id = ? AND should_use = 0 ORDER BY chunk_index"
        with self._connection() as con:
            return [dict(r) for r in con.execute(sql, (doc_id,)).fetchall()]

    def search_lexical(self, query: str, limit: int = 10, doc_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """BM25-ranked chunk ids from FTS5 ([] when unavailable or the query has no usable token)."""
        fts = _fts_query(query)
        if not self.has_fts or not fts:
            return []
        sql = "SELECT chunk_id, bm25(chunks_fts) AS rank FROM chunks_fts WHERE chunks_fts MATCH ?"
        params: List[Any] = [fts]
        if doc_id:
            sql += " AND doc_id = ?"
            params.append(doc_id)
        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)
        try:
            with self._connection() as con:
                return [dict(r) for r in con.execute(sql, params).fetchall()]
        except sqlite3.OperationalError as e:
            logger.warning(f"FTS query failed ({e}); lexical search skipped")
            return []

    # ------------------------------------------------------------------ enrichment work queue

    def get_pending_documents(self, limit: int = 10, exclude: Optional[Iterable[str]] = None) -> List[str]:
        """Documents with at least one usable chunk nobody has attempted yet. A chunk counts as
        attempted once it has a QA pair, an enrichment row or a rejection row."""
        exclude = list(exclude or [])
        not_in = f"AND c.doc_id NOT IN ({','.join('?' * len(exclude))})" if exclude else ""
        sql = f"""
            SELECT DISTINCT c.doc_id FROM chunks c
            WHERE c.should_use = 1 {not_in}
              AND NOT EXISTS (SELECT 1 FROM chunk_qa q WHERE q.chunk_id = c.chunk_id)
              AND NOT EXISTS (SELECT 1 FROM chunk_enrichments e WHERE e.chunk_id = c.chunk_id)
              AND NOT EXISTS (SELECT 1 FROM chunk_rejections r WHERE r.chunk_id = c.chunk_id)
            LIMIT ?
        """
        with self._connection() as con:
            return [r["doc_id"] for r in con.execute(sql, [*exclude, limit]).fetchall()]

    def get_chunks_to_enrich(self, doc_id: str) -> List[Dict[str, Any]]:
        """Usable chunks of a document, in order, that have no QA yet (an interrupted run resumes here)."""
        sql = """
            SELECT c.*, e.summary AS existing_summary, e.tags AS existing_tags
            FROM chunks c
            LEFT JOIN chunk_enrichments e ON c.chunk_id = e.chunk_id
            WHERE c.doc_id = ? AND c.should_use = 1
              AND NOT EXISTS (SELECT 1 FROM chunk_qa q WHERE q.chunk_id = c.chunk_id)
              AND NOT EXISTS (SELECT 1 FROM chunk_rejections r WHERE r.chunk_id = c.chunk_id)
            ORDER BY c.chunk_index
        """
        with self._connection() as con:
            return [self._chunk_row(r) for r in con.execute(sql, (doc_id,)).fetchall()]

    def save_enrichment(self, chunk_id: str, data: Dict[str, Any]) -> None:
        with self._connection() as con:
            con.execute(
                "INSERT OR REPLACE INTO chunk_enrichments (chunk_id, tags, triplets, summary, processed_at) VALUES (?,?,?,?,?)",
                (chunk_id, json.dumps(data.get("tags", [])), json.dumps(data.get("triplets", [])), data.get("summary", ""), _now()),
            )

    def delete_enrichment(self, chunk_id: str) -> None:
        """Forget a chunk's enrichment so it counts as not yet attempted."""
        with self._connection() as con:
            con.execute("DELETE FROM chunk_enrichments WHERE chunk_id = ?", (chunk_id,))

    def get_enrichment(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        with self._connection() as con:
            row = con.execute("SELECT * FROM chunk_enrichments WHERE chunk_id = ?", (chunk_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["tags"] = json.loads(d["tags"] or "[]")
        d["triplets"] = json.loads(d["triplets"] or "[]")
        return d

    def save_qa(self, chunk_id: str, pairs: Sequence[Dict[str, Any]]) -> None:
        rows = []
        for i, qa in enumerate(pairs):
            rows.append(
                (
                    f"{chunk_id}_q{i + 1}", chunk_id,
                    qa.get("question_text", qa.get("question", "")).strip(),
                    qa.get("answer_text", qa.get("answer", "")).strip(),
                    qa.get("source_quote", "").strip(),
                    qa.get("difficulty", "Medium"),
                    qa.get("question_type", qa.get("type", "Fact")).capitalize(),
                )
            )
        if rows:
            with self._connection() as con:
                con.executemany(
                    "INSERT OR REPLACE INTO chunk_qa (qa_id, chunk_id, question_text, answer_text, source_quote, difficulty, question_type) VALUES (?,?,?,?,?,?,?)",
                    rows,
                )

    def get_qa_for_chunk(self, chunk_id: str) -> List[Dict[str, Any]]:
        with self._connection() as con:
            return [dict(r) for r in con.execute("SELECT * FROM chunk_qa WHERE chunk_id = ?", (chunk_id,)).fetchall()]

    def get_qa_for_document(self, doc_id: str) -> List[Dict[str, Any]]:
        sql = """
            SELECT q.*, c.doc_id FROM chunk_qa q JOIN chunks c ON c.chunk_id = q.chunk_id
            WHERE c.doc_id = ? ORDER BY c.chunk_index
        """
        with self._connection() as con:
            return [dict(r) for r in con.execute(sql, (doc_id,)).fetchall()]

    def save_rejections(self, chunk_id: str, rejections: Sequence[Dict[str, Any]]) -> None:
        if not rejections:
            return
        now = _now()
        rows = [
            (
                f"{chunk_id}_rej{i + 1}", chunk_id, r.get("level"),
                (r.get("question") or "")[:500], (r.get("answer") or "")[:1000],
                r.get("reason", "Unknown"), now,
            )
            for i, r in enumerate(rejections)
        ]
        with self._connection() as con:
            con.execute("DELETE FROM chunk_rejections WHERE chunk_id = ?", (chunk_id,))  # re-runs replace, not append
            con.executemany(
                "INSERT INTO chunk_rejections (rejection_id, chunk_id, level, question_text, answer_text, reason, rejected_at) VALUES (?,?,?,?,?,?,?)",
                rows,
            )

    def get_rejections_for_document(self, doc_id: str) -> List[Dict[str, Any]]:
        sql = """
            SELECT r.* FROM chunk_rejections r JOIN chunks c ON c.chunk_id = r.chunk_id
            WHERE c.doc_id = ? ORDER BY r.rejected_at DESC
        """
        with self._connection() as con:
            return [dict(r) for r in con.execute(sql, (doc_id,)).fetchall()]

    def rejection_summary(self) -> Dict[str, int]:
        """{reason: count}: which gate rejects the most. The first thing to read when tuning."""
        with self._connection() as con:
            rows = con.execute("SELECT reason, COUNT(*) n FROM chunk_rejections GROUP BY reason ORDER BY n DESC").fetchall()
        return {r["reason"]: r["n"] for r in rows}

    def stats(self) -> Dict[str, int]:
        queries = {
            "documents": "SELECT COUNT(*) FROM documents",
            "chunks": "SELECT COUNT(*) FROM chunks",
            "usable_chunks": "SELECT COUNT(*) FROM chunks WHERE should_use = 1",
            "enriched_chunks": "SELECT COUNT(*) FROM chunk_enrichments",
            "qa_pairs": "SELECT COUNT(*) FROM chunk_qa",
            "rejected_pairs": "SELECT COUNT(*) FROM chunk_rejections",
        }
        with self._connection() as con:
            return {k: con.execute(q).fetchone()[0] for k, q in queries.items()}
