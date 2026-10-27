"""
DisasterShield Document Loader & PDF Processor
===============================================
Extracts text and metadata from official disaster management PDF documents.
Handles security validations, filename sanitization, scanned PDF detection,
and page-level text extraction.
"""

import os
import re
import hashlib
from typing import Dict, Any, List
from pathlib import Path
from pypdf import PdfReader
from rag.config import RAGConfig


class DocumentProcessingError(Exception):
    """Raised when PDF extraction or validation fails."""
    pass


class ScannedPDFError(DocumentProcessingError):
    """Raised when PDF contains only scanned raster images without an embedded text layer."""
    pass


class DocumentLoader:
    """Extracts, cleans, and structures text from uploaded official PDF guidelines."""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent directory traversal and filesystem attacks.
        Strips path separators, control characters, and dangerous sequences.
        """
        base = os.path.basename(filename).strip()
        clean = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", base)
        if not clean.lower().endswith(".pdf"):
            clean += ".pdf"
        if clean.startswith("."):
            clean = "document_" + clean[1:]
        return clean

    @classmethod
    def validate_file(cls, file_path: Path) -> None:
        """Validate file existence, size, extension, and PDF header magic bytes."""
        if not file_path.exists():
            raise DocumentProcessingError(f"File not found: {file_path}")

        size = file_path.stat().st_size
        if size == 0:
            raise DocumentProcessingError("File is empty (0 bytes).")
        if size > RAGConfig.MAX_UPLOAD_BYTES:
            max_mb = RAGConfig.MAX_UPLOAD_SIZE_MB
            raise DocumentProcessingError(f"File size exceeds maximum allowed limit ({max_mb} MB).")

        if file_path.suffix.lower() not in RAGConfig.ALLOWED_EXTENSIONS:
            raise DocumentProcessingError(f"Unsupported file format '{file_path.suffix}'. Only PDF files are supported.")

        try:
            with open(file_path, "rb") as f:
                header = f.read(5)
                if header != b"%PDF-":
                    raise DocumentProcessingError("Invalid file header: File is not a valid PDF document.")
        except Exception as e:
            if isinstance(e, DocumentProcessingError):
                raise
            raise DocumentProcessingError(f"Error reading PDF header: {str(e)}")

    @classmethod
    def compute_file_hash(cls, file_path: Path) -> str:
        """Compute SHA256 checksum of document for deduplication."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    @classmethod
    def extract_document(
        cls,
        file_path: Path,
        custom_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Extract text from PDF page-by-page preserving document metadata.
        Returns structured document dictionary with list of extracted pages.
        """
        cls.validate_file(file_path)
        custom_metadata = custom_metadata or {}

        try:
            reader = PdfReader(str(file_path))
        except Exception as e:
            raise DocumentProcessingError(f"Corrupted or password-protected PDF document: {str(e)}")

        total_pages = len(reader.pages)
        if total_pages == 0:
            raise DocumentProcessingError("PDF document contains no pages.")

        doc_hash = cls.compute_file_hash(file_path)
        clean_filename = cls.sanitize_filename(file_path.name)
        # Strip internal doc_xxxx_ prefix from filename if present
        display_name = re.sub(r"^doc_[a-f0-9]{8,12}_", "", clean_filename)
        doc_id = custom_metadata.get("doc_id") or f"doc_{doc_hash[:12]}"

        pages: List[Dict[str, Any]] = []
        total_text_length = 0

        for page_idx, page in enumerate(reader.pages, start=1):
            try:
                raw_text = page.extract_text() or ""
            except Exception:
                raw_text = ""

            cleaned_text = cls.clean_text(raw_text)
            total_text_length += len(cleaned_text)

            pages.append({
                "page_number": page_idx,
                "text": cleaned_text,
                "char_count": len(cleaned_text),
                "is_empty": len(cleaned_text.strip()) == 0
            })

        if total_text_length < (total_pages * 30):
            raise ScannedPDFError(
                f"The uploaded document '{clean_filename}' appears to be a scanned image-only PDF without an "
                f"embedded digital text layer. OCR processing is required before this document can be indexed."
            )

        # Infer title
        pdf_meta = reader.metadata or {}
        embedded_title = getattr(pdf_meta, "title", None) or ""
        inferred_title = custom_metadata.get("title")

        if not inferred_title and embedded_title and embedded_title != "(anonymous)":
            inferred_title = embedded_title

        if not inferred_title and pages and pages[0]["text"]:
            first_line = pages[0]["text"].splitlines()[0].strip()
            if len(first_line) > 5 and len(first_line) < 100:
                inferred_title = first_line

        if not inferred_title:
            inferred_title = display_name.replace(".pdf", "").replace("_", " ").title()

        organization = custom_metadata.get("organization")
        if not organization and pages and len(pages) > 0:
            for l in pages[0]["text"].splitlines()[:8]:
                if "issuing authority:" in l.lower():
                    organization = l.split(":", 1)[1].split("|")[0].strip()
                    break
        if not organization:
            organization = "Official Disaster Management Authority"

        category = custom_metadata.get("disaster_category") or cls._infer_category(clean_filename, inferred_title, pages[0]["text"] if pages else "")
        url = custom_metadata.get("source_url") or ""

        return {
            "doc_id": doc_id,
            "filename": clean_filename,
            "file_hash": doc_hash,
            "file_size_bytes": file_path.stat().st_size,
            "title": inferred_title,
            "organization": organization,
            "disaster_category": category,
            "source_url": url,
            "total_pages": total_pages,
            "pages": pages
        }

    @staticmethod
    def _infer_category(filename: str, title: str, text: str) -> str:
        """Infer disaster category by prioritizing filename and title over incidental body text."""
        name_str = f"{filename} {title}".lower()
        if "landslide" in name_str or "debris flow" in name_str or "rockfall" in name_str:
            return "landslide"
        if "flood" in name_str or "inundation" in name_str or "flash flood" in name_str:
            return "flood"
        if "earthquake" in name_str or "seismic" in name_str or "tremor" in name_str:
            return "earthquake"

        t_lower = text.lower()
        counts = {
            "earthquake": t_lower.count("earthquake") + t_lower.count("tremor"),
            "flood": t_lower.count("flood") + t_lower.count("inundation"),
            "landslide": t_lower.count("landslide") + t_lower.count("debris flow")
        }
        best = max(counts, key=counts.get)
        return best if counts[best] > 0 else "general"

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean extraction artifacts while preserving critical safety punctuation."""
        if not text:
            return ""

        text = text.replace("\x00", "")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = text.replace("\xa0", " ")
        text = re.sub(r"\t+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ ]{2,}", " ", text)
        return text.strip()
