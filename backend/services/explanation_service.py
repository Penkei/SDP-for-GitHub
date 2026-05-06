import shap
import pandas as pd


class ExplanationService:
    def __init__(self, model, feature_names):
        self.model = model
        self.feature_names = feature_names
        self.explainer = shap.TreeExplainer(self.model)

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

            summary = "; ".join([
                f"{row['feature']}={row['feature_value']} "
                f"({'increase defect risk' if row['shap_value'] > 0 else 'decrease defect risk'})"
                for _, row in top_features.iterrows()
            ])

            explanation_summaries.append(summary)

        prediction_df["top_contributing_metrics"] = explanation_summaries

        return prediction_df