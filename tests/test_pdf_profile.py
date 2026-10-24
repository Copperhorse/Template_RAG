"""pdf_profile: built from tiny PDFs made with PyMuPDF, so no model and no fixture files are needed."""

import pymupdf
import pytest

from rag_template.pdf_profile import PdfProfile, choose_backend, profile_pdf

PROSE = "The regulator may by order in writing require the company to furnish returns within thirty days. " * 4


def make_pdf(path, pages):
    """pages: list of callables (page) -> None"""
    doc = pymupdf.open()
    for draw in pages:
        draw(doc.new_page())
    doc.save(str(path))
    return str(path)


def prose(page):
    page.insert_textbox(pymupdf.Rect(50, 50, 560, 700), PROSE, fontname="helv", fontsize=11)


def code(page):
    page.insert_textbox(
        pymupdf.Rect(50, 50, 560, 700), "def f(x):\n    return x + 1\n" * 12, fontname="cour", fontsize=10
    )


def maths(page):
    page.insert_textbox(pymupdf.Rect(50, 50, 560, 300), PROSE, fontname="helv", fontsize=11)
    # the built-in Symbol font stands in for a math font (its glyphs are not extractable as Unicode, its name is)
    page.insert_textbox(
        pymupdf.Rect(50, 320, 560, 700), "ab cd ef gh ij kl mn op qr st " * 6, fontname="symb", fontsize=11
    )


def bullets(page):
    page.insert_textbox(pymupdf.Rect(50, 50, 560, 700), PROSE, fontname="helv", fontsize=11)
    for i in range(8):
        page.insert_text((30, 60 + 20 * i), "a", fontname="symb", fontsize=11)  # one Symbol glyph per bullet


def scanned(page):
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 200, 200), False)
    pix.set_rect(pix.irect, (230, 230, 230))
    page.insert_image(page.rect, pixmap=pix)


def test_plain_prose_goes_to_pymupdf4llm(tmp_path):
    p = profile_pdf(make_pdf(tmp_path / "a.pdf", [prose] * 4))
    assert p.scanned_share == 0 and p.math_pages_share == 0 and choose_backend(p) == "pymupdf4llm"


def test_code_alone_stays_with_pymupdf4llm(tmp_path):
    p = profile_pdf(make_pdf(tmp_path / "b.pdf", [code] * 4))
    assert p.mono_share > 0.9 and choose_backend(p) == "pymupdf4llm"


def test_math_heavy_document_goes_to_docling(tmp_path):
    p = profile_pdf(make_pdf(tmp_path / "c.pdf", [maths] * 4))
    assert p.math_pages_share == 1.0 and choose_backend(p) == "docling"


def test_scanned_pages_go_to_docling(tmp_path):
    p = profile_pdf(make_pdf(tmp_path / "d.pdf", [scanned] * 4))
    assert p.scanned_share == 1.0 and choose_backend(p) == "docling"


def test_symbol_font_bullets_are_not_math(tmp_path):
    p = profile_pdf(make_pdf(tmp_path / "g.pdf", [bullets] * 6))
    assert p.math_pages_share == 0 and choose_backend(p) == "pymupdf4llm"


def test_a_few_math_pages_in_a_long_text_do_not_flip_the_choice(tmp_path):
    p = profile_pdf(make_pdf(tmp_path / "e.pdf", [prose] * 18 + [maths] * 2))  # 10% of pages
    assert 0 < p.math_pages_share < 0.2 and choose_backend(p) == "pymupdf4llm"


@pytest.mark.parametrize(
    "scanned_share,math_pages,expected", [(0.5, 0, "docling"), (0.49, 0.19, "pymupdf4llm"), (0, 0.2, "docling")]
)
def test_thresholds(scanned_share, math_pages, expected):
    prof = PdfProfile(
        pages=10,
        sampled=10,
        scanned_share=scanned_share,
        math_font_share=0,
        math_char_share=0,
        mono_share=0,
        math_pages_share=math_pages,
    )
    assert choose_backend(prof) == expected


def test_sampling_caps_the_work_on_a_long_document(tmp_path):
    p = profile_pdf(make_pdf(tmp_path / "f.pdf", [prose] * 60), sample_pages=10)
    assert p.pages == 60 and p.sampled == 10


def test_a_conversion_with_undecoded_formulas_is_not_cached_so_a_re_upload_converts_again(tmp_path, monkeypatch):
    import pymupdf

    from rag_template import converters
    from rag_template.config import PdfSettings

    pdf = tmp_path / "paper.pdf"
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), "hello")
    doc.save(pdf)
    cache = tmp_path / "cache"
    settings = PdfSettings(backend="pymupdf4llm", cache=str(cache), check=False)  # formulas=True by default
    outputs = iter(
        ["Equation <!-- formula-not-decoded --> left by a crashed stage.", "Equation y = x repaired on the second run."]
    )
    monkeypatch.setattr(converters, "_run_backend", lambda *a, **k: next(outputs))

    _, first = converters.convert_pdf(pdf, settings)
    assert "formula-not-decoded" in first and not list(cache.glob("*.md"))  # damaged: nothing was stored
    _, second = converters.convert_pdf(pdf, settings)  # same file, converted again rather than served from the cache
    assert "repaired" in second and len(list(cache.glob("*.md"))) == 1
    monkeypatch.setattr(
        converters, "_run_backend", lambda *a, **k: (_ for _ in ()).throw(AssertionError("served from the cache"))
    )
    assert "repaired" in converters.convert_pdf(pdf, settings)[1]
