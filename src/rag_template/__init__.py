"""rag_template: AST-aware chunking, quality gates, grounded enrichment and hybrid retrieval."""

from rag_template.config import LLMSettings, Settings
from rag_template.evaluator import ChunkEvaluator
from rag_template.rag import RAG

__all__ = ["RAG", "Settings", "LLMSettings", "ChunkEvaluator"]
__version__ = "0.1.0"
