"""
Skill Schema
------------
This file defines the standardized structure used across the system
for storing skills extracted from GitHub and Resume.

We keep skill objects consistent so we can:
- merge skills
- calculate confidence
- detect gaps
- generate roadmaps
"""

from typing import TypedDict, Literal, Optional, List


SkillSource = Literal["github", "resume", "both"]
SkillCategory = Literal[
    "language",
    "frontend",
    "backend",
    "database",
    "devops",
    "cloud",
    "ml",
    "tool",
    "other",
]


class Skill(TypedDict, total=False):
    name: str                      # e.g. "Python", "React", "Docker"
    category: SkillCategory        # e.g. "backend"
    source: SkillSource            # "github" | "resume" | "both"

    # Confidence from 0 to 100
    confidence: float              # e.g. 82.5

    # Extra metadata (optional)
    evidence: Optional[List[str]]  # e.g. ["requirements.txt", "import fastapi"]
    frequency: Optional[int]       # e.g. number of files using this skill


# -----------------------------
# Standard containers
# -----------------------------
class SkillSet(TypedDict):
    skills: List[Skill]
