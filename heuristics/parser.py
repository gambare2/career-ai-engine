import re
import json

try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except ImportError:
    nlp = None
except OSError:
    # Model not found, could download here but usually done via CLI
    nlp = None

def extract_entities(text):
    if not nlp:
        return []
    doc = nlp(text)
    return [(ent.text, ent.label_) for ent in doc.ents]

def parse_resume_text(text: str) -> dict:
    """
    Advanced heuristics parser to extract structured data from raw resume text
    using regex and spaCy.
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if not lines:
        return {}

    parsed_data = {
        "name": "",
        "email": "",
        "phone": "",
        "linkedin": "",
        "portfolio": "",
        "summary": "",
        "experience": [],
        "education": [],
        "projects": [],
        "skills": "",
        "certifications": [],
        "internships": [],
        "technologies_used": []
    }

    # Extract basic info
    parsed_data["name"] = lines[0] if lines else ""

    email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
    if email_match:
        parsed_data["email"] = email_match.group(0)

    phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    if phone_match:
        parsed_data["phone"] = phone_match.group(0)

    linkedin_match = re.search(r'(linkedin\.com/in/[a-zA-Z0-9-]+)', text, re.IGNORECASE)
    if linkedin_match:
        parsed_data["linkedin"] = linkedin_match.group(0)

    github_match = re.search(r'(github\.com/[a-zA-Z0-9-]+)', text, re.IGNORECASE)
    if github_match:
        parsed_data["portfolio"] = github_match.group(0)

    # NLP based extraction (Names, Orgs)
    entities = extract_entities(text[:1000]) # Scan first 1000 chars
    for ent_text, label in entities:
        if label == "PERSON" and not parsed_data["name"]:
            parsed_data["name"] = ent_text

    # Section Splitting
    sections = {
        "summary": [],
        "experience": [],
        "education": [],
        "projects": [],
        "skills": [],
        "certifications": [],
        "internships": []
    }
    
    current_section = None

    for line in lines[1:]:
        line_upper = line.upper()
        # Detect section headers
        if any(keyword in line_upper for keyword in ["SUMMARY", "PROFILE", "ABOUT ME"]):
            current_section = "summary"
            continue
        elif any(keyword in line_upper for keyword in ["INTERNSHIP", "INTERNSHIPS"]):
            current_section = "internships"
            continue
        elif any(keyword in line_upper for keyword in ["EXPERIENCE", "WORK HISTORY", "EMPLOYMENT"]):
            current_section = "experience"
            continue
        elif any(keyword in line_upper for keyword in ["EDUCATION", "ACADEMIC", "UNIVERSITY"]):
            current_section = "education"
            continue
        elif any(keyword in line_upper for keyword in ["PROJECT", "PROJECTS", "PORTFOLIO"]):
            current_section = "projects"
            continue
        elif any(keyword in line_upper for keyword in ["SKILL", "TECHNOLOGIES"]):
            current_section = "skills"
            continue
        elif any(keyword in line_upper for keyword in ["CERTIFICATE", "CERTIFICATIONS", "LICENSES"]):
            current_section = "certifications"
            continue

        if current_section:
            sections[current_section].append(line)

    # Process Sections
    parsed_data["summary"] = " ".join(sections["summary"])
    parsed_data["skills"] = " ".join(sections["skills"])
    parsed_data["certifications"] = sections["certifications"]

    # Technologies used (extract from skills and projects)
    tech_keywords = ["python", "java", "javascript", "react", "node", "sql", "aws", "docker", "kubernetes", "c++", "c#", "html", "css", "typescript", "git"]
    tech_found = set()
    for word in text.lower().replace(",", " ").split():
        if word in tech_keywords:
            tech_found.add(word)
    parsed_data["technologies_used"] = list(tech_found)

    # Basic heuristic to chunk experience
    if sections["experience"]:
        exp_block = {"id": 1, "company": "", "role": "", "duration": "", "description": ""}
        counter = 1
        desc_lines = []
        for line in sections["experience"]:
            date_match = re.search(r'(19|20)\d{2}.*(19|20)\d{2}|(19|20)\d{2}.*Present', line, re.IGNORECASE)
            if date_match and len(line) < 50:
                if exp_block["company"]:
                    exp_block["description"] = "\n".join(desc_lines)
                    parsed_data["experience"].append(exp_block)
                    counter += 1
                    exp_block = {"id": counter, "company": "", "role": "", "duration": "", "description": ""}
                    desc_lines = []
                exp_block["duration"] = line
            elif len(line) < 50 and not exp_block["company"]:
                exp_block["company"] = line
            elif len(line) < 50 and not exp_block["role"]:
                exp_block["role"] = line
            else:
                desc_lines.append(line)
        
        if exp_block["company"] or desc_lines:
            exp_block["description"] = "\n".join(desc_lines)
            parsed_data["experience"].append(exp_block)

    # Internships
    if sections["internships"]:
        intern_block = {"id": 1, "company": "", "role": "", "duration": "", "description": ""}
        counter = 1
        desc_lines = []
        for line in sections["internships"]:
            date_match = re.search(r'(19|20)\d{2}.*(19|20)\d{2}|(19|20)\d{2}.*Present', line, re.IGNORECASE)
            if date_match and len(line) < 50:
                if intern_block["company"]:
                    intern_block["description"] = "\n".join(desc_lines)
                    parsed_data["internships"].append(intern_block)
                    counter += 1
                    intern_block = {"id": counter, "company": "", "role": "", "duration": "", "description": ""}
                    desc_lines = []
                intern_block["duration"] = line
            elif len(line) < 50 and not intern_block["company"]:
                intern_block["company"] = line
            elif len(line) < 50 and not intern_block["role"]:
                intern_block["role"] = line
            else:
                desc_lines.append(line)
        
        if intern_block["company"] or desc_lines:
            intern_block["description"] = "\n".join(desc_lines)
            parsed_data["internships"].append(intern_block)

    # Basic heuristic for education
    if sections["education"]:
        edu_block = {"id": 1, "school": "", "degree": "", "duration": "", "gpa": ""}
        counter = 1
        for line in sections["education"]:
            date_match = re.search(r'(19|20)\d{2}.*(19|20)\d{2}', line)
            gpa_match = re.search(r'(GPA|gpa)[\s:]*([0-4]\.\d{1,2})', line)
            
            if date_match and len(line) < 50:
                edu_block["duration"] = line
            elif gpa_match:
                edu_block["gpa"] = gpa_match.group(2)
            elif len(line) < 60 and not edu_block["school"]:
                edu_block["school"] = line
            elif len(line) < 80 and not edu_block["degree"]:
                edu_block["degree"] = line
            else:
                if "university" in line.lower() or "college" in line.lower() or "institute" in line.lower():
                    parsed_data["education"].append(edu_block)
                    counter += 1
                    edu_block = {"id": counter, "school": line, "degree": "", "duration": "", "gpa": ""}
        
        if edu_block["school"] or edu_block["degree"]:
            parsed_data["education"].append(edu_block)

    # Basic heuristic for projects
    if sections["projects"]:
        proj_block = {"id": 1, "name": "", "tech": "", "description": ""}
        counter = 1
        desc_lines = []
        for line in sections["projects"]:
            if len(line) < 40 and not proj_block["name"]:
                proj_block["name"] = line
            elif ("react" in line.lower() or "python" in line.lower() or "node" in line.lower() or "stack" in line.lower()) and len(line) < 60 and not proj_block["tech"]:
                proj_block["tech"] = line
            else:
                desc_lines.append(line)
        
        proj_block["description"] = "\n".join(desc_lines)
        if proj_block["name"] or proj_block["description"]:
            parsed_data["projects"].append(proj_block)

    # Fallbacks
    if not parsed_data["experience"]:
        parsed_data["experience"] = [{"id": 1, "company": "Company Name", "role": "Job Title", "duration": "Month Year - Month Year", "description": "Describe your achievements..."}]
    if not parsed_data["education"]:
        parsed_data["education"] = [{"id": 1, "school": "University", "degree": "Degree", "duration": "Year - Year", "gpa": "GPA"}]
    if not parsed_data["projects"]:
        parsed_data["projects"] = [{"id": 1, "name": "Project Name", "tech": "Tech Stack", "description": "Project description..."}]

    return parsed_data
