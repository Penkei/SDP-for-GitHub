import pandas as pd
import joblib
import os
import numpy as np

model = joblib.load("models/github_defect_prediction_model.pkl")
feature_names = joblib.load("models/github_model_features.pkl")

estimator = model

if hasattr(model, "named_steps"):
    estimator = model.named_steps.get("classifier", model)

if hasattr(estimator, "feature_importances_"):
    importances = estimator.feature_importances_
elif hasattr(estimator, "coef_"):
    importances = np.abs(estimator.coef_[0])
else:
    raise ValueError("Current model does not expose feature importances or coefficients.")

total_importance = importances.sum()

if total_importance > 0:
    importances = importances / total_importance

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
