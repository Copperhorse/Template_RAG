"""
converters.py: turn a file into (metadata, text) for the chunkers.

    .md .txt .rst ...   read as text (UTF-8, falling back to latin-1)
    source code         read as text; the chunker is chosen by extension (chunking.router)
    .pdf                pymupdf4llm or Docling -> Markdown, chosen per file by pdf_profile (needs the `pdf` extra; RAG_PDF_BACKEND)

Add a format by registering a function `(path, pdf_settings) -> (metadata dict, text)` with `register_converter`.
PDF behaviour comes from `config.PdfSettings` (passed in; this module does not read the environment).
"""

import hashlib
import html
import logging
import threading
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from rag_template.config import PdfSettings
from rag_template.mdclean import clean_markdown
from rag_template.pages import mark_pages, split_pages

logger = logging.getLogger("rag_template.converters")

Converter = Callable[[Path, PdfSettings], Tuple[Dict[str, Any], str]]
_registry: Dict[str, Converter] = {}


def register_converter(extension: str, fn: Converter) -> None:
    _registry[extension.lower()] = fn


def read_text(path: Path, pdf: Optional[PdfSettings] = None) -> Tuple[Dict[str, Any], str]:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    return {"format": path.suffix.lstrip(".").lower() or "text", "title": path.stem}, text


_pdf_lock = threading.Lock()
_docling: Dict[Tuple[bool, str], Any] = {}  # built Docling converters, keyed by the options that shape them


def _onnx_cuda_available() -> bool:
    try:
        import onnxruntime

        return "CUDAExecutionProvider" in onnxruntime.get_available_providers()
    except Exception:
        return False


_LAYOUT_ENGINES = {"onnxruntime": "onnxruntime", "onnx": "onnxruntime", "torch": "torch", "transformers": "torch"}


def _layout_engine(pdf: PdfSettings) -> str:
    """The Docling layout model to run: the setting, else onnxruntime when onnxruntime-gpu is installed (same output as torch
    on the pages tested, 1.7x faster on the GPU), otherwise torch."""
    return _LAYOUT_ENGINES.get(pdf.layout_engine) or ("onnxruntime" if _onnx_cuda_available() else "torch")


def _docling_converter(pdf: PdfSettings):
    key = (pdf.formulas, _layout_engine(pdf))
    if key not in _docling:
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import AcceleratorDevice, AcceleratorOptions, PdfPipelineOptions
        from docling.document_converter import DocumentConverter, PdfFormatOption

        opts = PdfPipelineOptions()
        opts.do_formula_enrichment = pdf.formulas
        opts.accelerator_options = AcceleratorOptions(device=AcceleratorDevice.AUTO, num_threads=4)
        if key[1] == "onnxruntime":
            from docling.datamodel.object_detection_engine_options import OnnxRuntimeObjectDetectionEngineOptions
            from docling.datamodel.pipeline_options import LayoutObjectDetectionOptions

            opts.layout_options = LayoutObjectDetectionOptions.from_preset(
                "layout_heron_default", engine_options=OnnxRuntimeObjectDetectionEngineOptions()
            )
        _docling[key] = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})
    return _docling[key]


def _pdf_backend(path: Path, pdf: PdfSettings) -> str:
    """The backend for this file: `pdf.backend`, or for `auto` whatever `pdf_profile` picks (scans and formula-heavy documents ->
    Docling, the rest -> pymupdf4llm; see evals/results/pdf_backends.md)."""
    if pdf.backend != "auto":
        return pdf.backend
    from rag_template.pdf_profile import choose_backend, profile_pdf

    return choose_backend(profile_pdf(str(path)))


