# DisasterShield — Advanced RAG-Powered Disaster Management Assistant
## Academic Project Report & Comprehensive Architectural Specification

**Coursework**: Advanced College Assignment in Expert Systems & Retrieval-Augmented Generation (RAG)  
**Project Title**: DisasterShield — Hybrid Intelligent Disaster Management Guidance & Knowledge System  
**System Architecture**: Dual-Mode Hybrid Architecture (Deterministic Rule Engine + Advanced RAG Pipeline)  
**Technology Stack**: Python 3.14, Flask, FAISS, Scikit-Learn, PyPDF, Vanilla HTML5/CSS3/JavaScript  
**Academic Date**: October 2026  

---

## 1. Executive Summary & Project Objective

Natural hazards—specifically **earthquakes**, **floods**, and **landslides**—pose catastrophic threats across the Indian subcontinent. In emergency contexts, generic generative language models present profound risks: hallucinating emergency numbers, fabricating evacuation protocols, claiming non-existent live weather tracking, or failing entirely during network outages.

The objective of **DisasterShield** is to deliver a production-grade, locally runnable, **hybrid disaster management assistant** combining:
1. **Mode A: Deterministic Rule-Based Emergency Guidance Engine**: An offline-first, zero-latency decision tree that evaluates situational urgency through structured multiple-choice questions, executing explicit Python logic to guide users through life-or-death decisions without generative AI unpredictability.
2. **Mode B: Disaster Knowledge Assistant (Advanced RAG Pipeline)**: A document-grounded question-answering assistant that retrieves verified official guidelines published by statutory Indian authorities (**NDMA**, **GSI**, **CWC**, and **NDRF**) using hybrid vector search, delivering evidence-backed answers with exact page citations.
3. **Official Document Repository (Admin Ingestion)**: A secure document management interface enabling administrators to upload official PDF guidelines, view chunking statistics, delete obsolete documents with automatic index synchronization, and rebuild vector stores.

---

## 2. Hybrid Dual-Mode Architecture

The core design principle of DisasterShield is the **strict architectural separation of immediate crisis navigation from general academic/preparedness research**:

```
+===================================================================================+
|                               DISASTERSHIELD CLIENT                               |
|                  (Responsive Vanilla HTML5 / Modern CSS / ES6+ JS)                |
+===================================================================================+
        |                                                           |
   [Mode A Requests]                                           [Mode B Requests]
        |                                                           |
        v                                                           v
+-------------------------------+       +-------------------------------------------+
|    MODE A: EMERGENCY ENGINE   |       |         MODE B: ADVANCED RAG PIPELINE     |
|   (Deterministic State Graph) |       |  (Hybrid FAISS Retrieval & Synthesis)     |
+-------------------------------+       +-------------------------------------------+
| • 35 Canonical Decision Paths |       | Stage 1: PDF Text Extraction & Validation |
| • Earthquake, Flood, Landslide|       | Stage 2: Semantic Chunking (800 / 120 ov) |
| • Urgency Classification      |       | Stage 3: Local TF-IDF L2 Embeddings (1024)|
| • Offline JSON Knowledge Bases|       | Stage 4: Persistent FAISS Index (Cosine)  |
| • Audit-Grade Text Transcripts|       | Stage 5: Hybrid Retrieval (Dense+Sparse)  |
| • Mermaid Flowchart Generation|       | Stage 6: Prompt Isolation & Anti-Injection|
|                               |       | Stage 7: Grounded Answer Synthesis        |
+-------------------------------+       +-------------------------------------------+
        |                                                           |
        +-----------------------------+-----------------------------+
                                      |
                                      v
              +===============================================+
              |           STATUTORY SAFETY AUTHORITY          |
              |   NDMA (Earthquake) | CWC (Flood) | GSI (Mud)  |
              |   Verified Emergency Helplines: 112, 1078, 101|
              +===============================================+
```

### Mode Comparison Matrix

| Architectural Dimension | Mode A: Emergency Guidance | Mode B: Knowledge Assistant (RAG) |
| :--- | :--- | :--- |
| **Primary Use Case** | Active physical peril, immediate structural danger | Preparedness, mitigation, recovery protocols |
| **User Input Style** | Multi-choice situation buttons (zero typing required) | Natural-language query string with category filters |
| **Execution Model** | Explicit deterministic state-machine graph traversal | Hybrid dense vector + sparse keyword search |
| **AI / Model Role** | Zero LLM involvement; 100% deterministic Python | Local grounded extractive synthesizer or hosted LLM |
| **Citation Granularity** | SOP Section & Statutory Framework reference | Exact source PDF title, issuing body, and page number |
| **Emergency Fallback** | Fully functional offline with zero network connectivity| Automatic detection redirects user to 112 / 1078 |

