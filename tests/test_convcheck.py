"""convcheck: each check on synthetic reference/output text, plus one integration test with a built PDF."""

import itertools
import shutil

import pymupdf
import pytest

from rag_template import convcheck as cc

_SYL = ["ba", "ko", "ri", "mu", "te", "so", "la", "vi", "no", "ge"]
_WORDS = ["".join(p) for p in itertools.product(_SYL, repeat=3)]  # 1000 distinct letter-only words, no digits


def filler(start: int, n: int) -> str:
    return " ".join(_WORDS[(start + i * 7) % len(_WORDS)] for i in range(n))


def ref_page(*parts: str) -> str:
    return " ".join(parts)


BASE = ref_page(filler(0, 120))


def check(ref_pages, md):
    return cc.compare(ref_pages, md)


def test_a_faithful_conversion_has_no_warnings():
    r = check([BASE], "# Title\n\n" + BASE)
    assert r.verdict == "ok" and not r.warnings and r.metrics["word_recall"] > 0.99 and r.metrics["run6_recall"] > 0.99


def test_a_marker_fused_into_a_value_is_reported():
    ref = ref_page(filler(0, 60), "footnote 1 5M on Sudoku and 19M on Maze", filler(300, 60))
    md = ref_page(filler(0, 60), "footnote 15M on Sudoku and 19M on Maze", filler(300, 60))
    r = check([ref], md)
    assert r.metrics["fused_numeric"] == 1 and "15m" in r.warnings[0] and r.verdict == "warn"
    assert any("15M" in s for s in r.examples["fused"])


def test_three_fused_numbers_make_the_verdict_bad():
    ref = ref_page(filler(0, 60), "a 1 5M b 2 7K c 3 9G", filler(300, 60))
    md = ref_page(filler(0, 60), "a 15M b 27K c 39G", filler(300, 60))
    assert check([ref], md).verdict == "bad"


def test_a_number_the_pdf_never_contained_is_novel_not_fused():
    ref = ref_page(filler(0, 100), "value 42")
    md = ref_page(filler(0, 100), "value 4242")
    r = check([ref], md)
    assert r.metrics["novel_numeric"] == 1 and r.metrics["fused_numeric"] == 0


def test_dropped_numbers_are_reported_when_many_vanish():
    nums = " ".join(f"row {n} value {n * 3 + 1}" for n in range(10, 40))
    r = check([ref_page(filler(0, 100), nums)], ref_page(filler(0, 100)))
    assert (
        r.metrics["dropped_numeric_ratio"] > 0.5 and any("missing" in w for w in r.warnings) and r.examples["dropped"]
    )


def test_page_numbers_and_running_headers_are_not_counted_as_dropped():
    pages = [f"Journal of Things\n{filler(i * 40, 60)}\n{i + 1}\n" for i in range(8)]
    md = "\n\n".join(filler(i * 40, 60) for i in range(8))
    r = check(pages, md)
    assert r.metrics["dropped_numeric_ratio"] == 0 and r.verdict == "ok"


def test_interleaved_text_keeps_the_words_but_breaks_the_runs():
    a, b = filler(0, 100).split(), filler(500, 100).split()
    ref = " ".join(a) + " " + " ".join(b)
    md = " ".join(x for pair in zip(a, b) for x in pair)  # every word still there, no 6-word run intact
    r = check([ref], md)
    assert r.metrics["word_recall"] > 0.99 and r.metrics["order_gap"] > cc.ORDER_GAP_WARN
    assert any("6-word runs" in w for w in r.warnings)


def test_dropped_text_lowers_word_recall():
    r = check([BASE], " ".join(BASE.split()[:80]))
    assert r.metrics["word_recall"] < cc.COVERAGE_WARN and any("words appear" in w for w in r.warnings)


def test_spaced_out_letters_are_junk_unless_the_pdf_has_them_too():
    junk = "$$f o r w a r d p a s s o f H$$"
    assert check([BASE], BASE + "\n" + junk).metrics["spaced_letter_runs"] == 1
    assert check([BASE + " f o r w a r d p a s s o f H"], BASE + "\n" + junk).metrics["spaced_letter_runs"] == 0


