"""
AI Resume Screening — Flask Backend
Provides REST API endpoints for uploading job descriptions,
uploading resumes, and analyzing candidates.
"""

import os
import sys
import csv
import io
import re
import uuid
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS

# Add project root to path so we can import backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.text_extractor import extract_text
from backend.scorer import analyze_candidates

# ── App Configuration ─────────────────────────────────────────────────────────
app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "static"),
    template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "templates"),
)
CORS(app)

# Upload directory
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Allowed file extensions
ALLOWED_RESUME_EXT = {".pdf", ".docx", ".txt"}
ALLOWED_JD_EXT = {".pdf", ".txt"}

# In-memory session store (simple approach for local use)
session_store = {
    "jd_text": None,
    "resumes": [],  # List of {"name": str, "text": str}
    "results": None,  # Latest analysis results (full dict with summary + candidates)
}


def _allowed_file(filename: str, allowed: set) -> bool:
    """Check if a file has an allowed extension."""
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed


def _extract_candidate_name(filename: str) -> str:
    """
    Extract a human-readable candidate name from the filename.
    E.g., 'John_Doe_Resume.pdf' → 'John Doe'
    """
    # Remove extension
    name = os.path.splitext(filename)[0]
    # Remove common suffixes
    for suffix in ["_resume", "_Resume", "_cv", "_CV", "-resume", "-Resume", "-cv", "-CV",
                   " resume", " Resume", " cv", " CV"]:
        name = name.replace(suffix, "")
    # Replace underscores and hyphens with spaces
    name = name.replace("_", " ").replace("-", " ")
    # Clean up extra spaces
    name = re.sub(r"\s+", " ", name).strip()
    # Title case
    name = name.title()
    return name if name else "Unknown Candidate"


# ── Serve Frontend ────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the main HTML page."""
    return send_from_directory(app.template_folder, "index.html")


# ── API Endpoints ─────────────────────────────────────────────────────────────

@app.route("/upload-jd", methods=["POST"])
def upload_jd():
    """
    Upload a Job Description.
    Accepts either:
      - A text field 'jd_text' with the JD content
      - A file upload 'jd_file' (PDF or TXT)
    """
    jd_text = None

    # Check for text input first
    if "jd_text" in request.form and request.form["jd_text"].strip():
        jd_text = request.form["jd_text"].strip()

    # Check for file upload
    elif "jd_file" in request.files:
        file = request.files["jd_file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        if not _allowed_file(file.filename, ALLOWED_JD_EXT):
            return jsonify({"error": f"Invalid file type. Allowed: {', '.join(ALLOWED_JD_EXT)}"}), 400

        # Save and extract text
        filepath = os.path.join(UPLOAD_DIR, f"jd_{uuid.uuid4().hex[:8]}_{file.filename}")
        file.save(filepath)
        try:
            jd_text = extract_text(filepath)
        except Exception as e:
            return jsonify({"error": str(e)}), 400
        finally:
            # Clean up uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)
    else:
        return jsonify({"error": "No job description provided. Send 'jd_text' or 'jd_file'."}), 400

    if not jd_text:
        return jsonify({"error": "Could not extract text from the job description."}), 400

    # Store in session
    session_store["jd_text"] = jd_text
    session_store["results"] = None  # Clear previous results

    return jsonify({
        "message": "Job description uploaded successfully.",
        "preview": jd_text[:300] + ("..." if len(jd_text) > 300 else ""),
        "length": len(jd_text),
    })


@app.route("/upload-resumes", methods=["POST"])
def upload_resumes():
    """
    Upload multiple resumes.
    Accepts file uploads via 'resume_files' (multiple files).
    """
    if "resume_files" not in request.files:
        return jsonify({"error": "No resume files provided."}), 400

    files = request.files.getlist("resume_files")
    if not files or all(f.filename == "" for f in files):
        return jsonify({"error": "No files selected."}), 400

    resumes = []
    errors = []

    for file in files:
        if file.filename == "":
            continue

        if not _allowed_file(file.filename, ALLOWED_RESUME_EXT):
            errors.append(f"{file.filename}: Invalid file type")
            continue

        # Save and extract text
        filepath = os.path.join(UPLOAD_DIR, f"resume_{uuid.uuid4().hex[:8]}_{file.filename}")
        file.save(filepath)
        try:
            text = extract_text(filepath)
            candidate_name = _extract_candidate_name(file.filename)
            resumes.append({
                "name": candidate_name,
                "text": text,
                "filename": file.filename,
            })
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    if not resumes:
        return jsonify({"error": "No valid resumes could be processed.", "details": errors}), 400

    # Store in session
    session_store["resumes"] = resumes
    session_store["results"] = None  # Clear previous results

    response = {
        "message": f"{len(resumes)} resume(s) uploaded successfully.",
        "candidates": [{"name": r["name"], "filename": r["filename"]} for r in resumes],
    }
    if errors:
        response["warnings"] = errors

    return jsonify(response)


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Analyze all uploaded resumes against the job description.
    Returns summary stats + scored, ranked candidates with explanations.
    """
    # Validate we have both JD and resumes
    if not session_store["jd_text"]:
        return jsonify({"error": "No job description uploaded. Please upload a JD first."}), 400

    if not session_store["resumes"]:
        return jsonify({"error": "No resumes uploaded. Please upload resumes first."}), 400

    try:
        # Run analysis — now returns full dict with summary + candidates
        results = analyze_candidates(
            session_store["jd_text"],
            session_store["resumes"],
        )

        # Store results for CSV export
        session_store["results"] = results

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


@app.route("/export-csv", methods=["GET"])
def export_csv():
    """Export the latest analysis results as a CSV file."""
    results = session_store.get("results")
    if not results:
        return jsonify({"error": "No analysis results to export. Run analysis first."}), 400

    candidates = results.get("candidates", [])

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Rank", "Name", "Score", "Status", "Certificates",
        "Skills Match", "Experience Score", "Projects Score",
        "Matched Skills", "Missing Skills", "Reason"
    ])

    # Data rows
    for candidate in candidates:
        comp = candidate.get("component_scores", {})
        writer.writerow([
            candidate["rank"],
            candidate["name"],
            candidate["score"],
            candidate.get("status", ""),
            candidate.get("certificates", 0),
            comp.get("skills", ""),
            comp.get("experience", ""),
            comp.get("projects", ""),
            ", ".join(candidate.get("matched_skills", [])),
            ", ".join(candidate.get("missing_skills", [])),
            candidate["reason"],
        ])

    # Send as downloadable CSV
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name="resume_screening_results.csv",
    )


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"})


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    print(f"\n{'='*60}")
    print(f"  AI Resume Screening — Server Starting")
    print(f"  Open http://localhost:{port} in your browser")
    print(f"{'='*60}\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