def _run_backend(path: Path, backend: str, pdf: PdfSettings) -> str:
    with _pdf_lock:
        try:
            if backend == "docling":
                doc = _docling_converter(pdf).convert(source=str(path)).document
                return mark_pages([(n, doc.export_to_markdown(page_no=n)) for n in sorted(doc.pages)])
            import pymupdf4llm

            return mark_pages([(c["metadata"]["page_number"], c["text"]) for c in pymupdf4llm.to_markdown(str(path), page_chunks=True)])
        except ImportError as e:
            raise ImportError(f"The {backend} PDF backend needs the `pdf` extra: pip install 'rag-template[pdf]'") from e


def convert_pdf(path: Path, pdf: Optional[PdfSettings] = None) -> Tuple[Dict[str, Any], str]:
    """PDF -> Markdown with the backend `pdf` selects (default: `PdfSettings.from_env()`). Docling converters are built once per
    option set and calls are serialised: their thread-safety is not documented and the models are expensive to reload."""
    pdf = pdf or PdfSettings.from_env()
    try:
        import pymupdf
    except ImportError as e:
        raise ImportError("PDF support needs the `pdf` extra: pip install 'rag-template[pdf]'") from e

    with pymupdf.open(str(path)) as doc:
        meta = dict(doc.metadata or {})
    backend = _pdf_backend(path, pdf)
    info = {"format": "pdf", "title": meta.get("title") or path.stem, "author": meta.get("author", ""), "backend": backend}

    cache = _cache_file(path, backend, pdf)
    if cache is not None and cache.exists():
        markdown = cache.read_text(encoding="utf-8")
    else:
        markdown = html.unescape(_run_backend(path, backend, pdf))  # Docling escapes & < > as entities; quotes must match the source text
        if cache is not None and markdown.strip() and pdf.formulas and "<!-- formula-not-decoded -->" in markdown:
            # with the formula model on, an undecoded formula means that stage failed (GPU out of memory); caching it would make every
            # later upload of the same file reuse the damaged text, even after the document was deleted and the GPU freed
            logger.warning(f"Not caching the conversion of {path.name}: formulas were left undecoded (the formula stage probably failed)")
        elif cache is not None and markdown.strip():
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(markdown, encoding="utf-8")
    # the cache keeps the raw converter output, so cleanup changes need no reconversion
    markdown, marks = split_pages(clean_markdown(markdown))
    if marks:
        info["page_marks"] = marks
    return info, _checked(path, info, markdown, pdf)


def _checked(path: Path, info: Dict[str, Any], markdown: str, pdf: PdfSettings) -> str:
    """Attach the conversion check (convcheck.py) to `info`; it only reports, the Markdown is returned unchanged."""
    if pdf.check:
        from rag_template.convcheck import check_conversion

        info["conversion_check"] = check_conversion(path, markdown).as_dict()
    return markdown


def _cache_file(path: Path, backend: str, pdf: PdfSettings) -> Optional[Path]:
    """Converted Markdown is cached by file hash + converter settings (`PdfSettings.cache`). Converting a long PDF takes tens of
    seconds to minutes and the result is deterministic for one setting."""
    if pdf.cache.lower() in ("off", "0", "false", "no"):
        return None
    root = Path(pdf.cache) if pdf.cache else Path.home() / ".cache" / "rag_template" / "converted"
    try:
        from importlib.metadata import version

        docling_version = version("docling")
    except Exception:
        docling_version = "?"
    with open(path, "rb") as f:
        file_hash = hashlib.file_digest(f, "sha256").hexdigest()  # streamed, not read into memory
    key = "|".join([file_hash, backend, _layout_engine(pdf), str(int(pdf.formulas)), docling_version, "pages"])  # "pages": the cached text carries page markers
    return root / (hashlib.sha256(key.encode()).hexdigest()[:24] + ".md")


register_converter(".pdf", convert_pdf)


def convert(path: str | Path, pdf: Optional[PdfSettings] = None) -> Tuple[Dict[str, Any], str]:
    path = Path(path)
    return _registry.get(path.suffix.lower(), read_text)(path, pdf or PdfSettings.from_env())
