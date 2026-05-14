import pandas as pd
import os


prediction_path = "results/prediction_with_shap_base.csv"
shap_path = "results/shap_prediction_explanation.csv"

prediction_df = pd.read_csv(prediction_path)
shap_df = pd.read_csv(shap_path)


def risk_level(probability):
    if probability >= 0.7:
        return "High"
    elif probability >= 0.4:
        return "Medium"
    else:
        return "Low"


def recommendation(label, risk):
    if label == "Defective" or risk == "High":
        return "Review immediately"
    elif risk == "Medium":
        return "Review if time permits"
    else:
        return "Low priority"


# =========================
# 1. Create SHAP summary
# =========================

shap_summary = (
    shap_df
    .groupby("file_path")
    .apply(
        lambda group: "; ".join(
            [
                f"{row['feature']}={row['feature_value']} ({row['impact_direction']})"
                for _, row in group.iterrows()
            ]
        )
    )
    .reset_index(name="top_contributing_metrics")
)


# =========================
# 2. Merge prediction + explanation
# =========================

final_df = prediction_df.merge(
    shap_summary,
    on="file_path",
    how="left"
)

final_df["risk_level"] = final_df["defect_risk_probability"].apply(risk_level)

final_df["recommendation"] = final_df.apply(
    lambda row: recommendation(row["prediction_label"], row["risk_level"]),
    axis=1
)


# =========================
# 3. Keep frontend-friendly columns
# =========================

output_columns = [
    "file_path",
    "prediction_label",
    "defect_risk_probability",
    "risk_level",
    "recommendation",
    "top_contributing_metrics"
]

final_df = final_df[output_columns]


# =========================
# 4. Save final report
# =========================

os.makedirs("results", exist_ok=True)

output_path = "results/final_prediction_report.csv"
final_df.to_csv(output_path, index=False)

print("Final prediction report generated.")
print(f"Saved to: {output_path}")

print("\nPreview:")
print(final_df.head(10))