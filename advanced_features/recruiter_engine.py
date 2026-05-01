def generate_recruiter_report(developer_score, score_breakdown, developer_level):
    return {
        "hireability_score": developer_score,
        "engineering_maturity": "High" if developer_score > 80 else "Medium",
        "team_fit_prediction": "Strong collaborative potential based on clean code practices" if score_breakdown['code_quality'] > 80 else "Requires mentorship",
        "ownership_score": 85,
        "communication_quality_estimation": "Clear architecture suggests good technical communication" if score_breakdown['architecture'] > 75 else "Architecture documentation needed"
    }
