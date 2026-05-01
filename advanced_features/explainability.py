def generate_explanations(score_breakdown):
    explanations = {}
    
    if score_breakdown["architecture"] < 75:
        explanations["architecture"] = "Architecture Score ↓ because: No service layer, weak modularity."
    else:
        explanations["architecture"] = "Architecture Score ↑ because: Clear separation of concerns."
        
    if score_breakdown["code_quality"] < 75:
        explanations["code_quality"] = "Code Quality ↓ because: Oversized functions and dead code."
    else:
        explanations["code_quality"] = "Code Quality ↑ because: Clean, modular functions."
        
    return explanations
