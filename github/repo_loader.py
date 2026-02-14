import os
import shutil
import subprocess


def clone_repo(repo_url: str, target_dir: str):
    """
    Clones a GitHub repo locally.
    """

    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)

    subprocess.run(
        ["git", "clone", "--depth=1", repo_url, target_dir],
        check=True
    )

    return target_dir
