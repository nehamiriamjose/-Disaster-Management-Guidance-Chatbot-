"""
DisasterShield — Flask Web Application Backend
===============================================
Serves the responsive dashboard, REST API for rule-based chatbot decision
tree execution, dynamic flowchart data, official references, and transcripts.
Integrates the Advanced RAG Pipeline for official document Q&A and document management.
"""

import os
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

from chatbot_engine import DisasterRuleEngine, RuleEngineError
from rag.pipeline import DisasterRAGPipeline
from rag.document_loader import DocumentProcessingError, ScannedPDFError
from rag.config import RAGConfig

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = RAGConfig.MAX_UPLOAD_BYTES

# Mode A: Deterministic Rule-Based Emergency Decision-Tree Engine
engine = DisasterRuleEngine()

# Mode B: Advanced Retrieval-Augmented Generation (RAG) Pipeline
rag_pipeline = DisasterRAGPipeline()

# Ensure default official knowledge base is indexed if vector index is empty
if rag_pipeline.vector_store.get_chunk_count() == 0:
    try:
        rag_pipeline.rebuild_index()
    except Exception as e:
        print(f"[Warning] Automatic initial index build: {e}")


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
        "version": "2.0.0 (Hybrid Rule-Based + RAG)",
        "rag_documents_indexed": rag_pipeline.vector_store.get_document_count(),
        "rag_chunks_indexed": rag_pipeline.vector_store.get_chunk_count()
    })


# ==============================================================================
# MODE A: RULE-BASED EMERGENCY GUIDANCE ENDPOINTS
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


# ==============================================================================
# MODE B: ADVANCED RAG (DISASTER KNOWLEDGE ASSISTANT) ENDPOINTS
# ==============================================================================
@app.route("/api/rag/ask", methods=["POST"])
def rag_ask():
    """
    Query the official knowledge base using hybrid retrieval and grounded generation.
    Expected JSON:
    {
        "query": "What precautions should families take for an earthquake?",
        "category_filter": "earthquake" (optional: "earthquake", "flood", "landslide", or null)
    }
    """
    payload = request.get_json(silent=True) or {}
    query = payload.get("query", "").strip()
    category_filter = payload.get("category_filter")

    if not query:
        return jsonify({
            "status": "error",
            "message": "Query string cannot be empty."
        }), 400

    try:
        result = rag_pipeline.ask(query=query, category_filter=category_filter)
        response_dict = {
            "status": "success",
            "data": result
        }
        # Expose top-level fields for convenience
        response_dict.update(result)
        return jsonify(response_dict)
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Knowledge Assistant retrieval error: {str(e)}"
        }), 500


@app.route("/api/rag/documents", methods=["GET"])
def rag_list_documents():
    """List all currently indexed official disaster management PDF documents."""
    docs = rag_pipeline.list_documents()
    total_chunks = rag_pipeline.vector_store.get_chunk_count()
    return jsonify({
        "status": "success",
        "data": {
            "total_documents": len(docs),
            "total_chunks": total_chunks,
            "documents": docs
        },
        "documents": docs,
        "total_documents": len(docs),
        "total_chunks": total_chunks
    })


@app.route("/api/rag/upload", methods=["POST"])
def rag_upload_document():
    """
    Upload and index a new official disaster management PDF document.
    Expects multipart/form-data with file and optional metadata fields:
    title, organization, disaster_category, source_url.
    """
    if "file" not in request.files:
        return jsonify({
            "status": "error",
            "message": "No file uploaded. Please attach a PDF document."
        }), 400

    file = request.files["file"]
    if not file or file.filename.strip() == "":
        return jsonify({
            "status": "error",
            "message": "Uploaded filename is empty."
        }), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({
            "status": "error",
            "message": "Only official PDF documents are accepted."
        }), 400

    # Save to temporary file first
    temp_dir = RAGConfig.DATA_DIR / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_filename = secure_filename(file.filename) or "upload.pdf"
    temp_path = temp_dir / temp_filename

    try:
        file.save(str(temp_path))

        # Collect optional metadata from form
        metadata = {
            "title": request.form.get("title", "").strip() or None,
            "organization": request.form.get("organization", "").strip() or None,
            "disaster_category": request.form.get("disaster_category", "").strip() or None,
            "source_url": request.form.get("source_url", "").strip() or None
        }

        # Process and index
        ingest_res = rag_pipeline.ingest_pdf(temp_path, metadata)

        return jsonify({
            "status": "success",
            "message": f"Successfully parsed and indexed '{ingest_res['title']}' into FAISS vector database.",
            "data": ingest_res,
            "document": ingest_res
        }), 201

    except ScannedPDFError as spe:
        return jsonify({
            "status": "error",
            "error_type": "scanned_pdf",
            "message": str(spe)
        }), 422
    except DocumentProcessingError as dpe:
        return jsonify({
            "status": "error",
            "error_type": "processing_error",
            "message": str(dpe)
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Unexpected server error during document processing: {str(e)}"
        }), 500
    finally:
        # Clean up temporary upload
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass


@app.route("/api/rag/documents/<doc_id>", methods=["DELETE"])
def rag_delete_document(doc_id: str):
    """Remove a document and its chunks from the FAISS vector database."""
    success = rag_pipeline.delete_document(doc_id)
    if success:
        return jsonify({
            "status": "success",
            "message": f"Document '{doc_id}' successfully removed from knowledge base."
        })
    return jsonify({
        "status": "error",
        "message": f"Document '{doc_id}' not found in catalog."
    }), 404


@app.route("/api/rag/rebuild", methods=["POST"])
def rag_rebuild_index():
    """Rebuild the FAISS index and vector representations for all stored documents."""
    try:
        res = rag_pipeline.rebuild_index()
        return jsonify({
            "status": "success",
            "message": "FAISS vector index successfully rebuilt.",
            "data": res,
            "indexed_chunks": res.get("total_chunks", 0)
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to rebuild index: {str(e)}"
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[*] Starting DisasterShield web server on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
