import os
import joblib
import pandas as pd
from services.feature_transform_service import transform_model_features


class PredictionService:
    def __init__(self):
        self.model_path = "../ml_workspace/models/github_defect_prediction_model.pkl"
        self.features_path = "../ml_workspace/models/github_model_features.pkl"
        self.threshold_path = "../ml_workspace/models/github_prediction_threshold.pkl"
        self.transform_stats_path = "../ml_workspace/models/github_feature_transform_stats.pkl"

        self.model = joblib.load(self.model_path)
        self.feature_names = joblib.load(self.features_path)
        self.prediction_threshold = self._load_prediction_threshold()
        self.feature_transform_stats = self._load_feature_transform_stats()

    def predict(self, metrics_df: pd.DataFrame, prediction_threshold: float = None) -> pd.DataFrame:
        if metrics_df.empty:
            return metrics_df

        missing_features = [
            feature for feature in self.feature_names
            if feature not in metrics_df.columns
        ]

        if missing_features:
            raise ValueError(f"Missing required features: {missing_features}")

        X = transform_model_features(
            metrics_df[self.feature_names],
            self.feature_transform_stats
        )
        threshold = self._resolve_prediction_threshold(prediction_threshold)

        metrics_df["defect_risk_probability"] = self.model.predict_proba(X)[:, 1]
        metrics_df["defect_prediction"] = (
            metrics_df["defect_risk_probability"] >= threshold
        ).astype(int)
        metrics_df["prediction_threshold"] = threshold

        metrics_df["prediction_label"] = metrics_df["defect_prediction"].map({
            0: "Non-defective",
            1: "Defective"
        })

        return metrics_df

    def _load_prediction_threshold(self) -> float:
        if os.path.exists(self.threshold_path):
            return float(joblib.load(self.threshold_path))

        return 0.5

    def _load_feature_transform_stats(self) -> dict:
        if os.path.exists(self.transform_stats_path):
            return joblib.load(self.transform_stats_path)

        return {}

    def _resolve_prediction_threshold(self, prediction_threshold: float = None) -> float:
        if prediction_threshold is None:
            return self.prediction_threshold

        return max(0.05, min(0.95, float(prediction_threshold)))
