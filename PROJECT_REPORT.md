# DisasterShield — Disaster Management Guidance Chatbot
## Academic Project Report & Comprehensive System Specification

**Coursework**: Advanced College Assignment in Expert Systems & Decision-Tree Automation  
**Project Title**: DisasterShield — Deterministic Emergency Guidance Chatbot  
**System Architecture**: Pure Deterministic State-Machine Decision-Tree Expert System  
**Technology Stack**: Python 3.10+ / 3.14, Flask, Vanilla HTML5 / Modern CSS3 / ES6+ JavaScript, Pytest  
**Academic Date**: October 2026  

---

## 1. Executive Summary & Problem Formulation

Natural hazards—specifically **earthquakes**, **floods**, and **landslides**—pose severe life-safety threats across vulnerable regions. During active crisis events, generic generative language models present profound hazards:
- **Hallucinated Hotlines**: Fabricating defunct or fictitious telephone numbers instead of verified emergency helplines (`112`, `1078`).
- **Dangerous Speculation**: Formulating improvised evacuation advice that violates civil defense protocols (e.g., advising people to run into streets during active seismic tremors or attempt to drive through moving floodwaters).
- **Network Dependency**: Generative cloud APIs fail entirely when cellular towers, power grids, or internet backbones collapse during disaster events.
- **High Latency & Inconsistent Outputs**: Variable generation latency and non-deterministic variations when users need instant, standardized life-safety instructions.

**DisasterShield** resolves these life-critical issues by implementing an **offline-first, 100% deterministic rule-based expert decision tree chatbot system**. Through structured, multi-choice situational triage, DisasterShield guides individuals through validated survival protocols published by statutory Indian disaster management authorities: the **National Disaster Management Authority (NDMA)**, **Geological Survey of India (GSI)**, **Central Water Commission (CWC)**, and **National Disaster Response Force (NDRF)**.

---

## 2. Deterministic Expert System Architecture

The core engineering principle of DisasterShield is **absolute determinism, zero hallucinations, and complete offline survivability**.

```
+===================================================================================+
|                               DISASTERSHIELD CLIENT                               |
|                  (Responsive Vanilla HTML5 / Modern CSS / ES6+ JS)                |
+===================================================================================+
                                        |
                             [REST API JSON Requests]
                                        |
                                        v
+-----------------------------------------------------------------------------------+
|               DISASTERSHIELD RULE-BASED EMERGENCY GUIDANCE ENGINE                 |
|                             (chatbot_engine.py)                                   |
+-----------------------------------------------------------------------------------+
| • Pure Python State Machine Traversal (Zero External AI API Dependencies)         |
| • 35 Canonical Decision Paths across 4 Hierarchical Decision Stages               |
| • Situational Urgency Triage (NORMAL, PRECAUTIONARY, URGENT, CRITICAL)            |
| • Dynamic Interactive Flowchart Visualizer & Mermaid Syntax Generator             |
| • Audit-Grade Session Transcript Generator & Text Exporter                        |
| • 72-Hour Emergency Go-Bag Checklist with Local Storage Persistence               |
+-----------------------------------------------------------------------------------+
                                        |
                                        v
+-----------------------------------------------------------------------------------+
|                          STRUCTURED KNOWLEDGE BASES                               |
|       earthquake.json (13 paths) | flood.json (12 paths) | landslide.json (10)    |
|               checklist.json (Go-Bag) | sources.json (Hotlines)                   |
+-----------------------------------------------------------------------------------+
                                        |
                                        v
+===================================================================================+
|                            STATUTORY AUTHORITIES                                  |
|   NDMA (Earthquake) | CWC (Flood) | GSI (Landslide) | NDRF (Tactical Rescue)      |
|              Verified Official Helplines: 112, 1078, 101, 108                     |
+===================================================================================+
```

### Architectural Benefits Over Generative AI:
1. **Mathematical Reproducibility**: Given an identical sequence of situational inputs, the engine guarantees identical, validated life-safety guidance every time.
2. **Zero Latency**: Sub-millisecond response times executed entirely in local memory.
3. **Auditability & Traceability**: Every decision node maps directly to statutory standard operating procedures (SOPs).
4. **Resilience to Infrastructure Failure**: Runs 100% locally with zero internet, token budgets, or external API keys required.

