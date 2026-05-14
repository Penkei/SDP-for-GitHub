import pandas as pd
import joblib
import os


# =========================
# 1. Load Final Model
# =========================

model = joblib.load("models/final_baseline_model.pkl")
feature_names = joblib.load("models/final_baseline_features.pkl")


# =========================
# 2. Load Input CSV
# =========================
# This CSV should contain multiple files with extracted metrics.

input_path = "data/prediction_input_java_sample.csv"

df = pd.read_csv(input_path)


# =========================
# 3. Validate Required Features
# =========================

missing_features = [feature for feature in feature_names if feature not in df.columns]

if missing_features:
    raise ValueError(f"Missing required features: {missing_features}")


# =========================
# 4. Predict
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
# 5. Save Result
# =========================

os.makedirs("results", exist_ok=True)

output_path = "results/prediction_result.csv"
df.to_csv(output_path, index=False)

print("Batch prediction completed.")
print(f"Saved result to: {output_path}")

print("\nPreview:")
print(df.head())