def test_ragged_table_flattened_code_and_unbalanced_fence_are_reported():
    table = "| a | b | c |\n|---|---|---|\n| 1 | 2 |\n| 3 | 4 | 5 | 6 |\n| 7 |\n"
    r = check([BASE], BASE + "\n\n" + table)
    assert r.metrics["ragged_tables"] == 1
    long_line = (
        "from typing import Annotated, Literal from pydantic import Field def search( query: str, limit: int = 10, order: str = 'a') "
        * 3
    )
    r = check([BASE], BASE + f"\n\n```\n{long_line}\n```\n\n```\n{long_line}\n```\n")
    assert r.metrics["flattened_code_blocks"] == 2 and any("one line" in w for w in r.warnings)
    assert check([BASE], BASE + "\n```\nx = 1\n").metrics["unbalanced_fences"] == 1


def test_a_well_formed_table_and_code_block_raise_nothing():
    md = BASE + "\n\n| a | b |\n|---|---|\n| x | y |\n| z | w |\n\n```\nx = 1\ny = 2\n```\n"
    assert check([BASE], md).verdict == "ok"


def test_too_little_text_is_not_run():
    assert cc.compare(["tiny"], "tiny").verdict == "not-run"


def test_missing_pdftotext_is_not_run_not_an_error(monkeypatch, tmp_path):
    monkeypatch.setattr(shutil, "which", lambda name: None)
    r = cc.check_conversion(tmp_path / "x.pdf", "text")
    assert r.verdict == "not-run" and "pdftotext" in r.reason and "not run" in r.summary()


def test_report_round_trips_through_a_dict():
    r = check([BASE], BASE)
    assert cc.ConversionReport.from_dict(r.as_dict()) == r


@pytest.mark.skipif(shutil.which("pdftotext") is None, reason="needs Poppler's pdftotext")
def test_integration_a_scan_is_not_run_and_a_text_pdf_is_compared(tmp_path):
    scan = pymupdf.open()
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 100, 100), False)
    pix.set_rect(pix.irect, (240, 240, 240))
    scan.new_page().insert_image(pymupdf.Rect(0, 0, 200, 200), pixmap=pix)
    scan.save(str(tmp_path / "scan.pdf"))
    assert cc.check_conversion(tmp_path / "scan.pdf", "anything").verdict == "not-run"

    doc = pymupdf.open()
    page = doc.new_page()
    text = " ".join(f"{w}." if i % 9 == 8 else w for i, w in enumerate(filler(0, 150).split()))
    page.insert_textbox(pymupdf.Rect(40, 40, 570, 760), text, fontname="helv", fontsize=10)
    doc.save(str(tmp_path / "text.pdf"))
    r = cc.check_conversion(tmp_path / "text.pdf", text)
    assert r.verdict == "ok" and r.metrics["word_recall"] > 0.95


def test_a_marker_glued_to_a_word_in_the_reference_is_not_a_dropped_number():
    ref = ref_page(filler(0, 100), "the sum on thursday2 was 5")
    r = check([ref], ref_page(filler(0, 100), "the sum on thursday was 5"))
    assert r.metrics["dropped_numeric_ratio"] == 0


def test_ordinals_in_any_notation_match_each_other():
    ref = ref_page(filler(0, 100), "on the 23rd day and the 7th")
    for notation in ("23rd day and the 7th", "23^rd day and the 7^th", "23 rd day and the 7 th"):
        r = check([ref], ref_page(filler(0, 100), "on the " + notation))
        assert r.metrics["dropped_numeric_ratio"] == 0 and r.metrics["novel_numeric"] == 0, notation


def test_letter_spaced_capitals_are_typography_not_junk():
    assert check([BASE], BASE + "\nC O N T E N T S O F T H E B O O K").metrics["spaced_letter_runs"] == 0


def test_numeric_findings_become_informational_on_equation_heavy_documents():
    ref = ref_page(filler(0, 60), "footnote 1 5M on Sudoku", filler(300, 60))
    md = ref_page(filler(0, 60), "footnote 15M on Sudoku", filler(300, 60))
    r = cc.compare([ref], md, numeric_checks=False)
    assert r.metrics["fused_numeric"] == 1 and not r.warnings and r.verdict == "ok"
