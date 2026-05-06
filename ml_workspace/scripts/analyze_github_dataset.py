import pandas as pd

df = pd.read_csv("data/github_defect_dataset.csv")

print("Dataset shape:", df.shape)

print("\nLabel distribution:")
print(df["defect"].value_counts())

print("\nRepositories:")
print(df["repo_url"].value_counts())

print("\nAverage metrics by label:")
numeric_cols = [
    "nosi", "dit", "cbo", "rfc", "loc",
    "comparisonsQty", "returnQty", "wmc",
    "lcom", "totalMethods"
]

print(df.groupby("defect")[numeric_cols].mean())

print("\nBug-fix commit samples:")
print(df[df["defect"] == 1][["commit_sha", "file_path", "commit_message"]].head(10))

print("\nNon-bug commit samples:")
print(df[df["defect"] == 0][["commit_sha", "file_path", "commit_message"]].head(10))

df.to_csv("data/github_defect_dataset_analysis.csv", index=False)