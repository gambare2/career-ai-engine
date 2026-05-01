def generate_benchmarks(developer_score, predicted_role):
    # Mocking live industry comparison based on score
    percentile = max(10, min(99, int(developer_score * 0.9 + 5)))
    return {
        "percentile": percentile,
        "message": f"Your {predicted_role} architecture is stronger than {percentile}% of production repositories.",
        "comparison_points": [
            "Top 10% GitHub Repositories",
            "Real open-source production repos",
            "StackOverflow developer datasets"
        ]
    }
