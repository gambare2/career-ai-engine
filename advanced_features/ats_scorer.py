def generate_ats_score(resume_skills):
    # Mocking ATS score based on skills list length
    score = min(95, 40 + len(resume_skills) * 5)
    return {
        "ats_score": score,
        "readability_score": score - 5,
        "weaknesses": [
            "Missing quantified achievements and impact metrics",
            "Weak project impact statements"
        ],
        "suggestions": ["Add metrics (e.g. 'Improved speed by 40%')", "Include missing standard skills"]
    }
