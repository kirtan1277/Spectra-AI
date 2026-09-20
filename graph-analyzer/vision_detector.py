"""
vision_detector.py - Graph Photo Recognition Module

This module uses Gemini Multimodal Vision to inspect an uploaded image
of a graph (handwritten, drawn, screenshot, textbook diagram, or Cartesian coordinate plot)
and automatically extract its vertex labels and undirected edges.

Features:
- Automatic vertex inference: does NOT require pre-drawn dots, circles, or labels in the image!
  Infers intercepts, corners, intersections, and endpoints from the lines and geometry.
- Replaces internal commas inside coordinate points with spaces: '(0, 3.5)' -> '(0 3.5)', preventing comma conflicts
- Supports Cartesian coordinate plots, linear equation graphs, and standard network diagrams
- Supports graphs labeled with numbers (0, 1, 2, 3...) or letters (A, B, C...)
- Automatically labels unlabeled graphs (empty circles, dots, stick lines)
- Automatically normalizes transparent PNGs onto clean white background

Author: Graph Analyzer Team
"""

import os
import io
import re
import json
from PIL import Image

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def get_gemini_api_key(passed_key: str = None) -> str:
    """
    Resolves the Gemini API key from the request payload,
    or falls back to environment variables.
    """
    if passed_key and passed_key.strip():
        return passed_key.strip()
    
    env_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if env_key and env_key.strip():
        return env_key.strip()

    return ""


def normalize_point_label(label: str) -> str:
    """
    Normalizes point/coordinate labels by replacing internal commas with spaces.
    e.g. '(0, 3.5)' -> '(0 3.5)'
         '(7, 0)'   -> '(7 0)'
         '(0,9)'    -> '(0 9)'
         '(0, 3.5)-(7, 0)' -> '(0 3.5)-(7 0)'
    """
    def replacer(match):
        inner = match.group(1)
        # Replace commas inside the parenthesis with a single space
        clean_inner = re.sub(r'\s*,\s*', ' ', inner)
        return f"({clean_inner})"

    return re.sub(r'\(([^)]+)\)', replacer, label)


