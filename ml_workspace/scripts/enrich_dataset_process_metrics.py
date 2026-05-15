import os
import shutil

import pandas as pd
from git import Repo

from build_multi_repo_dataset import (
    clone_repository,
    extract_process_metrics,
    safe_repo_name,
)


DATASET_PATH = "data/github_defect_dataset.csv"
BACKUP_PATH = "data/github_defect_dataset_before_process_metrics.csv"
PROCESS_COLUMNS = [
    "file_change_count",
    "file_bug_fix_count",
    "recent_file_change_count",
    "days_since_last_change",
    "last_change_lines_added",
    "last_change_lines_deleted",
    "last_change_churn",
    "last_change_file_count",
    "author_file_change_count",
]


def needs_enrichment(df):
    return any(column not in df.columns for column in PROCESS_COLUMNS) or df[PROCESS_COLUMNS].isna().any().any()


def enrich_dataset():
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    df = pd.read_csv(DATASET_PATH)

    for column in PROCESS_COLUMNS:
        if column not in df.columns:
            df[column] = pd.NA

    if not needs_enrichment(df):
        print("Dataset already contains process metrics. No changes required.")
        return

    shutil.copy2(DATASET_PATH, BACKUP_PATH)
    print(f"Backup created: {BACKUP_PATH}")

    repo_urls = df["repo_url"].dropna().unique().tolist()

    for repo_index, repo_url in enumerate(repo_urls, start=1):
        repo_name = safe_repo_name(repo_url)
        repo_dir = os.path.join("data", "process_metric_repos", repo_name)

        print(f"\n[{repo_index}/{len(repo_urls)}] Processing repository: {repo_url}")

        if os.path.exists(repo_dir):
            repo = Repo(repo_dir)
            repo.git.fetch("--all", "--tags", "--prune")
        else:
            repo = clone_repository(repo_url, repo_dir)

        repo_mask = df["repo_url"] == repo_url
        repo_rows = df[repo_mask]

        for row_number, (row_index, row) in enumerate(repo_rows.iterrows(), start=1):
            if row_number % 50 == 0:
                print(f"  Enriched {row_number}/{len(repo_rows)} rows")

            if not pd.isna(row.get("file_change_count")):
                continue

            try:
                commit = repo.commit(row["commit_sha"])
                process_metrics = extract_process_metrics(repo, commit, row["file_path"])

                for column, value in process_metrics.items():
                    df.at[row_index, column] = value

            except Exception as error:
                print(
                    f"  Skipped {str(row.get('commit_sha', ''))[:8]} "
                    f"{row.get('file_path', '')}: {error}"
                )

    df[PROCESS_COLUMNS] = df[PROCESS_COLUMNS].fillna(0)
    df.to_csv(DATASET_PATH, index=False)

    print("\nProcess metric enrichment completed.")
    print(f"Updated dataset: {DATASET_PATH}")
    print(f"Dataset shape: {df.shape}")


if __name__ == "__main__":
    enrich_dataset()
