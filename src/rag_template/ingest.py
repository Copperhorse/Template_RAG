"""
ingest.py: file -> text -> duplicate check -> chunks -> quality gate -> database.

    ingest(path, db, dedupe)  ->  IngestResult(status="ok" | "duplicate" | "failed", ...)

Never raises for expected failures; inspect `.status`. Two duplicate checks run before any
expensive work: an exact SHA-256 of the file bytes (before conversion, so a re-uploaded PDF is
rejected in milliseconds) and a SimHash of the text (near-duplicates).

This module only touches the database. To replace a changed file use `RAG.ingest_path(path, replace=True)`,
which removes the old vectors first.
"""

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal, Optional

from rag_template import converters
from rag_template.config import PdfSettings
from rag_template.convcheck import ConversionReport
from rag_template.chunking import ChunkConfig, chunk_file
from rag_template.evaluator import ChunkEvaluator
from rag_template.pages import assign_pages
from rag_template.store.db import Database
from rag_template.store.dedupe import SimHashIndex

logger = logging.getLogger("rag_template.ingest")


@dataclass(frozen=True)
class IngestResult:
    status: Literal["ok", "duplicate", "failed"]
    doc_id: Optional[str] = None  # set when status == "ok"
    duplicate_of: Optional[str] = None  # set when status == "duplicate"
    message: str = ""
    chunks: int = 0
    usable_chunks: int = 0
    rejection_reasons: Optional[dict] = None
    conversion: Optional[dict] = None  # the PDF conversion check (convcheck.ConversionReport.as_dict()), when one ran

    @property
    def ok(self) -> bool:
        return self.status == "ok"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def ingest(
    path: str | Path,
    db: Database,
    dedupe: SimHashIndex,
    chunk_config: Optional[ChunkConfig] = None,
    evaluator: Optional[ChunkEvaluator] = None,
    source: Optional[str] = None,
    chunk_fn: Optional[Callable[..., list]] = None,
    pdf: Optional[PdfSettings] = None,
) -> IngestResult:
    """`source` is the name chunks cite (default: the path as given, which for a repository ingest is
    the path relative to its root). `chunk_fn(path, text, config, source=...)` replaces the default chunker
    (`chunk_file`), e.g. the fixed-window baseline used by the evals."""
    path = Path(path)
    source = source or str(path)
    evaluator = evaluator or ChunkEvaluator()
    chunk_config = chunk_config or ChunkConfig()

    try:
        digest = sha256_of(path)
    except OSError as e:
        return IngestResult("failed", message=f"Cannot read file: {e}")
    same = db.get_document_by_sha256(digest)
    if same:
        return IngestResult("duplicate", duplicate_of=same["doc_id"], message="Identical file already ingested")

    try:
        metadata, text = converters.convert(path, pdf)
    except Exception as e:
        logger.error(f"Conversion failed for {path}: {e}")
        return IngestResult("failed", message=f"Conversion failed: {e}")
    if not text or not text.strip():
        return IngestResult("failed", message="The document has no extractable text")

    check = dedupe.check(text)
    if check.is_duplicate:
        logger.warning(f"Near-duplicate: {path} ~ {check.duplicate_ids[0]}")
        return IngestResult(
            "duplicate", duplicate_of=check.duplicate_ids[0], message="Near-duplicate of an existing document"
        )

    conversion = metadata.get("conversion_check")
    chunks = (chunk_fn or chunk_file)(str(path), text, chunk_config, source=source)
    if not chunks:
        return IngestResult("failed", message="No chunks were produced")
    if metadata.get("page_marks"):
        located = assign_pages(chunks, text, metadata["page_marks"])
        logger.info(f"Page numbers for {located}/{len(chunks)} chunks of {source}")
    stats = evaluator.evaluate_chunks(chunks)

    doc_id = str(uuid.uuid4())
    try:
        db.save_document(
            doc_id,
            source,
            check.simhash,
            len(text),
            digest,
            kind=metadata.get("format", ""),
            title=metadata.get("title", ""),
            conversion_json=json.dumps(conversion) if conversion else None,
        )
        db.save_chunks(doc_id, stats["evaluated_chunks"])
    except Exception as e:
        logger.exception(f"Database error for {path}")
        db.delete_document(doc_id)
        return IngestResult("failed", message=f"Database error: {e}")

    report = ConversionReport.from_dict(conversion) if conversion else None
    if report and report.flagged:
        logger.warning(f"Conversion check for {source}: {report.summary()}")
    dedupe.add(doc_id, check.simhash)
    logger.info(f"Ingested {source}: {stats['accepted_chunks']}/{stats['total_chunks']} chunks usable")
    return IngestResult(
        "ok",
        doc_id=doc_id,
        chunks=stats["total_chunks"],
        usable_chunks=stats["accepted_chunks"],
        rejection_reasons=stats["rejection_reasons"],
        conversion=conversion,
    )
