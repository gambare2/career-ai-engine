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
    interested_field: str = None


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
# Resume Upload (PDF)
# -------------------------------------------------
from fastapi import UploadFile, File, Form
import pdfplumber
import docx
from io import BytesIO
from heuristics.reviewer import review_resume, recommend_career_path
from heuristics.parser import parse_resume_text

@app.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    interested_field: str = Form(None)
):
    try:
        # Read the file
        content = await file.read()
        text = ""
        if file.filename.lower().endswith(".pdf"):
            with pdfplumber.open(BytesIO(content)) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
        elif file.filename.lower().endswith(".docx"):
            doc = docx.Document(BytesIO(content))
            for para in doc.paragraphs:
                text += para.text + "\n"
        else:
            # Fallback or plain text
            text = content.decode("utf-8", errors="ignore")
            
        # Analyze using heuristics
        review_result = review_resume(text)
        
        # Add career recommendation if interested_field is provided
        recommendation = None
        if interested_field:
            recommendation = recommend_career_path(
                skills=review_result.get("extracted_skills", []), 
                interested_field=interested_field
            )
            
        # Parse text into structured builder data
        parsed_data = parse_resume_text(text)
            
        return {
            "status": "success",
            "filename": file.filename,
            "review": review_result,
            "recommendation": recommendation,
            "parsed_data": parsed_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process resume PDF: {str(e)}"
        )


# -------------------------------------------------
# MAIN Endpoint: GitHub + Resume → CareerAI Output
# -------------------------------------------------
@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    try:
        repo_url = request.repo_url
        resume_skills = request.resume_skills or []
        interested_field = request.interested_field

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
                resume_skill_list=resume_skills,
                interested_field=interested_field
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
