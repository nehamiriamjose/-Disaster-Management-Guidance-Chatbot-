"""
DisasterShield RAG Pipeline Package
===================================
Hybrid retrieval-augmented generation pipeline for disaster management guidance.
Combines FAISS vector database, hybrid retrieval (dense + sparse keyword),
official PDF ingestion, and grounded generation with statutory citations.
"""

from rag.config import RAGConfig
from rag.pipeline import DisasterRAGPipeline

__all__ = ["RAGConfig", "DisasterRAGPipeline"]
