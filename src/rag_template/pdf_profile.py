"""
pdf_profile.py: a cheap look at a PDF (no model, a few seconds) to pick the converter that suits it.

Measured (evals/results/pdf_backends.md): pymupdf4llm keeps clean digital text and code intact and is fast;
Docling recovers display equations (as LaTeX) and reads scans about twice as fast, but scrambled the reading order
of a statute and flattened code to one line. So the choice depends on what the document contains:

    scanned pages (no text layer)         -> docling      (equal OCR quality, ~2x faster, one document)
    formula-heavy and not code-heavy      -> docling      (pymupdf4llm drops display equations)
    everything else                       -> pymupdf4llm

The profile is sampled (evenly spaced pages), so it costs about the same for a 20-page and a 700-page book.
"""

import os
import re
from functools import lru_cache
from dataclasses import dataclass
from typing import List

# Fonts that typeset mathematics: TeX (Computer Modern math), Symbol, Mathematical Pi, STIX, MathType, Cambria Math...
_MATH_FONT = re.compile(
    r"(cmmi|cmsy|cmex|cmbsy|cmmib|msam|msbm|eufm|rsfs|lmmath|latinmodern-?math|cambria ?math|stix(?:two)?math|"
    r"mathematicalpi|mtmi|mtsy|mt-?extra|mtsymbol|euclid|symbolmt|^symbol|asana-?math|xits-?math|texgyre.*math)",
    re.I,
)
_SYMBOL_FONT = re.compile(r"^symbol", re.I)
_MONO_FONT = re.compile(
    r"(courier|mono|consolas|menlo|inconsolata|lucidaconsole|source ?code|fira ?code|cmtt|dejavusansmono|jetbrains)",
    re.I,
)
# Greek, mathematical operators, arrows, super/subscripts and the n-ary/relations blocks
_MATH_CHAR = re.compile(r"[Ͱ-Ͽ⁰-₟←-⇿∀-⋿⨀-⫿⟀-⟯⦀-⧿]")


@dataclass
class PdfProfile:
    pages: int
    sampled: int
    scanned_share: float  # sampled pages with (almost) no text and an image
    math_font_share: float  # characters set in a math font / all characters
    math_char_share: float  # math symbols (Greek, operators, ...) / all characters
    mono_share: float  # characters in a monospace font / all characters
    math_pages_share: float  # sampled pages where math characters are > 1% of the page


def _sample(n: int, k: int) -> List[int]:
    if n <= k:
        return list(range(n))
    step = n / k
    return sorted({int(i * step + step / 2) for i in range(k)})


def profile_pdf(path: str, sample_pages: int = 40) -> PdfProfile:
    """Memoised per (file, size, mtime): ingestion asks twice (backend routing, then the conversion check)."""
    st = os.stat(path)
    return _profile(str(path), st.st_size, st.st_mtime_ns, sample_pages)


@lru_cache(maxsize=16)
def _profile(path: str, size: int, mtime_ns: int, sample_pages: int) -> PdfProfile:
    import pymupdf

    with pymupdf.open(path) as doc:
        n = len(doc)
        idx = _sample(n, sample_pages)
        chars = math_font = math_chars = mono = scanned = math_pages = 0
        for i in idx:
            page = doc[i]
            page_chars = page_math = 0
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        text = span["text"]
                        k = len(text.strip())
                        if not k:
                            continue
                        page_chars += k
                        font = span["font"].split("+")[-1]
                        is_math_font = bool(_MATH_FONT.search(font)) and not (
                            k == 1 and _SYMBOL_FONT.match(font)
                        )  # Word/PowerPoint bullets are one Symbol glyph
                        if is_math_font:
                            math_font += k
                            page_math += k
                        if _MONO_FONT.search(font):
                            mono += k
                        m = len(_MATH_CHAR.findall(text))
                        math_chars += m
                        page_math += 0 if is_math_font else m
            chars += page_chars
            if page_chars < 20 and page.get_images():
                scanned += 1
            if page_chars and page_math / page_chars > 0.01:
                math_pages += 1
    total = max(chars, 1)
    return PdfProfile(
        pages=n,
        sampled=len(idx),
        scanned_share=scanned / max(len(idx), 1),
        math_font_share=math_font / total,
        math_char_share=math_chars / total,
        mono_share=mono / total,
        math_pages_share=math_pages / max(len(idx), 1),
    )


SCANNED_THRESHOLD = 0.5  # share of sampled pages with no text layer
MATH_PAGES_THRESHOLD = (
    0.2  # measured gap: math-heavy books 0.33-0.65, everything else <= 0.10 (see evals/results/pdf_backends.md)
)


def choose_backend(profile: PdfProfile) -> str:
    """ "docling" for scans and formula-heavy documents, otherwise "pymupdf4llm". Thresholds come from 13 documents
    of which only 4 had a known better backend; treat them as a starting point, not a result. A book that mixes
    heavy math and code goes to docling, which keeps its equations but may flatten code (unresolved)."""
    if profile.scanned_share >= SCANNED_THRESHOLD:
        return "docling"
    if profile.math_pages_share >= MATH_PAGES_THRESHOLD:
        return "docling"
    return "pymupdf4llm"
