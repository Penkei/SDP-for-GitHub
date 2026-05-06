from services.github_service import GitHubService
from services.metric_extraction_service import MetricExtractionService
from services.prediction_service import PredictionService
from services.explanation_service import ExplanationService
from services.report_service import ReportService


class DefectPredictionPipeline:
    def __init__(self):
        self.github_service = GitHubService()
        self.metric_service = MetricExtractionService()
        self.prediction_service = PredictionService()
        self.explanation_service = ExplanationService(
            self.prediction_service.model,
            self.prediction_service.feature_names
        )
        self.report_service = ReportService()

    def run(self, repo_url: str, commit_sha: str) -> list:
        repo_path = None

        try:
            repo_path = self.github_service.clone_and_checkout(repo_url, commit_sha)

            metrics_df = self.metric_service.extract_from_project(repo_path)

            if metrics_df.empty:
                return []

            prediction_df = self.prediction_service.predict(metrics_df)

            explained_df = self.explanation_service.explain(prediction_df)

            final_result = self.report_service.generate(explained_df)

            return final_result

        finally:
            if repo_path:
                self.github_service.cleanup_repo(repo_path)