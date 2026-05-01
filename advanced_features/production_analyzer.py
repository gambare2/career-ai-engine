def analyze_production_readiness(repo_analysis, ast_analysis):
    score = 50
    issues = []
    
    if repo_analysis.get("has_services"): score += 20
    if not ast_analysis.get("complexity_problems"): score += 20
    
    if score < 70:
        issues.append("Lacks automated testing and CI/CD maturity")
    if not repo_analysis.get("has_api"):
        issues.append("Missing clear API boundary")
        
    return {
        "production_readiness_score": min(100, score),
        "issues": issues,
        "message": "This project is technically strong but lacks testing and CI/CD maturity" if score < 70 else "Project is production-ready."
    }
