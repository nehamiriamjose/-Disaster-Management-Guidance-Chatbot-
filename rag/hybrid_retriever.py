"""
DisasterShield Hybrid Retrieval Engine
======================================
Combines dense FAISS vector similarity with sparse disaster keyword matching.
Implements category filtering, deduplication, score fusion, and strict relevance thresholding.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from rag.config import RAGConfig
from rag.vector_store import FAISSVectorStore
from rag.embeddings import BaseEmbeddingProvider


class HybridRetriever:
    """Orchestrates hybrid (dense + sparse) document passage retrieval."""

    # High-signal disaster domain terms for sparse keyword weighting
    DISASTER_KEYWORDS = {
        "earthquake", "tremor", "aftershock", "seismic", "richter", "fault",
        "drop", "cover", "hold", "collapse", "rubble", "cracks", "unreinforced",
        "flood", "flash", "inundation", "waterlogged", "drainage", "current",
        "turn around", "dont drown", "breaker", "submerged", "rooftop", "attic",
        "landslide", "mudflow", "debris", "rockfall", "slope", "tension crack",
        "lateral", "sprint", "culvert", "river dam", "go-bag", "first aid",
        "ndma", "gsi", "cwc", "ndrf", "preparedness", "precautions", "evacuation"
    }

    def __init__(
        self,
        vector_store: Optional[FAISSVectorStore] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
        top_k: int = RAGConfig.TOP_K_CANDIDATES,
        threshold: float = RAGConfig.SIMILARITY_THRESHOLD,
        alpha: float = RAGConfig.HYBRID_ALPHA
    ):
        if embedding_provider is None:
            from rag.embeddings import get_embedding_provider
            self.embedding_provider = get_embedding_provider()
        else:
            self.embedding_provider = embedding_provider

        if vector_store is None:
            self.vector_store = FAISSVectorStore(dimension=self.embedding_provider.dimension)
        else:
            self.vector_store = vector_store

        self.top_k = top_k
        self.threshold = threshold
        self.alpha = alpha  # Weight for dense vector search (0.0 to 1.0)

    def retrieve(
        self,
        query: str,
        category_filter: Optional[str] = None,
        category: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Execute hybrid search for query.
        Returns (ranked_chunks_with_scores, insufficient_evidence_flag).
        """
        target_cat = category_filter or category
        query_clean = query.strip()
        if not query_clean or self.vector_store.get_chunk_count() == 0:
            return [], True

        # 1. Dense FAISS Vector Search
        query_vec = self.embedding_provider.embed_query(query_clean)
        dense_results = self.vector_store.search(
            query_vector=query_vec,
            top_k=self.top_k * 3,
            category_filter=target_cat
        )

        dense_scores_by_id = {chunk["chunk_id"]: score for chunk, score in dense_results}
        candidate_chunks_by_id = {chunk["chunk_id"]: chunk for chunk, _ in dense_results}

        # 2. Sparse Keyword Matching
        all_chunks = self.vector_store.get_all_chunks()
        query_tokens = self._tokenize(query_clean)

        keyword_scores_by_id: Dict[str, float] = {}
        for chunk in all_chunks:
            # Category filter check for keyword search
            if target_cat:
                chunk_cat = (chunk.get("disaster_category") or "general").lower()
                if chunk_cat != "general" and chunk_cat != target_cat.lower():
                    continue

            kw_score = self._compute_keyword_score(query_tokens, chunk["text"])
            if kw_score > 0.1:
                chunk_id = chunk["chunk_id"]
                keyword_scores_by_id[chunk_id] = kw_score
                if chunk_id not in candidate_chunks_by_id:
                    candidate_chunks_by_id[chunk_id] = chunk

        if not candidate_chunks_by_id:
            return [], True

        # Detect disaster topic mentioned in query
        detected_disaster = None
        q_lower = query_clean.lower()
        if "earthquake" in q_lower or "seismic" in q_lower or "tremor" in q_lower:
            detected_disaster = "earthquake"
        elif "flood" in q_lower or "inundation" in q_lower or "waterlogging" in q_lower:
            detected_disaster = "flood"
        elif "landslide" in q_lower or "debris flow" in q_lower or "rockfall" in q_lower:
            detected_disaster = "landslide"

        # 3. Hybrid Score Fusion
        fused_candidates: List[Tuple[Dict[str, Any], float, float, float]] = []

        for chunk_id, chunk in candidate_chunks_by_id.items():
            dense_score = max(0.0, dense_scores_by_id.get(chunk_id, 0.0))
            kw_score = keyword_scores_by_id.get(chunk_id, 0.0)

            # Combined score = alpha * dense + (1 - alpha) * sparse
            combined = (self.alpha * dense_score) + ((1.0 - self.alpha) * kw_score)

            # Topic affinity boost if query specifically targets this disaster
            chunk_cat = (chunk.get("disaster_category") or "").lower()
            chunk_title = (chunk.get("title") or "").lower()
            if detected_disaster and (detected_disaster in chunk_cat or detected_disaster in chunk_title):
                combined += 0.15
            elif detected_disaster and (detected_disaster not in chunk_cat and detected_disaster not in chunk.get("text", "").lower()):
                # Penalize unrelated disasters when query explicitly named a specific disaster
                combined *= 0.5

            if combined >= self.threshold:
                fused_candidates.append((chunk, combined, dense_score, kw_score))

        # Sort by combined score descending
        fused_candidates.sort(key=lambda x: x[1], reverse=True)

        # Select top_k deduplicated passages
        final_results: List[Dict[str, Any]] = []
        for chunk, combined_score, d_score, kw_score in fused_candidates[:self.top_k]:
            result_item = dict(chunk)
            result_item["similarity_score"] = round(float(combined_score), 4)
            result_item["final_score"] = round(float(combined_score), 4)
            result_item["dense_score"] = round(float(d_score), 4)
            result_item["keyword_score"] = round(float(kw_score), 4)
            final_results.append(result_item)

        insufficient_evidence = len(final_results) == 0
        return final_results, insufficient_evidence

    def _tokenize(self, text: str) -> List[str]:
        """Normalize text into lowercase alphanumeric tokens."""
        clean = re.sub(r"[^\w\s]", " ", text.lower())
        return [w for w in clean.split() if len(w) > 2]

    def _compute_keyword_score(self, query_tokens: List[str], chunk_text: str) -> float:
        """
        Compute normalized term-frequency overlap with disaster keyword weighting.
        """
        if not query_tokens:
            return 0.0

        chunk_lower = chunk_text.lower()
        chunk_tokens = set(self._tokenize(chunk_text))

        matches = 0.0
        for token in query_tokens:
            if token in chunk_tokens:
                # Give extra weight to high-signal disaster terminology
                weight = 1.8 if token in self.DISASTER_KEYWORDS else 1.0
                matches += weight
            elif token in chunk_lower:
                matches += 0.5

        # Normalize score between 0.0 and 1.0
        max_possible = len(query_tokens) * 1.8
        return min(1.0, matches / max_possible)
