"""
Scoring Module
Implements hybrid matching: keyword-based + semantic similarity.
Generates scores, rankings, explanations, and selection status for each candidate.

Score Weights:
  - Skills Match:        50%
  - Experience Relevance: 30%
  - Projects Relevance:   20%

Selection Threshold: candidates scoring >= 60 are marked "Selected".
"""

import math
from typing import Dict, List
from backend.preprocessor import preprocess_document, extract_skills
from backend.embeddings import compute_similarity


# ── Score weights ─────────────────────────────────────────────────────────────
WEIGHT_SKILLS = 0.50
WEIGHT_EXPERIENCE = 0.30
WEIGHT_PROJECTS = 0.20

# ── Selection threshold (0–100) ──────────────────────────────────────────────
SELECTION_THRESHOLD = 60


def compute_skills_score(jd_skills: List[str], resume_skills: List[str]) -> Dict:
    """
    Compute keyword-based skills match score.
    Returns score (0-1), matched skills, and missing skills.
    """
    if not jd_skills:
        return {"score": 0.0, "matched": [], "missing": []}

    jd_set = set(jd_skills)
    resume_set = set(resume_skills)

    matched = sorted(jd_set & resume_set)
    missing = sorted(jd_set - resume_set)

    score = len(matched) / len(jd_set) if jd_set else 0.0

    return {
        "score": score,
        "matched": matched,
        "missing": missing,
    }


def compute_experience_score(jd_text: str, resume_experience: str) -> float:
    """Compute semantic similarity between JD and resume experience section."""
    if not resume_experience.strip():
        return 0.0
    return compute_similarity(jd_text, resume_experience)


def compute_projects_score(jd_text: str, resume_projects: str) -> float:
    """Compute semantic similarity between JD and resume projects section."""
    if not resume_projects.strip():
        return 0.0
    return compute_similarity(jd_text, resume_projects)


def generate_explanation(
    skills_data: Dict,
    experience_score: float,
    projects_score: float,
    final_score: float,
) -> str:
    """
    Generate a human-readable explanation for the candidate's score.
    """
    parts = []

    # Skills commentary
    matched = skills_data["matched"]
    missing = skills_data["missing"]

    if matched:
        if len(matched) <= 5:
            parts.append(f"Strong match in {', '.join(matched)}")
        else:
            top_skills = matched[:5]
            parts.append(f"Strong match in {', '.join(top_skills)} and {len(matched) - 5} more skills")

    if missing:
        if len(missing) <= 3:
            parts.append(f"lacks {', '.join(missing)}")
        else:
            top_missing = missing[:3]
            parts.append(f"lacks {', '.join(top_missing)} and {len(missing) - 3} more")

    # Experience commentary
    if experience_score >= 0.7:
        parts.append("highly relevant work experience")
    elif experience_score >= 0.4:
        parts.append("moderately relevant experience")
    elif experience_score > 0:
        parts.append("limited relevant experience")

    # Projects commentary
    if projects_score >= 0.7:
        parts.append("strong project alignment")
    elif projects_score >= 0.4:
        parts.append("some relevant projects")

    # Overall assessment
    if final_score >= 80:
        assessment = "Excellent candidate."
    elif final_score >= 60:
        assessment = "Good potential fit."
    elif final_score >= 40:
        assessment = "Partial match — may need additional evaluation."
    else:
        assessment = "Weak match for this role."

    explanation = ". ".join(parts) + ". " + assessment if parts else assessment
    # Capitalize first letter
    explanation = explanation[0].upper() + explanation[1:]

    return explanation


def score_single_candidate(
    jd_processed: Dict,
    resume_processed: Dict,
    candidate_name: str,
) -> Dict:
    """
    Score a single candidate against the job description.
    Returns a dict with name, score, component scores, matched/missing skills,
    certificates, status, and explanation.
    """
    # 1. Skills match (keyword-based)
    skills_data = compute_skills_score(
        jd_processed["skills"],
        resume_processed["skills"],
    )

    # 2. Experience relevance (semantic)
    experience_score = compute_experience_score(
        jd_processed["full_text"],
        resume_processed["experience_section"],
    )

    # 3. Projects relevance (semantic)
    projects_score = compute_projects_score(
        jd_processed["full_text"],
        resume_processed["projects_section"],
    )

    # 4. Weighted final score (0-100)
    raw_score = (
        skills_data["score"] * WEIGHT_SKILLS
        + experience_score * WEIGHT_EXPERIENCE
        + projects_score * WEIGHT_PROJECTS
    )
    final_score = round(raw_score * 100, 1)
    final_score = min(100, max(0, final_score))

    # 5. Generate explanation
    explanation = generate_explanation(
        skills_data, experience_score, projects_score, final_score
    )

    # 6. Certificates from preprocessor
    certs = resume_processed.get("certificates", {"count": 0, "items": []})

    # 7. Selection status
    status = "Selected" if final_score >= SELECTION_THRESHOLD else "Rejected"

    return {
        "name": candidate_name,
        "score": final_score,
        "rank": 0,  # Will be set during ranking
        "reason": explanation,
        "matched_skills": skills_data["matched"],
        "missing_skills": skills_data["missing"],
        "certificates": certs["count"],
        "certificate_details": certs["items"],
        "status": status,
        "component_scores": {
            "skills": round(skills_data["score"] * 100, 1),
            "experience": round(experience_score * 100, 1),
            "projects": round(projects_score * 100, 1),
        },
    }


def rank_candidates(candidates: List[Dict]) -> List[Dict]:
    """
    Sort candidates by score (descending) and assign ranks.
    Handles ties by giving the same rank.
    """
    # Sort by score descending
    sorted_candidates = sorted(candidates, key=lambda c: c["score"], reverse=True)

    # Assign ranks (handle ties)
    current_rank = 1
    for i, candidate in enumerate(sorted_candidates):
        if i > 0 and candidate["score"] < sorted_candidates[i - 1]["score"]:
            current_rank = i + 1
        candidate["rank"] = current_rank

    return sorted_candidates


def analyze_candidates(jd_text: str, resumes: List[Dict]) -> Dict:
    """
    Main analysis function.
    Takes raw JD text and a list of resume dicts [{"name": ..., "text": ...}].
    Returns a dict with summary stats and ranked candidate results.
    """
    # Preprocess JD
    jd_processed = preprocess_document(jd_text)

    # Score each candidate
    results = []
    for resume in resumes:
        resume_processed = preprocess_document(resume["text"])
        result = score_single_candidate(
            jd_processed,
            resume_processed,
            resume["name"],
        )
        results.append(result)

    # Rank candidates
    ranked = rank_candidates(results)

    # Compute summary statistics
    scores = [c["score"] for c in ranked]
    total_candidates = len(ranked)
    selected_count = sum(1 for c in ranked if c["status"] == "Selected")
    avg_score = round(sum(scores) / total_candidates, 1) if total_candidates else 0
    top_score = max(scores) if scores else 0

    return {
        "total_candidates": total_candidates,
        "selected": selected_count,
        "average_score": avg_score,
        "top_score": top_score,
        "candidates": ranked,
    }
