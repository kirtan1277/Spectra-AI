"""
app.py - Flask Web Server for Graph Analyzer

This file serves:
1. The frontend web page (GET /).
2. The graph analysis API endpoint (POST /analyze).
3. The photo recognition endpoint (POST /detect-graph).

Author: Graph Analyzer Team
"""

from flask import Flask, render_template, request, jsonify
from analyzer import parse_and_validate_graph, analyze_graph
from vision_detector import detect_graph_from_image
import os

# Initialize Flask application
app = Flask(__name__)

# Max upload size: 10 MB
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.route("/")
def index():
    """
    Renders the main single-page interface for Graph Analyzer.
    """
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    API endpoint that accepts graph vertices and edges via JSON,
    validates the input, computes graph-theory properties, and returns JSON.
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({
                "success": False,
                "error": "Invalid request. Please provide JSON payload with 'vertices' and 'edges'."
            }), 400

        vertices_raw = data.get("vertices", "")
        edges_raw = data.get("edges", "")

        vertices, edges, error = parse_and_validate_graph(vertices_raw, edges_raw)
        if error:
            return jsonify({
                "success": False,
                "error": error
            }), 400

        analysis_results = analyze_graph(vertices, edges)

        return jsonify({
            "success": True,
            "data": analysis_results
        }), 200

    except Exception as exc:
        print(f"[app.py /analyze ERROR] {exc}", flush=True)
        return jsonify({
            "success": False,
            "error": f"An unexpected error occurred during analysis: {str(exc)}"
        }), 500


@app.route("/detect-graph", methods=["POST"])
def detect_graph():
    """
    API endpoint that accepts an uploaded photo of a graph,
    uses Gemini Vision to extract vertex labels and undirected edges,
    and returns them to pre-populate the input fields.
    """
    try:
        if "image" not in request.files:
            return jsonify({
                "success": False,
                "error": "No image file provided in the request."
            }), 400

        file = request.files["image"]
        if not file or file.filename == "":
            return jsonify({
                "success": False,
                "error": "No image file selected."
            }), 400

        user_api_key = request.form.get("apiKey", "").strip()
        model_name = request.form.get("model", "gemini-3.6-flash").strip()

        image_bytes = file.read()
        if not image_bytes:
            return jsonify({
                "success": False,
                "error": "Uploaded image file is empty."
            }), 400

        # Save uploaded file copy for inspection and reference
        save_path = os.path.join(UPLOAD_DIR, "last_uploaded.png")
        try:
            with open(save_path, "wb") as f:
                f.write(image_bytes)
        except Exception as save_err:
            print(f"[app.py] Could not save upload backup: {save_err}", flush=True)

        mime_type = file.mimetype or "image/png"

        print(f"[app.py /detect-graph] File: {file.filename}, Size: {len(image_bytes)} bytes, Model: {model_name}", flush=True)

        vertices_str, edges_str, error = detect_graph_from_image(
            image_bytes=image_bytes,
            mime_type=mime_type,
            api_key=user_api_key,
            model_name=model_name
        )

        if error:
            print(f"[app.py /detect-graph ERROR] {error}", flush=True)
            return jsonify({
                "success": False,
                "error": error
            }), 400

        print(f"[app.py /detect-graph SUCCESS] Vertices: {vertices_str} | Edges: {edges_str.splitlines()}", flush=True)
        return jsonify({
            "success": True,
            "vertices": vertices_str,
            "edges": edges_str
        }), 200

    except Exception as exc:
        print(f"[app.py /detect-graph EXCEPTION] {exc}", flush=True)
        return jsonify({
            "success": False,
            "error": f"Error processing image: {str(exc)}"
        }), 500


if __name__ == "__main__":
    print("==================================================", flush=True)
    print(" Starting Graph Analyzer Server...", flush=True)
    print(" Open your browser and visit: http://127.0.0.1:5000", flush=True)
    print("==================================================", flush=True)
    app.run(debug=True, host="127.0.0.1", port=5000)
