"""
Profile Schema
--------------
This schema represents the final unified user profile after combining:

- GitHub extracted skills (EvalAI + code intelligence)
- Resume extracted skills (SmartHire resume module)

It also stores job prediction results and roadmap recommendations.
"""

from typing import TypedDict, List, Dict, Optional
from features.skill_schema import Skill


class JobMatchResult(TypedDict, total=False):
    target_role: str                         # e.g. "Backend Developer"
    job_readiness: float                     # 0–100
    job_level: str                           # Beginner/Junior/Mid/Senior

    matched_skills: List[str]
    missing_skills: List[str]

    recommended_next: List[str]              # roadmap items
    explanation: str                         # human readable explanation


class RepoAnalysisSummary(TypedDict, total=False):
    repo_name: str
    repo_url: str

    # From repo_analyzer
    languages: Dict[str, float]              # {"Python": 60.0, "JS": 40.0}
    frameworks: List[str]                    # ["FastAPI", "React"]

    file_count: int
    folder_count: int
    max_depth: int
    ui_score: float
    complexity_score: float

    # From ML predictor
    quality_score: float
    role: str
    risk: str
    confidence: float


class UnifiedUserProfile(TypedDict, total=False):
    # -------------------------
    # User identity (optional)
    # -------------------------
    user_id: str
    github_username: str
    email: Optional[str]

    # -------------------------
    # Skill Sources
    # -------------------------
    github_skills: List[Skill]
    resume_skills: List[Skill]

    # Final merged skills (deduplicated)
    merged_skills: List[Skill]

    # -------------------------
    # Repo evaluation summary
    # -------------------------
    repos_analyzed: List[RepoAnalysisSummary]
    overall_github_strength: float           # 0–100

    # -------------------------
    # Job recommendation output
    # -------------------------
    job_matches: List[JobMatchResult]

    # -------------------------
    # System metadata
    # -------------------------
    created_at: str
    updated_at: str
