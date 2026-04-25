import pandas as pd
import joblib

from features.features_schema import BASE_FEATURE_COLUMNS
from features.features_extracted import build_feature_payload


ROLE_RISK_COLUMNS = BASE_FEATURE_COLUMNS + ["quality_score"]


# -------------------------------------------------
# Skill Weight Configuration (AI logic)
# -------------------------------------------------
LANGUAGE_WEIGHTS = {
    "Python": 1.0,
    "JavaScript": 0.9,
    "TypeScript": 1.0,
    "Java": 1.0,
    "C++": 1.1,
    "Go": 1.1,
    "Rust": 1.1,
    "PHP": 0.8,
}

FRAMEWORK_WEIGHTS = {
    "React": 0.8,
    "Next.js": 0.9,
    "Express": 0.9,
    "NestJS": 1.0,
    "Django": 1.0,
    "Flask": 0.8,
    "FastAPI": 1.0,
    "Spring": 1.1,
    "Laravel": 0.9,
    "Vue": 0.8,
    "Angular": 0.9,
}


# -------------------------------------------------
# Job Level Calculator
# -------------------------------------------------
def job_level_from_score(readiness: float) -> str:
    if readiness < 40:
        return "Beginner"
    elif readiness < 65:
        return "Junior"
    elif readiness < 80:
        return "Mid-Level"
    return "Senior"


