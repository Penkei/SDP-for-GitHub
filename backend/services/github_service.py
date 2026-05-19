import os
import shutil
import re
import uuid
import stat
import time
import hashlib
import tempfile
<<<<<<< HEAD
=======
import gc
>>>>>>> Refinement
from threading import RLock
from git import Git, Repo


class GitHubService:
    def __init__(self, base_dir=None, cache_ttl_seconds=300):
        self.base_dir = base_dir or os.path.join(
            tempfile.gettempdir(),
            "sdp_github_temp_repos"
        )
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

<<<<<<< HEAD
=======
            repo = None

>>>>>>> Refinement
            try:
                print(f"Refreshing repository cache: {repo_url}")
                repo = Repo(cache_path)
                repo.git.fetch("--prune", "--tags", "origin")
                self._repo_fetch_times[cache_path] = time.time()
            except Exception as e:
                print(f"Warning: failed to refresh cache for {repo_url}: {e}")
<<<<<<< HEAD
=======
            finally:
                self._close_repo(repo)
>>>>>>> Refinement

            return cache_path

    def _remove_readonly(self, func, path, exc_info):
<<<<<<< HEAD
        os.chmod(path, stat.S_IWRITE)
        func(path)
=======
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except PermissionError:
            time.sleep(0.2)
            os.chmod(path, stat.S_IWRITE)
            func(path)
>>>>>>> Refinement

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

<<<<<<< HEAD
        print(f"Checking out commit: {commit_sha}")
        repo.git.checkout(commit_sha)
=======
        try:
            print(f"Checking out commit: {commit_sha}")
            repo.git.checkout(commit_sha)
        finally:
            self._close_repo(repo)
>>>>>>> Refinement

        return repo_path

    def cleanup_repo(self, repo_path: str):
<<<<<<< HEAD
        try:
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path, onerror=self._remove_readonly)
                print(f"Cleaned up temp repo: {repo_path}")
        except Exception as e:
            print(f"Warning: failed to clean temp repo {repo_path}: {e}")
=======
        if not repo_path or not os.path.exists(repo_path):
            return

        last_error = None

        for attempt in range(1, 6):
            try:
                gc.collect()
                shutil.rmtree(repo_path, onerror=self._remove_readonly)
                print(f"Cleaned up temp repo: {repo_path}")
                return
            except Exception as e:
                last_error = e
                time.sleep(0.35 * attempt)

        self._quarantine_locked_repo(repo_path, last_error)

    def get_changed_files(self, repo_path: str, commit_sha: str) -> list:
        repo = None

        try:
            repo = Repo(repo_path)
            commit = repo.commit(commit_sha)

            if not commit.parents:
                return []

            parent = commit.parents[0]
            changed_files = []

            for diff in parent.diff(commit):
                file_path = diff.b_path or diff.a_path

                if file_path:
                    changed_files.append(file_path.replace("\\", "/"))

            return sorted(set(changed_files))

        finally:
            self._close_repo(repo)
>>>>>>> Refinement

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
<<<<<<< HEAD
=======
        repo = None
>>>>>>> Refinement

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
<<<<<<< HEAD
=======
            self._close_repo(repo)
>>>>>>> Refinement
            self.cleanup_repo(repo_path)

    def get_branch_list(self, repo_url: str) -> list:
        cache_key = self._cache_key("branches", repo_url)

        with self._lock:
            cached_branches = self._get_cached_metadata(cache_key)

        if cached_branches is not None:
            print(f"Using cached branch list: {repo_url}")
            return cached_branches

        branches = []
        branch_output = Git().ls_remote("--heads", repo_url)

        for line in branch_output.splitlines():
            parts = line.split()

            if len(parts) < 2 or not parts[1].startswith("refs/heads/"):
                continue

            branch_name = parts[1].replace("refs/heads/", "", 1)

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

        tags = []
        tag_output = Git().ls_remote("--tags", repo_url)

        for line in tag_output.splitlines():
            parts = line.split()

            if len(parts) < 2 or not parts[1].startswith("refs/tags/"):
                continue

            if parts[1].endswith("^{}"):
                continue

            tag_name = parts[1].replace("refs/tags/", "", 1)

            tags.append({
                "name": tag_name,
                "type": "tag"
            })

        tags.sort(key=lambda tag: tag["name"].lower())

        with self._lock:
            self._set_cached_metadata(cache_key, tags)

        return tags
<<<<<<< HEAD
=======

    def _close_repo(self, repo):
        if not repo:
            return

        try:
            repo.close()
        except Exception:
            pass

        try:
            repo.git.clear_cache()
        except Exception:
            pass

    def _quarantine_locked_repo(self, repo_path: str, error: Exception):
        locked_path = f"{repo_path}_cleanup_pending_{int(time.time())}"

        try:
            os.rename(repo_path, locked_path)
            print(
                "Warning: temp repo is locked and was moved for later cleanup: "
                f"{locked_path}. Original error: {error}"
            )
        except Exception:
            print(f"Warning: failed to clean temp repo {repo_path}: {error}")
>>>>>>> Refinement
