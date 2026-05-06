import pandas as pd

df = pd.read_csv("data/github_defect_dataset.csv")

print("Dataset shape:", df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nLabel distribution:")
print(df["defect"].value_counts())

print("\nMissing values:")
print(df.isnull().sum())

print("\nSample rows:")
print(df[[
    "commit_sha",
    "file_path",
    "commit_message",
    "defect"
]].head(10))