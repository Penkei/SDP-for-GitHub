import pandas as pd
import joblib
import shap
import os


# =========================
# 1. Load Model and Features
# =========================

model = joblib.load("models/github_defect_prediction_model.pkl")
feature_names = joblib.load("models/github_model_features.pkl")


# =========================
# 2. Load Prediction Input
# =========================

input_path = "data/prediction_input.csv"
df = pd.read_csv(input_path)

X = df[feature_names]


# =========================
# 3. Predict
# =========================

df["defect_prediction"] = model.predict(X)
df["defect_risk_probability"] = model.predict_proba(X)[:, 1]

df["prediction_label"] = df["defect_prediction"].map({
    0: "Non-defective",
    1: "Defective"
})


# =========================
# 4. SHAP Explanation
# =========================

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X)

# For binary classification, use class 1 explanation
if isinstance(shap_values, list):
    shap_class_1 = shap_values[1]
else:
    shap_class_1 = shap_values[:, :, 1] if len(shap_values.shape) == 3 else shap_values


# =========================
# 5. Extract Top Contributing Features Per File
# =========================

explanation_rows = []

for i in range(len(X)):
    file_path = df.loc[i, "file_path"] if "file_path" in df.columns else f"file_{i}"

    feature_contributions = pd.DataFrame({
        "feature": feature_names,
        "feature_value": X.iloc[i].values,
        "shap_value": shap_class_1[i]
    })

    feature_contributions["absolute_impact"] = feature_contributions["shap_value"].abs()

    top_features = feature_contributions.sort_values(
        by="absolute_impact",
        ascending=False
    ).head(5)

    for _, row in top_features.iterrows():
        explanation_rows.append({
            "file_path": file_path,
            "prediction_label": df.loc[i, "prediction_label"],
            "defect_risk_probability": df.loc[i, "defect_risk_probability"],
            "feature": row["feature"],
            "feature_value": row["feature_value"],
            "shap_value": row["shap_value"],
            "impact_direction": "increase_defect_risk" if row["shap_value"] > 0 else "decrease_defect_risk"
        })


# =========================
# 6. Save Explanation Result
# =========================

os.makedirs("results", exist_ok=True)

explanation_df = pd.DataFrame(explanation_rows)
explanation_df.to_csv("results/shap_prediction_explanation.csv", index=False)

df.to_csv("results/prediction_with_shap_base.csv", index=False)

print("SHAP explanation completed.")
print("Saved to: results/shap_prediction_explanation.csv")
print("Saved prediction base to: results/prediction_with_shap_base.csv")

print("\nPreview:")
print(explanation_df.head(15))