import pandas as pd


class ReportService:

    def generate(self, prediction_df: pd.DataFrame) -> list:
        if prediction_df.empty:
            return []

        prediction_df["risk_level"] = prediction_df["defect_risk_probability"].apply(
            self._get_risk_level
        )

        prediction_df["recommendation"] = prediction_df.apply(
            lambda row: self._get_recommendation(
                row["prediction_label"],
                row["risk_level"]
            ),
            axis=1
        )

        output_columns = [
            "file_path",
            "prediction_label",
            "defect_risk_probability",
            "risk_level",
            "recommendation",
            "top_contributing_metrics"
        ]

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

    def _get_recommendation(self, label: str, risk: str) -> str:
        if label == "Defective" or risk == "High":
            return "Review immediately"
        elif risk == "Medium":
            return "Review if time permits"
        else:
            return "Low priority"