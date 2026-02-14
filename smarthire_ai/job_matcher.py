JOB_ROLE_SKILLS = {
    "Frontend Developer": ["JavaScript", "TypeScript", "React", "Next.js"],
    "Backend Developer": ["Python", "Node.js", "Express", "Django", "FastAPI"],
    "Full Stack Developer": ["React", "Node.js", "MongoDB", "SQL"],
    "ML Engineer": ["Python", "NumPy", "Pandas", "scikit-learn"],
}


def recommend_roles(merged_skills: list):
    skill_names = {s["name"] for s in merged_skills}

    matches = []

    for role, required in JOB_ROLE_SKILLS.items():
        matched = [x for x in required if x in skill_names]
        score = (len(matched) / len(required)) * 100

        matches.append({
            "role": role,
            "match_score": round(score, 2),
            "matched_skills": matched,
            "missing_skills": [x for x in required if x not in skill_names]
        })

    matches.sort(key=lambda x: x["match_score"], reverse=True)
    return matches
