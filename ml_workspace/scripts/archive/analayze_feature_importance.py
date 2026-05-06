import pandas as pd

df = pd.read_csv("results/feature_importance.csv")

print("Top 10 Important Features:")
print(df.head(10))

df.head(10).to_csv("results/top_10_features.csv", index=False)

print("\nSaved top 10 features to results/top_10_features.csv")