# =================================================
# Unified Predictor (EvalAI + SmartHire AI)
# =================================================
class UnifiedPredictor:
    def __init__(self):
        self.quality_model = joblib.load("models/quality_model.pkl")

        self.role_model = joblib.load("models/role_model.pkl")
        self.role_encoder = joblib.load("models/role_label_encoder.pkl")

        self.risk_model = joblib.load("models/risk_model.pkl")
        self.risk_encoder = joblib.load("models/risk_label_encoder.pkl")

    # -------------------------------
    # Utility
    # -------------------------------
    def _confidence(self, model, df):
        probs = model.predict_proba(df)[0]
        return round(float(max(probs) * 100), 2)

    # -------------------------------
    # Skill Score Engine
    # -------------------------------
    def _skill_score(self, languages: dict, frameworks: list):
        """
        languages example:
        {
          "Python": 65.2,
          "JavaScript": 34.8
        }

        frameworks example:
        ["FastAPI", "React"]
        """

        score = 0.0

        # Language score (max ~40)
        for lang, percent in languages.items():
            weight = LANGUAGE_WEIGHTS.get(lang, 0.7)
            score += (float(percent) / 100.0) * weight * 40

        # Framework score (max ~60)
        for fw in frameworks:
            score += FRAMEWORK_WEIGHTS.get(fw, 0.5) * 10

        return round(min(score, 100), 2)

    # -------------------------------
    # Explanation Engine
    # -------------------------------
    def _explain(self, quality, role, risk, languages, frameworks):
        reasons = {}

        # Risk reason
        if risk == "high":
            reasons["risk_reason"] = (
                "High risk due to weaker modular structure, shallow architecture depth, "
                "and low complexity indicators."
            )
        elif risk == "medium":
            reasons["risk_reason"] = (
                "Moderate risk caused by average architecture depth and acceptable complexity."
            )
        else:
            reasons["risk_reason"] = (
                "Low risk due to good project structure, deeper folder hierarchy, "
                "and strong complexity indicators."
            )

        # Role reason
        if role == "frontend":
            reasons["role_reason"] = (
                "Frontend suitability inferred from UI patterns and frontend framework signals."
            )
        elif role == "backend":
            reasons["role_reason"] = (
                "Backend suitability inferred from deeper architecture and backend framework usage."
            )
        elif role == "mobile":
            reasons["role_reason"] = (
                "Mobile suitability inferred from compact structure and mobile-related code patterns."
            )
        else:
            reasons["role_reason"] = (
                "General software development suitability inferred from balanced repo signals."
            )

        # Tech reason
        if languages:
            top_lang = max(languages, key=languages.get)
            reasons["top_language_reason"] = f"Dominant programming language detected: {top_lang}."

        if frameworks:
            reasons["framework_reason"] = (
                "Frameworks detected from source code imports/configs: "
                + ", ".join(frameworks[:6])
            )

        return reasons

    # -------------------------------
    # MAIN PREDICT
    # -------------------------------
    def predict(self, repo_analysis: dict, resume_skill_list=None, interested_field=None):
        """
        Input:
          repo_analysis -> output of repo_analyzer.analyze_repo()
          resume_skill_list -> optional list of skills extracted from resume
          interested_field -> optional user interested field for recommendation
          
        Output:
          EvalAI ML predictions + SmartHire merged skills + readiness + level + recommendations
        """

        if resume_skill_list is None:
            resume_skill_list = []

        # ------------------------------------------
        # Build payload (EvalAI + SmartHire)
        # ------------------------------------------
        payload = build_feature_payload(
            repo_analysis=repo_analysis,
            resume_skill_list=resume_skill_list
        )

        evalai_features = payload["evalai_features"]
        languages = payload.get("languages", {})
        frameworks = payload.get("frameworks", [])

        # ------------------------------------------
        # Quality Prediction (EvalAI)
        # ------------------------------------------
        quality_df = pd.DataFrame(
            [[evalai_features[c] for c in BASE_FEATURE_COLUMNS]],
            columns=BASE_FEATURE_COLUMNS
        )

        quality_score = float(self.quality_model.predict(quality_df)[0])

        # Add quality_score into features for role/risk models
        enriched = evalai_features.copy()
        enriched["quality_score"] = quality_score

        full_df = pd.DataFrame(
            [[enriched[c] for c in ROLE_RISK_COLUMNS]],
            columns=ROLE_RISK_COLUMNS
        )

        # ------------------------------------------
        # Role Prediction
        # ------------------------------------------
        role_encoded = self.role_model.predict(full_df)[0]
        role = self.role_encoder.inverse_transform([role_encoded])[0]

        # ------------------------------------------
        # Risk Prediction
        # ------------------------------------------
        risk_encoded = self.risk_model.predict(full_df)[0]
        risk = self.risk_encoder.inverse_transform([risk_encoded])[0]

        # ------------------------------------------
        # Model Confidence
        # ------------------------------------------
        role_conf = self._confidence(self.role_model, full_df)
        risk_conf = self._confidence(self.risk_model, full_df)
        model_confidence = round((role_conf + risk_conf) / 2, 2)

        # ------------------------------------------
        # AI Skill Intelligence (SmartHire merged)
        # ------------------------------------------
        skill_score = self._skill_score(languages, frameworks)

        # ------------------------------------------
        # Job Readiness (CareerAI)
        # ------------------------------------------
        # You can tune these weights later
        job_readiness = round(
            (quality_score * 0.45) +
            (skill_score * 0.35) +
            (model_confidence * 0.20),
            2
        )

        job_level = job_level_from_score(job_readiness)

        # ------------------------------------------
        # Feature Importance (Explainable AI)
        # ------------------------------------------
        importances = self.risk_model.feature_importances_
        importance_map = {
            ROLE_RISK_COLUMNS[i]: round(float(importances[i]), 4)
            for i in range(len(importances))
        }

        # ------------------------------------------
        # Explanation
        # ------------------------------------------
        explanation = self._explain(
            quality=quality_score,
            role=role,
            risk=risk,
            languages=languages,
            frameworks=frameworks
        )
        
        # ------------------------------------------
        # Career Recommendation
        # ------------------------------------------
        from heuristics.reviewer import recommend_career_path
        
        merged_skills_list = [s["name"] for s in payload["merged_skills"]]
        recommendations = recommend_career_path(merged_skills_list, interested_field)

        # ------------------------------------------
        # FINAL OUTPUT
        # ------------------------------------------
        return {
            # EvalAI ML results
            "quality_score": round(quality_score, 2),
            "role": role,
            "risk": risk,
            "model_confidence": model_confidence,

            # SmartHire AI merged results
            "skill_score": skill_score,
            "job_readiness": job_readiness,
            "job_level": job_level,

            # Detected stack
            "languages_detected": languages,
            "frameworks_detected": frameworks,

            # Skill objects (schema-based)
            "github_skills": payload["github_skills"],
            "resume_skills": payload["resume_skills"],
            "merged_skills": payload["merged_skills"],

            # Explainability
            "explanation": explanation,
            "feature_importance": importance_map,
            
            # New Advanced Review
            "code_review": repo_analysis.get("code_review", {}),
            "career_recommendation": recommendations
        }
