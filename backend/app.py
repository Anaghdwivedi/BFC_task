"""Flask web server entry point."""

import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
from backend.chat_logic import make_session, handle_message

# ── App and in-memory session store ───────────────────────────────────────
app = Flask(__name__)
SESSIONS = {}


# ── CORS — applied to every response ──────────────────────────────────────
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


# ── OPTIONS preflight for /chat ────────────────────────────────────────────
@app.route("/chat", methods=["OPTIONS"])
def chat_options():
    return jsonify({}), 200


# ── Health check ───────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "ok", "message": "Financial Chatbot API is running."})


# ── Serve frontend UI ──────────────────────────────────────────────────────
@app.route("/ui")
def serve_ui():
    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
    frontend_dir = os.path.abspath(frontend_dir)
    return send_from_directory(frontend_dir, "index.html")


# ── Main chat route ────────────────────────────────────────────────────────
@app.route("/chat", methods=["POST"])
def chat():
    # Step 1 — Parse request body
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    # Step 2 — Validate message
    message = data.get("message", "")
    if not isinstance(message, str) or not message.strip():
        return jsonify({"error": "Field 'message' must be a non-empty string."}), 400

    # Step 3 — Validate session_id
    session_id = data.get("session_id", "")
    if not isinstance(session_id, str) or not session_id.strip():
        return jsonify({"error": "Field 'session_id' must be a non-empty string."}), 400
    session_id = session_id.strip()

    # Step 4 — Look up or create session
    if session_id not in SESSIONS:
        SESSIONS[session_id] = make_session()
    session = SESSIONS[session_id]

    # Step 5 — Process message
    reply = handle_message(message, session)

    # Step 6 — Return reply
    return jsonify({"reply": reply})


# ── Entry point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
