import re

# Simple knowledge base for fields
FIELD_SKILLS_KB = {
    "frontend": ["javascript", "typescript", "react", "next.js", "vue", "angular", "html", "css", "tailwind", "redux"],
    "backend": ["python", "nodejs", "express", "django", "fastapi", "java", "spring", "go", "sql", "postgresql", "mongodb", "docker", "aws"],
    "fullstack": ["javascript", "typescript", "react", "nodejs", "express", "postgresql", "mongodb", "docker", "aws", "html", "css"],
    "data science": ["python", "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "sql", "matplotlib", "seaborn"],
    "devops": ["docker", "kubernetes", "aws", "gcp", "azure", "linux", "bash", "jenkins", "github actions", "terraform"],
    "mobile": ["react native", "flutter", "swift", "kotlin", "java", "objective-c", "android", "ios"]
}

SKILL_KEYWORDS = [
    "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust", "php", "ruby",
    "react", "angular", "vue", "next.js", "svelte", "html", "css", "tailwind", "bootstrap",
    "nodejs", "express", "django", "flask", "fastapi", "spring", "laravel", "ruby on rails",
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra",
    "docker", "kubernetes", "aws", "gcp", "azure", "jenkins", "github actions", "terraform",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
    "git", "linux", "bash"
]

def review_resume(text: str) -> dict:
    text_lower = text.lower()
    
    found_skills = set()
    for skill in SKILL_KEYWORDS:
        # Basic word boundary search
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.add(skill)
            
    # Simple score based on number of skills
    score = min(len(found_skills) * 5, 100)
    
    feedback = "Good start on the resume. "
    if len(found_skills) < 3:
        feedback += "However, it lacks clear technical skills. Make sure to explicitly list the programming languages, frameworks, and tools you know."
    elif len(found_skills) > 15:
        feedback += "You have a very broad range of skills listed. Consider tailoring them to the specific job you are applying for."
    else:
        feedback += "You have a solid set of skills listed."
        
    return {
        "extracted_skills": list(found_skills),
        "score": score,
        "feedback": feedback
    }

def recommend_career_path(skills: list, interested_field: str) -> dict:
    if not interested_field:
        return {
            "skills_to_learn": [],
            "resume_upgrades": ["Please specify an interested field to get tailored recommendations."]
        }
        
    target_field = interested_field.lower()
    best_match_field = None
    
    # Try to find the closest field in our KB
    for field in FIELD_SKILLS_KB.keys():
        if field in target_field or target_field in field:
            best_match_field = field
            break
            
    if not best_match_field:
        # Fallback if unknown field
        return {
            "skills_to_learn": ["Industry standard tools for " + interested_field],
            "resume_upgrades": [f"Highlight any experience related to {interested_field}"]
        }
        
    required_skills = set(FIELD_SKILLS_KB[best_match_field])
    user_skills_lower = set([s.lower() for s in skills])
    
    missing_skills = list(required_skills - user_skills_lower)
    matching_skills = list(required_skills.intersection(user_skills_lower))
    
    upgrades = []
    if not matching_skills:
        upgrades.append(f"Your resume does not currently highlight any core skills for {best_match_field}. Start by learning and adding the basics.")
    else:
        upgrades.append(f"Great job highlighting {', '.join(matching_skills[:3])}. Make sure to detail projects using these skills.")
        
    if missing_skills:
        upgrades.append(f"Consider learning and adding: {', '.join(missing_skills[:3])} to be more competitive.")
        
    return {
        "field": best_match_field,
        "skills_to_learn": missing_skills[:5],  # Top 5 to learn
        "resume_upgrades": upgrades
    }

def analyze_code_snippets(files_list: list, repo_path: str) -> dict:
    """
    Takes a list of relative file paths in the repo to provide project upgrades and identify unnecessary code.
    """
    upgrades = []
    unnecessary_code = []
    
    has_env_example = any('.env.example' in f for f in files_list)
    has_docker = any('Dockerfile' in f or 'docker-compose' in f for f in files_list)
    has_readme = any('README.md' in f or 'readme.md' in f.lower() for f in files_list)
    has_tests = any('test' in f.lower() or 'spec' in f.lower() for f in files_list)
    
    if not has_readme:
        upgrades.append("Missing README.md: Add a comprehensive README with setup instructions and project overview.")
    if not has_env_example and any('.env' in f for f in files_list):
         upgrades.append("Missing .env.example: Found an .env file. You should provide an .env.example to show what environment variables are needed.")
    if not has_docker:
        upgrades.append("Missing Containerization: Consider adding a Dockerfile to make your project easy to deploy and run across environments.")
    if not has_tests:
        upgrades.append("Missing Tests: No obvious test files found. Adding unit tests (e.g., using Jest or PyTest) will significantly improve code quality.")
        
    # Check for things that shouldn't be committed
    for f in files_list:
        if 'node_modules' in f:
            unnecessary_code.append(f"Remove {f} from version control. Add 'node_modules/' to .gitignore.")
        elif '__pycache__' in f or f.endswith('.pyc'):
            unnecessary_code.append(f"Remove {f} from version control. Add '__pycache__/' and '*.pyc' to .gitignore.")
        elif '.env' in f and '.env.example' not in f:
             unnecessary_code.append(f"SECURITY RISK: {f} is committed. Never commit actual .env files containing secrets.")
        elif 'venv' in f or 'env/' in f:
             unnecessary_code.append(f"Remove virtual environment folder ({f}) from version control. Add it to .gitignore.")
             
    if not upgrades:
        upgrades.append("Project structure looks good based on standard heuristics.")
        
    if not unnecessary_code:
        unnecessary_code.append("No common unnecessary files found committed. Good job keeping the repo clean.")
        
    return {
        "upgrades": upgrades,
        "unnecessary_code": unnecessary_code
    }
