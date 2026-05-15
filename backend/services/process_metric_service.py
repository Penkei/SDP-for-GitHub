import os
import re
from datetime import datetime, timezone

import pandas as pd
from git import Repo


class ProcessMetricService:
    BUG_KEYWORDS = [
        "fix", "fixed", "fixes", "bug", "bugfix",
        "defect", "fault", "crash", "exception",
        "error", "failure", "broken", "incorrect"
    ]

    def __init__(self, history_limit: int = 200, recent_days: int = 90):
        self.history_limit = history_limit
        self.recent_days = recent_days

    def enrich_with_process_metrics(
        self,
        metrics_df: pd.DataFrame,
        repo_path: str,
        commit_sha: str
    ) -> pd.DataFrame:
        if metrics_df.empty:
            return metrics_df

        repo = Repo(repo_path)
        target_commit = repo.commit(commit_sha)
        rows = []

        for _, row in metrics_df.iterrows():
            file_path = self._to_git_path(row["file_path"])
            process_metrics = self.extract_for_file(repo, target_commit, file_path)
            merged_row = row.to_dict()
            merged_row.update(process_metrics)
            rows.append(merged_row)

        return pd.DataFrame(rows)

    def extract_for_file(self, repo: Repo, target_commit, file_path: str) -> dict:
        history = self._get_file_history(repo, target_commit.hexsha, file_path)
        history_before_target = [
            commit for commit in history
            if commit.hexsha != target_commit.hexsha
        ]

        recent_file_change_count = 0
        file_bug_fix_count = 0
        author_file_change_count = 0
        days_since_last_change = 9999
        last_change_lines_added = 0
        last_change_lines_deleted = 0
        last_change_churn = 0
        last_change_file_count = 0

        target_author = self._author_key(target_commit)
        target_date = self._as_utc(target_commit.committed_datetime)

        for commit in history_before_target:
            commit_date = self._as_utc(commit.committed_datetime)
            age_days = max(0, (target_date - commit_date).days)

            if age_days <= self.recent_days:
                recent_file_change_count += 1

            if self._is_bug_fix_message(commit.message):
                file_bug_fix_count += 1

            if self._author_key(commit) == target_author:
                author_file_change_count += 1

        if history_before_target:
            last_change = history_before_target[0]
            days_since_last_change = max(
                0,
                (target_date - self._as_utc(last_change.committed_datetime)).days
            )
            last_stats = self._get_file_stats(last_change, file_path)
            last_change_lines_added = last_stats["lines_added"]
            last_change_lines_deleted = last_stats["lines_deleted"]
            last_change_churn = last_stats["code_churn"]
            last_change_file_count = len(last_change.stats.files)

        return {
            "file_change_count": len(history_before_target),
            "file_bug_fix_count": file_bug_fix_count,
            "recent_file_change_count": recent_file_change_count,
            "days_since_last_change": days_since_last_change,
            "last_change_lines_added": last_change_lines_added,
            "last_change_lines_deleted": last_change_lines_deleted,
            "last_change_churn": last_change_churn,
            "last_change_file_count": last_change_file_count,
            "author_file_change_count": author_file_change_count,
        }

    def _get_file_history(self, repo: Repo, commit_sha: str, file_path: str) -> list:
        try:
            return list(
                repo.iter_commits(
                    rev=commit_sha,
                    paths=file_path,
                    max_count=self.history_limit
                )
            )
        except Exception:
            return []

    def _get_file_stats(self, commit, file_path: str) -> dict:
        stats = commit.stats.files
        normalized_path = self._to_git_path(file_path)
        file_stats = stats.get(normalized_path)

        if not file_stats:
            matching_paths = [
                path for path in stats
                if self._to_git_path(path).endswith(normalized_path)
                or normalized_path.endswith(self._to_git_path(path))
            ]
            file_stats = stats.get(matching_paths[0], {}) if matching_paths else {}

        lines_added = int(file_stats.get("insertions", 0) or 0)
        lines_deleted = int(file_stats.get("deletions", 0) or 0)

        return {
            "lines_added": lines_added,
            "lines_deleted": lines_deleted,
            "code_churn": lines_added + lines_deleted,
        }

    def _is_bug_fix_message(self, message: str) -> bool:
        message = (message or "").lower()
        return any(
            re.search(rf"\b{re.escape(keyword)}\b", message)
            for keyword in self.BUG_KEYWORDS
        )

    def _author_key(self, commit) -> str:
        return f"{commit.author.name} {commit.author.email}".strip().lower()

    def _as_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)

    def _to_git_path(self, file_path: str) -> str:
        return str(file_path).replace(os.sep, "/")
