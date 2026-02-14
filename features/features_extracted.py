from typing import Dict, List, Any
from datetime import datetime

from features.features_schema import BASE_FEATURE_COLUMNS
from features.skill_schema import Skill


# ---------------------------------------------------------
# Helper: normalize skill names (very important)
# ---------------------------------------------------------
def normalize_skill_name(name: str) -> str:
    if not name:
        return name

    name = name.strip()

    # Basic normalization
    mapping = {
        "node": "Node.js",
        "nodejs": "Node.js",
        "reactjs": "React",
        "nextjs": "Next.js",
        "expressjs": "Express",
        "mongo": "MongoDB",
        "mongodb": "MongoDB",
        "postgres": "PostgreSQL",
        "postgresql": "PostgreSQL",
        "js": "JavaScript",
        "ts": "TypeScript",
    }

    key = name.lower().replace(" ", "").replace("-", "")
    return mapping.get(key, name)


# ---------------------------------------------------------
# Helper: categorize skills (basic version)
# ---------------------------------------------------------
def categorize_skill(skill_name: str) -> str:
    s = skill_name.lower()

    if s in ["python", "javascript", "typescript", "java", "c++", "go", "php", "rust"]:
        return "language"

    if s in ["react", "next.js", "vue", "angular"]:
        return "frontend"

    if s in ["node.js", "express", "nestjs", "django", "flask", "fastapi", "spring", "laravel"]:
        return "backend"

    if s in ["mongodb", "postgresql", "mysql", "sqlite", "redis"]:
        return "database"

    if s in ["docker", "kubernetes", "nginx", "github actions", "ci/cd"]:
        return "devops"

    if s in ["aws", "azure", "gcp", "firebase"]:
        return "cloud"

    if s in ["numpy", "pandas", "scikit-learn", "tensorflow", "pytorch"]:
        return "ml"

    return "other"


# ---------------------------------------------------------
# 1) Extract ML-ready features for EvalAI models
# ---------------------------------------------------------
def extract_evalai_features(repo_analysis: Dict[str, Any]) -> Dict[str, float]:
    """
    Takes output of repo_analyzer.analyze_repo()
    and returns only the ML columns needed by your models.
    """

    # Ensure all base columns exist
    features = {}

    for col in BASE_FEATURE_COLUMNS:
        if col not in repo_analysis:
            # Safe fallback
            features[col] = 0
        else:
            features[col] = repo_analysis[col]

    return features


# ---------------------------------------------------------
# 2) Extract Skill Objects (GitHub side)
# ---------------------------------------------------------
def extract_github_skills(repo_analysis: Dict[str, Any]) -> List[Skill]:
    """
    Builds skill objects from:
    - languages dict (confidence %)
    - frameworks list
    """

    skills: List[Skill] = []

    # Languages
    languages = repo_analysis.get("languages", {})
    for lang, conf in languages.items():
        lang = normalize_skill_name(lang)

        skills.append({
            "name": lang,
            "category": categorize_skill(lang),
            "source": "github",
            "confidence": float(conf),
            "evidence": ["file_extensions_distribution"]
        })

    # Frameworks
    frameworks = repo_analysis.get("frameworks", [])
    for fw in frameworks:
        fw = normalize_skill_name(fw)

        skills.append({
            "name": fw,
            "category": categorize_skill(fw),
            "source": "github",
            "confidence": 70.0,  # default confidence (can be improved later)
            "evidence": ["import_pattern_detection"]
        })

    return skills


# ---------------------------------------------------------
# 3) Extract Skill Objects (Resume side)
# ---------------------------------------------------------
def extract_resume_skills(resume_skill_list: List[str]) -> List[Skill]:
    """
    Takes resume extracted skills as list of strings.
    Example:
      ["Python", "FastAPI", "MongoDB"]
    """

    skills: List[Skill] = []

    for s in resume_skill_list:
        s = normalize_skill_name(s)

        skills.append({
            "name": s,
            "category": categorize_skill(s),
            "source": "resume",
            "confidence": 60.0,  # default resume confidence
            "evidence": ["resume_text_extraction"]
        })

    return skills


# ---------------------------------------------------------
# 4) Merge Skills (GitHub + Resume)
# ---------------------------------------------------------
def merge_skills(github_skills: List[Skill], resume_skills: List[Skill]) -> List[Skill]:
    """
    Deduplicate skills and merge confidence.
    Priority:
      - If both sources have same skill -> source becomes "both"
      - Confidence becomes max(confidence)
    """

    merged: Dict[str, Skill] = {}

    def add_skill(skill: Skill):
        name = normalize_skill_name(skill["name"])

        if name not in merged:
            merged[name] = skill.copy()
            merged[name]["name"] = name
            return

        existing = merged[name]

        # Update confidence (take max)
        existing["confidence"] = max(float(existing.get("confidence", 0)), float(skill.get("confidence", 0)))

        # Update source
        if existing.get("source") != skill.get("source"):
            existing["source"] = "both"

        # Merge evidence
        ev1 = existing.get("evidence", []) or []
        ev2 = skill.get("evidence", []) or []
        existing["evidence"] = list(set(ev1 + ev2))

        merged[name] = existing

    for s in github_skills:
        add_skill(s)

    for s in resume_skills:
        add_skill(s)

    return list(merged.values())


# ---------------------------------------------------------
# 5) Build Unified Feature Output
# ---------------------------------------------------------
def build_feature_payload(
    repo_analysis: Dict[str, Any],
    resume_skill_list: List[str] = None
) -> Dict[str, Any]:
    """
    This is the MAIN function you will call from:
    - predictor.py
    - api.py

    It returns a combined payload:
    - EvalAI ML features
    - GitHub skills
    - Resume skills
    - Merged skills
    """

    if resume_skill_list is None:
        resume_skill_list = []

    # ML Features
    evalai_features = extract_evalai_features(repo_analysis)

    # Skills
    github_skills = extract_github_skills(repo_analysis)
    resume_skills = extract_resume_skills(resume_skill_list)

    merged = merge_skills(github_skills, resume_skills)

    # Add metadata
    payload = {
        "timestamp": datetime.utcnow().isoformat(),

        # ML features (for quality/role/risk models)
        "evalai_features": evalai_features,

        # skill intelligence
        "github_skills": github_skills,
        "resume_skills": resume_skills,
        "merged_skills": merged,

        # raw detection (useful for UI)
        "languages": repo_analysis.get("languages", {}),
        "frameworks": repo_analysis.get("frameworks", []),
    }

    return payload
