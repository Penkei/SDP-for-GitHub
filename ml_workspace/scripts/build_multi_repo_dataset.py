import os
import shutil
import re
import tempfile
import pandas as pd
from git import Repo

from extract_java_metrics import SUPPORTED_SOURCE_EXTENSIONS, extract_metrics_from_source


BUG_KEYWORDS = [
    "fix", "fixed", "fixes", "bug", "bugfix",
    "defect", "fault", "crash", "exception",
    "error", "failure", "broken", "incorrect"
]

NON_BUG_KEYWORDS = [
    "feature", "refactor", "docs", "style",
    "cleanup", "rename", "format", "comment",
    "update", "add", "remove", "improve"
]

EXCLUDE_PATH_KEYWORDS = [
    "/test/", "\\test\\",
    "/tests/", "\\tests\\",
    "/target/", "\\target\\",
    "/build/", "\\build\\",
    "/generated/", "\\generated\\",
    "/vendor/", "\\vendor\\",
    "/third_party/", "\\third_party\\",
    "/node_modules/", "\\node_modules\\",
    "/dist/", "\\dist\\"
]

BOT_AUTHOR_KEYWORDS = [
    "dependabot",
    "renovate",
    "github-actions",
    "pre-commit-ci"
]


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
        "merge branch", "merge pull request", "merge remote",
        "merge origin", "merge main", "merge master",
        "merged", "resolving conflicts", "resolved conflict", "conflict"
    ]
    return any(keyword in message for keyword in merge_keywords)


def is_bot_commit(commit):
    author_text = f"{commit.author.name} {commit.author.email}".lower()
    return any(keyword in author_text for keyword in BOT_AUTHOR_KEYWORDS)


def should_exclude_file(file_path):
    lower_path = file_path.lower()
    extension = os.path.splitext(lower_path)[1]

    if extension not in SUPPORTED_SOURCE_EXTENSIONS:
        return True

    for keyword in EXCLUDE_PATH_KEYWORDS:
        if keyword in lower_path:
            return True

    file_name = os.path.basename(lower_path)

    if file_name.startswith("test"):
        return True

    if file_name.endswith(("_test.py", "_test.cpp", "_test.cc", "_test.cxx")):
        return True

    return False


def safe_repo_name(repo_url):
    name = repo_url.rstrip("/").replace(".git", "").split("/")[-1]
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    return safe_name[:24]


def clone_repository(repo_url, output_dir):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    print(f"\nCloning repository: {repo_url}")
    repo = Repo.clone_from(
        repo_url,
        output_dir,
        multi_options=["--config", "core.longpaths=true"],
        allow_unsafe_options=True
    )
    repo.git.config("core.longpaths", "true")
    return repo


def get_changed_source_files(commit):
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


