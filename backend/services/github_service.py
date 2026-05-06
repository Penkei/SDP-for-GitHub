import os
import shutil
import re
import uuid
import stat
from git import Repo
import uuid


class GitHubService:
    def __init__(self, base_dir="temp_repos"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _safe_repo_name(self, repo_url: str) -> str:
        name = repo_url.rstrip("/").replace(".git", "").split("/")[-1]
        return re.sub(r"[^a-zA-Z0-9_-]", "_", name)

    def _remove_readonly(self, func, path, exc_info):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def clone_and_checkout(self, repo_url: str, commit_sha: str) -> str:
        repo_name = self._safe_repo_name(repo_url)
        request_id = str(uuid.uuid4())[:8]

        repo_path = os.path.join(
            self.base_dir,
            f"{repo_name}_{request_id}"
        )

        print(f"Cloning repository: {repo_url}")
        repo = Repo.clone_from(repo_url, repo_path)

        print(f"Checking out commit: {commit_sha}")
        repo.git.checkout(commit_sha)

        return repo_path

    def cleanup_repo(self, repo_path: str):
        try:
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path, onerror=self._remove_readonly)
                print(f"Cleaned up temp repo: {repo_path}")
        except Exception as e:
            print(f"Warning: failed to clean temp repo {repo_path}: {e}")

    def get_commit_list(
        self,
        repo_url: str,
        git_ref: str,
        max_commits: int = 20,
        skip: int = 0
    ) -> list:
        repo_name = self._safe_repo_name(repo_url)
        request_id = str(uuid.uuid4())[:8]

        repo_path = os.path.join(
            self.base_dir,
            f"{repo_name}_commits_{request_id}"
        )

        try:
            print(f"Cloning repository for commit list: {repo_url}")
            repo = Repo.clone_from(repo_url, repo_path)

            print(f"Checking out reference for commit list: {git_ref}")
            repo.git.checkout(git_ref)

            total_to_fetch = skip + max_commits
            commits = list(repo.iter_commits("HEAD", max_count=total_to_fetch))

            page_commits = commits[skip:skip + max_commits]

            commit_list = []

            for commit in page_commits:
                commit_list.append({
                    "sha": commit.hexsha,
                    "short_sha": commit.hexsha[:8],
                    "message": commit.message.strip().replace("\n", " "),
                    "author": commit.author.name,
                    "date": commit.committed_datetime.isoformat()
                })

            return commit_list

        finally:
            self.cleanup_repo(repo_path)

    def get_branch_list(self, repo_url: str) -> list:
        repo_name = self._safe_repo_name(repo_url)
        request_id = str(uuid.uuid4())[:8]

        repo_path = os.path.join(
            self.base_dir,
            f"{repo_name}_branches_{request_id}"
        )

        try:
            print(f"Cloning repository for branch list: {repo_url}")
            repo = Repo.clone_from(repo_url, repo_path)

            branches = []

            for ref in repo.remote().refs:
                branch_name = ref.remote_head

                if branch_name == "HEAD":
                    continue

                branches.append({
                    "name": branch_name,
                    "type": "branch"
                })

            return branches

        finally:
            self.cleanup_repo(repo_path)


    def get_tag_list(self, repo_url: str) -> list:
        repo_name = self._safe_repo_name(repo_url)
        request_id = str(uuid.uuid4())[:8]

        repo_path = os.path.join(
            self.base_dir,
            f"{repo_name}_tags_{request_id}"
        )

        try:
            print(f"Cloning repository for tag list: {repo_url}")
            repo = Repo.clone_from(repo_url, repo_path)

            tags = []

            for tag in repo.tags:
                tags.append({
                    "name": tag.name,
                    "type": "tag"
                })

            return tags

        finally:
            self.cleanup_repo(repo_path)