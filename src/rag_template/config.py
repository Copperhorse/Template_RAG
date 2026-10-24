"""
config.py: every tunable in one place, read from the environment (see .env.example).

Nothing in the package reads os.environ except this module, `env.py` and `models.py` (device), so a
library user can build `Settings(...)` by hand and never touch the environment.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from rag_template import env


def _json_mode(value: str) -> str:
    v = value.strip().lower()
    if v in ("1", "true", "yes", "on", "json", "json_object"):
        return "json_object"
    if v == "schema":
        return "schema"
    return "off"


def _int(name: str, default: int) -> int:
    return int(os.environ.get(name, default))


def _route_margin(raw: Optional[str]) -> Optional[float]:
    """RAG_ROUTE_MARGIN: unset = the default margin; off / none / empty = routing off; otherwise the margin."""
    if raw is None:
        return Settings.route_margin
    return None if raw.strip().lower() in ("", "off", "none") else float(raw)


def _float(name: str, default: float) -> float:
    return float(os.environ.get(name, default))


@dataclass(frozen=True)
class PdfSettings:
    """How PDFs are converted and checked (converters.py, convcheck.py). Passed to the converter, never read from the
    environment there. `Settings.from_env` fills it from RAG_PDF_BACKEND, RAG_PDF_FORMULAS, RAG_PDF_LAYOUT_ENGINE,
    RAG_CONVERT_CACHE and RAG_CONVERSION_CHECK."""

    backend: str = "auto"  # auto (pdf_profile picks per file) | pymupdf4llm | docling
    formulas: bool = True  # Docling's formula-enrichment model (LaTeX for equations)
    layout_engine: str = (
        ""  # Docling layout model: "" = onnxruntime when onnxruntime-gpu is installed, else torch | onnxruntime | torch
    )
    cache: str = ""  # converted-Markdown cache: "" = ~/.cache/rag_template/converted | off | a directory
    check: bool = True  # run the conversion check at ingest (convcheck.py); it only reports

    @classmethod
    def from_env(cls) -> "PdfSettings":
        backend = os.environ.get("RAG_PDF_BACKEND", "auto").strip().lower()
        return cls(
            backend=backend if backend in ("auto", "pymupdf4llm", "docling") else "auto",
            formulas=env.flag("RAG_PDF_FORMULAS"),
            layout_engine=os.environ.get("RAG_PDF_LAYOUT_ENGINE", "").strip().lower(),
            cache=os.environ.get("RAG_CONVERT_CACHE", "").strip(),
            check=env.flag("RAG_CONVERSION_CHECK"),
        )


@dataclass
class LLMSettings:
    base_url: str = "http://localhost:8080/v1"
    model: str = "local-model"
    api_key: str = "no-key"
    # The openai library defaults (10 min read timeout, 2 retries) let a hung server stall a run
    # for half an hour per call.
    timeout_s: float = 120.0
    max_retries: int = 1
    health_timeout_s: float = 5.0
    # llama-server counts thinking tokens against max_tokens, so every request must allow
    # budget + the answer itself. 0 = non-reasoning model, -1 = unlimited (capped below).
    reasoning_budget: int = 4096
    unlimited_reasoning_cap: int = 8192
    metadata_answer_tokens: int = 800
    questions_answer_tokens: int = 1000
    reference_answer_tokens: int = 500
    temperature: float = 0.1
    # Sent as extra_body; llama.cpp/vLLM understand them, hosted APIs may reject unknown fields.
    # Constrain structured replies. "schema" (the default): the caller's JSON schema is enforced, so a required key cannot be
    # left out and a quote's source can only be an id that was shown (llama.cpp compiles the schema to a grammar; vLLM, Ollama
    # and OpenAI support it too). "json_object": valid JSON only. "off": ask politely and parse what comes back, for a server that
    # rejects response_format. A caller with no schema (the enrichment stage) gets json_object in "schema" mode. A bool is read as
    # json_object / off. Measured: evals/results/answer_policies.md, golden_pera.md, pdf_backends.md.
    json_mode: str | bool = "schema"
    extra_body: dict = field(default_factory=lambda: {"top_k": 50, "repetition_penalty": 1.05})


@dataclass
class Settings:
    data_dir: Path = Path("data")
    db_path: Optional[Path] = None
    vector_store: str = "chroma"  # chroma | memory
    vector_dir: Optional[Path] = None
    embedder: str = "sentence-transformers"  # sentence-transformers | openai | hash
    embed_model: str = "google/embeddinggemma-2"
    embed_dtype: str = "auto"  # auto (bfloat16 on GPU) | bfloat16 | float16 | float32
    embed_modalities: str = (
        "text"  # EmbeddingGemma 2: "text" (270M encoder) or "text,image" (adds the 170M vision encoder)
    )
    embed_dim: Optional[int] = None  # Matryoshka truncation (EmbeddingGemma 2: 128, 256, 512, 768)
    query_task: Optional[str] = None  # task-aware embedders: "search result" (default), "code retrieval", ...
    max_chunk_tokens: int = 500
    min_chunk_tokens: int = 50
    rerank: str = "auto"  # auto (use the reranker; fall back to ms-marco with a warning if it cannot load) | on (fail if it cannot load) | off
    # jina-reranker-v3.5: listwise, 0.6B, CC-BY-NC-4.0 (non-commercial) and needs trust_remote_code. rerankers.py pins the audited
    # commit and trusts only that pair. Any sentence-transformers CrossEncoder id also works (e.g. cross-encoder/ms-marco-MiniLM-L-6-v2).
    rerank_model: str = "jinaai/jina-reranker-v3.5"
    rerank_revision: str = ""  # "" = the audited commit for the Jina model, else "main"
    rerank_trust_remote_code: bool = False  # only needed for a custom-code model other than the audited Jina pair
    rerank_top: Optional[int] = (
        20  # candidates the reranker reads per query (a listwise model reads them all in one pass)
    )
    rerank_mode: str = "auto"  # auto (replace for the Jina listwise reranker, fuse for any other) | fuse (the reranker is a third voter) | replace (order by it alone)
    # How strict the answer gate is (retrieve.POLICIES) and whether the model writes its evidence before its answer.
    # Measured on 70 real questions with Gemma 4 E2B (evals/results/answer_policies.md): balanced + quotes-first +
    # LLM_JSON_MODE=schema flags 12% of correct answers; strict with a plain reply flagged 57%.
    # Refuse before calling the LLM when the best reranker score is below this (None = off, the default). The number is specific
    # to the reranker; for jina-reranker-v3.5 see evals/results/answerability.md for the measured cost and benefit of each value.
    answer_min_relevance: Optional[float] = None
    route_margin: Optional[float] = (
        0.10  # document routing: keep only the best-scoring document's chunks when it leads the next by this reranker margin (None = off, RAG_ROUTE_MARGIN=off)
    )
    answer_policy: str = "balanced"
    answer_quotes_first: bool = True
    prompt_set: str = "fewshot"  # only used by the optional enrichment stage
    judge: str = "off"  # off | llm  (optional enrichment stage)
    llm: LLMSettings = field(default_factory=LLMSettings)
    pdf: PdfSettings = field(default_factory=PdfSettings)

    def __post_init__(self) -> None:
        self.data_dir = Path(self.data_dir)
        self.db_path = Path(self.db_path) if self.db_path else self.data_dir / "rag.db"
        self.vector_dir = Path(self.vector_dir) if self.vector_dir else self.data_dir / "vectors"

    def ensure_dirs(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.vector_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls) -> "Settings":
        e = os.environ.get
        llm = LLMSettings(
            base_url=e("LLM_BASE_URL", LLMSettings.base_url),
            model=e("LLM_MODEL", LLMSettings.model),
            api_key=e("LLM_API_KEY", LLMSettings.api_key),
            timeout_s=_float("LLM_TIMEOUT_S", LLMSettings.timeout_s),
            reasoning_budget=_int("LLM_REASONING_BUDGET", LLMSettings.reasoning_budget),
            json_mode=_json_mode(e("LLM_JSON_MODE", LLMSettings.json_mode)),
        )
        return cls(
            data_dir=Path(e("RAG_DATA_DIR", "data")),
            db_path=Path(e("RAG_DB_PATH")) if e("RAG_DB_PATH") else None,
            vector_store=e("RAG_VECTOR_STORE", cls.vector_store).lower(),
            vector_dir=Path(e("RAG_VECTOR_DIR")) if e("RAG_VECTOR_DIR") else None,
            embedder=e("RAG_EMBEDDER", cls.embedder).lower(),
            embed_model=e("RAG_EMBED_MODEL", cls.embed_model),
            embed_dtype=e("RAG_EMBED_DTYPE", cls.embed_dtype).lower(),
            embed_modalities=e("RAG_EMBED_MODALITIES", cls.embed_modalities).lower(),
            embed_dim=_int("RAG_EMBED_DIM", 0) or None,
            query_task=e("RAG_QUERY_TASK") or None,
            max_chunk_tokens=_int("RAG_MAX_CHUNK_TOKENS", cls.max_chunk_tokens),
            rerank=e("RAG_RERANK", cls.rerank).lower(),
            rerank_model=e("RAG_RERANK_MODEL", cls.rerank_model),
            rerank_revision=e("RAG_RERANK_REVISION", ""),
            rerank_trust_remote_code=e("RAG_TRUST_REMOTE_CODE", "").lower() in ("1", "true", "yes", "on"),
            rerank_top=_int("RAG_RERANK_TOP", 20) or None,
            rerank_mode=e("RAG_RERANK_MODE", cls.rerank_mode).lower(),
            answer_min_relevance=float(e("RAG_MIN_RELEVANCE")) if e("RAG_MIN_RELEVANCE") else None,
            route_margin=_route_margin(e("RAG_ROUTE_MARGIN")),
            answer_policy=e("RAG_ANSWER_POLICY", cls.answer_policy).lower(),
            answer_quotes_first=e("RAG_ANSWER_QUOTES_FIRST", "1").lower() in ("1", "true", "yes", "on"),
            prompt_set=e("RAG_PROMPT_SET", cls.prompt_set).lower(),
            judge=e("RAG_JUDGE", cls.judge).lower(),
            llm=llm,
            pdf=PdfSettings.from_env(),
        )
