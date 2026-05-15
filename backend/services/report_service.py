import pandas as pd

from services.readable_explanation_service import ReadableExplanationService


class ReportService:

    def __init__(self):
        self.readable_explanation_service = ReadableExplanationService()

    def generate(self, prediction_df: pd.DataFrame) -> list:
        if prediction_df.empty:
            return []

        prediction_df["risk_level"] = prediction_df["defect_risk_probability"].apply(
            self._get_risk_level
        )

        prediction_df["recommendation"] = prediction_df.apply(
            lambda row: self._get_recommendation(
                row["prediction_label"],
                row["risk_level"],
                row["defect_risk_probability"]
            ),
            axis=1
        )

        prediction_df["readable_explanation"] = prediction_df.apply(
            lambda row: self.readable_explanation_service.generate(
                row["top_contributing_metrics"],
                row["risk_level"],
                row["defect_risk_probability"]
            ),
            axis=1
        )

        output_columns = [
            "file_path",
            "language",
            "prediction_label",
            "defect_risk_probability",
            "risk_level",
            "recommendation",
            "file_change_count",
            "file_bug_fix_count",
            "recent_file_change_count",
            "days_since_last_change",
            "last_change_churn",
            "author_file_change_count",
            "top_contributing_metrics",
            "readable_explanation"
        ]

        for column in output_columns:
            if column not in prediction_df.columns:
                prediction_df[column] = ""

        result_df = prediction_df[output_columns].copy()

        result_df["defect_risk_probability"] = result_df[
            "defect_risk_probability"
        ].round(4)

        return result_df.to_dict(orient="records")

    def _get_risk_level(self, probability: float) -> str:
        if probability >= 0.7:
            return "High"
        elif probability >= 0.4:
            return "Medium"
        else:
            return "Low"

    def _get_recommendation(self, label: str, risk: str, probability: float) -> str:
        if risk == "High" or label == "Defective":
            return "Review immediately before release"

        if risk == "Medium":
            return "Review key logic when time permits"

        return "Low priority, monitor if modified later"
