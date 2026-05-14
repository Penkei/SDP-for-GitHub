import os
import shutil
import pandas as pd

from build_multi_repo_dataset import build_dataset_for_repo, read_repo_list


DATASET_PATH = "data/github_defect_dataset.csv"
APPEND_REPO_PATH = "data/repositories_append.txt"
BACKUP_PATH = "data/github_defect_dataset_before_append.csv"
DUPLICATE_KEYS = ["repo_url", "commit_sha", "file_path", "defect"]


def load_existing_dataset():
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(
            f"Existing dataset not found: {DATASET_PATH}. Run build_multi_repo_dataset.py first."
        )

    return pd.read_csv(DATASET_PATH)


def append_new_repositories(max_commits: int, max_rows_per_repo: int):
    existing_df = load_existing_dataset()
    repos = read_repo_list(APPEND_REPO_PATH)

    if not repos:
        raise ValueError(f"No repositories found in {APPEND_REPO_PATH}.")

    existing_repo_urls = set(existing_df.get("repo_url", pd.Series(dtype=str)).dropna())
    new_rows = []

    for repo_url in repos:
        if repo_url in existing_repo_urls:
            print(f"Skipping already present repo: {repo_url}")
            continue

        try:
            rows = build_dataset_for_repo(repo_url, max_commits, max_rows_per_repo)
            new_rows.extend(rows)
        except Exception as e:
            print(f"Failed repository {repo_url}: {e}")

    if not new_rows:
        raise ValueError("No new rows were collected. Existing dataset was not changed.")

    append_df = pd.DataFrame(new_rows)
    combined_df = pd.concat([existing_df, append_df], ignore_index=True)
    combined_df = combined_df.drop_duplicates(
        subset=DUPLICATE_KEYS,
        keep="first"
    )

    shutil.copy2(DATASET_PATH, BACKUP_PATH)
    combined_df.to_csv(DATASET_PATH, index=False)

    print("\nAppend completed.")
    print(f"Previous dataset backed up to: {BACKUP_PATH}")
    print("Old shape:", existing_df.shape)
    print("New rows collected:", append_df.shape)
    print("Combined shape:", combined_df.shape)

    print("\nRows by repository:")
    print(combined_df["repo_name"].value_counts())

    if "language" in combined_df.columns:
        print("\nRows by language:")
        print(combined_df["language"].value_counts())


if __name__ == "__main__":
    max_commits_input = input("Enter max commits per new repo, example 300: ").strip()
    max_rows_input = input("Enter max rows per new repo, example 500: ").strip()

    max_commits = int(max_commits_input) if max_commits_input else 300
    max_rows_per_repo = int(max_rows_input) if max_rows_input else 500

    append_new_repositories(max_commits, max_rows_per_repo)
