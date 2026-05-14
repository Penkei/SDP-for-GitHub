import os
import pandas as pd
import joblib

from extract_java_metrics import scan_java_project


# =========================
# 1. Paths
# =========================

PROJECT_PATH = "temp_repo"
MODEL_PATH = "models/github_defect_prediction_model.pkl"
FEATURES_PATH = "models/github_model_features.pkl"
OUTPUT_PATH = "results/prediction_result.csv"


# =========================
# 2. Load Model
# =========================

model = joblib.load(MODEL_PATH)
feature_names = joblib.load(FEATURES_PATH)


# =========================
# 3. Extract Metrics
# =========================

df = scan_java_project(PROJECT_PATH)

if df.empty:
    print("No Java files found.")
    exit()

print("Metric extraction completed.")
print("Files scanned:", len(df))


# =========================
# 4. Validate Features
# =========================

missing_features = [feature for feature in feature_names if feature not in df.columns]

if missing_features:
    raise ValueError(f"Missing required features: {missing_features}")


# =========================
# 5. Predict
# =========================

X = df[feature_names]

df["defect_prediction"] = model.predict(X)
df["defect_risk_probability"] = model.predict_proba(X)[:, 1]

df["prediction_label"] = df["defect_prediction"].map({
    0: "Non-defective",
    1: "Defective"
})

df["risk_level"] = pd.cut(
    df["defect_risk_probability"],
    bins=[0, 0.4, 0.7, 1.0],
    labels=["Low", "Medium", "High"],
    include_lowest=True
)


def get_recommendation(row):
    if row["risk_level"] == "High":
        return "Review immediately"
    elif row["risk_level"] == "Medium":
        return "Review if time permits"
    else:
        return "Low priority"


df["recommendation"] = df.apply(get_recommendation, axis=1)


# =========================
# 6. Save Result
# =========================

os.makedirs("results", exist_ok=True)

df.to_csv(OUTPUT_PATH, index=False)

print("\nPrediction completed.")
print(f"Saved result to: {OUTPUT_PATH}")

print("\nPrediction Summary:")
print(df[[
    "file_path",
    "prediction_label",
    "defect_risk_probability",
    "risk_level",
    "recommendation"
]])