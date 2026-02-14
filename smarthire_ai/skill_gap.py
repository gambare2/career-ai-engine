def compute_skill_gap(job_match: dict):
    return {
        "missing_skills": job_match.get("missing_skills", []),
        "matched_skills": job_match.get("matched_skills", [])
    }
