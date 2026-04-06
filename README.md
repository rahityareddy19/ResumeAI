# ResumeAI — AI Resume Screening Application

An AI-powered resume screening web application that automatically evaluates, scores, ranks, and explains candidate suitability against a job description.

## ✨ Features

- **Upload Job Description** — Paste text or upload a PDF/TXT file
- **Upload Multiple Resumes** — Supports PDF, DOCX, and TXT formats
- **AI-Powered Analysis** — Hybrid keyword + semantic matching
- **Detailed Scoring** — Skills (50%), Experience (30%), Projects (20%)
- **Candidate Ranking** — Automatic ranking with per-candidate explanations
- **Missing Skills Detection** — Highlights gaps for each candidate
- **CSV Export** — Download results as a CSV file
- **Beautiful Dark UI** — Modern glassmorphism design with animations

## 🏗️ Architecture

```
/anti-gravity
├── backend/
│   ├── app.py              # Flask application & REST API
│   ├── text_extractor.py   # PDF/DOCX/TXT text extraction
│   ├── preprocessor.py     # Text cleaning & section extraction
│   ├── embeddings.py       # Sentence-transformers for semantic similarity
│   └── scorer.py           # Hybrid scoring & ranking engine
├── frontend/
│   ├── templates/
│   │   └── index.html      # Main UI page
│   └── static/
│       ├── style.css       # Dark theme styles
│       └── app.js          # Frontend logic
├── samples/                # Sample test data
├── uploads/                # Temporary file uploads (auto-created)
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.9+** installed
- **pip** package manager

### 1. Install Dependencies

```bash
cd anti-gravity
pip install -r requirements.txt
```

> **Note:** The first install will download the `all-MiniLM-L6-v2` sentence-transformers model (~80MB). This is a one-time download.

### 2. Start the Server

```bash
python backend/app.py
```

The server will start at `http://localhost:5000`.

### 3. Open in Browser

Navigate to **http://localhost:5000** in your web browser.

### 4. Test the System

1. **Step 1 — Job Description:** Paste the contents of `samples/sample_jd.txt` or upload it
2. **Step 2 — Resumes:** Upload the sample resumes from the `samples/` folder
3. **Step 3 — Analyze:** Click "Run AI Analysis" and view the results

## 📡 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Serve the frontend UI |
| `/upload-jd` | POST | Upload job description (text or file) |
| `/upload-resumes` | POST | Upload multiple resume files |
| `/analyze` | POST | Run AI analysis on uploaded data |
| `/export-csv` | GET | Download results as CSV |
| `/health` | GET | Health check |

### Example API Response (`/analyze`)

```json
{
  "candidates": [
    {
      "name": "Alice Johnson",
      "score": 85.2,
      "rank": 1,
      "reason": "Strong match in react, node.js, typescript, aws, docker and 8 more skills. Highly relevant work experience. Strong project alignment. Excellent candidate.",
      "matched_skills": ["react", "node.js", "typescript", ...],
      "missing_skills": ["terraform"],
      "component_scores": {
        "skills": 92.3,
        "experience": 78.5,
        "projects": 71.2
      }
    }
  ]
}
```

## 🧠 Scoring Algorithm

| Component | Weight | Method |
|---|---|---|
| **Skills Match** | 50% | Keyword overlap between JD and resume skills |
| **Experience Relevance** | 30% | Semantic similarity (embeddings) of experience sections |
| **Projects Relevance** | 20% | Semantic similarity (embeddings) of projects sections |

**AI Model:** `all-MiniLM-L6-v2` from sentence-transformers — runs **100% locally**, no API key needed.

## 🔧 Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `PORT` | `5000` | Server port |
| `FLASK_DEBUG` | `true` | Enable Flask debug mode |

## 📝 License

MIT License — free for personal and commercial use.
