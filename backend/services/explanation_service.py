import shap
import pandas as pd
from services.feature_transform_service import transform_model_features


class ExplanationService:
    DOMINANT_CONTRIBUTION_RATIO = 0.6
    PROCESS_FEATURES = {
        "file_change_count",
        "file_bug_fix_count",
        "recent_file_change_count",
        "days_since_last_change",
        "last_change_lines_added",
        "last_change_lines_deleted",
        "last_change_churn",
        "last_change_file_count",
        "author_file_change_count",
    }

    def __init__(self, model, feature_names, feature_transform_stats=None):
        self.model = model
        self.feature_names = feature_names
        self.feature_transform_stats = feature_transform_stats or {}
        try:
            self.explainer = shap.TreeExplainer(self.model)
            self.explainer_type = "tree"
        except Exception:
            self.explainer = None
            self.explainer_type = "fallback"

    def _get_feature_meaning(self, feature: str) -> str:
        meanings = {
            "rfc": "Method interaction complexity",
            "comparisonsQty": "Number of conditional checks",
            "nosi": "Static method usage",
            "lcom": "Class cohesion complexity",
            "totalMethods": "Number of methods",
            "loc": "File size",
            "cbo": "Dependency between classes",
            "wmc": "Overall method complexity",
            "returnQty": "Number of return paths",
            "dit": "Inheritance depth",
            "file_change_count": "Historical file change frequency",
            "file_bug_fix_count": "Previous bug-fix activity for this file",
            "recent_file_change_count": "Recent file change activity",
            "days_since_last_change": "Time since the file was last changed",
            "last_change_lines_added": "Lines added in the previous file change",
            "last_change_lines_deleted": "Lines deleted in the previous file change",
            "last_change_churn": "Code churn in the previous file change",
            "last_change_file_count": "Files changed together in the previous commit",
            "author_file_change_count": "Selected commit author's prior changes to this file"
        }

        return meanings.get(feature, feature)
    
    def explain(self, prediction_df: pd.DataFrame) -> pd.DataFrame:
        if prediction_df.empty:
            return prediction_df

        X = transform_model_features(
            prediction_df[self.feature_names],
            self.feature_transform_stats
        )

        if self.explainer_type == "tree":
            shap_values = self.explainer.shap_values(X)

            if isinstance(shap_values, list):
                shap_class_1 = shap_values[1]
            else:
                shap_class_1 = shap_values[:, :, 1] if len(shap_values.shape) == 3 else shap_values
        else:
            fallback_explainer = shap.Explainer(self.model.predict_proba, X)
            shap_values = fallback_explainer(X)
            shap_class_1 = (
                shap_values.values[:, :, 1]
                if len(shap_values.values.shape) == 3
                else shap_values.values
            )

        explanation_summaries = []
        confidence_warnings = []

        for i in range(len(X)):
            feature_contributions = pd.DataFrame({
                "feature": self.feature_names,
                "feature_value": X.iloc[i].values,
                "shap_value": shap_class_1[i]
            })

            feature_contributions["absolute_impact"] = feature_contributions["shap_value"].abs()

            top_features = feature_contributions.sort_values(
                by="absolute_impact",
                ascending=False
            ).head(5)
            top_impact_sum = top_features["absolute_impact"].sum()
            strongest_feature = top_features.iloc[0]
            strongest_feature_name = strongest_feature["feature"]
            strongest_ratio = (
                strongest_feature["absolute_impact"] / top_impact_sum
                if top_impact_sum > 0
                else 0
            )

            summary_points = []

            for _, row in top_features.iterrows():
                feature = row["feature"]
                value = prediction_df.iloc[i][feature]
                direction = row["shap_value"]

                meaning = self._get_feature_meaning(feature)

                if direction > 0:
                    summary_points.append(
                        f"{meaning} ({feature}={value}) pushed the model score higher for this file"
                    )
                else:
                    summary_points.append(
                        f"{meaning} ({feature}={value}) pushed the model score lower for this file"
                    )

            summary = ". ".join(summary_points) + "."

            explanation_summaries.append(summary)
            confidence_warnings.append(
                self._build_confidence_warning(
                    strongest_feature_name,
                    strongest_ratio
                )
            )

        prediction_df["top_contributing_metrics"] = explanation_summaries
        prediction_df["confidence_warning"] = confidence_warnings

        return prediction_df

    def _build_confidence_warning(
        self,
        strongest_feature: str,
        strongest_ratio: float
    ) -> str:
        if strongest_ratio < self.DOMINANT_CONTRIBUTION_RATIO:
            return ""

        feature_meaning = self._get_feature_meaning(strongest_feature)
        contribution_percent = round(strongest_ratio * 100)

        if strongest_feature in self.PROCESS_FEATURES:
            return (
                f"Confidence note: {contribution_percent}% of the top explanation impact "
                f"comes from one commit-history signal ({feature_meaning}). "
                "Use this as a review hint and also inspect the source code metrics before deciding."
            )

        return (
            f"Confidence note: {contribution_percent}% of the top explanation impact "
            f"comes from one metric ({feature_meaning}). "
            "The prediction may be sensitive to this single signal, so review the file context as well."
        )
