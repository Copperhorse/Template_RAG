import os
import textwrap

os.environ["RAG_NO_DOTENV"] = "1"  # a developer's real .env must never reach a test

import pytest  # noqa: E402
from llm_stub import StubLLM  # noqa: E402

from rag_template.config import LLMSettings, Settings  # noqa: E402
from rag_template.enrichment.enricher import Gates  # noqa: E402
from rag_template.enrichment.llm import LLMClient  # noqa: E402
from rag_template.store.db import Database  # noqa: E402
from rag_template.store.embedders import HashingEmbedder  # noqa: E402
from rag_template.store.vector import InMemoryVectorStore  # noqa: E402

SAMPLE_PY = textwrap.dedent('''
    """Retry helpers for flaky network calls."""

    import time

    DEFAULT_ATTEMPTS = 3


    def retry(fn, attempts=DEFAULT_ATTEMPTS, delay=0.5):
        """Call fn until it succeeds, sleeping delay * 2 ** i between attempts."""
        for i in range(attempts):
            try:
                return fn()
            except OSError:
                time.sleep(delay * 2 ** i)
        raise RuntimeError("gave up after repeated failures")


    class Cache:
        """A tiny time-to-live cache."""

        def __init__(self, ttl=60):
            self.ttl = ttl
            self._items = {}

        def get(self, key):
            """Return the stored value for key, or None when it has expired."""
            value, stored_at = self._items.get(key, (None, 0))
            if time.time() - stored_at > self.ttl:
                return None
            return value

        def put(self, key, value):
            """Store value under key and remember when it was stored."""
            self._items[key] = (value, time.time())
''').lstrip()

SAMPLE_MD = textwrap.dedent("""
    # Deployment Guide

    ## Overview

    The deployment pipeline builds a container image and pushes it to the registry. Every merge to the main branch triggers a build, and the build fails when the test suite fails.

    ## Rollbacks

    A rollback redeploys the previous image tag. The previous tag is stored in the release manifest, so rolling back never needs a rebuild and completes in under two minutes.
""").lstrip()


class AcceptAll:
    """Stand-in checker: no models, no gates."""

    def validate(self, question, answer, chunk, source_quote):
        return True, "ok"


@pytest.fixture
def db(tmp_path):
    return Database(tmp_path / "test.db")


@pytest.fixture
def stub():
    with StubLLM() as s:
        yield s


def make_llm(stub, timeout=2.0, retries=0, **llm_kwargs):
    return LLMClient(LLMSettings(base_url=stub.url, timeout_s=timeout, max_retries=retries, reasoning_budget=0, **llm_kwargs))


@pytest.fixture
def make_rag(tmp_path):
    from rag_template.rag import RAG

    def build(stub=None, **kwargs):
        settings = Settings(data_dir=tmp_path / "data", vector_store="memory", embedder="hash", rerank="off", max_chunk_tokens=200, min_chunk_tokens=30, route_margin=None)  # routing is tested on its own
        llm = make_llm(stub) if stub is not None else None
        return RAG(settings, store=InMemoryVectorStore(), embedder=HashingEmbedder(), llm=llm, **kwargs)

    return build


@pytest.fixture
def sample_repo(tmp_path):
    root = tmp_path / "repo"
    (root / "pkg").mkdir(parents=True)
    (root / "pkg" / "retry.py").write_text(SAMPLE_PY)
    (root / "docs").mkdir()
    (root / "docs" / "deploy.md").write_text(SAMPLE_MD)
    (root / "node_modules").mkdir()
    (root / "node_modules" / "junk.js").write_text("module.exports = 1;\n" * 10)
    return root
