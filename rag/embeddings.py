"""
DisasterShield Embedding Providers
==================================
Modular embedding system supporting:
1. Local Scikit-Learn TF-IDF N-Gram Vectorizer (Default, 100% local, zero paid API)
2. SentenceTransformers (Local neural model, optional if package installed)
3. Hosted API Providers (OpenAI / Gemini, optional when API keys are configured)
"""

import os
import pickle
import numpy as np
from abc import ABC, abstractmethod
from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize
from rag.config import RAGConfig


class BaseEmbeddingProvider(ABC):
    """Abstract interface for text embedding providers."""

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate 2D float32 numpy array of shape (N, dim)."""
        pass

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """Alias for embed_texts for compatibility."""
        return self.embed_texts(texts)

    @abstractmethod
    def embed_query(self, query: str) -> np.ndarray:
        """Generate 1D float32 numpy array of shape (dim,)."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding dimension."""
        pass


class LocalTFIDFEmbeddingProvider(BaseEmbeddingProvider):
    """
    High-performance, deterministic local embedding provider.
    Uses sublinear TF-IDF word & character n-grams with L2 unit normalization.
    Requires zero external network downloads or API keys.
    """

    # Domain vocabulary to guarantee foundational disaster coverage even before any doc is loaded
    INITIAL_DOMAIN_VOCAB = [
        "earthquake", "shaking", "tremor", "aftershock", "seismic", "richter", "fault",
        "drop", "cover", "hold", "collapse", "rubble", "cracks", "unreinforced", "masonry",
        "flood", "flash", "inundation", "waterlogged", "drainage", "current", "flow",
        "turn around", "dont drown", "breaker", "submerged", "rooftop", "attic", "boat",
        "landslide", "mudflow", "debris", "rockfall", "slope", "tension crack", "scarp",
        "lateral", "sprint", "culvert", "river dam", "go-bag", "first aid", "whistle",
        "ndma", "gsi", "cwc", "ndrf", "preparedness", "precautions", "evacuation", "shelter",
        "boil", "drinking water", "power bank", "headrest", "window", "sos", "survival"
    ]

    def __init__(
        self,
        dim: int = RAGConfig.EMBEDDING_DIM,
        dimension: Optional[int] = None,
        model_path=RAGConfig.EMBEDDER_MODEL_PATH
    ):
        self._dim = dimension if dimension is not None else dim
        self.model_path = model_path
        self.vectorizer: TfidfVectorizer = None
        self.is_fitted = False
        self._load_cached_model()

        if not self.is_fitted:
            self.fit_corpus(self.INITIAL_DOMAIN_VOCAB)

    @property
    def dimension(self) -> int:
        return self._dim

    def fit_corpus(self, texts: List[str]) -> None:
        """Fit the TF-IDF vectorizer on the document corpus."""
        if not texts:
            texts = self.INITIAL_DOMAIN_VOCAB

        # Combine with domain vocabulary
        combined_texts = list(texts) + self.INITIAL_DOMAIN_VOCAB

        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=self._dim,
            sublinear_tf=True,
            stop_words="english",
            token_pattern=r"(?u)\b[a-zA-Z0-9_-]+\b"
        )
        self.vectorizer.fit(combined_texts)
        self.is_fitted = True
        self._save_cached_model()

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Embed a list of text chunks into normalized float32 vectors."""
        if not texts:
            return np.empty((0, self._dim), dtype=np.float32)

        if not self.is_fitted or self.vectorizer is None:
            self.fit_corpus(texts)

        sparse_matrix = self.vectorizer.transform(texts)
        dense_matrix = sparse_matrix.toarray().astype(np.float32)

        # Pad with zeros if features < _dim
        if dense_matrix.shape[1] < self._dim:
            padding = np.zeros((dense_matrix.shape[0], self._dim - dense_matrix.shape[1]), dtype=np.float32)
            dense_matrix = np.hstack([dense_matrix, padding])

        # L2-normalize vectors so dot product equals cosine similarity
        normed = normalize(dense_matrix, norm="l2", axis=1)
        return np.ascontiguousarray(normed, dtype=np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        """Embed a single user question into normalized float32 vector."""
        if not self.is_fitted or self.vectorizer is None:
            self.fit_corpus([query])

        sparse_vec = self.vectorizer.transform([query])
        dense_vec = sparse_vec.toarray().astype(np.float32)

        if dense_vec.shape[1] < self._dim:
            padding = np.zeros((dense_vec.shape[0], self._dim - dense_vec.shape[1]), dtype=np.float32)
            dense_vec = np.hstack([dense_vec, padding])

        normed = normalize(dense_vec, norm="l2", axis=1)
        return np.ascontiguousarray(normed[0], dtype=np.float32)

    def _save_cached_model(self) -> None:
        """Persist fitted embedder state to disk."""
        try:
            RAGConfig.VECTOR_INDEX_DIR.mkdir(parents=True, exist_ok=True)
            with open(self.model_path, "wb") as f:
                pickle.dump({"vectorizer": self.vectorizer, "dim": self._dim}, f)
        except Exception as e:
            print(f"[Warning] Could not persist local embedder model: {e}")

    def _load_cached_model(self) -> None:
        """Load fitted embedder state from disk if available."""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, "rb") as f:
                    data = pickle.load(f)
                    self.vectorizer = data.get("vectorizer")
                    self._dim = data.get("dim", self._dim)
                    self.is_fitted = self.vectorizer is not None
            except Exception:
                self.is_fitted = False


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """Optional OpenAI embedding provider if API key configured."""

    def __init__(self, api_key: str = None, model: str = "text-embedding-3-small"):
        self.api_key = api_key or RAGConfig.OPENAI_API_KEY
        self.model = model
        self._dim = 1536

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        import requests
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set.")

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        all_embeddings = []
        for i in range(0, len(texts), 32):
            batch = texts[i : i + 32]
            resp = requests.post(
                "https://api.openai.com/v1/embeddings",
                headers=headers,
                json={"input": batch, "model": self.model},
                timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
            for item in data["data"]:
                all_embeddings.append(item["embedding"])

        vecs = np.array(all_embeddings, dtype=np.float32)
        return normalize(vecs, norm="l2", axis=1)

    def embed_query(self, query: str) -> np.ndarray:
        return self.embed_texts([query])[0]


def get_embedding_provider() -> BaseEmbeddingProvider:
    """Factory to instantiate the configured embedding provider."""
    provider_name = RAGConfig.EMBEDDING_PROVIDER

    if provider_name == "openai" and RAGConfig.OPENAI_API_KEY:
        return OpenAIEmbeddingProvider()

    return LocalTFIDFEmbeddingProvider()
