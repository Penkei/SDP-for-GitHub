import shap
import pandas as pd


class ExplanationService:
    def __init__(self, model, feature_names):
        self.model = model
        self.feature_names = feature_names
        self.explainer = shap.TreeExplainer(self.model)

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
            "dit": "Inheritance depth"
        }

        return meanings.get(feature, feature)
    
    def explain(self, prediction_df: pd.DataFrame) -> pd.DataFrame:
        if prediction_df.empty:
            return prediction_df

        X = prediction_df[self.feature_names]

        shap_values = self.explainer.shap_values(X)

        if isinstance(shap_values, list):
            shap_class_1 = shap_values[1]
        else:
            shap_class_1 = shap_values[:, :, 1] if len(shap_values.shape) == 3 else shap_values

        explanation_summaries = []

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

            summary_points = []

            for _, row in top_features.iterrows():
                feature = row["feature"]
                value = row["feature_value"]
                direction = row["shap_value"]

                meaning = self._get_feature_meaning(feature)

                if direction > 0:
                    summary_points.append(
                        f"{meaning} is relatively high ({feature}={value}), which may increase defect risk"
                    )
                else:
                    summary_points.append(
                        f"{meaning} appears less risky ({feature}={value}), which may reduce defect risk"
                    )

            summary = ". ".join(summary_points) + "."

            explanation_summaries.append(summary)

        prediction_df["top_contributing_metrics"] = explanation_summaries

        return prediction_df