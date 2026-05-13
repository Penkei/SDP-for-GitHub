import os
import shutil
import re
import uuid
import stat
import time
import hashlib
from threading import RLock
from git import Repo


class GitHubService:
    def __init__(self, base_dir="temp_repos", cache_ttl_seconds=300):
        self.base_dir = base_dir
        self.worktree_dir = os.path.join(self.base_dir, "worktrees")
        self.cache_dir = os.path.join(self.base_dir, "repo_cache")
        self.cache_ttl_seconds = cache_ttl_seconds
        self._metadata_cache = {}
        self._repo_fetch_times = {}
        self._lock = RLock()

        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(self.worktree_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)

    def _safe_repo_name(self, repo_url: str) -> str:
        name = repo_url.rstrip("/").replace(".git", "").split("/")[-1]
        return re.sub(r"[^a-zA-Z0-9_-]", "_", name)

    def _repo_cache_path(self, repo_url: str) -> str:
        repo_name = self._safe_repo_name(repo_url)
        repo_hash = hashlib.sha1(repo_url.strip().lower().encode("utf-8")).hexdigest()[:12]
        return os.path.join(self.cache_dir, f"{repo_name}_{repo_hash}.git")

    def _cache_key(self, *parts) -> tuple:
        return tuple(str(part).strip().lower() for part in parts)

    def _get_cached_metadata(self, key: tuple):
        cached_item = self._metadata_cache.get(key)

        if not cached_item:
            return None

        cached_at, value = cached_item

        if time.time() - cached_at > self.cache_ttl_seconds:
            self._metadata_cache.pop(key, None)
            return None

        return value

    def _set_cached_metadata(self, key: tuple, value):
        self._metadata_cache[key] = (time.time(), value)

    def _ensure_cached_repo(self, repo_url: str) -> str:
        cache_path = self._repo_cache_path(repo_url)

        with self._lock:
            cache_exists = os.path.exists(cache_path)
            last_fetch = self._repo_fetch_times.get(cache_path, 0)
            cache_is_fresh = time.time() - last_fetch <= self.cache_ttl_seconds

            if not cache_exists:
                print(f"Creating repository cache: {repo_url}")
                Repo.clone_from(repo_url, cache_path, multi_options=["--mirror"])
                self._repo_fetch_times[cache_path] = time.time()
                return cache_path

            if cache_is_fresh:
                return cache_path

            try:
                print(f"Refreshing repository cache: {repo_url}")
                repo = Repo(cache_path)
                repo.git.fetch("--prune", "--tags", "origin")
                self._repo_fetch_times[cache_path] = time.time()
            except Exception as e:
                print(f"Warning: failed to refresh cache for {repo_url}: {e}")

            return cache_path

    def _remove_readonly(self, func, path, exc_info):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def clone_and_checkout(self, repo_url: str, commit_sha: str) -> str:
        repo_name = self._safe_repo_name(repo_url)
        request_id = str(uuid.uuid4())[:8]
        cache_path = self._ensure_cached_repo(repo_url)

        repo_path = os.path.join(
            self.worktree_dir,
            f"{repo_name}_{request_id}"
        )

        print(f"Cloning repository from local cache: {repo_url}")
        repo = Repo.clone_from(cache_path, repo_path)

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
        cache_key = self._cache_key(
            "commits",
            repo_url,
            git_ref,
            max_commits,
            skip
        )

        with self._lock:
            cached_commits = self._get_cached_metadata(cache_key)

        if cached_commits is not None:
            print(f"Using cached commit list: {repo_url} [{git_ref}]")
            return cached_commits

        repo_name = self._safe_repo_name(repo_url)
        request_id = str(uuid.uuid4())[:8]
        cache_path = self._ensure_cached_repo(repo_url)

        repo_path = os.path.join(
            self.worktree_dir,
            f"{repo_name}_commits_{request_id}"
        )

        try:
            print(f"Cloning repository from local cache for commit list: {repo_url}")
            repo = Repo.clone_from(cache_path, repo_path)

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

            with self._lock:
                self._set_cached_metadata(cache_key, commit_list)

            return commit_list

        finally:
            self.cleanup_repo(repo_path)

    def get_branch_list(self, repo_url: str) -> list:
        cache_key = self._cache_key("branches", repo_url)

        with self._lock:
            cached_branches = self._get_cached_metadata(cache_key)

        if cached_branches is not None:
            print(f"Using cached branch list: {repo_url}")
            return cached_branches

        cache_path = self._ensure_cached_repo(repo_url)
        repo = Repo(cache_path)

        branches = []
        branch_output = repo.git.for_each_ref("--format=%(refname:short)", "refs/heads")

        for branch_name in branch_output.splitlines():
            if not branch_name:
                continue

            branches.append({
                "name": branch_name,
                "type": "branch"
            })

        branches.sort(key=lambda branch: branch["name"].lower())

        with self._lock:
            self._set_cached_metadata(cache_key, branches)

        return branches


    def get_tag_list(self, repo_url: str) -> list:
        cache_key = self._cache_key("tags", repo_url)

        with self._lock:
            cached_tags = self._get_cached_metadata(cache_key)

        if cached_tags is not None:
            print(f"Using cached tag list: {repo_url}")
            return cached_tags

        cache_path = self._ensure_cached_repo(repo_url)
        repo = Repo(cache_path)

        tags = []
        tag_output = repo.git.tag("-l")

        for tag_name in tag_output.splitlines():
            if not tag_name:
                continue

            tags.append({
                "name": tag_name,
                "type": "tag"
            })

        tags.sort(key=lambda tag: tag["name"].lower())

        with self._lock:
            self._set_cached_metadata(cache_key, tags)

        return tags
