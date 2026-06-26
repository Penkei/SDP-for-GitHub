import os
import sys
import tempfile
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.pop("DATABASE_URL", None)

import pandas as pd
from pydantic import ValidationError

from config import settings
from models.request_models import FeedbackRequest, GitHubRepoRequest, PredictionRequest
from services.feedback_service import FeedbackService
from services.metric_extraction_service import MetricExtractionService
from services.prediction_history_service import PredictionHistoryService
from services.prediction_service import PredictionService
from services.report_service import ReportService

settings.database_url = ""


class RequestValidationTests(unittest.TestCase):
    def test_github_repository_url_is_normalized(self):
        request = GitHubRepoRequest(repo_url=" https://github.com/sclorg/s2i-python-container.git ")

        self.assertEqual(request.repo_url, "https://github.com/sclorg/s2i-python-container.git")

    def test_invalid_repository_host_is_rejected(self):
        with self.assertRaises(ValidationError):
            GitHubRepoRequest(repo_url="https://gitlab.com/example/project")

    def test_prediction_threshold_range_is_validated(self):
        valid_request = PredictionRequest(
            repo_url="https://github.com/sclorg/s2i-python-container.git",
            commit_sha="1234567890abcdef1234567890abcdef12345678",
            prediction_threshold=0.5,
        )

        self.assertEqual(valid_request.prediction_threshold, 0.5)

        with self.assertRaises(ValidationError):
            PredictionRequest(
                repo_url="https://github.com/sclorg/s2i-python-container.git",
                commit_sha="1234567890abcdef1234567890abcdef12345678",
                prediction_threshold=0.99,
            )

    def test_feedback_request_requires_rating_and_message(self):
        request = FeedbackRequest(rating=5, message="Useful application for review")

        self.assertEqual(request.message, "Useful application for review")

        with self.assertRaises(ValidationError):
            FeedbackRequest(rating=0, message="Bad rating")

        with self.assertRaises(ValidationError):
            FeedbackRequest(rating=4, message="   ")