def preprocess_image_bytes(image_bytes: bytes) -> tuple[bytes, str, str]:
    """
    Validates, optimizes, and standardizes image bytes.
    - Resolves transparent PNGs by pasting them onto a white background.
    - Resizes extremely large images down to max 1600px dimension.
    - Saves clean JPEG bytes.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.load()

        if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
            image = image.convert("RGBA")
            bg = Image.new("RGBA", image.size, (255, 255, 255, 255))
            bg.paste(image, (0, 0), image)
            image = bg.convert("RGB")
        else:
            image = image.convert("RGB")

        max_dim = 1600
        if image.width > max_dim or image.height > max_dim:
            image.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        output_io = io.BytesIO()
        image.save(output_io, format="JPEG", quality=92)
        clean_bytes = output_io.getvalue()

        return clean_bytes, "image/jpeg", None

    except Exception as exc:
        return None, None, f"Invalid or corrupted image file: {str(exc)}"


def detect_graph_from_image(image_bytes: bytes, mime_type: str = "image/png", api_key: str = None, model_name: str = "gemini-3.6-flash"):
    """
    Inspects graph image bytes and extracts vertices and edges using Gemini Vision.
    Automatically infers vertices even if no dots, circles, or labels are pre-drawn in the image.

    Parameters:
        image_bytes (bytes): Binary data of the image.
        mime_type (str): Original MIME type of the uploaded image.
        api_key (str): Optional Gemini API key provided by the user.
        model_name (str): Model name (defaults to 'gemini-3.6-flash').

    Returns:
        tuple: (vertices_str, edges_str, error_message)
    """
    # 1. Preprocess image
    clean_bytes, proc_mime, img_err = preprocess_image_bytes(image_bytes)
    if img_err:
        return "", "", img_err

    # 2. Check for API key
    resolved_key = get_gemini_api_key(api_key)
    if not resolved_key:
        return "", "", (
            "Gemini API key is required to analyze graph photos. "
            "Please enter your key in the 'Gemini API Key' field below or set GEMINI_API_KEY in your environment. "
            "You can obtain a free API key at https://aistudio.google.com/."
        )

    # 3. Call Gemini Vision API
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=resolved_key)

        prompt_instructions = (
            "You are an expert graph theorist, mathematician, and computer vision system.\n"
            "Analyze the provided image of a graph (which may be a mathematical coordinate/function plot, linear equation graph, geometric shape, or network diagram).\n\n"
            "CRITICAL REQUIREMENT - AUTOMATIC VERTEX INFERENCE (NO PRE-DRAWN POINTS REQUIRED):\n"
            "The image does NOT need to have pre-drawn dots, circles, or labeled vertex points! You must automatically identify the vertex points from the graph itself:\n\n"
            "1. FOR COORDINATE / FUNCTION / LINEAR EQUATION PLOTS (e.g. lines or curves on an X-Y grid):\n"
            "   - You do NOT need pre-drawn red dots or plotted circles!\n"
            "   - Automatically detect the key points of the line/curve on the grid as the vertices:\n"
            "     * Axis intercepts: find where the line crosses the Y-axis (Y-intercept) and X-axis (X-intercept).\n"
            "       Example: if a line crosses (0, 3.5) on the y-axis and (7, 0) on the x-axis, the vertices are '(0 3.5)' and '(7 0)'.\n"
            "     * If an equation is written in the image (e.g. 'x + 2y = 7' or 'y = 2x + 1'), use the equation and line to determine its intercepts or grid points.\n"
            "     * If multiple lines are present, include their intersection points as vertices.\n"
            "     * Format each coordinate vertex with a space instead of a comma inside the parentheses: e.g. '(0 3.5)', '(7 0)', '(0 9)', '(3 2)'. Do NOT put commas inside the parentheses.\n"
            "   - Define the edges as the line segments connecting these vertices: e.g. '(0 3.5)-(7 0)'.\n\n"
            "2. FOR GEOMETRIC SHAPES & NETWORKS WITHOUT LABELED DOTS (e.g. polygons, trees, stick graphs):\n"
            "   - Every line intersection, corner, bend, or line endpoint constitutes a vertex.\n"
            "   - Automatically assign clean sequential labels to them: 'A', 'B', 'C', 'D'... (or 'V1', 'V2'...). ordered top-to-bottom and left-to-right.\n"
            "   - Connect the vertices with edges according to the drawn lines.\n\n"
            "3. FOR STANDARD GRAPH THEORY DIAGRAMS (with circles or labeled nodes):\n"
            "   - Use the node labels if present (e.g. 'A', 'B', '0', '1').\n"
            "   - If circles are unlabeled or empty, assign labels: 'A', 'B', 'C'...\n\n"
            "OUTPUT FORMAT:\n"
            "Return ONLY a valid JSON object matching this schema:\n"
            "{\n"
            '  "vertices": ["(0 3.5)", "(7 0)"],\n'
            '  "edges": ["(0 3.5)-(7 0)"]\n'
            "}\n"
            "Always return the vertices and edges you can infer from the lines and geometry, even if no dots or points were explicitly drawn."
        )

        preferred_models = []
        if model_name and model_name.strip():
            preferred_models.append(model_name.strip())
        
        for candidate in ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.8-flash", "gemini-2.0-flash", "gemini-1.5-flash"]:
            if candidate not in preferred_models:
                preferred_models.append(candidate)

        last_error = None
        response = None

        for target_model in preferred_models:
            try:
                print(f"[VisionDetector] Attempting vision analysis with model: {target_model}", flush=True)
                response = client.models.generate_content(
                    model=target_model,
                    contents=[
                        types.Part.from_bytes(data=clean_bytes, mime_type=proc_mime),
                        prompt_instructions
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1
                    )
                )
                if response and response.text:
                    print(f"[VisionDetector] Successfully received response from {target_model}", flush=True)
                    break
            except Exception as model_err:
                err_str = str(model_err)
                print(f"[VisionDetector] Error with {target_model}: {err_str}", flush=True)
                last_error = err_str
                if "API_KEY_INVALID" in err_str or ("400" in err_str and "API key" in err_str):
                    return "", "", "The provided Gemini API key is invalid. Please check your key at https://aistudio.google.com/."
                continue

        if not response or not response.text:
            return "", "", f"Vision analysis failed: {last_error or 'No response from model'}"

        raw_text = response.text.strip()
        print(f"[VisionDetector] Raw model response: {raw_text}", flush=True)

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            clean = raw_text.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean)

        raw_vertices = parsed.get("vertices", [])
        raw_edges = parsed.get("edges", [])

        # Normalize vertices: replace commas inside (x, y) with spaces (x y)
        cleaned_vertices = []
        for v in raw_vertices:
            v_norm = normalize_point_label(str(v).strip())
            if v_norm and v_norm not in cleaned_vertices:
                cleaned_vertices.append(v_norm)

        if not cleaned_vertices:
            return "", "", (
                "Could not detect any vertices in the uploaded photo. "
                "Please ensure the image clearly shows the lines, curve, or structure of the graph."
            )

        # Normalize edges: replace commas inside coordinates with spaces
        cleaned_edges = []
        seen_edges = set()
        for e in raw_edges:
            e_str = str(e).strip()
            if not e_str:
                continue

            if isinstance(e, list) and len(e) == 2:
                u = normalize_point_label(str(e[0]).strip())
                v = normalize_point_label(str(e[1]).strip())
            else:
                e_norm = normalize_point_label(e_str)
                parts = []
                cur = []
                depth = 0
                for ch in e_norm:
                    if ch in "([{":
                        depth += 1
                        cur.append(ch)
                    elif ch in ")]}":
                        if depth > 0:
                            depth -= 1
                        cur.append(ch)
                    elif ch == "-" and depth == 0:
                        parts.append("".join(cur).strip())
                        cur = []
                    else:
                        cur.append(ch)
                if cur:
                    parts.append("".join(cur).strip())

                if len(parts) == 2:
                    u, v = parts[0], parts[1]
                else:
                    continue

            if u and v:
                edge_key = tuple(sorted([u, v]))
                if edge_key not in seen_edges:
                    seen_edges.add(edge_key)
                    cleaned_edges.append(f"{u}-{v}")

        vertices_str = ",".join(cleaned_vertices)
        edges_str = "\n".join(cleaned_edges)

        return vertices_str, edges_str, None

    except Exception as exc:
        err_msg = str(exc)
        if "API_KEY_INVALID" in err_msg or "400" in err_msg and "API key" in err_msg:
            return "", "", "The provided Gemini API key is invalid. Please verify your key from https://aistudio.google.com/."
        return "", "", f"Vision analysis failed: {err_msg}"
