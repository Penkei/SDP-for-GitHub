import pandas as pd

df = pd.read_csv("data/github_defect_dataset.csv")

print("Dataset shape:", df.shape)

print("\nLabel distribution:")
print(df["defect"].value_counts())

print("\nRepositories:")
print(df["repo_url"].value_counts())

if "language" in df.columns:
    print("\nLanguages:")
    print(df["language"].value_counts())

    print("\nLabel distribution by language:")
    print(pd.crosstab(df["language"], df["defect"]))

print("\nAverage metrics by label:")
numeric_cols = [
    "nosi", "dit", "cbo", "rfc", "loc",
    "comparisonsQty", "returnQty", "wmc",
<<<<<<< HEAD
    "lcom", "totalMethods"
=======
    "lcom", "totalMethods",
    "file_change_count", "file_bug_fix_count",
    "recent_file_change_count", "days_since_last_change",
    "last_change_lines_added", "last_change_lines_deleted",
    "last_change_churn", "last_change_file_count",
    "author_file_change_count"
>>>>>>> Refinement
]

available_numeric_cols = [
    column for column in numeric_cols
    if column in df.columns
]

print(df.groupby("defect")[available_numeric_cols].mean())

duplicate_count = df.duplicated(
    subset=["repo_url", "commit_sha", "file_path", "defect"]
).sum()

print("\nDuplicate rows by repo/commit/file/label:", duplicate_count)

print("\nBug-fix commit samples:")
print(df[df["defect"] == 1][["commit_sha", "file_path", "commit_message"]].head(10))

print("\nNon-bug commit samples:")
print(df[df["defect"] == 0][["commit_sha", "file_path", "commit_message"]].head(10))

df.to_csv("data/github_defect_dataset_analysis.csv", index=False)
