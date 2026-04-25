import os

IGNORE_DIRS = {
    'node_modules', '.git', '__pycache__', 'venv', 'env', '.venv', 
    'dist', 'build', '.next', '.cache', 'coverage'
}

def scan_repo_files(repo_path: str):
    """
    Returns list of all file paths in the repo, ignoring unnecessary folders.
    """
    all_files = []

    for root, dirs, files in os.walk(repo_path):
        # Modify dirs in-place to skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            all_files.append(os.path.join(root, file))

    return all_files
