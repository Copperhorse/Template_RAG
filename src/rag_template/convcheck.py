"""
convcheck.py: validate a PDF -> Markdown conversion against an independent copy of the PDF's text, at ingest.

Why: every converter we tried corrupts text silently and differently (evals/results/pdf_backends.md, golden_trm.md):
pymupdf4llm fused a footnote marker into a value ("1" + "5M" -> "15M"), dropped display equations and mislabelled sections;
Docling scrambled a statute's reading order, flattened code to one line and emitted junk letters in formulas. Nothing
downstream can notice. This module compares the converted text with the PDF's text layer and *reports*; it never changes
what is indexed.

The reference must come from an engine independent of the converter: PyMuPDF's own text already reads "15M" (the
superscript marker and the text are adjacent spans with no space), so a PyMuPDF reference shares the bug. Poppler's
`pdftotext` keeps "1 5M". If `pdftotext` is missing, or the PDF has no text layer (a scan), the verdict is "not-run".

Checks (cheap, deterministic, no model):
  fused / novel numbers  (not on equation-heavy PDFs, where subscripts make them unreliable) digit-bearing tokens in the output that the PDF does not contain; "fused" = two adjacent
                         reference tokens glued together
  dropped numbers        digit tokens of the PDF that vanish from the output
  coverage and order     word recall, and the share of the PDF's 6-word runs that survive contiguous (a big gap = reordered)
  junk                   runs of single letters ("f o r w a r d"), U+FFFD, leftover tags
  structure              ragged tables, unbalanced code fences, code flattened to one line

Not caught: a scramble confined to a few paragraphs (tested: Docling's statute definitions; a windowed order check flags
the same layout-heavy regions for both backends and cannot isolate it), defects both extractors share (footnote text spliced into a sentence at a page break), table
columns that are misaligned but contain the right words, heading levels, and any scanned file. The thresholds were set
from a handful of documents (evals/results/conversion_check.md): a starting point, not a guarantee.
"""

import collections
import itertools
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from rag_template.mdclean import FENCE, TAGS
from rag_template.pdf_profile import MATH_PAGES_THRESHOLD, profile_pdf

_TOKEN = re.compile(r"\d+(?:[.,]\d+)+%?|[A-Za-z0-9]+%?")
_NUMBER_LIKE = re.compile(
    r"\d+(?:[.,]\d+)*(?:%|[a-z]{1,2})?$"
)  # a number, optionally with a unit ("5m", "87.4", "20%"); not "the1"
_ORDINAL = re.compile(r"(\d)\s*\^?\s*(?:st|nd|rd|th)\b", re.I)  # "23rd", "23 rd", "23^rd" are one thing
_SPACED_LETTERS = re.compile(r"(?:(?<![A-Za-z0-9])[A-Za-z](?![A-Za-z0-9]) ){6,}[A-Za-z](?![A-Za-z0-9])")
_PAGE_NUMBER_LINE = re.compile(r"^\s*\d{1,4}\s*$")
GRAM = 6

# Calibrated on the benchmark documents (evals/results/conversion_check.md); see the module docstring.
FUSED_BAD = 3  # fused numeric tokens at or above this make the verdict "bad"
DROPPED_RATIO_WARN = 0.10  # share of the PDF's distinct numeric tokens missing from the output
COVERAGE_WARN = 0.90
BAD_COVERAGE = 0.7  # below this share of the PDF's words the output is 'bad'
FLAT_CODE_WARN = 2  # code blocks collapsed onto one line
FLAT_CODE_BAD = 5
ORDER_GAP_WARN = 0.25  # unigram recall minus 6-gram recall; layout-heavy documents sit at 0.05-0.17, so only gross interleaving fires


@dataclass
class ConversionReport:
    verdict: str  # ok | warn | bad | not-run
    reason: str = ""  # why the check did not run
    metrics: Dict[str, float] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    examples: Dict[str, List[str]] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ConversionReport":
        return cls(
            d.get("verdict", "not-run"),
            d.get("reason", ""),
            d.get("metrics", {}),
            d.get("warnings", []),
            d.get("examples", {}),
        )

    @property
    def flagged(self) -> bool:
        """True when the conversion needs the reader's attention."""
        return self.verdict in ("warn", "bad")

    def summary(self) -> str:
        if self.verdict == "not-run":
            return f"conversion check not run: {self.reason}"
        head = f"conversion check: {self.verdict}"
        return head + ("".join(f"\n  - {w}" for w in self.warnings) if self.warnings else "")


# --------------------------------------------------------------------------- reference text


def reference_pages(pdf: str | Path, timeout: float = 120.0) -> Tuple[Optional[List[str]], str]:
    """The PDF's text per page from Poppler's pdftotext, or (None, reason)."""
    exe = shutil.which("pdftotext")
    if not exe:
        return None, "pdftotext (Poppler) is not installed"
    try:
        out = subprocess.run(
            [exe, "-enc", "UTF-8", str(pdf), "-"], capture_output=True, text=True, timeout=timeout, check=True
        ).stdout
    except (subprocess.SubprocessError, OSError) as e:
        return None, f"pdftotext failed: {e}"
    pages = out.split("\f")
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    if not pages or sum(len(p.strip()) for p in pages) < 40 * len(pages):
        return None, "the PDF has no text layer (a scan)"
    return pages, ""


