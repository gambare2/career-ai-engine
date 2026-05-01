def generate_interview_prep(predicted_role, developer_level):
    questions = {
        "Backend": ["Explain Redis caching strategy", "Design scalable authentication system", "Explain JWT refresh token flow"],
        "Frontend": ["Explain React Virtual DOM", "How do you optimize Webpack bundle size?", "Design an autocomplete component"],
        "ML": ["Explain backpropagation", "How to handle imbalanced datasets?", "Design a recommendation engine"],
        "Data": ["Explain Hadoop architecture", "Optimize this slow SQL query", "What is data skew?"]
    }
    
    role_key = next((k for k in questions.keys() if k in predicted_role), "Backend")
    
    return {
        "readiness_score": 85 if developer_level in ["Intermediate", "Senior"] else 60,
        "questions": questions.get(role_key, ["Explain SOLID principles", "Design a REST API"]),
        "roadmap": ["Review core concepts", "Practice System Design", "Do Mock Interviews"],
        "hr_prep": ["Tell me about a time you failed", "Why do you want to work here?"]
    }
