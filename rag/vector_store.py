"""
DisasterShield FAISS Vector Store
=================================
Persistent vector storage and metadata repository using FAISS IndexFlatIP (Cosine Similarity).
Handles document catalog management, chunk indexing, category filtering,
deduplication, and index reconstruction.
"""

import os
import json
import numpy as np
import faiss
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from rag.config import RAGConfig


class FAISSVectorStore:
    """Manages persistent FAISS vector index and paired JSON chunk metadata."""

    def __init__(
        self,
        dimension: int = RAGConfig.EMBEDDING_DIM,
        index_path: Path = RAGConfig.FAISS_INDEX_PATH,
        metadata_path: Path = RAGConfig.CHUNKS_METADATA_PATH,
        catalog_path: Path = RAGConfig.DOCUMENTS_CATALOG_PATH
    ):
        self.dimension = dimension
        self.index_path = Path(index_path)
        self.metadata_path = Path(metadata_path)
        self.catalog_path = Path(catalog_path)

        self.index: Optional[faiss.IndexFlatIP] = None
        self.chunks_metadata: List[Dict[str, Any]] = []
        self.documents_catalog: Dict[str, Dict[str, Any]] = {}

        self._initialize_store()

    def _initialize_store(self) -> None:
        """Load existing index and metadata from disk, or create fresh instances."""
        RAGConfig.ensure_directories()

        # Load Document Catalog
        if self.catalog_path.exists():
            try:
                with open(self.catalog_path, "r", encoding="utf-8") as f:
                    self.documents_catalog = json.load(f)
            except Exception:
                self.documents_catalog = {}

        # Load Chunks Metadata
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    self.chunks_metadata = json.load(f)
            except Exception:
                self.chunks_metadata = []

        # Load FAISS Index
        if self.index_path.exists():
            try:
                loaded_index = faiss.read_index(str(self.index_path))
                if loaded_index.d == self.dimension:
                    self.index = loaded_index
                else:
                    print(f"[*] Recreating FAISS index: Dimension changed from {loaded_index.d} to {self.dimension}")
                    self.index = faiss.IndexFlatIP(self.dimension)
            except Exception as e:
                print(f"[Warning] Failed to read FAISS index from {self.index_path}: {e}. Creating new index.")
                self.index = faiss.IndexFlatIP(self.dimension)
        else:
            self.index = faiss.IndexFlatIP(self.dimension)

    def save(self) -> None:
        """Persist index, metadata, and catalog to disk."""
        RAGConfig.ensure_directories()

        if self.index is not None:
            faiss.write_index(self.index, str(self.index_path))

        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.chunks_metadata, f, indent=2, ensure_ascii=False)

        with open(self.catalog_path, "w", encoding="utf-8") as f:
            json.dump(self.documents_catalog, f, indent=2, ensure_ascii=False)

    def add_document(
        self,
        doc_metadata: Dict[str, Any],
        chunks: List[Dict[str, Any]],
        embeddings: np.ndarray
    ) -> None:
        """
        Index a document and its chunk vectors into FAISS.
        Handles deduplication: if document was previously indexed, its old chunks are removed.
        """
        doc_id = doc_metadata["doc_id"]

        # Check for existing document to avoid duplicate chunk entries
        if doc_id in self.documents_catalog:
            self.delete_document(doc_id, save_after=False)

        if len(chunks) == 0 or embeddings.shape[0] == 0:
            return

        # Ensure embeddings match FAISS dimension
        if embeddings.shape[1] != self.dimension:
            raise ValueError(f"Embedding dimension {embeddings.shape[1]} does not match FAISS dimension {self.dimension}.")

        # Add vectors to FAISS index
        self.index.add(np.ascontiguousarray(embeddings, dtype=np.float32))

        # Append chunk metadata
        self.chunks_metadata.extend(chunks)

        # Update document catalog
        self.documents_catalog[doc_id] = {
            "doc_id": doc_id,
            "filename": doc_metadata.get("filename"),
            "title": doc_metadata.get("title"),
            "organization": doc_metadata.get("organization"),
            "disaster_category": doc_metadata.get("disaster_category"),
            "source_url": doc_metadata.get("source_url"),
            "file_size_bytes": doc_metadata.get("file_size_bytes", 0),
            "total_pages": doc_metadata.get("total_pages", 0),
            "total_chunks": len(chunks),
            "status": "indexed"
        }

        self.save()

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = RAGConfig.TOP_K_CANDIDATES,
        category_filter: Optional[str] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Perform vector similarity search against FAISS index.
        Returns list of (chunk_metadata, similarity_score) tuples.
        """
        if self.index is None or self.index.ntotal == 0 or len(self.chunks_metadata) == 0:
            return []

        # Reshape query vector to (1, dimension)
        if query_vector.ndim == 1:
            query_vector = np.expand_dims(query_vector, axis=0)

        query_vector = np.ascontiguousarray(query_vector, dtype=np.float32)

        # Search for more candidates if category filter is active to prevent starving top_k
        fetch_k = min(self.index.ntotal, top_k * 4 if category_filter else top_k * 2)

        distances, indices = self.index.search(query_vector, fetch_k)

        results: List[Tuple[Dict[str, Any], float]] = []

        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1 or idx >= len(self.chunks_metadata):
                continue

            chunk = self.chunks_metadata[idx]
            similarity_score = float(dist)

            # Category filtering
            if category_filter:
                chunk_cat = (chunk.get("disaster_category") or "general").lower()
                req_cat = category_filter.lower()
                if chunk_cat != "general" and chunk_cat != req_cat:
                    continue

            results.append((chunk, similarity_score))

            if len(results) >= top_k:
                break

        return results

    def similarity_search(
        self,
        query: str,
        top_k: int = RAGConfig.TOP_K_CANDIDATES,
        category_filter: Optional[str] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Convenience method for vector search from a natural language string query."""
        from rag.embeddings import get_embedding_provider
        embedder = get_embedding_provider()
        query_vec = embedder.embed_query(query)
        return self.search(query_vector=query_vec, top_k=top_k, category_filter=category_filter)

    def delete_document(self, doc_id: str, save_after: bool = True) -> bool:
        """
        Remove a document and its chunks. Rebuilds the FAISS index with remaining chunks.
        """
        if doc_id not in self.documents_catalog:
            return False

        del self.documents_catalog[doc_id]

        # Identify which chunks to keep
        remaining_chunks = [c for c in self.chunks_metadata if c.get("doc_id") != doc_id]
        self.chunks_metadata = remaining_chunks

        # Re-initialize index
        self.index = faiss.IndexFlatIP(self.dimension)

        if save_after:
            self.save()

        return True

    def clear(self) -> None:
        """Clear the vector store completely."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.chunks_metadata = []
        self.documents_catalog = {}
        self.save()

    def get_document_count(self) -> int:
        return len(self.documents_catalog)

    def get_chunk_count(self) -> int:
        return len(self.chunks_metadata)

    def get_catalog(self) -> List[Dict[str, Any]]:
        return list(self.documents_catalog.values())

    def get_all_chunks(self) -> List[Dict[str, Any]]:
        return list(self.chunks_metadata)
