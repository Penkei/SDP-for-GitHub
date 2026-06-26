import os
import shutil
import re
import uuid
import stat
import time
import hashlib
import tempfile
import gc
import json
import subprocess
from threading import RLock
from urllib.parse import quote, urlparse, urlunparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from git import Git, Repo

from config import settings


class GitHubService:
    def __init__(self, base_dir=None, cache_ttl_seconds=300):
        self.base_dir = base_dir or settings.temp_repo_dir or os.path.join(
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

    def _repo_owner_name(self, repo_url: str) -> tuple:
        parsed_url = urlparse(repo_url)
        path_parts = [part for part in parsed_url.path.strip("/").split("/") if part]

        if len(path_parts) < 2:
            raise ValueError("Repository URL must include both owner and repository name.")

        owner = path_parts[0]
        repo_name = path_parts[1].removesuffix(".git")

        return owner, repo_name

    def _cache_key(self, *parts) -> tuple:
        return tuple(str(part).strip().lower() for part in parts)

    def _build_authenticated_url(self, repo_url: str, github_token: str = None) -> str:
        if not github_token:
            return repo_url

        parsed_url = urlparse(repo_url)
        token = quote(github_token, safe="")
        netloc = f"x-access-token:{token}@{parsed_url.netloc}"

        return urlunparse((
            parsed_url.scheme,
            netloc,
            parsed_url.path,
            parsed_url.params,
            parsed_url.query,
            parsed_url.fragment
        ))

    def _sanitize_error(self, error: Exception, repo_url: str, github_token: str = None) -> Exception:
        message = str(error)

        if github_token:
            message = message.replace(github_token, "***")
            message = re.sub(
                r"https://x-access-token:[^@\s]+@github\.com/",
                "https://github.com/",
                message
            )
            message = message.replace(
                self._build_authenticated_url(repo_url, github_token),
                repo_url
            )

        message = re.sub(r"POST git-upload-pack[^\n\r]*", "", message)
        message = re.sub(r"Updating files:\s*\d+%[^\n\r]*", "", message)
        message = re.sub(r"Authorization:\s*Bearer\s+[^\s'\"]+", "Authorization: Bearer ***", message)
        message = re.sub(r"\s+", " ", message).strip()

        if "unable to create file" in message and "Filename too long" in message:
            return Exception(
                "Git checkout failed because this repository contains file paths "
                "that are too long for the current Windows Git configuration. "
                "The backend requests Git long-path support, but Windows may "
                "still need long paths enabled system-wide."
            )

        lower_message = message.lower()

        if any(token in lower_message for token in ["authentication failed", "could not read username", "repository not found"]):
            if github_token:
                return Exception(
                    "GitHub authentication failed. Your Personal Access Token may be invalid, "
                    "expired, or missing access to this repository. Check the token and try again."
                )

            return Exception(
                "GitHub authentication failed or the repository is not accessible. "
                "Use a valid Personal Access Token or check the repository URL."
            )

        return Exception(message)

    def _run_git_command(
        self,
        args: list[str],
        repo_url: str,
        github_token: str = None,
        cwd: str = None
    ):
        command = ["git", *args]

        try:
            return subprocess.run(
                command,
                cwd=cwd,
                check=True,
                capture_output=True,
                text=True,
                timeout=settings.git_command_timeout_seconds
            )
        except subprocess.TimeoutExpired as error:
            raise self._sanitize_error(
                Exception(
                    "Git operation timed out. The repository may be too large "
                    "or the hosting server may be slow. Try again later or use a smaller commit."
                ),
                repo_url,
                github_token
            )
        except subprocess.CalledProcessError as error:
            output = "\n".join(
                part for part in [error.stdout, error.stderr]
                if part
            )
            raise self._sanitize_error(Exception(output or str(error)), repo_url, github_token)

    def _authenticated_git_args(self, github_token: str = None) -> list[str]:
        if not github_token:
            return []

        return [
            "-c",
            f"http.extraHeader=Authorization: Bearer {github_token}"
        ]

    def _clone_selected_commit_shallow(
        self,
        repo_url: str,
        repo_path: str,
        commit_sha: str,
        github_token: str = None
    ) -> bool:
        depth = max(2, int(settings.git_shallow_history_depth))
        auth_args = self._authenticated_git_args(github_token)

        os.makedirs(repo_path, exist_ok=True)

        self._run_git_command(
            ["-C", repo_path, "-c", "core.longpaths=true", "init"],
            repo_url,
            github_token
        )
        self._run_git_command(
            ["-C", repo_path, "remote", "add", "origin", repo_url],
            repo_url,
            github_token
        )
        self._run_git_command(
            [
                "-C",
                repo_path,
                *auth_args,
                "fetch",
                "--no-tags",
                f"--depth={depth}",
                "origin",
                commit_sha
            ],
            repo_url,
            github_token
        )
        self._run_git_command(
            ["-C", repo_path, "-c", "core.longpaths=true", "checkout", "--force", "FETCH_HEAD"],
            repo_url,
            github_token
        )

        return True

    def _github_api_get(self, repo_url: str, api_path: str, github_token: str = None):
        request_url = f"https://api.github.com{api_path}"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "SDP-for-GitHub",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"

        request = Request(request_url, headers=headers)

        try:
            with urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="ignore")

            if error.code in {401, 403}:
                token_hint = (
                    "Your GitHub Personal Access Token may be invalid, expired, "
                    "or missing access to this repository. Check the token and "
                    "make sure it has read access to repository contents and metadata."
                    if github_token
                    else "GitHub denied the request. Add a valid Personal Access Token or try again later."
                )
                raise Exception(token_hint)

            if error.code == 404:
                raise Exception(
                    "GitHub could not find this repository, branch, tag, or commit. "
                    "Check the repository URL and selected reference."
                )

            raise Exception(
                f"GitHub API request failed with status {error.code}. {detail}"
            )
        except URLError as error:
            raise Exception(f"GitHub API request failed: {error.reason}")

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
                Repo.clone_from(
                    repo_url,
                    cache_path,
                    multi_options=["--mirror", "-c", "core.longpaths=true"],
                    allow_unsafe_options=True
                )
                self._repo_fetch_times[cache_path] = time.time()
                return cache_path

            if cache_is_fresh:
                return cache_path

            repo = None

            try:
                print(f"Refreshing repository cache: {repo_url}")
                repo = Repo(cache_path)
                repo.git.fetch("--prune", "--tags", "origin")
                self._repo_fetch_times[cache_path] = time.time()
            except Exception as e:
                print(f"Warning: failed to refresh cache for {repo_url}: {e}")
            finally:
                self._close_repo(repo)

            return cache_path

    def _remove_readonly(self, func, path, exc_info):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except PermissionError:
            time.sleep(0.2)
            os.chmod(path, stat.S_IWRITE)
            func(path)

    def clone_and_checkout(
        self,
        repo_url: str,
        commit_sha: str,
        use_personal_access_token: bool = False,
        github_token: str = None
    ) -> str:
        repo_name = self._safe_repo_name(repo_url)
        request_id = str(uuid.uuid4())[:8]

        repo_path = os.path.join(
            self.worktree_dir,
            f"{repo_name}_{request_id}"
        )

        if use_personal_access_token:
            print(f"Fetching selected commit into temporary worktree: {repo_url}")
            try:
                self._clone_selected_commit_shallow(
                    repo_url,
                    repo_path,
                    commit_sha,
                    github_token=github_token
                )
                return repo_path
            except Exception as error:
                if "timed out" in str(error).lower():
                    raise self._sanitize_error(error, repo_url, github_token)

                print(
                    "Warning: shallow commit fetch failed. "
                    "Falling back to normal temporary clone."
                )
                self.cleanup_repo(repo_path)

                clone_url = self._build_authenticated_url(repo_url, github_token)

                try:
                    repo = Repo.clone_from(
                        clone_url,
                        repo_path,
                        multi_options=["-c", "core.longpaths=true"],
                        allow_unsafe_options=True
                    )
                except Exception as fallback_error:
                    raise self._sanitize_error(fallback_error, repo_url, github_token)
        else:
            cache_path = self._ensure_cached_repo(repo_url)
            print(f"Cloning repository from local cache: {repo_url}")
            try:
                repo = Repo.clone_from(
                    cache_path,
                    repo_path,
                    multi_options=["-c", "core.longpaths=true"],
                    allow_unsafe_options=True
                )
            except Exception as error:
                raise self._sanitize_error(error, repo_url, github_token)

        try:
            print(f"Checking out commit: {commit_sha}")
            repo.git.checkout(commit_sha)
        finally:
            self._close_repo(repo)

        return repo_path

    def cleanup_repo(self, repo_path: str):
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

    def get_commit_list(
        self,
        repo_url: str,
        git_ref: str,
        max_commits: int = 20,
        skip: int = 0,
        use_personal_access_token: bool = False,
        github_token: str = None
    ) -> list:
        cache_key = self._cache_key(
            "commits",
            repo_url,
            git_ref,
            max_commits,
            skip,
            "pat" if use_personal_access_token else "cache"
        )

        if not use_personal_access_token:
            with self._lock:
                cached_commits = self._get_cached_metadata(cache_key)

            if cached_commits is not None:
                print(f"Using cached commit list: {repo_url} [{git_ref}]")
                return cached_commits

        try:
            owner, repo_name = self._repo_owner_name(repo_url)
            page = (skip // max_commits) + 1 if max_commits > 0 else 1
            encoded_ref = quote(git_ref, safe="")
            api_path = (
                f"/repos/{quote(owner)}/{quote(repo_name)}/commits"
                f"?sha={encoded_ref}&per_page={max_commits}&page={page}"
            )
            print(f"Loading commit list from GitHub API: {repo_url} [{git_ref}] page {page}")
            api_commits = self._github_api_get(repo_url, api_path, github_token)

            commit_list = []

            for item in api_commits:
                commit = item.get("commit", {})
                author = commit.get("author") or {}

                commit_list.append({
                    "sha": item.get("sha", ""),
                    "short_sha": item.get("sha", "")[:8],
                    "message": (commit.get("message") or "").strip().replace("\n", " "),
                    "author": author.get("name") or "Unknown",
                    "date": author.get("date") or ""
                })

            if not use_personal_access_token:
                with self._lock:
                    self._set_cached_metadata(cache_key, commit_list)

            return commit_list

        except Exception as error:
            raise self._sanitize_error(error, repo_url, github_token)

    def get_branch_list(
        self,
        repo_url: str,
        use_personal_access_token: bool = False,
        github_token: str = None
    ) -> list:
        cache_key = self._cache_key(
            "branches",
            repo_url,
            "pat" if use_personal_access_token else "cache"
        )

        if not use_personal_access_token:
            with self._lock:
                cached_branches = self._get_cached_metadata(cache_key)

            if cached_branches is not None:
                print(f"Using cached branch list: {repo_url}")
                return cached_branches

        branches = []
        remote_url = self._build_authenticated_url(repo_url, github_token)
        default_branch = self._get_default_branch_name(remote_url, repo_url, github_token)

        try:
            branch_output = Git().ls_remote("--heads", remote_url)
        except Exception as error:
            raise self._sanitize_error(error, repo_url, github_token)

        for line in branch_output.splitlines():
            parts = line.split()

            if len(parts) < 2 or not parts[1].startswith("refs/heads/"):
                continue

            branch_name = parts[1].replace("refs/heads/", "", 1)

            branches.append({
                "name": branch_name,
                "type": "branch",
                "is_default": branch_name == default_branch
            })

        branches.sort(key=lambda branch: (
            not branch.get("is_default", False),
            branch["name"].lower()
        ))

        if not use_personal_access_token:
            with self._lock:
                self._set_cached_metadata(cache_key, branches)

        return branches

    def _get_default_branch_name(
        self,
        remote_url: str,
        repo_url: str,
        github_token: str = None
    ) -> str:
        try:
            head_output = Git().ls_remote("--symref", remote_url, "HEAD")
        except Exception as error:
            print(
                "Warning: failed to detect default branch for "
                f"{repo_url}: {self._sanitize_error(error, repo_url, github_token)}"
            )
            return ""

        for line in head_output.splitlines():
            parts = line.split()

            if len(parts) >= 3 and parts[0] == "ref:" and parts[1].startswith("refs/heads/"):
                return parts[1].replace("refs/heads/", "", 1)

        return ""


    def get_tag_list(
        self,
        repo_url: str,
        use_personal_access_token: bool = False,
        github_token: str = None
    ) -> list:
        cache_key = self._cache_key(
            "tags",
            repo_url,
            "pat" if use_personal_access_token else "cache"
        )

        if not use_personal_access_token:
            with self._lock:
                cached_tags = self._get_cached_metadata(cache_key)

            if cached_tags is not None:
                print(f"Using cached tag list: {repo_url}")
                return cached_tags

        tags = []
        remote_url = self._build_authenticated_url(repo_url, github_token)

        try:
            tag_output = Git().ls_remote("--tags", remote_url)
        except Exception as error:
            raise self._sanitize_error(error, repo_url, github_token)

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

        if not use_personal_access_token:
            with self._lock:
                self._set_cached_metadata(cache_key, tags)

        return tags

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
