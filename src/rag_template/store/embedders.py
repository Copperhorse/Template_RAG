"""
embedders.py: turn text into vectors.

    SentenceTransformerEmbedder   local models (EmbeddingGemma 2, bge, e5, ...); `local` extra
    OpenAICompatEmbedder          any /v1/embeddings endpoint (OpenAI, vLLM, Ollama, llama-server --embedding)
    HashingEmbedder               deterministic hashed bag-of-words; no model, no network. For tests,
                                  CI and wiring things up before you pick a model. Not semantic.

Documents and queries are written the way the model was trained (see formats.py): `embed_documents`
takes an optional title per text (the chunk's breadcrumb) and `embed_query` an optional task
("search result", "code retrieval", ...), which only task-aware models use.
"""

import logging
import hashlib
import math
import re
from typing import List, Optional, Protocol, Sequence

from rag_template.store.formats import EmbedFormat, format_for


logger = logging.getLogger("rag_template.embedders")


class Embedder(Protocol):
    name: str

    def embed_documents(self, texts: Sequence[str], titles: Optional[Sequence[Optional[str]]] = None) -> List[List[float]]: ...

    def embed_query(self, text: str, task: Optional[str] = None) -> List[float]: ...


def _titled(texts: Sequence[str], titles: Optional[Sequence[Optional[str]]]) -> List[Optional[str]]:
    return list(titles) if titles is not None else [None] * len(texts)


def _is_oom(e: BaseException) -> bool:
    return type(e).__name__ == "OutOfMemoryError" or "out of memory" in str(e).lower()


def _free_gpu_cache() -> None:
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass


def embedder_id(embedder: "Embedder") -> str:
    """What makes two embedders' vectors comparable: the model and the Matryoshka dimension (`name@dim`)."""
    dim = getattr(embedder, "truncate_dim", None)
    return f"{embedder.name}@{dim}" if dim and "@" not in embedder.name else embedder.name


def _truncate(vec: Sequence[float], dim: Optional[int]) -> List[float]:
    """Matryoshka truncation: keep the first `dim` components and re-normalise."""
    v = list(vec)[:dim] if dim else list(vec)
    norm = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / norm for x in v]


class SentenceTransformerEmbedder:
    def __init__(
        self,
        model_name: str = "google/embeddinggemma-2",
        batch_size: int = 16,
        dtype: str = "auto",
        truncate_dim: Optional[int] = None,
        fmt: Optional[EmbedFormat] = None,
        max_seq_length: Optional[int] = None,
        modalities: str = "text",
    ):
        """`dtype`: auto (bfloat16 on GPU, float32 on CPU) | bfloat16 | float16 | float32.
        `truncate_dim`: Matryoshka dimension for models trained for it (EmbeddingGemma 2: 128/256/512/768).
        `modalities`: EmbeddingGemma 2 only, "text" (270M, default) or "text,image" (440M)."""
        self.name = model_name
        self.batch_size, self.dtype, self.truncate_dim, self.max_seq_length, self.modalities = batch_size, dtype, truncate_dim, max_seq_length, modalities
        self.fmt = fmt or format_for(model_name)
        self._model = None

    def _get(self):
        if self._model is None:
            from rag_template import models

            self._model = models.get_bi_encoder(self.name, dtype=self.dtype, truncate_dim=self.truncate_dim, max_seq_length=self.max_seq_length, modalities=self.modalities)
        return self._model

    def _encode_batched(self, texts: List[str]):
        """Encode with `batch_size`; when the GPU runs out of memory (a long-lived process shares it with other models) free the cache and
        retry with half the batch, down to one text at a time. The usable batch size is remembered."""
        while True:
            try:
                return self._get().encode(texts, normalize_embeddings=True, batch_size=self.batch_size, show_progress_bar=False, convert_to_numpy=True)
            except Exception as e:
                if not _is_oom(e) or self.batch_size <= 1:
                    raise
                self.batch_size //= 2
                logger.warning("GPU out of memory while embedding; retrying with batch size %d", self.batch_size)
                _free_gpu_cache()

    def _encode(self, texts: List[str]) -> List[List[float]]:
        vecs = self._encode_batched(texts)
        out = []
        for v in vecs:
            v = v.astype("float32")
            norm = float((v * v).sum() ** 0.5)  # bfloat16 leaves the model's own normalisation ~0.4% off unit length
            out.append((v / norm if norm else v).tolist())
        return out

    def embed_documents(self, texts: Sequence[str], titles: Optional[Sequence[Optional[str]]] = None) -> List[List[float]]:
        if not texts:
            return []
        return self._encode([self.fmt.document(t, title) for t, title in zip(texts, _titled(texts, titles))])

    def embed_query(self, text: str, task: Optional[str] = None) -> List[float]:
        return self._encode([self.fmt.query(text, task)])[0]