---

## 3. Decision-Tree Hierarchy & Disaster Coverage

The system models crisis response across **4 hierarchical stages**:
- **Stage 1 (Root Assessment)**: Macro-environmental location triage (e.g., indoors vs. outdoors vs. transit).
- **Stage 2 (Immediate Hazard Triage)**: Evaluation of physical stability and structural peril (e.g., trapped under rubble, active tremors, water depth).
- **Stage 3 (Secondary Hazard Check)**: Detection of cascading secondary risks (e.g., gas leaks, electrical fires, road washouts).
- **Stage 4 (Terminal Guidance)**: Multi-faceted emergency action directive.

### 3.1 Earthquake Safety Decision Tree (13 Paths)
- **Indoor Stability**: Drop, Cover & Hold On under sturdy furniture; interior load-bearing wall crouch; bed survival posture with pillow head-shield.
- **Utility & Fire Defense**: Immediate domestic gas cylinder shutoff and breaker disconnection; prohibition of matches or open flames due to gas accumulation.
- **USAR Acoustic Signaling**: Rhythmic acoustic tapping (3 taps per minute) on metal pipes or structural beams to guide search-and-rescue dogs and acoustic listening devices.
- **Outdoor Hazards**: Immediate clearance of building envelopes (falling masonry/glass hazard zone), electric transmission lines, and overpasses.

### 3.2 Flood & Flash Flood Decision Tree (12 Paths)
- **Motorist Flooding**: Strict implementation of the statutory "Turn Around, Don't Drown" protocol. Highlights that 30 cm of moving water floats standard vehicles and 60 cm sweeps away heavy vehicles/SUVs.
- **Vertical Evacuation**: Directs occupants of multi-story structures to top floors or rooftops if ground levels are inundated, with bright visual signaling (cloth, mirrors, flashlights).
- **Submerged Electrical Isolation**: Prohibits touching submerged electrical breaker panels or wading through water touching live appliances.
- **Water Decontamination**: Standard water purification guidelines (vigorous 1-minute rolling boil or 4 drops chlorine disinfectant per liter).

### 3.3 Landslide & Debris Flow Decision Tree (10 Paths)
- **Pre-Failure Indicators**: Recognition of hillside tension cracks, tilting trees/poles, bulging retaining walls, and stuck doorframes.
- **Active Flow Escape**: Urgent lateral perpendicular escape sprint across the path of the slide rather than running downhill in the flow line.
- **Valley Debris Dams**: Immediate upslope evacuation upon noticing sudden river flow cessation or muddy surge warnings.
- **Impact Bracing**: Compact fetal curl protecting the head with intertwined arms if escape is physically blocked.

---

## 4. Structured Output Specification

Every completed decision-tree path yields a structured, audit-grade guidance payload comprising:

1. **Status & Severity**: Visual status banner with color-coded severity tag (`NORMAL`, `PRECAUTIONARY`, `URGENT`, `CRITICAL`).
2. **Executive Summary**: Clear, concise 2-sentence synopsis of the current operational posture.
3. **Immediate Life-Safety Actions**: Bulleted imperative actions to perform immediately.
4. **Actions to Strictly AVOID**: Explicit prohibitions preventing fatal user mistakes (e.g., *"DO NOT use elevators"*, *"DO NOT drink unboiled tap water"*).
5. **Preventive & Recovery Measures**: Follow-up safety steps after immediate stabilization.
6. **Verified Single-Tap Hotlines**: Click-to-call links directly connected to verified emergency numbers (`tel:112`, `tel:1078`, `tel:101`, `tel:108`).
7. **Statutory Reference**: Citation to the governing official manual (e.g., *NDMA National Earthquake Guidelines 2019, Section 4.2*).

---

## 5. Additional System Capabilities