class MetricExtractionTests(unittest.TestCase):
    def test_extracts_python_java_and_cpp_metrics(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            (project_dir / "sample.py").write_text(
                "import os\n\nclass Worker:\n    def run(self, value):\n        if value > 0:\n            return os.path.join('a', 'b')\n        return 'none'\n",
                encoding="utf-8",
            )
            (project_dir / "Sample.java").write_text(
                "import java.util.List;\npublic class Sample { private int total; public int run(int value) { if (value > 0) { return value; } return 0; } }\n",
                encoding="utf-8",
            )
            (project_dir / "sample.cpp").write_text(
                "#include <iostream>\nclass Sample { public: int run(int value) { if (value > 0) { return value; } return 0; } };\n",
                encoding="utf-8",
            )
            (project_dir / "node_modules").mkdir()
            (project_dir / "node_modules" / "ignored.py").write_text("def ignored():\n    return 1\n", encoding="utf-8")

            service = MetricExtractionService()
            metrics = service.extract_from_project(str(project_dir))

        languages = set(metrics["language"].tolist())
        paths = set(metrics["file_path"].tolist())

        self.assertEqual(languages, {"Python", "Java", "C++"})
        self.assertNotIn("node_modules/ignored.py", paths)
        self.assertTrue((metrics["loc"] > 0).all())
        self.assertTrue((metrics["totalMethods"] >= 0).all())

    def test_extracts_only_supported_target_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            (project_dir / "src").mkdir()
            (project_dir / "src" / "feature.py").write_text("def ok():\n    return True\n", encoding="utf-8")
            (project_dir / "README.md").write_text("not source", encoding="utf-8")

            service = MetricExtractionService()
            metrics = service.extract_from_project(
                str(project_dir),
                ["src/feature.py", "README.md", "../outside.py"],
            )

        self.assertEqual(metrics["file_path"].tolist(), ["src/feature.py"])
        self.assertEqual(metrics.iloc[0]["language"], "Python")


class ReportServiceTests(unittest.TestCase):
    def test_report_generates_risk_levels_and_test_file_flag(self):
        prediction_df = pd.DataFrame(
            [
                {
                    "file_path": "src/main.py",
                    "language": "Python",
                    "prediction_label": "Defective",
                    "defect_risk_probability": 0.82,
                    "top_contributing_metrics": "number of conditional checks",
                    "confidence_warning": "",
                },
                {
                    "file_path": "tests/test_main.py",
                    "language": "Python",
                    "prediction_label": "Non-defective",
                    "defect_risk_probability": 0.31,
                    "top_contributing_metrics": "file size",
                    "confidence_warning": "",
                },
            ]
        )

        report = ReportService().generate(prediction_df)

        self.assertEqual(report[0]["risk_level"], "High")
        self.assertEqual(report[0]["recommendation"], "Review immediately before release")
        self.assertFalse(report[0]["is_potential_test_file"])
        self.assertTrue(report[1]["is_potential_test_file"])
        self.assertIn("test folder", report[1]["test_file_reason"])


class PredictionServiceTests(unittest.TestCase):
    def test_trained_model_generates_probability_and_threshold_label(self):
        service = PredictionService()
        metrics = pd.DataFrame(
            [
                {
                    feature_name: 0
                    for feature_name in service.feature_names
                }
            ]
        )

        prediction = service.predict(
            metrics,
            prediction_threshold=0.5,
        )

        probability = prediction.iloc[0]["defect_risk_probability"]
        expected_label = "Defective" if probability >= 0.5 else "Non-defective"

        self.assertGreaterEqual(probability, 0)
        self.assertLessEqual(probability, 1)
        self.assertEqual(prediction.iloc[0]["prediction_threshold"], 0.5)
        self.assertEqual(
            prediction.iloc[0]["prediction_label"],
            expected_label,
        )


class FeedbackServiceTests(unittest.TestCase):
    def test_feedback_is_saved_and_listed_newest_first(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = FeedbackService(str(Path(temp_dir) / "feedback.db"))
            first = service.create_feedback("Alice", "Student", 4, "The dashboard is clear")
            second = service.create_feedback("Bob", "Developer", 5, "The feedback page works")

            feedback = service.list_feedback()

        self.assertEqual(len(feedback), 2)
        self.assertEqual(feedback[0]["id"], second["id"])
        self.assertEqual(feedback[1]["id"], first["id"])

    def test_feedback_service_rejects_invalid_input(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = FeedbackService(str(Path(temp_dir) / "feedback.db"))

            with self.assertRaises(ValueError):
                service.create_feedback(rating=6, message="Invalid rating")

            with self.assertRaises(ValueError):
                service.create_feedback(rating=5, message="   ")


class PredictionHistoryServiceTests(unittest.TestCase):
    def test_prediction_history_save_open_list_and_delete(self):
        prediction_response = {
            "repo_url": "https://github.com/sclorg/s2i-python-container.git",
            "commit_sha": "1234567890abcdef1234567890abcdef12345678",
            "prediction_threshold": 0.5,
            "total_files_scanned": 2,
            "results": [
                {
                    "file_path": "src/main.py",
                    "language": "Python",
                    "prediction_label": "Defective",
                    "defect_risk_probability": 0.8,
                    "risk_level": "High",
                    "recommendation": "Review immediately before release",
                    "top_contributing_metrics": "conditional checks",
                },
                {
                    "file_path": "src/helper.py",
                    "language": "Python",
                    "prediction_label": "Non-defective",
                    "defect_risk_probability": 0.2,
                    "risk_level": "Low",
                    "recommendation": "Low priority monitor if modified later",
                    "top_contributing_metrics": "file size",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            service = PredictionHistoryService(str(Path(temp_dir) / "history.db"))
            history_id = service.save_prediction(prediction_response)
            summaries = service.list_predictions()
            detail = service.get_prediction(history_id)
            deleted = service.delete_prediction(history_id)
            missing = service.get_prediction(history_id)

        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0]["high_risk_count"], 1)
        self.assertEqual(summaries[0]["low_risk_count"], 1)
        self.assertAlmostEqual(summaries[0]["average_risk_probability"], 0.5)
        self.assertEqual(detail["history_id"], history_id)
        self.assertEqual(len(detail["results"]), 2)
        self.assertTrue(deleted)
        self.assertIsNone(missing)


if __name__ == "__main__":
    unittest.main()

