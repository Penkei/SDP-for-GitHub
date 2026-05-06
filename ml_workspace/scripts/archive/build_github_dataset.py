import os
import shutil
import re
import pandas as pd
from git import Repo

from extract_java_metrics import extract_metrics_from_java


# =========================
# 1. Config
# =========================

BUG_KEYWORDS = [
    "fix", "fixed", "fixes", "bug", "bugfix",
    "defect", "fault", "crash", "exception",
    "error", "failure", "broken", "incorrect"
]

NON_BUG_KEYWORDS = [
    "feature", "refactor", "docs", "style",
    "cleanup", "rename", "format", "comment"
]

EXCLUDE_PATH_KEYWORDS = [
    "/test/",
    "\\test\\",
    "/tests/",
    "\\tests\\",
    "/target/",
    "\\target\\",
    "/build/",
    "\\build\\",
    "/generated/",
    "\\generated\\"
]


# =========================
# 2. Helper Functions
# =========================

def is_bug_fix_commit(message):
    message = message.lower()
    return any(re.search(rf"\b{re.escape(keyword)}\b", message) for keyword in BUG_KEYWORDS)


def is_non_bug_commit(message):
    message = message.lower()
    return any(re.search(rf"\b{re.escape(keyword)}\b", message) for keyword in NON_BUG_KEYWORDS)


def is_merge_commit(commit):
    return len(commit.parents) > 1


def is_merge_message(message):
    message = message.lower()

    merge_keywords = [
        "merge branch",
        "merge pull request",
        "merge remote",
        "merge origin",
        "merge main",
        "merge master",
        "merged",
        "resolving conflicts",
        "resolved conflict",
        "conflict"
    ]

    return any(keyword in message for keyword in merge_keywords)


def should_exclude_file(file_path):
    lower_path = file_path.lower()

    if not lower_path.endswith(".java"):
        return True

    for keyword in EXCLUDE_PATH_KEYWORDS:
        if keyword in lower_path:
            return True

    file_name = os.path.basename(lower_path)

    if file_name.endswith("test.java"):
        return True

    if file_name.startswith("test"):
        return True

    return False


def clone_repository(repo_url, output_dir="dataset_repo2"):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    print("Cloning repository...")
    repo = Repo.clone_from(repo_url, output_dir)
    return repo


def get_changed_java_files(commit):
    changed_files = []

    if not commit.parents:
        return changed_files

    parent = commit.parents[0]
    diffs = parent.diff(commit)

    for diff in diffs:
        file_path = diff.b_path

        if not file_path:
            continue

        if should_exclude_file(file_path):
            continue

        changed_files.append(file_path)

    return changed_files


def safe_checkout(repo, commit_sha):
    repo.git.reset("--hard")
    repo.git.clean("-fd")
    repo.git.checkout(commit_sha)


# =========================
# 3. Dataset Builder
# =========================

def build_dataset(repo_url, max_commits=300):
    repo_dir = "dataset_repo2"
    repo = clone_repository(repo_url, repo_dir)

    rows = []

    commits = list(repo.iter_commits("--all", max_count=max_commits))

    print(f"Total commits scanned: {len(commits)}")

    skipped_merge = 0
    skipped_unlabelled = 0
    skipped_no_java = 0

    for index, commit in enumerate(commits, start=1):
        try:
            commit_sha = commit.hexsha
            commit_message = commit.message.strip().replace("\n", " ")

            # Skip merge commits
            if is_merge_commit(commit) or is_merge_message(commit_message):
                skipped_merge += 1
                continue

            bug_fix = is_bug_fix_commit(commit_message)
            non_bug = is_non_bug_commit(commit_message)

            # If a commit contains both bug and non-bug words, prioritize bug-fix label
            if bug_fix:
                label = 1
            elif non_bug:
                label = 0
            else:
                skipped_unlabelled += 1
                continue

            changed_java_files = get_changed_java_files(commit)

            if not changed_java_files:
                skipped_no_java += 1
                continue

            print(f"[{index}/{len(commits)}] Processing commit: {commit_sha[:8]} | defect={label}")

            for file_path in changed_java_files:
                try:
                    # For bug-fix commit, defective version is usually before the fix
                    if label == 1 and commit.parents:
                        checkout_commit = commit.parents[0].hexsha
                    else:
                        checkout_commit = commit_sha

                    safe_checkout(repo, checkout_commit)

                    full_file_path = os.path.join(repo_dir, file_path)

                    if not os.path.exists(full_file_path):
                        continue

                    metrics = extract_metrics_from_java(full_file_path)

                    metrics["repo_url"] = repo_url
                    metrics["commit_sha"] = commit_sha
                    metrics["source_commit_used"] = checkout_commit
                    metrics["file_path"] = file_path
                    metrics["commit_message"] = commit_message
                    metrics["defect"] = label

                    rows.append(metrics)

                except Exception as e:
                    print(f"Skipped file {file_path}: {e}")

        except Exception as e:
            print(f"Skipped commit {commit.hexsha[:8]}: {e}")

    df = pd.DataFrame(rows)

    os.makedirs("data", exist_ok=True)

    output_path = "data/github_defect_dataset.csv"
    df.to_csv(output_path, index=False)

    print("\nDataset construction completed.")
    print(f"Saved to: {output_path}")
    print("Dataset shape:", df.shape)

    print("\nSkipped summary:")
    print("Skipped merge commits:", skipped_merge)
    print("Skipped unlabelled commits:", skipped_unlabelled)
    print("Skipped commits without Java files:", skipped_no_java)

    if not df.empty:
        print("\nLabel distribution:")
        print(df["defect"].value_counts())

        print("\nSample rows:")
        print(df[[
            "commit_sha",
            "file_path",
            "commit_message",
            "defect"
        ]].head(10))

    return df


# =========================
# 4. Main
# =========================

if __name__ == "__main__":
    repo_url = input("Enter GitHub repository URL: ").strip()
    max_commits_input = input("Enter max commits to scan, example 300: ").strip()

    if max_commits_input:
        max_commits = int(max_commits_input)
    else:
        max_commits = 300

    build_dataset(repo_url, max_commits)