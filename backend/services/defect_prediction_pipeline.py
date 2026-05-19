from services.github_service import GitHubService
from services.metric_extraction_service import MetricExtractionService
from services.process_metric_service import ProcessMetricService
from services.prediction_service import PredictionService
from services.explanation_service import ExplanationService
from services.report_service import ReportService


class DefectPredictionPipeline:
    def __init__(self):
        self.github_service = GitHubService()
        self.metric_service = MetricExtractionService()
        self.process_metric_service = ProcessMetricService()
        self.prediction_service = PredictionService()
        self.explanation_service = ExplanationService(
            self.prediction_service.model,
            self.prediction_service.feature_names,
            self.prediction_service.feature_transform_stats
        )
        self.report_service = ReportService()

    def run(
        self,
        repo_url: str,
        commit_sha: str,
        prediction_threshold: float = None,
        use_personal_access_token: bool = False,
        github_token: str = None,
        progress_callback=None
    ) -> list:
        repo_path = None

        try:
            self._report_progress(
                progress_callback,
                "cloning",
                15,
                "Cloning repository and checking out the selected commit"
            )
            repo_path = self.github_service.clone_and_checkout(
                repo_url,
                commit_sha,
                use_personal_access_token=use_personal_access_token,
                github_token=github_token
            )
            changed_files = self.github_service.get_changed_files(repo_path, commit_sha)
            supported_changed_files = [
                file_path for file_path in changed_files
                if self.metric_service.is_supported_source_path(file_path)
            ]

            self._report_progress(
                progress_callback,
                "extracting_metrics",
                40,
                "Extracting source code metrics from changed supported files"
                if supported_changed_files
                else "No changed supported files found; scanning a limited repository sample"
            )
            metrics_df = self.metric_service.extract_from_project(
                repo_path,
                target_files=supported_changed_files if supported_changed_files else None
            )

            if metrics_df.empty:
                self._report_progress(
                    progress_callback,
                    "completed",
                    100,
                    "No supported source files were found"
                )
                return []

            self._report_progress(
                progress_callback,
                "extracting_process_metrics",
                55,
                "Extracting commit-history process metrics for each file"
            )
            metrics_df = self.process_metric_service.enrich_with_process_metrics(
                metrics_df=metrics_df,
                repo_path=repo_path,
                commit_sha=commit_sha
            )

            self._report_progress(
                progress_callback,
                "predicting",
                72,
                "Running the trained defect prediction model"
            )
            prediction_df = self.prediction_service.predict(
                metrics_df,
                prediction_threshold=prediction_threshold
            )

            self._report_progress(
                progress_callback,
                "explaining",
                86,
                "Generating SHAP-based metric explanations"
            )
            explained_df = self.explanation_service.explain(prediction_df)

            self._report_progress(
                progress_callback,
                "generating_report",
                95,
                "Preparing prediction report"
            )
            final_result = self.report_service.generate(explained_df)

            self._report_progress(
                progress_callback,
                "completed",
                100,
                "Prediction completed"
            )
            return final_result

        finally:
            if repo_path:
                self.github_service.cleanup_repo(repo_path)

    def _report_progress(
        self,
        progress_callback,
        stage: str,
        percent: int,
        message: str
    ):
        if progress_callback:
            progress_callback(stage, percent, message)
