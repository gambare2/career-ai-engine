import random

def generate_roadmap(predicted_role, developer_level, skill_gaps):
    """
    Creates a phase-wise, role-based roadmap.
    Skips basics if developer_level is Intermediate/Senior.
    """
    roadmap = {
        "phase_1": [],
        "phase_2": [],
        "phase_3": []
    }
    
    # Simple rule-based core skills based on role (for phase 1 if beginner, or phase 2 if more advanced)
    core_improvements = []
    if "Frontend" in predicted_role:
        core_improvements = ["Advanced React Patterns", "State Management (Redux/Zustand)", "Performance Optimization"]
    elif "Backend" in predicted_role:
        core_improvements = ["Advanced Node.js/Python", "API Security", "Database Query Optimization"]
    elif "ML" in predicted_role:
        core_improvements = ["Model Deployment", "Advanced Pandas/NumPy", "Data Pipelines"]
    elif "Data" in predicted_role:
        core_improvements = ["Data Warehousing", "Advanced SQL", "ETL Optimization"]
    else:
        core_improvements = ["Advanced Language Features", "API Security", "Clean Code"]
        
    # Apportion based on level
    if developer_level == "Beginner":
        roadmap["phase_1"] = skill_gaps[:2] if skill_gaps else ["Language Basics", "Version Control"]
        roadmap["phase_2"] = core_improvements[:2]
        roadmap["phase_3"] = ["System Design", "Cloud Basics"]
    elif developer_level == "Junior":
        roadmap["phase_1"] = core_improvements[:2]
        roadmap["phase_2"] = skill_gaps if skill_gaps else ["Docker", "CI/CD"]
        roadmap["phase_3"] = ["System Design Basics", "Microservices"]
    else: # Intermediate / Senior -> Skip basics
        roadmap["phase_1"] = ["Architecture Scaling", "System Design"]
        roadmap["phase_2"] = skill_gaps if skill_gaps else ["Kubernetes", "Advanced Cloud Architecture"]
        roadmap["phase_3"] = ["Engineering Leadership", "High Availability Systems"]
        
    return roadmap


def generate_resources(skill_gaps):
    """
    Returns specific resource types for each skill gap.
    """
    resources = {}
    
    resource_templates = [
        ["videos", "notes", "projects"],
        ["docs", "practice", "github repos"],
        ["video tutorials", "official docs", "interactive labs"],
        ["cheat sheets", "articles", "real-world practice"]
    ]
    
    for skill in skill_gaps:
        # Pick a random template based on hash of skill to keep it deterministic per skill
        idx = hash(skill) % len(resource_templates)
        resources[skill] = resource_templates[idx]
        
    return resources


def generate_mentor_message(current_skills, skill_gaps):
    """
    Generates an AI mentor string.
    """
    known = current_skills[:2] if current_skills else ["the basics"]
    known_str = " + ".join(known)
    
    if skill_gaps:
        gaps_str = " + ".join(skill_gaps[:2])
        return f"You know {known_str} \u2192 Next focus on {gaps_str}"
    else:
        return f"You have a very strong grasp of {known_str}. Next, focus on architectural patterns and system design."


def generate_mock_progress():
    """
    Mock progress tracker output since we don't have historical DB in the intelligence layer.
    Can be used by the frontend to initialize progress state.
    """
    return {
        "weekly": "0%",
        "completed_topics": 0,
        "score_improvement": "+0",
        "roadmap_completion": "0%"
    }

def get_github_issues(ast_analysis):
    """
    Extract high-level github issues from the AST analysis.
    """
    issues = []
    
    # Complexity
    if ast_analysis.get("complexity_problems"):
        issues.append("High cyclomatic complexity in some functions")
    
    # Large functions
    if ast_analysis.get("large_functions"):
        issues.append("Oversized functions detected")
        
    # Dead code
    dead_code = ast_analysis.get("dead_code", {})
    if dead_code.get("unused_imports") or dead_code.get("unused_functions"):
        issues.append("Dead code (unused imports/functions) present")
        
    # Bad architecture
    if ast_analysis.get("bad_architecture"):
        issues.append(ast_analysis.get("bad_architecture")[0])
        
    # Default fallback if perfect code
    if not issues:
        issues.append("No critical issues. Consider adding more test coverage.")
        
    return issues
