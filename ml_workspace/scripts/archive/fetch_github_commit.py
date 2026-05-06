import os
import shutil
from git import Repo


def fetch_repository_commit(repo_url, commit_sha, output_dir):
    """
    Clone GitHub repository and checkout selected commit SHA.
    """

    # Remove old temp repo if exists
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    print("Cloning repository...")
    Repo.clone_from(repo_url, output_dir)

    repo = Repo(output_dir)

    print(f"Checking out commit: {commit_sha}")
    repo.git.checkout(commit_sha)

    print("Repository ready.")
    return output_dir


if __name__ == "__main__":
    output_dir="temp_repo"
    repo_url = input("Enter GitHub repository URL: ").strip()
    commit_sha = input("Enter commit SHA: ").strip()

    fetch_repository_commit(repo_url, commit_sha, output_dir)

    print(f"Done. Repository downloaded to {output_dir}/")