"""
DisasterShield Master RAG Pipeline
==================================
Coordinates PDF ingestion, semantic chunking, vector embedding, FAISS indexing,
hybrid retrieval, context safety isolation, and answer generation.
"""

import os
import shutil
from typing import Dict, Any, List, Optional
from pathlib import Path

from rag.config import RAGConfig
from rag.document_loader import DocumentLoader, DocumentProcessingError
from rag.chunker import DocumentChunker
from rag.embeddings import get_embedding_provider, BaseEmbeddingProvider
from rag.vector_store import FAISSVectorStore
from rag.hybrid_retriever import HybridRetriever
from rag.context_builder import ContextBuilder
from rag.generator import get_answer_generator, BaseAnswerGenerator


class DisasterRAGPipeline:
    """Master pipeline orchestrating the Knowledge Assistant and Document Management."""

    def __init__(self):
        RAGConfig.ensure_directories()
        self.embedding_provider: BaseEmbeddingProvider = get_embedding_provider()
        self.vector_store = FAISSVectorStore(dimension=self.embedding_provider.dimension)
        self.chunker = DocumentChunker()
        self.retriever = HybridRetriever(
            vector_store=self.vector_store,
            embedding_provider=self.embedding_provider
        )
        self.generator: BaseAnswerGenerator = get_answer_generator()

    def ask(
        self,
        query: str,
        category_filter: Optional[str] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user's natural language disaster management question.
        Returns grounded answer, statutory citations, and source passages.
        """
        query_clean = query.strip()
        chosen_cat = category_filter or category

        if not query_clean:
            return {
                "query": query,
                "answer": "Please enter a valid disaster safety or preparedness question.",
                "citations": [],
                "retrieved_chunks": [],
                "retrieved_chunks_count": 0,
                "is_emergency": False,
                "emergency_helplines": [],
                "evidence_found": False
            }

        # 1. Emergency Intent Detection
        is_emergency = ContextBuilder.check_emergency_intent(query_clean)

        # 2. Hybrid Retrieval
        retrieved_chunks, insufficient = self.retriever.retrieve(
            query=query_clean,
            category_filter=chosen_cat
        )

        # 3. Context & Citations Construction
        _, citations = ContextBuilder.build_prompt_context(query_clean, retrieved_chunks)

        # 4. Grounded Answer Generation
        result = self.generator.generate(
            query=query_clean,
            retrieved_chunks=retrieved_chunks,
            citations=citations,
            is_emergency=is_emergency
        )

        emergency_numbers = ["112", "1078", "101", "108"] if is_emergency else []

        return {
            "query": query_clean,
            "answer": result["answer"],
            "citations": result["citations"],
            "retrieved_chunks": retrieved_chunks,
            "retrieved_chunks_count": len(retrieved_chunks),
            "is_emergency": is_emergency,
            "emergency_helplines": emergency_numbers,
            "evidence_found": result["evidence_found"],
            "provider": result.get("provider", "local"),
            "category_filter": chosen_cat
        }

    def ingest_pdf(
        self,
        source_file_path: Path,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ingest, parse, chunk, embed, and index a disaster management PDF.
        Copies the file securely to data/documents/ and updates the FAISS index.
        """
        source_path = Path(source_file_path)
        metadata = metadata or {}

        # 1. Validate & Extract Text
        doc_data = DocumentLoader.extract_document(source_path, metadata)
        doc_id = doc_data["doc_id"]
        clean_filename = doc_data["filename"]

        # 2. Secure file persistence in data/documents/
        if source_path.parent.resolve() == RAGConfig.DOCUMENTS_DIR.resolve():
            dest_path = source_path
        else:
            dest_path = RAGConfig.DOCUMENTS_DIR / f"{doc_id}_{clean_filename}"
            shutil.copy2(source_path, dest_path)
        doc_data["file_path"] = str(dest_path)

        # 3. Semantic Chunking
        chunks = self.chunker.chunk_document(doc_data)
        if not chunks:
            raise DocumentProcessingError(f"No usable text chunks could be extracted from '{clean_filename}'.")

        # 4. Embedding Generation
        chunk_texts = [c["text"] for c in chunks]
        embeddings = self.embedding_provider.embed_texts(chunk_texts)

        # 5. Indexing into FAISS Vector Store
        self.vector_store.add_document(
            doc_metadata=doc_data,
            chunks=chunks,
            embeddings=embeddings
        )

        return {
            "doc_id": doc_id,
            "filename": clean_filename,
            "title": doc_data["title"],
            "organization": doc_data["organization"],
            "disaster_category": doc_data["disaster_category"],
            "total_pages": doc_data["total_pages"],
            "total_chunks": len(chunks),
            "status": "indexed"
        }

    def list_documents(self) -> List[Dict[str, Any]]:
        """Return catalog of all currently indexed documents."""
        return self.vector_store.get_catalog()

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove a document and its vectors from the index.
        Also deletes the stored PDF file from data/documents/.
        """
        doc_catalog = self.vector_store.documents_catalog.get(doc_id)
        if not doc_catalog:
            return False

        # Remove physical file if present
        for f in RAGConfig.DOCUMENTS_DIR.glob(f"{doc_id}_*"):
            try:
                f.unlink(missing_ok=True)
            except Exception:
                pass

        # Remove from FAISS and metadata
        success = self.vector_store.delete_document(doc_id, save_after=True)
        return success

    def rebuild_index(self) -> Dict[str, Any]:
        """
        Re-extract and re-index all stored PDF documents from data/documents/.
        Useful when embedding model or chunking parameters change.
        """
        stored_files = list(RAGConfig.DOCUMENTS_DIR.glob("*.pdf"))
        self.vector_store.clear()

        reindexed_count = 0
        total_chunks = 0
        errors = []

        for pdf_path in stored_files:
            try:
                meta = {"source_url": ""}
                res = self.ingest_pdf(pdf_path, meta)
                reindexed_count += 1
                total_chunks += res["total_chunks"]
            except Exception as e:
                errors.append(f"{pdf_path.name}: {str(e)}")

        return {
            "reindexed_documents": reindexed_count,
            "total_chunks": total_chunks,
            "errors": errors,
            "status": "rebuilt"
        }