---

## 3. Seven-Stage Advanced RAG Pipeline Specification

The RAG module (`rag/`) is organized into dedicated, decoupled components:

### Stage 1: Document Ingestion & Validation (`rag/document_loader.py`)
- **Format Verification**: Validates file extension (`.pdf`), maximum file size (bounded at 15 MB), and magic byte headers (`%PDF-`).
- **Path Traversal Defense**: Sanitizes filenames using regex `[^a-zA-Z0-9_\-\.]` and strips directory traversal tokens (`../`, `..\\`).
- **Scanned PDF Rejection**: Analyzes extracted character counts across all pages. If text density is zero, raises `ScannedPDFError` indicating that OCR processing is required, preventing corrupted empty embeddings.
- **Metadata Extraction**: Computes SHA-256 hash for document deduplication and infers issuing organization and disaster category from content headers.

### Stage 2: Text Cleaning & Semantic Chunking (`rag/chunker.py`)
- **Boundary-Aware Splitting**: Splits text on paragraph breaks and sentence terminators (`.`, `!`, `?`), ensuring that vital safety instructions ("DO NOT run outside") are never severed into misleading fragments ("run outside").
- **Configurable Geometry**: Default chunk size of ~800 tokens (~3,200 characters) with ~120 tokens (~480 characters) overlap.
- **Traceability Inheritance**: Every chunk inherits its parent `doc_id`, `filename`, `title`, `organization`, `disaster_category`, `source_url`, and explicit `page_number`.

### Stage 3: Embedding Generation (`rag/embeddings.py`)
- **Zero-API Local Architecture**: Implements `LocalTFIDFEmbeddingProvider` producing 1024-dimensional float32 vector representations.
- **Domain Seeding**: Initialized with high-priority Indian disaster vocabulary (NDMA, Richter, inundation, tension crack, lateral sprint, Go-Bag) ensuring rich representations from first startup.
- **L2 Unit Normalization**: Every document vector and query vector is normalized to $\|v\|_2 = 1.0$, allowing dot products to evaluate exactly to cosine similarity.
- **Model Persistence**: Serializes the fitted vectorizer to `data/vector_index/local_embedder.pkl` to prevent redundant retraining.

### Stage 4: Persistent Vector Database (`rag/vector_store.py`)
- **Engine**: Persistent FAISS index (`faiss.IndexFlatIP`) implementing inner-product metric on normalized vectors.
- **Catalog & Metadata Storage**: Paired with `chunks_metadata.json` and `documents_catalog.json` storing complete chunk records and issuing authority details.
- **Idempotency & Deduplication**: If an updated document with matching checksum or identifier is re-uploaded, existing vector records are excised before new vectors are appended.
- **Safe Rebuilding**: `rebuild_index()` reconstructs the vector index from all original documents stored on disk.

### Stage 5: Hybrid Retrieval Engine (`rag/hybrid_retriever.py`)
- **Score Fusion**: Combines dense FAISS cosine similarity ($S_{dense}$) with sparse term-frequency keyword matching ($S_{sparse}$) using configurable interpolation weight $\alpha = 0.60$:
  $$S_{hybrid} = \alpha \cdot S_{dense} + (1 - \alpha) \cdot S_{sparse}$$
- **Disaster Affinity Weighting**: Detects explicit disaster names in user queries and grants a $+0.15$ affinity boost to matching document categories while penalizing mismatched disasters.
- **Strict Relevance Threshold**: Enforces a minimum threshold ($0.10$). If no passage achieves this score, the system declines to generate speculative text and flags `evidence_found = False`.

### Stage 6: Context Construction & Prompt Defense (`rag/context_builder.py`)
- **Untrusted Passage Isolation**: Wraps retrieved document excerpts inside protective demarcation blocks:
  ```
  [Source 1]: "NDMA Earthquake Guidelines" | Page 2 | Section: Shaking Protocol
  <<<DOC_PASSAGE_START>>>
  When ground shaking commences, immediate life-safety action dictates...
  <<<DOC_PASSAGE_END>>>
  ```
