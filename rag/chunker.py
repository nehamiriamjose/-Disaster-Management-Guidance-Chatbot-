"""
DisasterShield Document Chunker
===============================
Splits extracted document text into semantically cohesive, metadata-rich chunks.
Preserves page numbers, document origin, and section headings while maintaining
sentence boundaries to protect the integrity of safety warnings.
"""

import re
from typing import List, Dict, Any
from rag.config import RAGConfig


class DocumentChunker:
    """Configurable chunker splitting documents into vector-indexable passages."""

    def __init__(
        self,
        chunk_size_chars: int = RAGConfig.CHUNK_SIZE_CHARS,
        chunk_overlap_chars: int = RAGConfig.CHUNK_OVERLAP_CHARS,
        min_chunk_chars: int = RAGConfig.MIN_CHUNK_CHARS
    ):
        self.chunk_size = chunk_size_chars
        self.chunk_overlap = chunk_overlap_chars
        self.min_chunk_size = min_chunk_chars

    def chunk_document(self, doc_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split a parsed document dictionary (from DocumentLoader) into chunks.
        Each chunk inherits document metadata and explicit page number.
        """
        all_chunks: List[Dict[str, Any]] = []
        doc_id = doc_data["doc_id"]
        doc_title = doc_data.get("title", "")
        organization = doc_data.get("organization", "")
        category = doc_data.get("disaster_category", "general")
        source_url = doc_data.get("source_url", "")
        filename = doc_data.get("filename", "")

        chunk_counter = 0

        for page in doc_data.get("pages", []):
            page_num = page["page_number"]
            page_text = page.get("text", "").strip()

            if not page_text or len(page_text) < self.min_chunk_size:
                # If short, check if it has meaningful content
                if len(page_text) > 40:
                    chunk_counter += 1
                    all_chunks.append({
                        "chunk_id": f"{doc_id}_p{page_num}_c{chunk_counter}",
                        "doc_id": doc_id,
                        "filename": filename,
                        "title": doc_title,
                        "organization": organization,
                        "disaster_category": category,
                        "source_url": source_url,
                        "page_number": page_num,
                        "section_heading": self._detect_heading(page_text),
                        "text": page_text,
                        "content": page_text,
                        "char_count": len(page_text)
                    })
                continue

            page_chunks = self._split_page_text(page_text)

            for text_chunk in page_chunks:
                text_chunk = text_chunk.strip()
                if len(text_chunk) < self.min_chunk_size:
                    continue

                chunk_counter += 1
                heading = self._detect_heading(text_chunk)

                all_chunks.append({
                    "chunk_id": f"{doc_id}_p{page_num}_c{chunk_counter}",
                    "doc_id": doc_id,
                    "filename": filename,
                    "title": doc_title,
                    "organization": organization,
                    "disaster_category": category,
                    "source_url": source_url,
                    "page_number": page_num,
                    "section_heading": heading,
                    "text": text_chunk,
                    "content": text_chunk,
                    "char_count": len(text_chunk)
                })

        return all_chunks

    def _split_page_text(self, text: str) -> List[str]:
        """
        Split text using paragraph breaks first, then sentence boundaries,
        respecting chunk_size and chunk_overlap without chopping safety advice mid-sentence.
        """
        if len(text) <= self.chunk_size:
            return [text]

        paragraphs = text.split("\n\n")
        chunks: List[str] = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding this paragraph exceeds chunk size:
            if len(current_chunk) + len(para) + 2 > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    # Retain overlap from end of current_chunk
                    overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                    # Snap to nearest sentence or word boundary in overlap
                    last_period = overlap_text.rfind(". ")
                    if last_period != -1:
                        overlap_text = overlap_text[last_period + 2:]
                    current_chunk = overlap_text + "\n\n" + para if overlap_text else para
                else:
                    # Single paragraph is larger than chunk_size: split by sentences
                    sentence_chunks = self._split_by_sentences(para)
                    chunks.extend(sentence_chunks[:-1])
                    current_chunk = sentence_chunks[-1] if sentence_chunks else ""
            else:
                current_chunk = current_chunk + "\n\n" + para if current_chunk else para

        if current_chunk and len(current_chunk.strip()) >= self.min_chunk_size:
            chunks.append(current_chunk.strip())

        return chunks

    def _split_by_sentences(self, long_text: str) -> List[str]:
        """Split a large paragraph along sentence boundaries."""
        sentences = re.split(r"(?<=[.!?])\s+", long_text)
        result: List[str] = []
        curr = ""

        for sent in sentences:
            if len(curr) + len(sent) + 1 > self.chunk_size:
                if curr:
                    result.append(curr.strip())
                curr = sent
            else:
                curr = (curr + " " + sent).strip()

        if curr:
            result.append(curr.strip())

        return result

    @staticmethod
    def _detect_heading(chunk_text: str) -> str:
        """Inspect the top lines of a chunk for section headings or uppercase headers."""
        lines = [line.strip() for line in chunk_text.splitlines() if line.strip()]
        if not lines:
            return "General Safety Guidance"

        first_line = lines[0]
        # Check markdown heading
        if first_line.startswith("#"):
            return first_line.lstrip("#").strip()
        # Check numbered section like "1.1 Pre-Monsoon Precautions" or "Section A: Indoor Safety"
        if re.match(r"^(\d+(\.\d+)*|[A-Z]\.|\bSection\b|\bChapter\b|\bStep\b)", first_line, re.IGNORECASE):
            return first_line[:80]
        # Check all caps line
        if first_line.isupper() and len(first_line) < 60:
            return first_line

        return "Official Guideline Section"
