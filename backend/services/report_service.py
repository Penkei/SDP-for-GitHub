import pandas as pd
import re

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
        prediction_df["is_potential_test_file"] = prediction_df["file_path"].apply(
            self._is_potential_test_file
        )
        prediction_df["test_file_reason"] = prediction_df["file_path"].apply(
            self._get_test_file_reason
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
            "readable_explanation",
            "confidence_warning",
            "is_potential_test_file",
            "test_file_reason"
        ]

        for column in output_columns:
            if column not in prediction_df.columns:
                prediction_df[column] = ""

        result_df = prediction_df[output_columns].copy()

        result_df["defect_risk_probability"] = result_df[
            "defect_risk_probability"
        ].round(4)
        result_df["is_potential_test_file"] = result_df[
            "is_potential_test_file"
        ].apply(lambda value: bool(value))

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

    def _is_potential_test_file(self, file_path: str) -> bool:
        return bool(self._get_test_file_reason(file_path))

    def _get_test_file_reason(self, file_path: str) -> str:
        normalized_path = str(file_path or "").replace("\\", "/").lower()
        path_parts = [part for part in normalized_path.split("/") if part]
        file_name = path_parts[-1] if path_parts else normalized_path

        test_directories = {
            "test",
            "tests",
            "__tests__",
            "spec",
            "specs",
            "testing",
        }

        for part in path_parts[:-1]:
            if part in test_directories:
                return f"Path contains a common test folder: {part}"

        filename_patterns = [
            (r"(^|[_\-.])test[_\-.]", "Filename contains a test prefix"),
            (r"[_\-.]test\.", "Filename contains .test pattern"),
            (r"[_\-.]spec\.", "Filename contains .spec pattern"),
            (r"test\.(py|js|jsx|ts|tsx|java|cpp|cc|cxx|h|hpp)$", "Filename ends with a test pattern"),
            (r"spec\.(py|js|jsx|ts|tsx|java|cpp|cc|cxx|h|hpp)$", "Filename ends with a spec pattern"),
            (r"test(case)?\.(py|cpp|cc|cxx|h|hpp)$", "Filename uses a common test file name"),
            (r".+test\.(java|cpp|cc|cxx|h|hpp)$", "Filename ends with Test"),
            (r".+tests\.(py|cpp|cc|cxx|h|hpp)$", "Filename ends with tests"),
        ]

        for pattern, reason in filename_patterns:
            if re.search(pattern, file_name):
                return reason

        return ""
