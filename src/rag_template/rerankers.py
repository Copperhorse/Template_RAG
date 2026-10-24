"""
rerankers.py: second-stage rerankers behind one protocol, `rerank(query, texts) -> one score per text, input order`.

    CrossEncoderReranker      a sentence-transformers CrossEncoder (query, passage) -> logit. Pairs are independent.
    JinaListwiseReranker      jinaai/jina-reranker-v3.5: ONE forward pass reads the query and every candidate together
                              and scores them by cosine similarity (a "listwise" model). Scores are comparable within
                              one call, not between calls, and a candidate list is bounded by memory: it is one sequence.

Safety of the Jina model
  * It ships its own modeling code, so loading it needs `trust_remote_code`. The file was audited (283 lines; imports
    only numpy, torch and transformers; no network, subprocess, exec, pickle or file access) at the commit pinned below,
    and the model is loaded from a snapshot of exactly that commit. Only that (model, commit) pair is trusted by default;
    any other model that needs remote code requires RAG_TRUST_REMOTE_CODE=1 (Settings.rerank_trust_remote_code).
  * Licence: CC-BY-NC-4.0, non-commercial use only. Check it before using this template in a product.
"""

import logging
import threading
from typing import List, Optional, Protocol, Sequence

logger = logging.getLogger("rag_template.rerankers")

JINA_ID = "jinaai/jina-reranker-v3.5"
JINA_SHA = "e8a93f33f0b22108f8c2364f8484ce3422552fbc"  # audited commit (see module docstring)
TRUSTED_REMOTE_CODE = {(JINA_ID, JINA_SHA)}
FALLBACK_RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class Reranker(Protocol):
    name: str

    def rerank(self, query: str, texts: Sequence[str]) -> List[float]: ...


class CrossEncoderReranker:
    """Cross-encoder relevance scores (needs the `local` extra). Scores are raw logits: only their order and
    differences mean anything, so calibrate any threshold on your own data."""

    def __init__(self, model_name: Optional[str] = None):
        from rag_template import models

        self.name = model_name or models.RERANKER_NAME
        self._model = models.get_cross_encoder(self.name)

    def rerank(self, query: str, texts: Sequence[str]) -> List[float]:
        if not texts:
            return []
        return [float(s) for s in self._model.predict([[query, t] for t in texts], show_progress_bar=False)]


class JinaListwiseReranker:
    def __init__(
        self,
        model_name: str = JINA_ID,
        revision: str = "",
        trust_remote_code: bool = False,
        dtype: str = "auto",
        model=None,  # injected in tests: any object with .rerank(query, documents) -> [{index, relevance_score}]
    ):
        self.name = model_name
        self.revision = revision or (JINA_SHA if model_name == JINA_ID else "main")
        self._lock = threading.Lock()  # one pass at a time: a pass uses most of the model's working memory
        if model is not None:
            self._model = model
            return
        if (model_name, self.revision) not in TRUSTED_REMOTE_CODE and not trust_remote_code:
            raise ValueError(
                f"{model_name}@{self.revision[:8]} needs trust_remote_code (it runs Python from the model repository) and is not an "
                "audited pair. Read its modeling.py, then set RAG_TRUST_REMOTE_CODE=1 to allow it."
            )
        self._model = self._load(dtype)

    def _load(self, dtype: str):
        try:
            import torch
            from huggingface_hub import snapshot_download
            from transformers import AutoModel
        except ImportError as e:
            raise ImportError(
                "the Jina reranker needs `torch` and `transformers` (pip install 'rag-template[local]')"
            ) from e
        from rag_template import models

        device = models.get_device()
        torch_dtype = models._resolve_dtype(dtype, device)
        logger.info(f"Loading {self.name}@{self.revision[:8]} on {device} ({torch_dtype})")
        # A local snapshot of the pinned commit: the tokenizer, which the model loads from its own path, comes from the
        # same files, and nothing is fetched from the hub at run time.
        local = snapshot_download(self.name, revision=self.revision)
        model = AutoModel.from_pretrained(local, dtype=torch_dtype, trust_remote_code=True, local_files_only=True)
        return model.to(device).eval()

    def rerank(self, query: str, texts: Sequence[str]) -> List[float]:
        if not texts:
            return []
        with self._lock:
            return self._score(query, list(texts))

    def _score(self, query: str, texts: List[str]) -> List[float]:
        try:
            results = self._model.rerank(query, texts)
        except Exception as e:  # noqa: BLE001 - only an out-of-memory error is recoverable here
            if not _is_oom(e) or len(texts) < 2:
                raise
            _free_gpu_memory()
            half = len(texts) // 2
            logger.warning(
                f"Out of GPU memory scoring {len(texts)} candidates in one pass; scoring {half} + {len(texts) - half} instead. "
                "Scores from separate passes are not strictly comparable: lower `rerank_top` to avoid this."
            )
            return self._score(query, texts[:half]) + self._score(query, texts[half:])
        scores = [0.0] * len(texts)
        for r in results:  # the model returns its results sorted by score, each with the index of its input
            scores[int(r["index"])] = float(r["relevance_score"])
        return scores


def _is_oom(e: BaseException) -> bool:
    return type(e).__name__ == "OutOfMemoryError" or "out of memory" in str(e).lower()


def _free_gpu_memory() -> None:
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass


def make_reranker(
    model_name: str, revision: str = "", trust_remote_code: bool = False, dtype: str = "auto"
) -> Reranker:
    """The right adapter for a model id: Jina listwise models get their own, everything else is a CrossEncoder."""
    if model_name.lower().startswith("jinaai/jina-reranker"):
        return JinaListwiseReranker(model_name, revision, trust_remote_code, dtype)
    return CrossEncoderReranker(model_name)


def default_rerank_mode(model_name: str) -> str:
    """ "replace" for the Jina listwise model, "fuse" for any other reranker.

    Measured on 70 hand-written queries (evals/results/rerankers_handwritten.md): jina alone beat hybrid RRF by +18.6
    recall@1 / +15.4 MRR (significant) and beat its own fused version, while ms-marco-MiniLM *lost* 4-14 points when it
    replaced the ranking and only broke even when fused. An unknown reranker gets the safe mode until it is measured."""
    return "replace" if model_name.lower().startswith("jinaai/jina-reranker") else "fuse"
