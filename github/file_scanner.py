import os


def scan_repo_files(repo_path: str):
    """
    Returns list of all file paths in the repo.
    """

    all_files = []

    for root, _, files in os.walk(repo_path):
        for file in files:
            all_files.append(os.path.join(root, file))

    return all_files
