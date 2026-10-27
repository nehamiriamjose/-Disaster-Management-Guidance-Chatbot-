# DisasterShield — Disaster Management Guidance Chatbot

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-black.svg)](https://palletsprojects.com/p/flask/)
[![Tests](https://img.shields.io/badge/Tests-20%20Passed%20(100%25)-success.svg)]()
[![Compliance](https://img.shields.io/badge/Compliance-NDMA%20%7C%20GSI%20%7C%20CWC%20%7C%20NDRF-red.svg)](https://ndma.gov.in)

> **DisasterShield** is an offline-capable, deterministic decision-tree emergency guidance chatbot designed to provide immediate life-safety guidance and survival triage during natural disasters. All guidance paths are strictly derived from official statutory protocols published by the National Disaster Management Authority (NDMA), Geological Survey of India (GSI), Central Water Commission (CWC), and National Disaster Response Force (NDRF).

---

## Table of Contents

1. [Key Features & System Architecture](#key-features--system-architecture)
2. [Disaster Decision Trees & Coverage](#disaster-decision-trees--coverage)
3. [Technology Stack](#technology-stack)
4. [Repository Structure](#repository-structure)
5. [Local Installation & Setup](#local-installation--setup)
6. [Running the Application](#running-the-application)
7. [Automated Testing](#automated-testing)
8. [Academic Deliverables & Documentation](#academic-deliverables--documentation)
9. [Statutory Sources & Emergency Hotlines](#statutory-sources--emergency-hotlines)

---

## Key Features & System Architecture

DisasterShield is built on a **pure deterministic rule-based expert system architecture**, guaranteeing:

- **100% Deterministic & Transparent**: Zero non-deterministic hallucinations, speculative advice, or altered helpline numbers. Every response is verified against statutory disaster management guidelines.
- **100% Offline-Capable**: Fully functional in high-stakes environments during network collapses or power grid failures without any cloud APIs, external tokens, or third-party dependencies.
- **35 Canonical Decision Paths**: Exhaustive 4-stage decision trees for Earthquake, Flood & Flash Flood, and Landslide & Debris Flow.
- **Real-Time Urgency Triage**: Dynamically classifies situational severity across `NORMAL`, `PRECAUTIONARY`, `URGENT`, and `CRITICAL`.
- **Structured Audit-Grade Guidance**: Terminal advice explicitly segregates:
  1. **Immediate Life-Safety Actions** (what to do right now)
  2. **Warnings & Actions to Strictly AVOID** (critical hazards and common mistakes)
  3. **Preventive & Recovery Measures** (secondary hazard precautions)
  4. **Verified Single-Tap Emergency Hotlines** (`112`, `1078`, `101`, `108`)
- **Interactive Visual Flowchart**: Interactive decision-tree graph viewer and instant Mermaid diagram syntax exporter for Markdown/GitHub.
- **72-Hour Emergency Go-Bag Checklist**: Categorized supply readiness checklist with real-time percentage tracking and persistent local storage.
- **Session Transcript Generator**: One-click generation, clipboard copying, and text file export of conversation transcripts for auditing.

---

## Disaster Decision Trees & Coverage

```
                          [ User Selects Disaster Scenario ]
                                          |
                +-------------------------+-------------------------+
                |                         |                         |
                v                         v                         v
        [ Earthquake ]            [ Flood & Flash Flood ]   [ Landslide & Debris Flow ]
        (13 Decision Paths)       (12 Decision Paths)       (10 Decision Paths)
                |                         |                         |
                +-------------------------+-------------------------+
                                          |
                                          v
                           [ Stage 1: Location Assessment ]
                                          |
                                          v
                         [ Stage 2: Immediate Hazard Triage ]
                                          |
                                          v
                         [ Stage 3: Secondary Threat Check ]
                                          |
                                          v
                      [ Stage 4: Structured Terminal Guidance ]
                      - Severity & Status Banner
                      - Immediate Life-Safety Actions
                      - Actions to Avoid
                      - Preventive Measures
                      - Single-Tap Emergency Hotlines
```

### 1. Earthquake Safety (13 Decision Paths)
- **Protocols**: Drop, Cover & Hold On under sturdy furniture; interior load-bearing wall crouch; bed survival posture with pillow head-shield; gas shutoff to prevent utility fires; USAR acoustic tapping (3 taps per minute) under rubble.

### 2. Flood & Flash Flood Safety (12 Decision Paths)
- **Protocols**: "Turn Around, Don't Drown" vehicle float limits (30 cm floating, 60 cm swept away); vertical rooftop evacuation with bright signaling; submerged electrical breaker isolation; post-flood water decontamination (boiling or chlorine disinfection).

### 3. Landslide & Debris Flow Safety (10 Decision Paths)
- **Protocols**: Pre-failure hillside slope indicators (new tension cracks, jammed doorframes, tilting trees); lateral perpendicular sprint escape from fall lines; valley debris dam burst warnings; compact fetal head-shield brace if escape is blocked.

---

## Technology Stack

- **Backend**: Python 3.10+ / 3.14 with Flask 3.0.0
- **Rule Engine**: Pure Python state-machine rule engine (`chatbot_engine.py`)
- **Knowledge Base**: Structured JSON schemas (`data/earthquake.json`, `data/flood.json`, `data/landslide.json`, `data/checklist.json`, `data/sources.json`)
- **Frontend**: Semantic HTML5, Vanilla CSS3 (Custom responsive emergency design system), Modern ES6+ JavaScript
- **Test Framework**: `pytest 9.0.2` / `unittest`

---

## Repository Structure

```
DisasterShield-AI/
├── app.py                     # Flask web server & REST endpoints
├── chatbot_engine.py          # Deterministic decision-tree rule engine
├── run.py                     # CLI launcher with optional browser auto-open
├── requirements.txt           # Python dependencies (Flask, pytest)
├── .env.example               # Environment configuration template
├── README.md                  # Comprehensive setup & project guide
├── PROJECT_REPORT.md          # Academic specification & project report
├── generate_transcripts.py    # Script to simulate scenarios and generate transcripts
│
├── data/                      # Decision trees & reference datasets
│   ├── earthquake.json        # 13 decision paths (NDMA seismic guidelines)
│   ├── flood.json             # 12 decision paths (CWC & NDMA flood guidelines)
│   ├── landslide.json         # 10 decision paths (GSI & NDMA landslide guidelines)
│   ├── checklist.json         # 72-Hour Go-Bag supply catalog
│   └── sources.json           # Verified statutory authorities & hotline directory
│
├── static/
│   ├── css/style.css          # Emergency design system & responsive layout
│   └── js/
│       ├── app.js             # Client-side controller & state machine
│       └── flowchart.js       # Dynamic decision-tree visualizer & Mermaid exporter
│
├── templates/
│   └── index.html             # Single-page responsive emergency dashboard
│
├── tests/
│   ├── test_rule_engine.py    # Rule engine unit tests (9 tests)
│   ├── test_api.py            # Flask REST API integration tests (11 tests)
│   └── __init__.py
│
└── docs/                      # Academic deliverables
    ├── PROJECT_REPORT.md      # Detailed academic specification
    ├── flowchart.md           # Decision-tree Mermaid flowcharts
    └── sample_transcript.md   # Chronological transcripts from actual test runs
```

---

## Local Installation & Setup

### Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14 installed.

### 1. Open Workspace Directory
```bash
cd c:\Users\loq\Documents\NEHA\Project\DisasterShield-AI
```

### 2. (Optional) Create a Virtual Environment
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

---

## Running the Application

Launch the local web server with automatic browser launch:
```bash
python run.py --open
```

Or start standard server:
```bash
python run.py
```
*(Or directly via Flask: `python app.py`)*

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## Automated Testing

DisasterShield includes an automated test suite of **20 tests** covering decision logic, path integrity, API responses, and error handling.

To execute the test suite:
```bash
pytest -v
```

### Expected Output:
```text
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
collected 20 items

tests/test_api.py ...........                                            [ 55%]
tests/test_rule_engine.py .........                                      [100%]

============================= 20 passed in 0.35s ==============================
```

---

## Academic Deliverables & Documentation

- [`PROJECT_REPORT.md`](file:///c:/Users/loq/Documents/NEHA/Project/DisasterShield-AI/PROJECT_REPORT.md): Comprehensive academic report detailing design philosophy, rule-engine implementation, and compliance.
- [`docs/flowchart.md`](file:///c:/Users/loq/Documents/NEHA/Project/DisasterShield-AI/docs/flowchart.md): Complete Mermaid flowchart code for all 3 disaster decision trees.
- [`docs/sample_transcript.md`](file:///c:/Users/loq/Documents/NEHA/Project/DisasterShield-AI/docs/sample_transcript.md): Official sample execution transcripts across 6 diverse disaster scenarios.

To regenerate fresh scenario transcripts:
```bash
python generate_transcripts.py
```

---

## Statutory Sources & Emergency Hotlines

All guidance rules and emergency numbers in DisasterShield are verified against official authorities:

| Emergency Service | Pan-India Number | Authority / Mandate |
| :--- | :--- | :--- |
| **All Emergencies** | **112** | Emergency Response Support System (ERSS), MHA |
| **Disaster Response** | **1078** | National Disaster Response Force (NDRF) |
| **Fire & Rescue** | **101** | National Fire Service |
| **Medical Ambulance** | **108** | Emergency Medical Services |
| **National Disaster Management** | — | [NDMA India](https://ndma.gov.in) |
| **Landslide Hazards** | — | [Geological Survey of India](https://www.gsi.gov.in) |
| **Flood Monitoring** | — | [Central Water Commission](http://cwc.gov.in) |
