"""
models.py: one place that loads the heavy models, once per process.

Before this module the same two sentence-transformers models were built separately by the
enrichment validator (every "Generate" click), the interview scorer, the Chroma debug verifier
and the vector indexer, and a fresh Docling converter was built for every upload. On a GPU that
duplicated VRAM and cost seconds per action.

    get_bi_encoder()        BAAI/bge-small-en-v1.5           (SentenceTransformer)
    get_cross_encoder()     cross-encoder/nli-deberta-v3-xsmall (CrossEncoder)
    get_docling_converter() a shared PDFDocumentConverter, calls serialised by a lock

All three are lazy, cached and thread-safe (concurrent first calls load once). Sentence models
follow "local files first, then download" so a warm cache never touches the network. A failed
load raises and is NOT cached, so the next call retries; callers that treat a model as optional
(the NLI stage of the interview scorer) catch the exception themselves.

Imports of torch / sentence_transformers / docling happen inside the functions so importing this
module is cheap. QP_PRELOAD=1 (see `preload_in_background`) warms everything at start-up.
"""

import logging
import os
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple

from qp_core.device import get_device

logger = logging.getLogger(__name__)

BI_ENCODER_NAME = "BAAI/bge-small-en-v1.5"
CROSS_ENCODER_NAME = "cross-encoder/nli-deberta-v3-xsmall"

_Key = Tuple[str, str, str]  # (kind, model name, device)

_cache: Dict[_Key, Any] = {}
_key_locks: Dict[_Key, threading.Lock] = {}
_registry_lock = threading.Lock()
_load_counts: Dict[_Key, int] = {}  # how many times each model was really constructed


class SharedModel:
    """Wraps a sentence-transformers model so concurrent callers (an enrichment run and interview
    scoring, say) take turns in encode()/predict(). Hugging Face fast tokenizers can raise
    "Already borrowed" when used from several threads at once, and on one GPU the calls would
    queue anyway. Everything else is delegated untouched."""

    def __init__(self, model: Any):
        self._model = model
        self._lock = threading.RLock()

    def encode(self, *args, **kwargs):
        with self._lock:
            return self._model.encode(*args, **kwargs)

    def predict(self, *args, **kwargs):
        with self._lock:
            return self._model.predict(*args, **kwargs)

    def __getattr__(self, name):  # only reached for attributes not defined above
        return getattr(self._model, name)


def _get_or_load(key: _Key, loader: Callable[[], Any]) -> Any:
    model = _cache.get(key)
    if model is not None:
        return model
    with _registry_lock:
        lock = _key_locks.setdefault(key, threading.Lock())
    with lock:  # concurrent first calls for the same model wait here, then reuse the result
        model = _cache.get(key)
        if model is None:
            logger.info(f"Loading {key[0]} {key[1]} on {key[2]}")
            model = loader()
            _cache[key] = model
            _load_counts[key] = _load_counts.get(key, 0) + 1
    return model


def _local_first(factory: Callable[..., Any], name: str, device: str) -> Any:
    """Try the local cache first (no network round-trip), then fall back to downloading."""
    try:
        return factory(name, device=device, local_files_only=True)
    except KeyboardInterrupt:
        raise
    except Exception:
        logger.info(f"{name} not fully cached, downloading")
        return factory(name, device=device)


def get_bi_encoder(name: str = BI_ENCODER_NAME):
    from sentence_transformers import SentenceTransformer

    device = get_device()
    return _get_or_load(
        ("bi-encoder", name, device),
        lambda: SharedModel(_local_first(SentenceTransformer, name, device)),
    )


def get_cross_encoder(name: str = CROSS_ENCODER_NAME):
    from sentence_transformers import CrossEncoder

    device = get_device()
    return _get_or_load(
        ("cross-encoder", name, device),
        lambda: SharedModel(_local_first(CrossEncoder, name, device)),
    )


class SerializedConverter:
    """Shares one Docling converter between threads by running one conversion at a time.

    Docling's thread-safety is not documented, so this trades parallel uploads for safety;
    ingestion is dominated by the conversion itself, and the models stay loaded between uploads.
    """

    def __init__(self, converter: Any):
        self._converter = converter
        self._lock = threading.Lock()

    def process_document(self, file_path):
        with self._lock:
            return self._converter.process_document(file_path)

    def convert_to_markdown(self, file_path):
        with self._lock:
            return self._converter.convert_to_markdown(file_path)

    def get_metadata(self, file_path):
        with self._lock:
            return self._converter.get_metadata(file_path)


def get_docling_converter() -> SerializedConverter:
    def build():
        from qp_pipeline.docling_ocr import PDFDocumentConverter

        return SerializedConverter(PDFDocumentConverter())

    return _get_or_load(("docling", "pdf", get_device()), build)


# ---------------------------------------------------------------- introspection


def loaded_models() -> List[Dict[str, Any]]:
    """What is in memory right now (for /api/status and tests)."""
    return [
        {"kind": kind, "name": name, "device": device, "loads": _load_counts.get((kind, name, device), 1)}
        for (kind, name, device) in sorted(_cache)
    ]


def load_count(kind: str, name: Optional[str] = None) -> int:
    """Times a model of `kind` (optionally a specific name) was actually constructed."""
    return sum(n for (k, nm, _), n in _load_counts.items() if k == kind and name in (None, nm))


def preload_enabled() -> bool:
    return os.environ.get("QP_PRELOAD", "").strip().lower() in ("1", "true", "yes", "on")


def preload_all() -> None:
    """Load every model now. Each failure is logged and skipped so a missing model can't stop start-up."""
    for label, loader in (
        ("bi-encoder", get_bi_encoder),
        ("cross-encoder", get_cross_encoder),
        ("docling", get_docling_converter),
    ):
        try:
            loader()
        except Exception as e:
            logger.warning(f"Preload of {label} failed: {e}")


def preload_in_background() -> threading.Thread:
    thread = threading.Thread(target=preload_all, name="qp-model-preload", daemon=True)
    thread.start()
    return thread


def _reset_for_tests() -> None:
    with _registry_lock:
        _cache.clear()
        _key_locks.clear()
        _load_counts.clear()
