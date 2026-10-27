# DisasterShield — Advanced RAG-Powered Disaster Management Assistant

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-black.svg)](https://palletsprojects.com/p/flask/)
[![FAISS](https://img.shields.io/badge/FAISS-CPU%20Vector%20Store-orange.svg)](https://github.com/facebookresearch/faiss)
[![Tests](https://img.shields.io/badge/Tests-49%20Passed%20(100%25)-success.svg)]()
[![Compliance](https://img.shields.io/badge/Compliance-NDMA%20%7C%20GSI%20%7C%20CWC%20%7C%20NDRF-red.svg)](https://ndma.gov.in)

> **DisasterShield** is a hybrid intelligent disaster management system that unites an offline deterministic decision-tree emergency guidance engine with an advanced Retrieval-Augmented Generation (RAG) assistant grounded in official Indian statutory PDF guidelines.

---

## Table of Contents

1. [Key Features & Dual-Mode Architecture](#key-features--dual-mode-architecture)
2. [Advanced RAG Pipeline (Mode B)](#advanced-rag-pipeline-mode-b)
3. [Official Pre-Indexed Knowledge Base](#official-pre-indexed-knowledge-base)
4. [Technology Stack](#technology-stack)
5. [Repository Structure](#repository-structure)
6. [Local Installation & Setup](#local-installation--setup)
7. [Running the Application](#running-the-application)
8. [Automated Testing & Benchmark Evaluation](#automated-testing--benchmark-evaluation)
9. [Document Repository Administration](#document-repository-administration)
10. [Academic Deliverables & Documentation](#academic-deliverables--documentation)
11. [Statutory Sources & Emergency Hotlines](#statutory-sources--emergency-hotlines)

---

## Key Features & Dual-Mode Architecture

DisasterShield enforces a strict architectural separation between **immediate life-safety crisis navigation** and **general disaster preparedness research**:

### Mode A: Emergency Guidance (Deterministic Decision Tree)
- **100% Deterministic & Offline-Capable**: Zero dependencies on external networks, paid AI APIs, or cloud databases.
- **35 Canonical Decision Paths**: Covers Earthquake, Flood & Flash Flood, and Landslide & Debris Flow across 4 hierarchical decision stages.
- **Urgency Triage**: Classifies situations from `NORMAL` through `PRECAUTIONARY`, `URGENT`, and `CRITICAL`.
- **Audit-Grade Output**: Terminal guidance segregated into **Immediate Actions**, **Warnings to Strictly Avoid**, **Preventive Measures**, and **Verified Single-Tap Hotlines**.
- **Interactive Visual Flowchart**: Interactive decision-tree graph viewer and Mermaid exporter.

### Mode B: Disaster Knowledge Assistant (Advanced RAG Pipeline)
- **Natural-Language Q&A**: Answers general disaster preparedness, mitigation, and recovery questions.
- **Official Grounding**: Answers are synthesized exclusively from verified official PDF manuals with exact page citations.
- **Hybrid Search**: Combines FAISS dense cosine similarity with sparse disaster-domain keyword matching.
- **Prompt Injection Defense**: Untrusted passage isolation (`<<<DOC_PASSAGE_START>>>`) and anti-override instructions.
- **Emergency Distress Interception**: Automatically detects immediate life-safety distress terms (`trapped`, `bleeding`, `crushed`, `gas leak`, `water rising`) and prioritizes emergency hotline redirection (`112` / `1078`).
- **Honest Refusal Doctrine**: Refuses to speculate or invent official guidelines when supporting evidence is absent.

---

## Advanced RAG Pipeline (Mode B)

```
[ User Natural Language Query ]
               |
               v
 [ Step 1: Emergency Intent Detector ] ---> If Life-Threat: Display Immediate 112/1078 Alert
               |
               v
 [ Step 2: Query Embedding (Local TF-IDF 1024-dim) ]
               |
               v
 [ Step 3: Hybrid Retrieval Engine ]
   ├── Dense Search: FAISS IndexFlatIP (Cosine Similarity)
   └── Sparse Search: Normalized Disaster Keyword Matcher
               |
               v
 [ Step 4: Category Filtering & Topic Affinity Boost ]
               |
               v
 [ Step 5: Relevance Threshold Check (Score >= 0.10) ]
   ├── Insufficient: Declines to fabricate unsupported advice
   └── Sufficient: Passes top-ranked deduplicated passages
               |
               v
 [ Step 6: Isolated Context Construction (Safe Boundaries) ]
               |
               v
 [ Step 7: Grounded Answer Synthesis & Page Citation Formatting ]
```

---

## Official Pre-Indexed Knowledge Base

DisasterShield includes verified, multi-page statutory guidelines published by the Government of India in `data/documents/`:

1. **NDMA Earthquake Safety Manual (`NDMA_Earthquake_Safety_Manual.pdf`)**
   - Issued by: National Disaster Management Authority (NDMA), Government of India
   - Scope: Seismic zones III–V, Drop-Cover-Hold On protocol, interior wall crouch, domestic gas shutoff, post-quake acoustic tapping signals under rubble.
2. **CWC & NDMA Flood Management Guide (`CWC_NDMA_Flood_Management_Guide.pdf`)**
   - Issued by: Central Water Commission (CWC) & NDMA
   - Scope: Flash flood warning signs, "Turn Around, Don't Drown" vehicle float limits (30 cm / 60 cm), vertical rooftop evacuation, drinking water purification.
3. **GSI Landslide Hazard Protocols (`GSI_NDMA_Landslide_Protocols.pdf`)**
   - Issued by: Geological Survey of India (GSI) & NDMA
   - Scope: Pre-failure slope indicators, tension cracks, lateral perpendicular sprint, valley debris dam burst warnings, post-slide slope stability.

---

## Technology Stack

- **Backend**: Python 3.14 / 3.10+ with Flask 3.0.0
- **Vector Database**: FAISS (Facebook AI Similarity Search - `faiss-cpu 1.15.1`)
- **Document Processing**: `pypdf 6.17.0` (Text extraction, page mapping, header validation)
- **Local Embeddings**: Scikit-Learn `TfidfVectorizer` (1024-dim, sublinear TF-IDF, L2 unit normalized)
- **PDF Generation**: ReportLab 4.4.1 (Official test document compilation)
- **Frontend**: Semantic HTML5, Vanilla CSS3 (Custom responsive emergency design system), Modern ES6+ JavaScript
- **Test Framework**: `pytest 9.0.2`

---

## Repository Structure

```
DisasterShield-AI/
├── app.py                     # Flask web server & REST endpoints (Modes A & B)
├── chatbot_engine.py          # Mode A: Deterministic decision-tree rule engine
├── run.py                     # Server launcher
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable configuration template
├── README.md                  # Comprehensive setup & project guide
├── PROJECT_REPORT.md          # Comprehensive academic project report
│
├── rag/                       # Mode B: Advanced RAG Pipeline
│   ├── __init__.py            # Module exports
│   ├── config.py              # Central configuration & thresholds
│   ├── document_loader.py     # PDF validation, text extraction & security
│   ├── chunker.py             # Semantic sentence-aware chunking
│   ├── embeddings.py          # Local TF-IDF & optional hosted embeddings
│   ├── vector_store.py        # Persistent FAISS IndexFlatIP & metadata catalog
│   ├── hybrid_retriever.py    # Dense + sparse score fusion & affinity weighting
│   ├── context_builder.py     # Context isolation & anti-injection defense
│   ├── generator.py           # Grounded answer synthesis & citation builder
│   └── pipeline.py            # Master RAG pipeline coordinator
│
├── data/
│   ├── documents/             # Official statutory PDF guidelines
│   ├── vector_index/          # Persistent FAISS index, embedder & metadata JSON
│   ├── earthquake.json        # Mode A decision tree (13 paths)
│   ├── flood.json             # Mode A decision tree (12 paths)
│   ├── landslide.json         # Mode A decision tree (10 paths)
│   ├── checklist.json         # 72-Hour Go-Bag supply catalog
│   └── sources.json           # Verified statutory authorities & hotlines
│
├── static/
│   ├── css/style.css          # Emergency design system & responsive layout
│   └── js/
│       ├── app.js             # Mode A & Mode B client-side controllers
│       └── flowchart.js       # Dynamic decision-tree visualizer
│
├── templates/
│   └── index.html             # Single-page hybrid emergency dashboard
│
├── tests/
│   ├── test_rule_engine.py    # Mode A unit tests (9 tests)
│   ├── test_api.py            # Mode A Flask endpoint tests (11 tests)
│   ├── test_rag_pipeline.py   # Mode B RAG unit & integration tests (20 tests)
│   └── test_evaluation.py     # Groundedness & citation benchmarks (9 tests)
│
├── docs/                      # Academic deliverables
│   ├── PROJECT_REPORT.md      # Detailed academic specification
│   ├── flowchart.md           # Decision-tree Mermaid flowcharts
│   └── sample_transcript.md   # Chronological transcripts from actual test runs
│
└── scripts/
    └── create_initial_knowledge_base.py # Generator for initial official PDFs
```

---

## Local Installation & Setup

### Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14 installed.
- Git (optional).

### 1. Open Workspace Directory
```bash
cd c:\Users\loq\Documents\NEHA\Project\DisasterShield-AI
```

### 2. (Recommended) Create a Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment (Optional)
The system runs **100% locally with zero paid API keys** by default. To inspect or customize settings, copy the example environment file:
```bash
copy .env.example .env
```

---

## Running the Application

Launch the local web server:
```bash
python run.py
```
*Or directly via Flask:*
```bash
python app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## Automated Testing & Benchmark Evaluation

DisasterShield includes a test suite of **49 automated tests** covering decision logic, RAG pipeline mechanics, security constraints, and safety benchmarks.

To execute the complete test suite:
```bash
pytest -v
```

### Expected Output:
```text
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
collected 49 items

tests/test_api.py ..................... [11 tests passed]
tests/test_evaluation.py .............. [ 9 tests passed]
tests/test_rag_pipeline.py ............ [20 tests passed]
tests/test_rule_engine.py ............. [ 9 tests passed]

============================= 49 passed in 3.27s =============================
```

### Test Suite Organization:
- `tests/test_rule_engine.py`: Validates all 35 decision-tree branches, urgency classification, and transcript generation.
- `tests/test_api.py`: Validates core Flask endpoints (`/api/chat/start`, `/api/chat/step`, `/api/sources`, `/api/flowchart/<id>`).
- `tests/test_rag_pipeline.py`: Tests PDF text parsing, chunk creation, 1024-dimension TF-IDF vector generation, FAISS index addition/deletion, hybrid retrieval, prompt injection defense, and RAG API routes.
- `tests/test_evaluation.py`: Evaluates earthquake, flood, and landslide queries, citation accuracy, immediate life-safety redirection, and appropriate refusal on irrelevant questions.

---

## Document Repository Administration

DisasterShield includes a built-in administrative interface under the **"Document Repository"** tab (`#paneDocAdmin`):

1. **Upload Official Guidelines**:
   - Drag and drop or browse for genuine official PDF documents (Max 15 MB).
   - Provide optional title, issuing organization, disaster category, and source URL.
   - The backend validates the PDF magic header, extracts text, generates chunks, computes embeddings, and updates the FAISS index automatically.
2. **Inspect Indexed Documents**:
   - View document filenames, issuing authorities, categories, page counts, chunk totals, and file sizes.
3. **Delete Obsolete Documents**:
   - Click "Delete" next to any document to excise its vector chunks from the index.
4. **Rebuild Vector Index**:
   - Click "Rebuild Vector Index" to re-extract, re-chunk, and re-embed all official PDFs stored in `data/documents/`.

---

## Academic Deliverables & Documentation

| Deliverable | Location | Description |
| :--- | :--- | :--- |
| **Complete Source Code** | `app.py`, `chatbot_engine.py`, `rag/`, `templates/`, `static/` | Fully functional hybrid web application |
| **Decision Flowchart** | [`docs/flowchart.md`](file:///c:/Users/loq/Documents/NEHA/Project/DisasterShield-AI/docs/flowchart.md) & In-App Viewer | Mermaid diagrams generated from actual decision logic |
| **Sample Conversation Transcripts** | [`docs/sample_transcript.md`](file:///c:/Users/loq/Documents/NEHA/Project/DisasterShield-AI/docs/sample_transcript.md) | Chronological session logs from actual runs |
| **Academic Project Report** | [`docs/PROJECT_REPORT.md`](file:///c:/Users/loq/Documents/NEHA/Project/DisasterShield-AI/docs/PROJECT_REPORT.md) | Comprehensive report detailing hybrid RAG architecture |
| **Test Suites** | `tests/` (49 tests) | 100% passing automated unit, integration, and evaluation tests |

---

## Statutory Sources & Emergency Hotlines

Every safety protocol in DisasterShield is mapped to statutory guidelines from:
- **NDMA (National Disaster Management Authority)**: Apex disaster body of India.
- **GSI (Geological Survey of India)**: Nodal agency for landslide monitoring and hazard zonation.
- **CWC (Central Water Commission)**: Hydrological monitoring and flood forecasting.
- **NDRF (National Disaster Response Force)**: Specialized disaster search and rescue operations.

### Verified Pan-India Emergency Telephone Numbers:
- **112**: Emergency Response Support System (ERSS - All Emergencies: Police, Fire, Ambulance)
- **1078**: NDRF 24/7 Operations Control Room
- **101**: Fire and Emergency Services
- **108 / 102**: Ambulance Medical Services & Emergency Triage
- **1033**: National Highways Roadside Helpline

---

## License & Academic Disclaimer

Developed for academic coursework and demonstration. In any live, active emergency event, users must always prioritize instructions given directly on-ground by official disaster response personnel (**NDRF**, local police, fire service, and district administration).
