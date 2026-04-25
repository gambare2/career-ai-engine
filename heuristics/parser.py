import re

def parse_resume_text(text: str) -> dict:
    """
    Hardcoded heuristics parser to extract structured data from raw resume text.
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
        "skills": ""
    }

    # 1. Name (Assume first non-empty line is the name)
    parsed_data["name"] = lines[0] if lines else ""

    # 2. Email & Phone (Search entire text)
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

    # 3. Section Splitting
    sections = {
        "summary": [],
        "experience": [],
        "education": [],
        "projects": [],
        "skills": []
    }
    
    current_section = None

    for line in lines[1:]:
        line_upper = line.upper()
        # Detect section headers
        if any(keyword in line_upper for keyword in ["SUMMARY", "PROFILE", "ABOUT ME"]):
            current_section = "summary"
            continue
        elif any(keyword in line_upper for keyword in ["EXPERIENCE", "WORK HISTORY", "EMPLOYMENT"]):
            current_section = "experience"
            continue
        elif any(keyword in line_upper for keyword in ["EDUCATION", "ACADEMIC"]):
            current_section = "education"
            continue
        elif any(keyword in line_upper for keyword in ["PROJECT", "PROJECTS", "PORTFOLIO"]):
            current_section = "projects"
            continue
        elif any(keyword in line_upper for keyword in ["SKILL", "TECHNOLOGIES"]):
            current_section = "skills"
            continue

        if current_section:
            sections[current_section].append(line)

    # 4. Process Sections
    parsed_data["summary"] = " ".join(sections["summary"])
    parsed_data["skills"] = " ".join(sections["skills"])

    # Basic heuristic to chunk experience
    # Every time we see a year-ish string (e.g., 2020 - 2022, Present), we start a new block or assign duration
    # This is a very rough hardcoded approximation
    if sections["experience"]:
        exp_block = {"id": 1, "company": "", "role": "", "duration": "", "description": ""}
        counter = 1
        desc_lines = []
        for line in sections["experience"]:
            date_match = re.search(r'(19|20)\d{2}.*(19|20)\d{2}|(19|20)\d{2}.*Present', line, re.IGNORECASE)
            if date_match and len(line) < 50:
                # Likely a date/header line
                if exp_block["company"]: # Save previous
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
        
        # append last block
        if exp_block["company"] or desc_lines:
            exp_block["description"] = "\n".join(desc_lines)
            parsed_data["experience"].append(exp_block)

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
                # Save and start new if we see another school
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
            # usually projects have short names
            if len(line) < 40 and not proj_block["name"]:
                proj_block["name"] = line
            elif ("react" in line.lower() or "python" in line.lower() or "node" in line.lower() or "stack" in line.lower()) and len(line) < 60 and not proj_block["tech"]:
                proj_block["tech"] = line
            else:
                desc_lines.append(line)
                # if we hit a newline in original text, might be a new project, but we stripped newlines.
                # Just clump it all for now or split on bullets.
        
        proj_block["description"] = "\n".join(desc_lines)
        if proj_block["name"] or proj_block["description"]:
            parsed_data["projects"].append(proj_block)

    # Fallback to avoid empty lists breaking the UI
    if not parsed_data["experience"]:
        parsed_data["experience"] = [{"id": 1, "company": "Company Name", "role": "Job Title", "duration": "Month Year - Month Year", "description": "Describe your achievements..."}]
    if not parsed_data["education"]:
        parsed_data["education"] = [{"id": 1, "school": "University", "degree": "Degree", "duration": "Year - Year", "gpa": "GPA"}]
    if not parsed_data["projects"]:
        parsed_data["projects"] = [{"id": 1, "name": "Project Name", "tech": "Tech Stack", "description": "Project description..."}]

    return parsed_data
