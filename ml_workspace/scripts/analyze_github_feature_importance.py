import pandas as pd
import joblib
import os

model = joblib.load("models/github_defect_prediction_model.pkl")
feature_names = joblib.load("models/github_model_features.pkl")

if hasattr(model, "feature_importances_"):
    importances = model.feature_importances_
else:
    raise ValueError("Current model does not support feature_importances_ directly.")

df = pd.DataFrame({
    "feature": feature_names,
    "importance": importances
}).sort_values(by="importance", ascending=False)

os.makedirs("results", exist_ok=True)

df.to_csv("results/github_feature_importance.csv", index=False)
df.head(10).to_csv("results/github_top_10_features.csv", index=False)

print("GitHub-trained model feature importance:")
print(df)

print("\nSaved to:")
print("results/github_feature_importance.csv")
print("results/github_top_10_features.csv")