# DisasterShield Implementation Plan & Architecture

## Overview
DisasterShield is a responsive web application and rule-based decision-tree chatbot for disaster safety guidance (Earthquake, Flood, Landslide) built for an academic assignment. It is fully self-contained using Python (Flask), Vanilla CSS, and modern JavaScript, strictly adhering to verified official disaster management guidance (NDMA India, GSI, CWC, NDRF, Emergency 112).

---

## Architecture

```
DisasterShield-AI/
├── app.py                     # Flask application routes and API endpoints
├── chatbot_engine.py          # Pure Python Rule Engine for decision tree traversal
├── data/
│   ├── earthquake.json        # Decision tree & safety guidance for Earthquakes
│   ├── flood.json             # Decision tree & safety guidance for Floods
│   ├── landslide.json         # Decision tree & safety guidance for Landslides
│   ├── checklist.json         # 72-Hour Emergency Preparedness Go-Bag checklist
│   └── sources.json           # Official verified sources (NDMA, GSI, CWC, IMD, NDRF)
├── static/
│   ├── css/
│   │   └── style.css          # Professional emergency-management dashboard styling
│   └── js/
│       ├── app.js             # Chatbot UI, state management, checklist, transcript
│       └── flowchart.js       # Interactive decision tree diagram renderer
├── templates/
│   └── index.html             # Main dashboard (Navbar, Disaster Cards, Chat, Checklist, Flowchart, Sources)
├── tests/
│   ├── __init__.py
│   ├── test_rule_engine.py    # Unit tests for rule tree traversal, branches, validation
│   └── test_api.py            # Integration tests for Flask endpoints and transcripts
├── docs/
│   ├── flowchart.md           # Mermaid decision tree flowchart for academic submission
│   ├── sample_transcript.md   # Actual test run transcripts for all 3 disaster branches
│   └── PROJECT_REPORT.md      # Academic report covering objectives, tech stack, rules, sources
├── run.py                     # CLI launcher
├── requirements.txt           # Minimal dependencies (Flask)
└── README.md                  # Comprehensive setup, run instructions, and project documentation
```

---

## Detailed Decision Branches (Minimum 4 Decision Points per Disaster)

### 1. Earthquake Tree:
- **Point 1 (Location):** Indoors vs Outdoors vs In a moving vehicle
  - **Point 2 (Immediate Situation):**
    - Indoors: Shaking actively ongoing vs Shaking stopped & checking surroundings vs Trapped under rubble/debris
    - Outdoors: Near tall buildings/power lines vs Open ground vs Near slope/cliff
    - In Vehicle: On a bridge/overpass vs Open road away from hazards
  - **Point 3 (Structural & Hazard Assessment):**
    - Indoors (Shaking stopped): Smell gas/electrical spark hazard vs Stairwell intact vs Blocked exits
    - Indoors (Trapped): Can move hands/feet vs Dust/smoke inhalation risk
  - **Point 4 (Action & Evacuation Stage):**
    - High-rise vs Single-story, Aftershock preparedness, Emergency signaling.
  - **Guidance Delivered:**
    - Immediate Action (Drop, Cover, Hold On; Protect head; Utility shutoff; Tapping on pipes).
    - Actions to Avoid (Do NOT run outside during shaking, Do NOT use elevators, Do NOT light matches).
    - Preventive / Recovery Measures.
    - Verified Helplines (112, 1078 NDRF).

### 2. Flood Tree:
- **Point 1 (Current Location/Scenario):** At Home/Building vs On Foot Outdoors vs Inside a Vehicle
  - **Point 2 (Water Behavior / Threat Level):**
    - Home: Water starting to enter ground floor vs Rapidly rising / Flash flood vs Stranded on upper floor/roof
    - Outdoors: Moving current across pathway vs In stagnant water vs Caught near riverbank
    - Vehicle: Approaching flooded road vs Vehicle stalled in rising water vs Vehicle being swept
  - **Point 3 (Hazard Assessment):**
    - Main electrical panel submerged/dry vs Drinking water contamination risk vs Live wires fallen in water
  - **Point 4 (Evacuation & Rescue Readiness):**
    - Evacuation route accessible vs Rooftop signaling needed vs Medical emergency present
  - **Guidance Delivered:**
    - Immediate Action ("Turn Around Don't Drown", Turn off main breaker before water reaches it, Move to highest level).
    - Actions to Avoid (NEVER drive or walk through moving water even 15cm deep, NEVER touch electrical equipment in wet areas).
    - Emergency contacts & official advice.

### 3. Landslide Tree:
- **Point 1 (Phase / Proximity):** Warning signs observed (cracks/rumbling) vs Active slide in progress vs Aftermath/Trapped
  - **Point 2 (Current Position):**
    - Warning: Inside home on steep slope vs Travelling on mountain road
    - Active: In the direct path outdoors vs Inside building collapsing vs In vehicle on hill road
    - Aftermath: Area stabilized vs Secondary slide threat / Blocked valley
  - **Point 3 (Escape Pathway / Feasibility):**
    - Clear uphill/lateral route vs Cut off by mudflow/gully vs Trapped inside vehicle
  - **Point 4 (Immediate Survival Stance):**
    - Uphill lateral sprint vs Curled into tight ball protecting head with helmet/cushion vs Rooftop / Upper floor
  - **Guidance Delivered:**
    - Immediate Action (Run laterally away from the flow line toward high ground, Curl and protect head if escape cut off).
    - Actions to Avoid (NEVER cross an active debris flow, NEVER shelter in low river valleys/culverts).
    - Recovery & reporting to GSI / District Disaster Management Authority (DDMA).

---

## Verified Official Sources (India Focus)
1. **National Disaster Management Authority (NDMA)**: Guidelines on Earthquake, Flood, and Landslide Management (`https://ndma.gov.in`).
2. **National Disaster Response Force (NDRF)**: Emergency Helpline `1078` (`https://www.ndrf.gov.in`).
3. **National Emergency Support System (ERSS)**: Single emergency number `112`.
4. **Geological Survey of India (GSI)**: Landslide Hazard Zonation and Early Warning (`https://www.gsi.gov.in`).
5. **Central Water Commission (CWC)**: Flood Forecasting and Inundation Monitoring (`https://cwc.gov.in`).
6. **India Meteorological Department (IMD)**: Severe Weather & Heavy Rain Warnings (`https://mausam.imd.gov.in`).
