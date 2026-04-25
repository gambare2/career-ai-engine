import os
from collections import defaultdict

from github.file_scanner import scan_repo_files
from heuristics.reviewer import analyze_code_snippets


LANGUAGE_EXTENSIONS = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".cpp": "C++",
    ".go": "Go",
    ".rs": "Rust",
    ".php": "PHP",
}

FRAMEWORK_KEYWORDS = {
    "react": "React",
    "next": "Next.js",
    "express": "Express",
    "nestjs": "NestJS",
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "spring": "Spring",
    "laravel": "Laravel",
    "vue": "Vue",
    "angular": "Angular",
}

SUPPORTED_EXTENSIONS = tuple(LANGUAGE_EXTENSIONS.keys())


def analyze_repo(repo_path: str) -> dict:
    files = scan_repo_files(repo_path)

    file_count = 0
    total_lines = 0
    folders = set()
    max_depth = 0

    has_services = 0
    has_utils = 0
    react_files = 0

    language_counter = defaultdict(int)
    frameworks = set()
    
    # Store relative paths for heuristic analysis
    rel_paths = []

    for file_path in files:
        rel_path = os.path.relpath(os.path.dirname(file_path), repo_path)
        depth = rel_path.count(os.sep)
        max_depth = max(max_depth, depth)

        # folder checks
        folder_name = os.path.basename(os.path.dirname(file_path)).lower()
        if folder_name == "services":
            has_services = 1
        if folder_name == "utils":
            has_utils = 1
            
        full_rel_path = os.path.relpath(file_path, repo_path)
        rel_paths.append(full_rel_path)

        ext = os.path.splitext(file_path)[1].lower()

        if ext in SUPPORTED_EXTENSIONS:
            file_count += 1
            language_counter[LANGUAGE_EXTENSIONS[ext]] += 1

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().lower()
                    lines = content.splitlines()
                    total_lines += len(lines)

                    # framework detection
                    for key, fw in FRAMEWORK_KEYWORDS.items():
                        if key in content:
                            frameworks.add(fw)

                    # react heuristic
                    if "react" in content or "jsx" in file_path.lower():
                        react_files += 1

            except Exception:
                pass

        # track folder
        folders.add(rel_path)
        
    # Analyze code snippets/files
    advanced_analysis = analyze_code_snippets(rel_paths, repo_path)

    avg_file_lines = total_lines / file_count if file_count else 0

    # Language confidence %
    total_lang_files = sum(language_counter.values())
    language_confidence = {}

    for lang, count in language_counter.items():
        language_confidence[lang] = round((count / total_lang_files) * 100, 2)

    # UI score heuristic
    ui_score = min(10.0, 5.0 + react_files / 5)

    # Complexity heuristic
    complexity_score = min(10.0, (file_count / 50) + (max_depth / 2))

    return {
        "languages": language_confidence,
        "frameworks": sorted(list(frameworks)),

        "file_count": file_count,
        "folder_count": len(folders),
        "max_depth": max_depth,
        "has_services": has_services,
        "has_utils": has_utils,
        "avg_file_lines": round(avg_file_lines, 2),
        "ui_score": round(ui_score, 2),
        "complexity_score": round(complexity_score, 2),
        "code_review": advanced_analysis
    }
