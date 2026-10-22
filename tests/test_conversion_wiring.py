"""The conversion check is carried through converters -> ingest -> the database, and never breaks ingestion."""
import json
import sqlite3

from rag_template import converters
from rag_template.ingest import ingest
from rag_template.store.db import Database
from rag_template.store.dedupe import SimHashIndex

REPORT = {"verdict": "warn", "reason": "", "metrics": {"fused_numeric": 1}, "warnings": ["1 numeric token(s) fused"], "examples": {"fused": ["15M on Sudoku"]}}


def test_an_old_database_gets_the_column_and_keeps_its_rows(tmp_path):
    path = tmp_path / "old.db"
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE documents (doc_id TEXT PRIMARY KEY, source TEXT, name TEXT, kind TEXT, title TEXT, simhash TEXT, sha256 TEXT, content_length INTEGER, processed_at TEXT)")
    con.execute("INSERT INTO documents VALUES ('d1','old.pdf','old.pdf','pdf','t','0','sha',5,'2026-01-01T00:00:00')")
    con.commit()
    con.close()
    db = Database(path)
    old = db.get_document("d1")
    assert old["source"] == "old.pdf" and old["conversion_json"] is None
    db.save_document("d2", "new.pdf", "0", 5, "sha2", conversion_json=json.dumps(REPORT))
    assert json.loads(db.get_document("d2")["conversion_json"])["verdict"] == "warn"


def test_ingest_stores_and_returns_the_check(tmp_path, monkeypatch, caplog):
    text = "# Title\n\n" + "A paragraph of ordinary prose that is long enough to be indexed as a chunk of its own. " * 6
    monkeypatch.setattr(converters, "convert", lambda path, pdf=None: ({"format": "pdf", "title": "t", "conversion_check": REPORT}, text))
    f = tmp_path / "doc.pdf"
    f.write_bytes(b"%PDF-1.4 stand-in")
    db = Database(tmp_path / "x.db")
    with caplog.at_level("WARNING"):
        res = ingest(f, db, SimHashIndex())
    assert res.ok and res.conversion == REPORT
    assert json.loads(db.get_document(res.doc_id)["conversion_json"]) == REPORT
    assert any("Conversion check" in r.message and "fused" in r.message for r in caplog.records)


def test_a_clean_or_absent_check_stores_nothing_and_logs_nothing(tmp_path, monkeypatch, caplog):
    text = "# Title\n\n" + "Another paragraph of ordinary prose that is long enough to be indexed on its own. " * 6
    monkeypatch.setattr(converters, "convert", lambda path, pdf=None: ({"format": "md", "title": "t"}, text))
    f = tmp_path / "doc.md"
    f.write_text("x")
    db = Database(tmp_path / "y.db")
    with caplog.at_level("WARNING"):
        res = ingest(f, db, SimHashIndex())
    assert res.ok and res.conversion is None and db.get_document(res.doc_id)["conversion_json"] is None
    assert not any("Conversion check" in r.message for r in caplog.records)


def test_the_setting_turns_the_check_off_and_a_failing_check_cannot_break_conversion(tmp_path, monkeypatch):
    from rag_template import convcheck
    from rag_template.config import PdfSettings

    monkeypatch.setattr(convcheck, "check_conversion", lambda pdf, md: convcheck.ConversionReport("ok"))
    info = {}
    assert converters._checked(tmp_path / "a.pdf", info, "md", PdfSettings(check=False)) == "md" and "conversion_check" not in info
    converters._checked(tmp_path / "a.pdf", info, "md", PdfSettings(check=True))
    assert info["conversion_check"]["verdict"] == "ok"
    # the real check swallows its own errors (a missing file is a 'not-run', not an exception)
    monkeypatch.undo()
    assert convcheck.check_conversion(tmp_path / "missing.pdf", "text").verdict == "not-run"


def test_pdf_settings_come_from_the_environment_in_one_place(monkeypatch):
    from rag_template.config import PdfSettings, Settings

    for name in ("RAG_PDF_BACKEND", "RAG_PDF_FORMULAS", "RAG_PDF_LAYOUT_ENGINE", "RAG_CONVERT_CACHE", "RAG_CONVERSION_CHECK"):
        monkeypatch.delenv(name, raising=False)
    assert PdfSettings.from_env() == PdfSettings() and Settings.from_env().pdf == PdfSettings()
    monkeypatch.setenv("RAG_PDF_BACKEND", "Docling")
    monkeypatch.setenv("RAG_PDF_FORMULAS", "off")
    monkeypatch.setenv("RAG_PDF_LAYOUT_ENGINE", "ONNX")
    monkeypatch.setenv("RAG_CONVERT_CACHE", "/tmp/c")
    monkeypatch.setenv("RAG_CONVERSION_CHECK", "0")
    assert Settings.from_env().pdf == PdfSettings(backend="docling", formulas=False, layout_engine="onnx", cache="/tmp/c", check=False)
    monkeypatch.setenv("RAG_PDF_BACKEND", "nonsense")
    assert PdfSettings.from_env().backend == "auto"


def test_the_converter_uses_the_settings_it_is_given_not_the_environment(tmp_path, monkeypatch):
    import pymupdf

    from rag_template.config import PdfSettings

    pdf = tmp_path / "t.pdf"
    doc = pymupdf.open()
    doc.new_page().insert_text((50, 100), "Plain text on the only page of this test document. " * 4, fontname="helv", fontsize=11)
    doc.save(str(pdf))
    calls = []
    monkeypatch.setattr(converters, "_run_backend", lambda path, backend, settings: calls.append(backend) or "# Heading\n\nBody text of the page.")
    monkeypatch.setenv("RAG_PDF_BACKEND", "docling")  # must be ignored: explicit settings win
    monkeypatch.setenv("RAG_CONVERSION_CHECK", "on")
    info, md = converters.convert_pdf(pdf, PdfSettings(backend="pymupdf4llm", cache="off", check=False))
    assert calls == ["pymupdf4llm"] and info["backend"] == "pymupdf4llm" and "conversion_check" not in info and "Body text" in md


def test_the_cache_key_follows_the_settings(tmp_path):
    from rag_template.config import PdfSettings

    pdf = tmp_path / "k.pdf"
    pdf.write_bytes(b"%PDF-1.4 stand-in")
    base = PdfSettings(cache=str(tmp_path / "cache"), layout_engine="torch")
    keys = {converters._cache_file(pdf, b, s) for b, s in (("docling", base), ("pymupdf4llm", base), ("docling", PdfSettings(cache=base.cache, layout_engine="torch", formulas=False)))}
    assert len(keys) == 3 and all(k.parent == tmp_path / "cache" for k in keys)
    assert converters._cache_file(pdf, "docling", PdfSettings(cache="off")) is None
