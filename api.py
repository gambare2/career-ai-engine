from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from inference.predictor import UnifiedPredictor
from github.repo_analyzer import analyze_repo
from github.repo_loader import clone_repo

import tempfile
import os
import subprocess


# -------------------------------------------------
# App
# -------------------------------------------------
app = FastAPI(
    title="CareerAI Engine",
    description="AI engine that evaluates GitHub projects + predicts job readiness + skill gaps",
    version="2.0.0"
)

# Load Predictor Once
predictor = UnifiedPredictor()


# -------------------------------------------------
# Request Schema
# -------------------------------------------------
class AnalyzeRequest(BaseModel):
    repo_url: str
    resume_skills: list[str] = []


# -------------------------------------------------
# Health Check
# -------------------------------------------------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "engine": "CareerAI Engine"
    }


# -------------------------------------------------
# MAIN Endpoint: GitHub + Resume → CareerAI Output
# -------------------------------------------------
@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    try:
        repo_url = request.repo_url
        resume_skills = request.resume_skills or []

        if not repo_url:
            raise HTTPException(status_code=400, detail="repo_url required")

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = os.path.join(tmpdir, "repo")

            # 1) Clone repo
            clone_repo(repo_url, repo_path)

            # 2) Analyze repo using AI logic
            repo_analysis = analyze_repo(repo_path)

            # 3) Predict (EvalAI + SmartHire AI merged)
            result = predictor.predict(
                repo_analysis=repo_analysis,
                resume_skill_list=resume_skills
            )

        return result

    except subprocess.CalledProcessError:
        raise HTTPException(
            status_code=400,
            detail="Failed to clone repository. Repo may be invalid or private."
        )

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"CareerAI analysis failed: {str(e)}"
        )


# -------------------------------------------------
# Optional: Keep this endpoint for debugging only
# -------------------------------------------------
@app.post("/extract/features")
def extract_features(payload: dict):
    repo_url = payload.get("repo_url")

    if not repo_url:
        raise HTTPException(status_code=400, detail="repo_url required")

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = os.path.join(tmpdir, "repo")

        clone_repo(repo_url, repo_path)
        repo_analysis = analyze_repo(repo_path)

    return {
        "repo_analysis": repo_analysis
    }
