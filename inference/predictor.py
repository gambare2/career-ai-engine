import pandas as pd
import joblib

from features.features_schema import BASE_FEATURE_COLUMNS
from features.features_extracted import build_feature_payload
from learning.learning_engine import generate_roadmap, generate_resources, generate_mentor_message, generate_mock_progress, get_github_issues

# New Advanced Features
from advanced_features.benchmarker import generate_benchmarks
from advanced_features.interview_engine import generate_interview_prep
from advanced_features.ats_scorer import generate_ats_score
from advanced_features.behavior_analyzer import analyze_github_behavior
from advanced_features.production_analyzer import analyze_production_readiness
from advanced_features.explainability import generate_explanations
from advanced_features.career_simulator import simulate_career_path
from advanced_features.recruiter_engine import generate_recruiter_report


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
    # Developer Scoring Engine
    # -------------------------------
    def _calculate_developer_score(self, repo_analysis, skill_score, quality_score):
        # CQ: Code Quality (derived from quality_score model prediction or avg_file_lines, etc.)
        cq = min(100, max(0, quality_score)) if quality_score else 70
        
        # AR: Architecture (derived from has_services, has_utils, max_depth, bad_architecture count)
        ar = 50
        if repo_analysis.get("has_services"): ar += 15
        if repo_analysis.get("has_utils"): ar += 10
        ar += min(20, repo_analysis.get("max_depth", 0) * 5)
        # Penalize bad architecture
        ast_analysis = repo_analysis.get("ast_analysis", {})
        bad_arch = len(ast_analysis.get("bad_architecture", []))
        ar -= (bad_arch * 10)
        ar = min(100, max(0, ar))
        
        # SK: Skill Level
        sk = min(100, max(0, skill_score))
        
        # PF: Performance (large functions, complexity)
        pf = 100
        large_fns = len(ast_analysis.get("large_functions", []))
        complexity = len(ast_analysis.get("complexity_problems", []))
        pf -= (large_fns * 5)
        pf -= (complexity * 5)
        pf = min(100, max(0, pf))
        
        # BP: Best Practices (dead code, duplicate logic)
        bp = 100
        dead_imports = len(ast_analysis.get("dead_code", {}).get("unused_imports", []))
        dead_funcs = len(ast_analysis.get("dead_code", {}).get("unused_functions", []))
        duplicates = len(ast_analysis.get("duplicate_logic", []))
        if dead_imports > 0 or dead_funcs > 0: bp -= 10
        if duplicates > 0: bp -= 20
        bp = min(100, max(0, bp))
        
        final_score = (cq * 0.25) + (ar * 0.20) + (sk * 0.25) + (pf * 0.15) + (bp * 0.15)
        
        if final_score >= 90:
            level = "Senior"
        elif final_score >= 75:
            level = "Intermediate"
        elif final_score >= 60:
            level = "Junior"
        else:
            level = "Beginner"
            
        return round(final_score, 2), level, {
            "code_quality": round(cq, 2),
            "architecture": round(ar, 2),
            "skill": round(sk, 2),
            "performance": round(pf, 2),
            "best_practices": round(bp, 2)
        }

    # -------------------------------
    # Career Role Prediction
    # -------------------------------
    def _predict_career_role(self, repo_analysis, resume_skills, frameworks, languages):
        project_type = repo_analysis.get("project_type", "Other")
        fw_lower = [fw.lower() for fw in frameworks]
        lang_lower = [lang.lower() for lang in languages]
        res_skills = [s.lower() for s in resume_skills]
        
        combined_skills = set(fw_lower + lang_lower + res_skills)
        
        ml_keywords = {"tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy"}
        data_keywords = {"spark", "kafka", "hadoop", "airflow", "sql", "postgresql", "aws"}
        
        if len(ml_keywords.intersection(combined_skills)) >= 2:
            return "ML Engineer"
        elif len(data_keywords.intersection(combined_skills)) >= 3:
            return "Data Engineer"
            
        if project_type == "Fullstack":
            return "Full Stack Developer"
        elif project_type == "Frontend":
            return "Frontend Developer"
        elif project_type == "Backend":
            return "Backend Developer"
            
        # Default fallback
        return "Backend Developer"

    # -------------------------------
    # Skill Gap Detection
    # -------------------------------
    def _detect_skill_gaps(self, predicted_role, current_skills):
        industry_expectations = {
            "Frontend Developer": ["React", "TypeScript", "CSS", "HTML", "Redux", "Webpack"],
            "Backend Developer": ["Node.js", "Python", "Docker", "SQL", "Redis", "System Design"],
            "Full Stack Developer": ["React", "Node.js", "Docker", "SQL", "TypeScript", "System Design"],
            "ML Engineer": ["Python", "TensorFlow", "PyTorch", "SQL", "Docker", "Pandas"],
            "Data Engineer": ["Python", "SQL", "Spark", "AWS", "Kafka", "Airflow"]
        }
        
        expected = industry_expectations.get(predicted_role, [])
        current_lower = set([s.lower() for s in current_skills])
        
        gaps = [skill for skill in expected if skill.lower() not in current_lower]
        
        recommendations = []
        if "Docker" in gaps or "Kubernetes" in gaps:
            recommendations.append("Learn containerization (Docker) and orchestration")
        if "System Design" in gaps or "Architecture" in gaps:
            recommendations.append("Practice scalable architecture and system design")
        if "React" in gaps or "Vue" in gaps:
            recommendations.append("Master modern frontend frameworks")
        if "TypeScript" in gaps:
            recommendations.append("Learn TypeScript for type-safe JavaScript development")
        if "SQL" in gaps or "Redis" in gaps:
            recommendations.append("Deepen database knowledge (SQL and caching)")
        if "AWS" in gaps or "GCP" in gaps:
            recommendations.append("Gain hands-on experience with cloud platforms")
            
        if not recommendations:
            recommendations.append("Focus on building complex, end-to-end projects in your domain")
            
        return gaps, recommendations

    # -------------------------------
    # MAIN PREDICT
    # -------------------------------
    def predict(self, repo_analysis: dict, resume_skill_list=None, interested_field=None):
        if resume_skill_list is None:
            resume_skill_list = []

        payload = build_feature_payload(
            repo_analysis=repo_analysis,
            resume_skill_list=resume_skill_list
        )

        evalai_features = payload["evalai_features"]
        languages = list(payload.get("languages", {}).keys())
        frameworks = payload.get("frameworks", [])
        merged_skills_list = [s["name"] for s in payload["merged_skills"]]
        
        # ------------------------------------------
        # 1. Quality Prediction
        # ------------------------------------------
        try:
            quality_df = pd.DataFrame(
                [[evalai_features[c] for c in BASE_FEATURE_COLUMNS]],
                columns=BASE_FEATURE_COLUMNS
            )
            quality_score = float(self.quality_model.predict(quality_df)[0])
        except Exception:
            quality_score = 75.0 # fallback

        # ------------------------------------------
        # 2. Skill Score Calculation
        # ------------------------------------------
        skill_score = self._skill_score(payload.get("languages", {}), frameworks)

        # ------------------------------------------
        # 3. Developer Scoring Engine
        # ------------------------------------------
        final_score, developer_level, score_breakdown = self._calculate_developer_score(
            repo_analysis=repo_analysis,
            skill_score=skill_score,
            quality_score=quality_score
        )

        # ------------------------------------------
        # 4. Career Role Prediction
        # ------------------------------------------
        predicted_role = self._predict_career_role(
            repo_analysis=repo_analysis,
            resume_skills=resume_skill_list,
            frameworks=frameworks,
            languages=languages
        )

        # ------------------------------------------
        # 5. Skill Gap Detection
        # ------------------------------------------
        all_skills = set(resume_skill_list + frameworks + languages + merged_skills_list)
        current_skills_list = list(all_skills)
        skill_gaps, recommendations = self._detect_skill_gaps(
            predicted_role=predicted_role,
            current_skills=current_skills_list
        )
        
        # ------------------------------------------
        # 6. Learning Engine & Roadmap
        # ------------------------------------------
        ast_analysis = repo_analysis.get("ast_analysis", {})
        github_issues = get_github_issues(ast_analysis)
        roadmap = generate_roadmap(predicted_role, developer_level, skill_gaps)
        resources = generate_resources(skill_gaps)
        mentor = generate_mentor_message(current_skills_list, skill_gaps)
        progress = generate_mock_progress()

        # ------------------------------------------
        # 7. Advanced Intelligence Engines
        # ------------------------------------------
        benchmarks = generate_benchmarks(final_score, predicted_role)
        interview_prep = generate_interview_prep(predicted_role, developer_level)
        ats_analysis = generate_ats_score(resume_skill_list)
        github_behavior = analyze_github_behavior(repo_analysis)
        production_readiness = analyze_production_readiness(repo_analysis, ast_analysis)
        explanations = generate_explanations(score_breakdown)
        career_simulation = simulate_career_path(final_score, predicted_role)
        recruiter_report = generate_recruiter_report(final_score, score_breakdown, developer_level)

        # Job readiness mapping requested by user
        readiness_map = {"Beginner": "Low", "Junior": "Low", "Intermediate": "Medium", "Senior": "High"}
        job_readiness_string = readiness_map.get(developer_level, "Medium")

        # ------------------------------------------
        # FINAL CLEAN JSON OUTPUT (MODULAR)
        # ------------------------------------------
        return {
            # Advanced feature outputs
            "benchmarks": benchmarks,
            "interview_prep": interview_prep,
            "ats_analysis": ats_analysis,
            "github_behavior": github_behavior,
            "production_readiness": production_readiness,
            "explanations": explanations,
            "career_simulation": career_simulation,
            "recruiter_report": recruiter_report,
            
            # New specific keys requested by user
            "developer_score": final_score,
            "job_readiness": job_readiness_string,
            "predicted_role": predicted_role,
            "skill_gaps": skill_gaps,
            "github_issues": github_issues,
            "roadmap": roadmap,
            "resources": resources,
            "mentor": mentor,
            "progress": progress,
            
            # Preserved for frontend backwards-compatibility (Report.tsx)
            "final_score": final_score,
            "developer_level": developer_level,
            "score_breakdown": score_breakdown,
            "recommendations": recommendations
        }