class OpenAICompatEmbedder:
    def __init__(self, base_url: str, model: str, api_key: str = "no-key", batch_size: int = 64, truncate_dim: Optional[int] = None):
        from openai import OpenAI

        self.name, self.batch_size, self.truncate_dim = model, batch_size, truncate_dim
        self.fmt = format_for(model)
        self._client = OpenAI(base_url=base_url, api_key=api_key)

    def _embed(self, inputs: List[str]) -> List[List[float]]:
        out: List[List[float]] = []
        for i in range(0, len(inputs), self.batch_size):
            resp = self._client.embeddings.create(model=self.name, input=inputs[i : i + self.batch_size])
            out.extend(_truncate(d.embedding, self.truncate_dim) for d in sorted(resp.data, key=lambda d: d.index))
        return out

    def embed_documents(self, texts: Sequence[str], titles: Optional[Sequence[Optional[str]]] = None) -> List[List[float]]:
        return self._embed([self.fmt.document(t, title) for t, title in zip(texts, _titled(texts, titles))])

    def embed_query(self, text: str, task: Optional[str] = None) -> List[float]:
        return self._embed([self.fmt.query(text, task)])[0]


_WORD = re.compile(r"[A-Za-z][a-z]+|[A-Z]+(?![a-z])|\d+")


class HashingEmbedder:
    """Hashed bag of lower-cased sub-words (snake_case and camelCase are split), L2-normalised."""

    def __init__(self, dim: int = 512):
        self.name = f"hashing-{dim}"
        self.dim = dim

    def _embed(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        for word in _WORD.findall(text):
            h = int.from_bytes(hashlib.blake2b(word.lower().encode(), digest_size=8).digest(), "big")
            vec[h % self.dim] += 1.0 if (h >> 63) & 1 else -1.0
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    def embed_documents(self, texts: Sequence[str], titles: Optional[Sequence[Optional[str]]] = None) -> List[List[float]]:
        return [self._embed(f"{title}\n{t}" if title else t) for t, title in zip(texts, _titled(texts, titles))]

    def embed_query(self, text: str, task: Optional[str] = None) -> List[float]:
        return self._embed(text)


class TruncatedEmbedder:
    """Matryoshka view of another embedder: the first `dim` components, re-normalised. Lets one model
    pass serve several dimensions (for storage/quality trade-off measurements)."""

    def __init__(self, base: "Embedder", dim: int):
        self.base, self.dim, self.name = base, dim, f"{base.name}@{dim}"

    def embed_documents(self, texts: Sequence[str], titles: Optional[Sequence[Optional[str]]] = None) -> List[List[float]]:
        return [_truncate(v, self.dim) for v in self.base.embed_documents(texts, titles)]

    def embed_query(self, text: str, task: Optional[str] = None) -> List[float]:
        return _truncate(self.base.embed_query(text, task), self.dim)


def make_embedder(kind: str, model: str, base_url: str = "", api_key: str = "no-key", dtype: str = "auto", truncate_dim: Optional[int] = None) -> Embedder:
    if kind in ("sentence-transformers", "st", "local"):
        return SentenceTransformerEmbedder(model, dtype=dtype, truncate_dim=truncate_dim)
    if kind == "openai":
        return OpenAICompatEmbedder(base_url, model, api_key, truncate_dim=truncate_dim)
    if kind == "hash":
        return HashingEmbedder()
    raise ValueError(f"unknown embedder '{kind}'; choose sentence-transformers, openai or hash")
