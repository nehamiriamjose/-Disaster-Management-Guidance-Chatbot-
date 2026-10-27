"""
DisasterShield — Flask Web Application Backend
===============================================
Serves the responsive dashboard, REST API for rule-based chatbot decision
tree execution, dynamic flowchart data, official references, and transcripts.
100% deterministic, offline-capable disaster management guidance.
"""

import os
from flask import Flask, render_template, request, jsonify
from chatbot_engine import DisasterRuleEngine, RuleEngineError

app = Flask(__name__)

# Deterministic Rule-Based Emergency Decision-Tree Engine
engine = DisasterRuleEngine()


# ==============================================================================
# HOMEPAGE & HEALTH
# ==============================================================================
@app.route("/")
def index():
    """Render the main DisasterShield dashboard."""
    disasters = engine.get_available_disasters()
    return render_template("index.html", disasters=disasters)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "app": "DisasterShield — Disaster Management Guidance Chatbot",
        "version": "1.0.0 (Deterministic Rule-Based Emergency Guidance Engine)"
    })


# ==============================================================================
# RULE-BASED EMERGENCY GUIDANCE ENDPOINTS
# ==============================================================================
@app.route("/api/disasters", methods=["GET"])
def get_disasters():
    """Return available disaster categories."""
    return jsonify({
        "status": "success",
        "data": engine.get_available_disasters()
    })


@app.route("/api/chat/start", methods=["POST"])
def start_chat():
    """Initialize a rule-based guidance chatbot session for a selected disaster."""
    payload = request.get_json(silent=True) or {}
    disaster_id = payload.get("disaster_id")

    if not disaster_id:
        return jsonify({
            "status": "error",
            "message": "Missing required field 'disaster_id'."
        }), 400

    try:
        session = engine.start_session(disaster_id)
        return jsonify({
            "status": "success",
            "session": session
        })
    except RuleEngineError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 404


@app.route("/api/chat/step", methods=["POST"])
def next_step():
    """Navigate to the next node in the rule-based decision tree."""
    payload = request.get_json(silent=True) or {}
    disaster_id = payload.get("disaster_id")
    current_node_id = payload.get("current_node_id")
    option_id = payload.get("option_id")
    history = payload.get("history", [])

    if not all([disaster_id, current_node_id, option_id]):
        return jsonify({
            "status": "error",
            "message": "Fields 'disaster_id', 'current_node_id', and 'option_id' are all required."
        }), 400

    try:
        result = engine.process_step(
            disaster_id=disaster_id,
            current_node_id=current_node_id,
            option_id=option_id,
            existing_history=history
        )
        return jsonify({
            "status": "success",
            "step_result": result
        })
    except RuleEngineError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


@app.route("/api/chat/transcript", methods=["POST"])
def format_transcript():
    """Generate a clean text transcript of the current session."""
    payload = request.get_json(silent=True) or {}
    history = payload.get("history", [])
    disaster_name = payload.get("disaster_name", "")

    transcript_text = engine.generate_transcript_text(history, disaster_name)
    return jsonify({
        "status": "success",
        "transcript": transcript_text
    })


@app.route("/api/checklist", methods=["GET"])
def get_checklist():
    """Return the 72-hour Disaster Go-Bag preparedness checklist."""
    return jsonify({
        "status": "success",
        "data": engine.checklist
    })


@app.route("/api/sources", methods=["GET"])
def get_sources():
    """Return verified official references and emergency hotline directories."""
    return jsonify({
        "status": "success",
        "data": engine.sources
    })


@app.route("/api/flowchart/<disaster_id>", methods=["GET"])
def get_flowchart(disaster_id: str):
    """Return decision tree flowchart representation in Graph and Mermaid syntax."""
    try:
        graph = engine.get_flowchart_graph(disaster_id)
        mermaid = engine.get_flowchart_mermaid(disaster_id)
        return jsonify({
            "status": "success",
            "graph": graph,
            "mermaid": mermaid
        })
    except RuleEngineError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[*] Starting DisasterShield web server on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
