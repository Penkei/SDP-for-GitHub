import os
import joblib
import pandas as pd


class PredictionService:
    def __init__(self):
        self.model_path = "../ml_workspace/models/github_defect_prediction_model.pkl"
        self.features_path = "../ml_workspace/models/github_model_features.pkl"
        self.threshold_path = "../ml_workspace/models/github_prediction_threshold.pkl"

        self.model = joblib.load(self.model_path)
        self.feature_names = joblib.load(self.features_path)
        self.prediction_threshold = self._load_prediction_threshold()

    def predict(self, metrics_df: pd.DataFrame) -> pd.DataFrame:
        if metrics_df.empty:
            return metrics_df

        missing_features = [
            feature for feature in self.feature_names
            if feature not in metrics_df.columns
        ]

        if missing_features:
            raise ValueError(f"Missing required features: {missing_features}")

        X = metrics_df[self.feature_names]

        metrics_df["defect_risk_probability"] = self.model.predict_proba(X)[:, 1]
        metrics_df["defect_prediction"] = (
            metrics_df["defect_risk_probability"] >= self.prediction_threshold
        ).astype(int)

        metrics_df["prediction_label"] = metrics_df["defect_prediction"].map({
            0: "Non-defective",
            1: "Defective"
        })

        return metrics_df

    def _load_prediction_threshold(self) -> float:
        if os.path.exists(self.threshold_path):
            return float(joblib.load(self.threshold_path))

        return 0.5
