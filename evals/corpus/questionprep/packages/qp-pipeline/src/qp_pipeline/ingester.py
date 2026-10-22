"""
ingester.py

"""

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

current_file = Path(__file__).resolve()
project_root = current_file.parents[4]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from qp_core import models
from qp_core.DBManager import DBManager
from qp_core.IDGenerator import IDGenerator
from qp_core.SimHashHandler import SimHashHandler

from qp_pipeline.ChunkEvaluator import ChunkEvaluator
from qp_pipeline.MarkdownChunker import ChunkConfig, MarkdownChunker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Ingester")


def get_default_db_path():
    return project_root / "data" / "rag_staging.db"


@dataclass(frozen=True)
class IngestResult:
    """Outcome of ingest(). `status` is one of ok | duplicate | failed."""

    status: Literal["ok", "duplicate", "failed"]
    file_id: Optional[str] = None  # set when status == "ok"
    duplicate_of: Optional[str] = None  # set when status == "duplicate"
    message: str = ""

    @property
    def ok(self) -> bool:
        return self.status == "ok"


def ingest(
    file_path,
    db_manager,
    converter,
    chunker,
    evaluator,
    id_generator,
    simhash_handler,
    on_duplicate: Literal["ask", "skip"] = "ask",
    sha256: Optional[str] = None,
) -> IngestResult:
    """
    Ingest a PDF file through the full pipeline.

    Never raises for expected failures; inspect `.status`:
        ok         file saved, `.file_id` set
        duplicate  near-duplicate of `.duplicate_of` (SimHash); nothing saved
        failed     conversion / empty document / DB error; nothing saved

    on_duplicate: "skip" (web / batch) drops the file; "ask" prompts on stdin (CLI).
    Which files count as duplicates is decided by whatever `simhash_handler` was loaded
    with, so callers scope it (the web app loads only the uploading user's files).
    `sha256` is stored on the file row so exact re-uploads can be caught before conversion.
    """
    file_path = Path(file_path)

    # Step 1: Convert
    try:
        metadata, markdown = converter.process_document(str(file_path))
        if not markdown:
            logger.error(f"Empty markdown for {file_path}")
            return IngestResult("failed", message="The document has no extractable text")
    except Exception as e:
        logger.error(f"Conversion failed for {file_path}: {e}")
        return IngestResult("failed", message=f"Conversion failed: {e}")

    # Step 2: Duplicate Detection
    duplicate_check = simhash_handler.check_duplicate(markdown)
    if duplicate_check["is_duplicate"]:
        original = duplicate_check["duplicate_file_ids"][0]
        logger.warning(f"Duplicate detected: {file_path} ~ {original}")
        if on_duplicate == "skip" or input("Continue anyway? (y/n): ").lower() != "y":
            return IngestResult(
                "duplicate",
                duplicate_of=original,
                message="Near-duplicate of an existing document",
            )

    # Step 3 & 4: ID and Chunking
    file_id = id_generator.generate_file_id()
    chunks = chunker.process(markdown)

    # Step 5: Evaluate
    eval_stats = evaluator.evaluate_chunks(chunks)
    evaluated_chunks = eval_stats["evaluated_chunks"]

    # Step 6 & 7: Database Save
    try:
        file_name = file_path.name
        if "_" in file_name:
            file_name = file_name.split("_", 1)[-1]

        db_manager.save_file_metadata(
            file_id=file_id,
            file_path=file_name,
            simhash=duplicate_check["simhash"],
            metadata=metadata,
            content_length=len(markdown),
            sha256=sha256,
        )
        db_manager.save_chunks(file_id=file_id, chunks=evaluated_chunks)
        simhash_handler.add_to_index(file_id, duplicate_check["simhash"])
        logger.info(f"Chunks saved for file {file_id[:8]}")
        return IngestResult("ok", file_id=file_id)
    except Exception as e:
        logger.error(f"DB Error for {file_path}: {e}")
        return IngestResult("failed", message=f"Database error: {e}")


def batch_process(db_path=None):
    """Processes all PDFs in a specified directory."""
    if db_path is None:
        db_path = get_default_db_path()

    dir_path = input("\nEnter directory path to scan for PDFs: ")
    p = Path(dir_path)
    if not p.exists() or not p.is_dir():
        print("❌ Invalid directory.")
        return

    files = list(p.glob("*.pdf"))
    print(f"\n📂 Found {len(files)} PDF files in {dir_path}")

    converter = models.get_docling_converter()
    chunk_config = ChunkConfig(max_chunk_tokens=1000, merge_short_chunks=True)
    chunker = MarkdownChunker(chunk_config)
    evaluator = ChunkEvaluator()
    id_generator = IDGenerator()
    simhash_handler = SimHashHandler(k=3)
    db_manager = DBManager(db_path=str(db_path))

    existing = (
        db_manager.get_all_simhashes()
        if hasattr(db_manager, "get_all_simhashes")
        else {}
    )
    simhash_handler.load_index_from_data(existing)

    success_count = 0
    for i, file_path in enumerate(files):
        print(f"\n[{i + 1}/{len(files)}] Processing: {file_path.name}")
        result = ingest(
            file_path,
            db_manager,
            converter,
            chunker,
            evaluator,
            id_generator,
            simhash_handler,
            on_duplicate="skip",
        )
        if result.ok:
            success_count += 1
            print(f"✅ Successfully processed (file_id={result.file_id[:8]}).")
        elif result.status == "duplicate":
            print(f"⚠️ Skipped: duplicate of {result.duplicate_of[:8]}.")
        else:
            print(f"⚠️ Failed: {result.message}")

    print(
        f"\n{'=' * 30}\nBATCH COMPLETE\nSuccess: {success_count}/{len(files)}\n{'=' * 30}"
    )


if __name__ == "__main__":
    target_db_path = get_default_db_path()
    mode = input("\nSelect mode:\n 1. Single file\n 2. Batch processing\nChoice: ")

    if mode == "1":
        converter = models.get_docling_converter()
        chunker = MarkdownChunker(ChunkConfig(max_chunk_tokens=1000))
        evaluator = ChunkEvaluator()
        id_generator = IDGenerator()
        simhash_handler = SimHashHandler()
        db_manager = DBManager(db_path=str(target_db_path))

        path = input("File path: ")
        result = ingest(
            path,
            db_manager,
            converter,
            chunker,
            evaluator,
            id_generator,
            simhash_handler,
        )
        print(f"Ingestion {result.status}. File ID: {result.file_id or result.duplicate_of}")
    elif mode == "2":
        batch_process(db_path=target_db_path)