def _strip_page_furniture(pages: Sequence[str]) -> List[str]:
    """Drop bare page numbers and lines repeated at the top/bottom of many pages: converters rightly omit them."""
    edge = collections.Counter()
    for p in pages:
        lines = [ln.strip() for ln in p.splitlines() if ln.strip()]
        for ln in set(lines[:2] + lines[-2:]):
            edge[re.sub(r"\d+", "#", ln)] += 1
    repeated = {k for k, n in edge.items() if n >= max(3, len(pages) // 4)}
    out = []
    for p in pages:
        lines = [ln for ln in p.splitlines()]
        keep = []
        nonblank = [i for i, ln in enumerate(lines) if ln.strip()]
        edges = set(nonblank[:2] + nonblank[-2:])
        for i, ln in enumerate(lines):
            if i in edges and (_PAGE_NUMBER_LINE.match(ln) or re.sub(r"\d+", "#", ln.strip()) in repeated):
                continue
            keep.append(ln)
        out.append("\n".join(keep))
    return out


# --------------------------------------------------------------------------- the checks


def _tokens(text: str) -> List[str]:
    return [t.lower() for t in _TOKEN.findall(_ORDINAL.sub(r"\1", text))]


def _has_digit(t: str) -> bool:
    return any(c.isdigit() for c in t)


def _snippet(md_norm: str, needle: str, width: int = 60) -> str:
    """The text around `needle` as a whole token in the (ordinal-normalised) Markdown."""
    m = re.search(r"(?<![A-Za-z0-9])" + re.escape(needle) + r"(?![A-Za-z0-9])", md_norm, re.I)
    if not m:
        return needle
    return re.sub(r"\s+", " ", md_norm[max(0, m.start() - width) : m.end() + width]).strip()


def _spaced_letters(text: str) -> List[str]:
    """Runs of single letters that include lower case: capitals are typography ("C O N T E N T S"), lower case is garbled maths."""
    return [r for r in _SPACED_LETTERS.findall(text) if any(c.islower() for c in r)]


@dataclass
class _Findings:
    metrics: Dict[str, float]
    warnings: List[str] = field(default_factory=list)
    examples: Dict[str, List[str]] = field(default_factory=dict)


def _numeric(f: _Findings, ref_c, ref_all: Sequence[str], out_c, md_norm: str, report: bool) -> None:
    """Fused / novel numeric tokens and dropped numbers. `report=False` keeps the examples but raises no warning."""
    pairs = {a + b for a, b in zip(ref_all, ref_all[1:])}
    ref_set = set(ref_c) | set(ref_all)
    novel = sorted((t for t in out_c if _has_digit(t) and t not in ref_set), key=lambda t: -out_c[t])
    fused = [t for t in novel if t in pairs]
    other = [t for t in novel if t not in pairs]
    f.metrics["fused_numeric"], f.metrics["novel_numeric"] = len(fused), len(other)
    if fused:
        f.examples["fused"] = [_snippet(md_norm, t) for t in fused[:5]]
        if report:
            f.warnings.append(
                f"{len(fused)} numeric token(s) fused from two words of the PDF, e.g. '{fused[0]}' (a footnote marker or label glued to a value)"
            )
    if other:
        f.examples["novel"] = [_snippet(md_norm, t) for t in other[:5]]

    ref_nums = [
        t for t in ref_c if _NUMBER_LIKE.match(t)
    ]  # pdftotext itself glues markers to words ("thursday2"); those are not numbers the converter lost
    dropped = [t for t in ref_nums if out_c.get(t, 0) == 0]
    ratio = len(dropped) / max(len(ref_nums), 1)
    f.metrics["dropped_numeric_ratio"] = round(ratio, 4)
    if dropped:
        f.examples["dropped"] = dropped[:8]
    if report and ratio > DROPPED_RATIO_WARN:
        f.warnings.append(
            f"{100 * ratio:.0f}% of the PDF's distinct numbers are missing from the output (lost table cells, equations or figures)"
        )


def _coverage_and_order(f: _Findings, ref: Sequence[str], out: Sequence[str], ref_c, out_c) -> None:
    cover = sum(min(n, out_c.get(t, 0)) for t, n in ref_c.items()) / len(ref)
    out_grams = {tuple(out[i : i + GRAM]) for i in range(len(out) - GRAM + 1)}
    ref_grams = [tuple(ref[i : i + GRAM]) for i in range(len(ref) - GRAM + 1)]
    gram_recall = sum(1 for g in ref_grams if g in out_grams) / max(len(ref_grams), 1)
    gap = cover - gram_recall
    f.metrics.update(word_recall=round(cover, 4), run6_recall=round(gram_recall, 4), order_gap=round(gap, 4))
    if cover < COVERAGE_WARN:
        f.warnings.append(f"only {100 * cover:.0f}% of the PDF's words appear in the output (dropped text)")
    if gap > ORDER_GAP_WARN:
        f.warnings.append(
            f"words are present but {100 * gap:.0f} points of 6-word runs are broken (reordered or interleaved text)"
        )


def _junk(f: _Findings, ref_text: str, markdown: str) -> None:
    spaced = _spaced_letters(markdown)
    extra = len(spaced) - len(_spaced_letters(ref_text))
    f.metrics["spaced_letter_runs"] = max(extra, 0)
    if extra >= 1:
        f.examples["spaced_letters"] = spaced[:3]
        f.warnings.append(f"{extra} run(s) of spaced-out single letters (garbled formula text)")
    f.metrics["replacement_chars"] = markdown.count("\ufffd")
    f.metrics["leftover_tags"] = len(TAGS.findall(markdown))
    if f.metrics["replacement_chars"] or f.metrics["leftover_tags"]:
        f.warnings.append(
            f"{int(f.metrics['replacement_chars'])} replacement character(s), {int(f.metrics['leftover_tags'])} leftover HTML tag(s)"
        )


def _structure(f: _Findings, markdown: str) -> None:
    ragged, tables = _ragged_tables(markdown)
    unbalanced, flat = _fence_problems(markdown)
    f.metrics.update(tables=tables, ragged_tables=ragged, unbalanced_fences=unbalanced, flattened_code_blocks=flat)
    if ragged:
        f.warnings.append(f"{ragged} of {tables} table(s) have rows with differing cell counts")
    if unbalanced:
        f.warnings.append("unbalanced code fence(s)")
    if flat >= FLAT_CODE_WARN:
        f.warnings.append(f"{flat} code block(s) collapsed onto one line")


def compare(reference_pages_: Sequence[str], markdown: str, numeric_checks: bool = True) -> ConversionReport:
    """Pure function: score `markdown` against the PDF's per-page reference text. `numeric_checks=False` (equation-heavy
    documents) reports the numeric findings as examples only: subscripts and reordered symbols make them unreliable there."""
    ref_text = "\n".join(_strip_page_furniture(reference_pages_))
    ref = _tokens(ref_text)
    if len(ref) < 50:
        return ConversionReport("not-run", reason="too little text in the PDF to compare")
    ref_all = _tokens("\n".join(reference_pages_))
    out = _tokens(markdown)
    ref_c, out_c = collections.Counter(ref), collections.Counter(out)
    f = _Findings({"reference_tokens": len(ref), "output_tokens": len(out), "numeric_checks": float(numeric_checks)})
    _numeric(f, ref_c, ref_all, out_c, _ORDINAL.sub(r"\1", markdown), numeric_checks)
    _coverage_and_order(f, ref, out, ref_c, out_c)
    _junk(f, ref_text, markdown)
    _structure(f, markdown)

    m = f.metrics
    bad = (
        (numeric_checks and m["fused_numeric"] >= FUSED_BAD)
        or m["flattened_code_blocks"] >= FLAT_CODE_BAD
        or m["word_recall"] < BAD_COVERAGE
    )
    return ConversionReport(
        "bad" if bad else "warn" if f.warnings else "ok", metrics=m, warnings=f.warnings, examples=f.examples
    )


def _ragged_tables(md: str) -> Tuple[int, int]:
    """(tables whose rows mostly disagree on the cell count, tables of >= 3 rows)."""
    tables = ragged = 0
    for is_row, lines in itertools.groupby(md.splitlines(), key=lambda ln: ln.lstrip().startswith("|")):
        widths = [ln.strip().strip("|").count("|") + 1 for ln in lines] if is_row else []
        if len(widths) >= 3:
            tables += 1
            ragged += collections.Counter(widths).most_common(1)[0][1] < 0.8 * len(widths)
    return int(ragged), tables


def _fence_problems(md: str) -> Tuple[int, int]:
    """(1 if a code fence is left open, number of fenced blocks of one very long line)."""
    flat = 0
    block: Optional[List[str]] = None
    for line in md.splitlines():
        if FENCE.match(line):
            if block is not None:
                body = [ln for ln in block if ln.strip()]
                flat += len(body) <= 1 and sum(len(ln) for ln in body) > 200
            block = None if block is not None else []
        elif block is not None:
            block.append(line)
    return int(block is not None), int(flat)


def _equation_heavy(pdf: str | Path) -> bool:
    try:
        return profile_pdf(str(pdf)).math_pages_share >= MATH_PAGES_THRESHOLD
    except Exception:
        return False


def check_conversion(pdf: str | Path, markdown: str) -> ConversionReport:
    """Reference extraction + compare. Never raises: a failure is a 'not-run' verdict."""
    try:
        pages, why = reference_pages(pdf)
        if pages is None:
            return ConversionReport("not-run", reason=why)
        return compare(pages, markdown, numeric_checks=not _equation_heavy(pdf))
    except Exception as e:  # a diagnostic must never break ingestion
        return ConversionReport("not-run", reason=f"{type(e).__name__}: {e}")
