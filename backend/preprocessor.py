"""
Text Preprocessing Module
Cleans text and extracts structured sections (skills, experience, projects, certificates)
from resumes and job descriptions.
"""

import re
from typing import Dict, List


# ── Common tech skills dictionary for keyword extraction ──────────────────────
TECH_SKILLS = {
    # Programming languages
    "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "go",
    "rust", "swift", "kotlin", "php", "scala", "r", "matlab", "perl",
    "html", "css", "sql", "nosql", "bash", "shell", "powershell",
    # Frontend frameworks
    "react", "reactjs", "react.js", "angular", "angularjs", "vue", "vuejs",
    "vue.js", "svelte", "next.js", "nextjs", "nuxt", "gatsby",
    # Backend frameworks
    "node.js", "nodejs", "express", "expressjs", "django", "flask", "fastapi",
    "spring", "spring boot", "springboot", "rails", "laravel", "asp.net",
    # Databases
    "mysql", "postgresql", "postgres", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "sqlite", "oracle", "firebase", "supabase",
    # Cloud & DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s",
    "terraform", "ansible", "jenkins", "ci/cd", "github actions", "gitlab ci",
    "heroku", "vercel", "netlify",
    # Data & ML
    "machine learning", "deep learning", "nlp", "natural language processing",
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
    "data science", "data analysis", "data engineering", "computer vision",
    "llm", "large language models", "generative ai", "transformers",
    # Tools & Others
    "git", "github", "gitlab", "jira", "confluence", "figma", "sketch",
    "rest", "restful", "graphql", "grpc", "microservices", "api",
    "agile", "scrum", "kanban", "tdd", "unit testing", "integration testing",
    "linux", "unix", "windows server",
}

# ── Certificate-related keywords ─────────────────────────────────────────────
CERTIFICATE_KEYWORDS = [
    r"\bcertified\b",
    r"\bcertificate\b",
    r"\bcertification\b",
    r"\bcertifications\b",
    r"\bcredential\b",
    r"\baccredited\b",
    r"\bdiploma\b",
    r"\blicense[d]?\b",
    r"\baws\s+certified\b",
    r"\bgoogle\s+certified\b",
    r"\bmicrosoft\s+certified\b",
    r"\bcisco\s+certified\b",
    r"\bpmp\b",
    r"\bscrum\s+master\b",
    r"\bcsm\b",
    r"\bcka\b",
    r"\bckad\b",
    r"\bcompTIA\b",
    r"\bceh\b",
    r"\bcissp\b",
    r"\bitil\b",
]


def clean_text(text: str) -> str:
    """Clean and normalize raw text."""
    # Normalize unicode characters
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2013", "-").replace("\u2014", "-")

    # Remove excessive whitespace while preserving newlines
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def extract_skills(text: str) -> List[str]:
    """
    Extract technical skills from text by matching against a known skills dictionary.
    Returns a list of matched skills (lowercased).
    """
    text_lower = text.lower()
    found_skills = []

    for skill in TECH_SKILLS:
        # Use word boundary matching to avoid partial matches
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found_skills.append(skill)

    return sorted(set(found_skills))


def extract_certificates(text: str) -> Dict:
    """
    Extract certificate-related information from text.
    Returns a dict with count and list of certificate mentions found.
    """
    text_lower = text.lower()
    found_certs = []

    # Extract lines containing certificate keywords
    lines = text.split("\n")
    for line in lines:
        line_lower = line.strip().lower()
        for pattern in CERTIFICATE_KEYWORDS:
            if re.search(pattern, line_lower):
                # Clean up the line and add it
                clean_line = line.strip()
                if clean_line and clean_line not in found_certs and len(clean_line) > 3:
                    found_certs.append(clean_line)
                break  # Avoid duplicating the same line

    # Deduplicate and count unique certificate mentions
    unique_certs = list(dict.fromkeys(found_certs))  # preserve order, remove dupes

    return {
        "count": len(unique_certs),
        "items": unique_certs,
    }


def extract_section(text: str, section_keywords: List[str]) -> str:
    """
    Extract a section from a resume based on common section header keywords.
    Looks for the section header and captures text until the next section header.
    """
    text_lines = text.split("\n")
    section_text = []
    capturing = False

    # Common section headers to detect section boundaries
    all_headers = [
        "education", "experience", "work experience", "professional experience",
        "employment", "projects", "personal projects", "academic projects",
        "skills", "technical skills", "core skills", "certifications",
        "achievements", "awards", "publications", "languages", "interests",
        "hobbies", "references", "summary", "objective", "profile",
        "contact", "about", "qualifications", "certificates",
    ]

    for line in text_lines:
        line_stripped = line.strip().lower()
        # Remove common formatting characters
        line_clean = re.sub(r"[:\-_=|#*]+", "", line_stripped).strip()

        # Check if this line is a section header
        is_header = any(
            line_clean == header or line_clean.startswith(header)
            for header in all_headers
        )

        if is_header:
            # Check if it's one of our target sections
            is_target = any(
                keyword in line_clean
                for keyword in section_keywords
            )
            if is_target:
                capturing = True
                continue
            elif capturing:
                # We've hit a different section header — stop capturing
                break

        if capturing:
            section_text.append(line)

    return "\n".join(section_text).strip()


def extract_experience_section(text: str) -> str:
    """Extract the experience/work history section from a resume."""
    keywords = ["experience", "work experience", "professional experience", "employment"]
    section = extract_section(text, keywords)
    return section if section else text  # Fallback to full text


def extract_projects_section(text: str) -> str:
    """Extract the projects section from a resume."""
    keywords = ["projects", "personal projects", "academic projects", "key projects"]
    section = extract_section(text, keywords)
    return section if section else ""


def preprocess_document(text: str) -> Dict:
    """
    Full preprocessing pipeline for a document.
    Returns a dictionary with cleaned text and extracted components.
    """
    cleaned = clean_text(text)
    return {
        "full_text": cleaned,
        "skills": extract_skills(cleaned),
        "experience_section": extract_experience_section(cleaned),
        "projects_section": extract_projects_section(cleaned),
        "certificates": extract_certificates(cleaned),
    }