### 5.1 72-Hour Emergency Go-Bag Checklist
An interactive supply catalog derived from NDMA recommendations, divided into 5 critical preparedness categories:
- Water & Hydration (3 liters/day per person for 72 hours)
- Food & Sustenance (Non-perishable, high-calorie canned food)
- First Aid & Medical Supplies (Trauma bandages, antiseptic, personal prescriptions)
- Tools & Emergency Equipment (Hand-crank radio, LED flashlight, emergency whistle)
- Essential Documents & Personal Items (Photocopies of identification, emergency cash, water-resistant pouch)

The checklist features real-time percentage readiness tracking and persists user check states across browser sessions via HTML5 `localStorage`.

### 5.2 Dynamic Flowchart Visualization Engine
- **Visual Hierarchical View**: Interactive collapsible decision tree rendered directly in the browser via `flowchart.js`.
- **Mermaid Diagram Export**: Generates raw, copyable Mermaid graph syntax for direct embedding in GitHub Markdown reports and civil defense documentation.

### 5.3 Session Transcript Generation
- Automatically tracks timestamps, sender identity (User / Bot), question prompts, option IDs, and final guidance.
- One-click copy to clipboard and downloadable `.txt` transcript file for post-incident auditing or coursework review.

---

## 6. Automated Testing Suite

The application is validated by an automated test suite of **20 tests** executed via `pytest`:

```text
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
collected 20 items

tests/test_api.py::TestDisasterShieldAPI::test_chat_step_progression PASSED [  5%]
tests/test_api.py::TestDisasterShieldAPI::test_checklist_endpoint PASSED [ 10%]
tests/test_api.py::TestDisasterShieldAPI::test_flowchart_endpoint PASSED [ 15%]
tests/test_api.py::TestDisasterShieldAPI::test_get_disasters PASSED      [ 20%]
tests/test_api.py::TestDisasterShieldAPI::test_health_endpoint PASSED    [ 25%]
tests/test_api.py::TestDisasterShieldAPI::test_index_page PASSED         [ 30%]
tests/test_api.py::TestDisasterShieldAPI::test_sources_endpoint PASSED   [ 35%]
tests/test_api.py::TestDisasterShieldAPI::test_start_chat_invalid_disaster PASSED [ 40%]
tests/test_api.py::TestDisasterShieldAPI::test_start_chat_missing_payload PASSED [ 45%]
tests/test_api.py::TestDisasterShieldAPI::test_start_chat_success PASSED [ 50%]
tests/test_api.py::TestDisasterShieldAPI::test_transcript_generation PASSED [ 55%]
tests/test_rule_engine.py::TestDisasterRuleEngine::test_all_decision_tree_paths_valid PASSED [ 60%]
tests/test_rule_engine.py::TestDisasterRuleEngine::test_datasets_loaded PASSED [ 65%]
tests/test_rule_engine.py::TestDisasterRuleEngine::test_earthquake_branching_outcomes PASSED [ 70%]
tests/test_rule_engine.py::TestDisasterRuleEngine::test_error_handling_invalid_inputs PASSED [ 75%]
tests/test_rule_engine.py::TestDisasterRuleEngine::test_flood_turn_around_dont_drown_branch PASSED [ 80%]
tests/test_rule_engine.py::TestDisasterRuleEngine::test_landslide_lateral_sprint_branch PASSED [ 85%]
tests/test_rule_engine.py::TestDisasterRuleEngine::test_mermaid_generation PASSED [ 90%]
tests/test_rule_engine.py::TestDisasterRuleEngine::test_sources_and_checklist_loaded PASSED [ 95%]
tests/test_rule_engine.py::TestDisasterRuleEngine::test_transcript_formatting PASSED [100%]

============================= 20 passed in 0.35s ==============================
```

---

## 7. Statutory Sources & Official Compliance

DisasterShield enforces strict fidelity to statutory Indian authorities:
- **National Disaster Management Authority (NDMA)**: [https://ndma.gov.in](https://ndma.gov.in)
- **Geological Survey of India (GSI)**: [https://www.gsi.gov.in](https://www.gsi.gov.in)
- **Central Water Commission (CWC)**: [http://cwc.gov.in](http://cwc.gov.in)
- **National Disaster Response Force (NDRF)**: 24/7 Control Room `1078`
- **Emergency Response Support System (ERSS)**: Universal Pan-India Helpline `112`