- **Prompt Injection Defense**: Explicit system directives instruct the generator to treat all document text as untrusted data, ignoring embedded commands attempting to alter system instructions.
- **Immediate Life-Safety Interception**: `ContextBuilder.check_emergency_intent()` scans incoming prompts for critical distress indicators (`trapped`, `bleeding`, `crushed`, `gas leak`, `water rising`, `collapse`). When detected, an emergency alert banner is immediately prepended with direct hotlines (`112`, `1078`).

### Stage 7: Grounded Answer Synthesis (`rag/generator.py`)
- **Local Grounded Synthesizer**: Extracts verified imperative directives, structures them into actionable bullet points, segregates critical prohibitions ("Warnings to Strictly Avoid"), and affixes citations.
- **Hosted LLM Compatibility**: Supports optional integration with OpenAI (`gpt-4o-mini`) or Google Gemini (`gemini-1.5-flash`) via standard environment variables.
- **Honest Refusal Doctrine**: When the knowledge base lacks supporting evidence, states clearly: *"The official indexed knowledge base does not contain sufficient supporting information to answer this question."*

---

## 4. Official Knowledge Base & Indian Statutory Sources

DisasterShield is pre-populated with verified, authentic disaster guidelines published by statutory authorities of the Government of India:

| Document Title | Issuing Body | Primary Scope & Verified Protocols | Indexed Pages / Chunks |
| :--- | :--- | :--- | :--- |
| **NDMA Earthquake Safety Manual** | National Disaster Management Authority (NDMA) | Seismic zones III–V, Drop-Cover-Hold On protocol, indoor wall shielding, gas line shutoff, post-quake structural void tapping. | 3 Pages / 3 Chunks |
| **CWC & NDMA Flood Management Guide** | Central Water Commission (CWC) & NDMA | Flash flood thresholds, "Turn Around, Don't Drown", vehicle float depths (30 cm / 60 cm), vertical rooftop evacuation, water purification. | 3 Pages / 3 Chunks |
| **GSI Landslide Hazard Protocols** | Geological Survey of India (GSI) | Slope failure indicators, tension cracks, lateral perpendicular sprint, valley debris dam monitoring, post-slide slope stability. | 3 Pages / 3 Chunks |

### Verified Statutory Emergency Hotlines
- **112**: Emergency Response Support System (ERSS - Single Pan-India Emergency Number).
- **1078**: National Disaster Response Force (NDRF) 24/7 Operations Control Room.
- **101**: Fire & Rescue Services.
- **108 / 102**: Emergency Medical Services & Ambulance Triage.

---

## 5. Automated Test Suite & Evaluation Benchmark

DisasterShield includes a test suite of **49 automated tests** executed via `pytest`:

```
tests/test_api.py ..................... [11 tests passed]
tests/test_rule_engine.py ............. [ 9 tests passed]
tests/test_rag_pipeline.py ............ [20 tests passed]
tests/test_evaluation.py .............. [ 9 tests passed]

============================= 49 passed in 3.27s =============================
```

### Test Coverage Highlights:
1. **Rule Engine Integrity**: Verifies all 35 decision tree paths, urgency tagging, and transcript export.
2. **Document Ingestion Security**: Tests PDF header validation, rejection of non-PDFs and empty files, and graceful error handling for scanned image PDFs.
3. **Chunking & Vector Geometry**: Verifies metadata preservation, 1024-dimension vector alignment, and L2 unit normalization ($\|v\|_2 = 1.0$).
4. **Hybrid Retrieval**: Tests dense + sparse score fusion, category filtering, and out-of-domain rejection.
5. **Prompt Defense**: Tests prompt injection isolation and emergency distress word interception.
6. **Domain Evaluation Benchmark**: Evaluates grounded answers for earthquake, flood, and landslide queries, citation accuracy, and refusal to hallucinate unsupported advice.

---

## 6. System Limitations & Safety Considerations

1. **Static Official Guidance vs. Real-Time Radar**: The knowledge base contains verified standard operating procedures; it does not claim access to live Doppler weather radar, satellite telemetry, or active river discharge gauges.
2. **Scanned PDF Ingestion**: Only PDFs containing an embedded digital text stream are parsed by the lightweight native engine. Scanned image-only PDFs require an upstream OCR pre-processor.
3. **Hardware & Connectivity Independence**: Designed intentionally to run entirely on a standard CPU without GPU acceleration, paid subscriptions, or internet access.
4. **Emergency Redirection**: Under no circumstances does the AI replace human emergency triage. In immediate life-safety peril, users are directed to official emergency services (`112` / `1078`).
