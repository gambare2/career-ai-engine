def generate_roadmap(missing_skills: list):
    roadmap = []

    for skill in missing_skills:
        roadmap.append(f"Learn {skill}")

    return roadmap[:10]
