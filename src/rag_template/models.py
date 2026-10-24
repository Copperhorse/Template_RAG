"""
models.py: one place that loads the heavy models, once per process.

    get_bi_encoder()      sentence-transformers bi-encoder (embeddings, similarity gate)
    get_cross_encoder()   sentence-transformers CrossEncoder (NLI validator, reranker)

Both are lazy, cached and thread-safe (concurrent first calls load once). Models follow "local files
first, then download" so a warm cache never touches the network. A failed load raises and is NOT
cached, so the next call retries. `torch` / `sentence_transformers` are imported inside the functions,
so importing this module is cheap and the package works without the `local` extra.
"""

import logging
import os
import threading
from functools import lru_cache
from typing import Any, Callable, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

BI_ENCODER_NAME = "BAAI/bge-small-en-v1.5"
NLI_CROSS_ENCODER_NAME = "cross-encoder/nli-deberta-v3-xsmall"
RERANKER_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_Key = Tuple[str, str, str]  # (kind, model name, device)
_cache: Dict[_Key, Any] = {}
_key_locks: Dict[_Key, threading.Lock] = {}
_registry_lock = threading.Lock()


@lru_cache(maxsize=1)
def get_device() -> str:
    """CUDA -> Apple MPS -> CPU. Override with QP_DEVICE (e.g. cpu, cuda:1)."""
    override = os.environ.get("QP_DEVICE", "").strip().lower()
    if override:
        logger.info(f"Device forced by QP_DEVICE: {override}")
        return override
    try:
        import torch
    except ImportError:
        return "cpu"
    if torch.cuda.is_available():
        return "cuda"
    mps = getattr(torch.backends, "mps", None)
    if mps is not None and mps.is_available():
        return "mps"
    return "cpu"


class SharedModel:
    """Wraps a sentence-transformers model so concurrent callers take turns in encode()/predict().
    Hugging Face fast tokenizers can raise "Already borrowed" when used from several threads."""

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
    return model


def _local_first(factory: Callable[..., Any], name: str, device: str) -> Any:
    try:
        return factory(name, device=device, local_files_only=True)
    except KeyboardInterrupt:
        raise
    except Exception:
        logger.info(f"{name} not fully cached, downloading")
        return factory(name, device=device)


def _require_sentence_transformers():
    try:
        import sentence_transformers
    except ImportError as e:
        raise ImportError("this feature needs the `local` extra: pip install 'rag-template[local]'") from e
    return sentence_transformers


def _resolve_dtype(dtype: str, device: str):
    import torch

    if dtype in ("", "auto"):
        return torch.bfloat16 if device.startswith("cuda") and torch.cuda.is_bf16_supported() else torch.float32
    try:
        return getattr(torch, dtype)
    except AttributeError:
        raise ValueError(f"unknown dtype '{dtype}'; choose auto, bfloat16, float16 or float32") from None


def is_embedding_gemma2(name: str) -> bool:
    return "embeddinggemma-2" in name.lower()


def get_bi_encoder(
    name: str = BI_ENCODER_NAME,
    dtype: str = "auto",
    truncate_dim: Optional[int] = None,
    max_seq_length: Optional[int] = None,
    modalities: str = "text",
):
    """`dtype` auto = bfloat16 on a GPU that supports it (half the memory, same ranking), else float32.
    `modalities` (EmbeddingGemma 2 only): "text" loads just the 270M text encoder; "text,image" also loads
    the 170M vision encoder. The other encoders are separate components, so leaving them out costs nothing."""
    st = _require_sentence_transformers()
    device = (
        os.environ.get("RAG_EMBED_DEVICE", "").strip().lower() or get_device()
    )  # e.g. cpu, to leave a shared GPU to the reranker
    if is_embedding_gemma2(name) and dtype.lower() in ("float16", "fp16", "half"):
        # Per the model card, float16 overflows its activation range: it returns NaN or silently degraded vectors.
        raise ValueError(
            "EmbeddingGemma 2 must not run in float16 (silent NaN / degraded embeddings); use bfloat16 or float32"
        )

    def load():
        torch_dtype = _resolve_dtype(dtype, device)
        extra = {}
        if is_embedding_gemma2(name):
            mods = {m.strip() for m in modalities.split(",")}
            extra["config_kwargs"] = {
                **({} if "image" in mods else {"vision_config": None}),
                **({} if "audio" in mods else {"audio_config": None}),
            }
        factory = lambda n, device, **kw: st.SentenceTransformer(
            n, device=device, truncate_dim=truncate_dim, model_kwargs={"dtype": torch_dtype}, **extra, **kw
        )  # noqa: E731
        model = _local_first(factory, name, device)
        if max_seq_length:
            model.max_seq_length = max_seq_length
        elif not model.max_seq_length or model.max_seq_length > 8192:  # some configs leave it unbounded
            model.max_seq_length = 2048
        return SharedModel(model)

    return _get_or_load(("bi-encoder", f"{name}|{dtype}|{truncate_dim}|{max_seq_length}|{modalities}", device), load)


def get_cross_encoder(name: str = NLI_CROSS_ENCODER_NAME):
    st = _require_sentence_transformers()
    device = get_device()
    return _get_or_load(
        ("cross-encoder", name, device), lambda: SharedModel(_local_first(st.CrossEncoder, name, device))
    )


def loaded_models() -> list:
    """What is in memory. A bi-encoder's cache key carries its settings ("name|dtype|dim|max_len|modalities")."""
    out = []
    for k, n, d in sorted(_cache):
        name, _, config = n.partition("|")
        out.append({"kind": k, "name": name, "device": d, **({"config": config} if config else {})})
    return out


def _reset_for_tests() -> None:
    with _registry_lock:
        _cache.clear()
        _key_locks.clear()
