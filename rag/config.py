"""
DisasterShield RAG Configuration
================================
Central configuration settings for document ingestion, chunking,
embedding models, vector persistence, and answer generation.
"""

import os
from pathlib import Path


class RAGConfig:
    # Base directories
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"
    DOCUMENTS_DIR = DATA_DIR / "documents"
    VECTOR_INDEX_DIR = DATA_DIR / "vector_index"

    # Vector index file paths
    FAISS_INDEX_PATH = VECTOR_INDEX_DIR / "disaster_faiss.index"
    CHUNKS_METADATA_PATH = VECTOR_INDEX_DIR / "chunks_metadata.json"
    DOCUMENTS_CATALOG_PATH = VECTOR_INDEX_DIR / "documents_catalog.json"
    EMBEDDER_MODEL_PATH = VECTOR_INDEX_DIR / "local_embedder.pkl"

    # Chunking configuration (defaults: ~800 tokens / 3200 chars, ~120 tokens / 480 chars overlap)
    CHUNK_SIZE_CHARS = int(os.environ.get("RAG_CHUNK_SIZE_CHARS", 3200))
    CHUNK_OVERLAP_CHARS = int(os.environ.get("RAG_CHUNK_OVERLAP_CHARS", 480))
    MIN_CHUNK_CHARS = int(os.environ.get("RAG_MIN_CHUNK_CHARS", 100))

    # Ingestion constraints
    MAX_UPLOAD_SIZE_MB = int(os.environ.get("RAG_MAX_UPLOAD_SIZE_MB", 15))
    MAX_UPLOAD_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    ALLOWED_EXTENSIONS = {".pdf"}

    # Embedding provider: 'local' (default), 'sentence_transformers', 'openai', 'gemini'
    EMBEDDING_PROVIDER = os.environ.get("RAG_EMBEDDING_PROVIDER", "local").lower().strip()
    EMBEDDING_DIM = int(os.environ.get("RAG_EMBEDDING_DIM", 1024))

    # Retrieval configuration
    TOP_K_CANDIDATES = int(os.environ.get("RAG_TOP_K", 4))
    SIMILARITY_THRESHOLD = float(os.environ.get("RAG_SIMILARITY_THRESHOLD", 0.10))
    HYBRID_ALPHA = float(os.environ.get("RAG_HYBRID_ALPHA", 0.60))  # 0.60 dense + 0.40 keyword

    # LLM Generator provider: 'local' (default), 'openai', 'gemini'
    GENERATOR_PROVIDER = os.environ.get("RAG_GENERATOR_PROVIDER", "local").lower().strip()
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")

    # Safety: Emergency keywords that trigger immediate life-safety redirection
    EMERGENCY_TRIGGER_WORDS = [
        "trapped", "bleeding", "crushed", "choking", "water rising", "water entering",
        "gas leak", "sparking", "collapse", "collapsed", "screaming", "can't breathe",
        "cannot breathe", "drowning", "swept away", "help me now", "save me", "under debris",
        "urgent help", "dying"
    ]

    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they do not exist."""
        cls.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.VECTOR_INDEX_DIR.mkdir(parents=True, exist_ok=True)


# Module-level convenience aliases
CHUNK_SIZE_CHARS = RAGConfig.CHUNK_SIZE_CHARS
CHUNK_OVERLAP_CHARS = RAGConfig.CHUNK_OVERLAP_CHARS
MIN_CHUNK_CHARS = RAGConfig.MIN_CHUNK_CHARS
EMBEDDING_DIMENSION = RAGConfig.EMBEDDING_DIM
RELEVANCE_THRESHOLD = RAGConfig.SIMILARITY_THRESHOLD
EMERGENCY_KEYWORDS = RAGConfig.EMERGENCY_TRIGGER_WORDS