def build_dataset_for_repo(repo_url, max_commits=500, max_rows_per_repo=800):
    repo_name = safe_repo_name(repo_url)
    repo_dir = os.path.join(
        tempfile.gettempdir(),
        "sdpds",
        repo_name
    )

    repo = clone_repository(repo_url, repo_dir)

    rows = []
    seen_file_commits = set()

    commits = list(repo.iter_commits("--all", max_count=max_commits))

    print(f"Total commits scanned for {repo_name}: {len(commits)}")

    skipped_merge = 0
    skipped_bot = 0
    skipped_unlabelled = 0
    skipped_no_supported_source = 0
    language_counts = {}

    for index, commit in enumerate(commits, start=1):
        try:
            if len(rows) >= max_rows_per_repo:
                print(f"Reached max rows for {repo_name}: {max_rows_per_repo}")
                break

            commit_sha = commit.hexsha
            commit_message = commit.message.strip().replace("\n", " ")

            if is_merge_commit(commit) or is_merge_message(commit_message):
                skipped_merge += 1
                continue

            if is_bot_commit(commit):
                skipped_bot += 1
                continue

            bug_fix = is_bug_fix_commit(commit_message)
            non_bug = is_non_bug_commit(commit_message)

            if bug_fix:
                label = 1
            elif non_bug:
                label = 0
            else:
                skipped_unlabelled += 1
                continue

            changed_source_files = get_changed_source_files(commit)

            if not changed_source_files:
                skipped_no_supported_source += 1
                continue

            print(f"[{repo_name}] [{index}/{len(commits)}] {commit_sha[:8]} | defect={label}")

            for file_path in changed_source_files:
                try:
                    if len(rows) >= max_rows_per_repo:
                        break

                    file_commit_key = (commit_sha, file_path)

                    if file_commit_key in seen_file_commits:
                        continue

                    seen_file_commits.add(file_commit_key)

                    if label == 1 and commit.parents:
                        checkout_commit = commit.parents[0].hexsha
                    else:
                        checkout_commit = commit_sha

                    safe_checkout(repo, checkout_commit)

                    full_file_path = os.path.join(repo_dir, file_path)

                    if not os.path.exists(full_file_path):
                        continue

                    metrics = extract_metrics_from_source(full_file_path)

                    metrics["repo_name"] = repo_name
                    metrics["repo_url"] = repo_url
                    metrics["commit_sha"] = commit_sha
                    metrics["source_commit_used"] = checkout_commit
                    metrics["file_path"] = file_path
                    metrics["commit_message"] = commit_message
                    metrics["defect"] = label

                    rows.append(metrics)
                    language = metrics.get("language", "Unknown")
                    language_counts[language] = language_counts.get(language, 0) + 1

                except Exception as e:
                    print(f"Skipped file {file_path}: {e}")

        except Exception as e:
            print(f"Skipped commit {commit.hexsha[:8]}: {e}")

    print(f"\nFinished repo: {repo_name}")
    print("Rows collected:", len(rows))
    print("Skipped merge commits:", skipped_merge)
    print("Skipped bot commits:", skipped_bot)
    print("Skipped unlabelled commits:", skipped_unlabelled)
    print("Skipped commits without supported source files:", skipped_no_supported_source)
    print("Rows by language:", language_counts)

    return rows


def read_repo_list(path="data/repositories.txt"):
    with open(path, "r", encoding="utf-8") as file:
        repos = [
            line.strip()
            for line in file.readlines()
            if line.strip() and not line.strip().startswith("#")
        ]

    return repos


if __name__ == "__main__":
    max_commits_input = input("Enter max commits per repo, example 500: ").strip()
    max_rows_input = input("Enter max rows per repo, example 800: ").strip()

    if max_commits_input:
        max_commits = int(max_commits_input)
    else:
        max_commits = 500

    if max_rows_input:
        max_rows_per_repo = int(max_rows_input)
    else:
        max_rows_per_repo = 800

    repos = read_repo_list()

    all_rows = []

    for repo_url in repos:
        try:
            rows = build_dataset_for_repo(repo_url, max_commits, max_rows_per_repo)
            all_rows.extend(rows)
        except Exception as e:
            print(f"Failed repository {repo_url}: {e}")

    df = pd.DataFrame(all_rows)

    os.makedirs("data", exist_ok=True)

    output_path = "data/github_defect_dataset.csv"
    backup_path = "data/github_defect_dataset_latest_backup.csv"

    if df.empty:
        raise ValueError("No dataset rows were collected. Try increasing max commits or checking repository URLs.")

    if os.path.exists(output_path):
        shutil.copy2(output_path, backup_path)
        print(f"Previous dataset backed up to: {backup_path}")

    df = df.drop_duplicates(
        subset=["repo_url", "commit_sha", "file_path", "defect"],
        keep="first"
    )

    df.to_csv(output_path, index=False)

    print("\nCombined dataset completed.")
    print(f"Saved to: {output_path}")
    print("Dataset shape:", df.shape)

    if not df.empty:
        print("\nLabel distribution:")
        print(df["defect"].value_counts())

        print("\nRows by repository:")
        print(df["repo_name"].value_counts())

        if "language" in df.columns:
            print("\nRows by language:")
            print(df["language"].value_counts())
