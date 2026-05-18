import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import RLock


class PredictionJobService:
    def __init__(self, pipeline, history_service=None, max_workers: int = 2):
        self.pipeline = pipeline
        self.history_service = history_service
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.jobs = {}
        self.lock = RLock()

    def start_job(
        self,
        repo_url: str,
        commit_sha: str,
        prediction_threshold: float = None,
        use_personal_access_token: bool = False,
        github_token: str = None
    ) -> dict:
        job_id = str(uuid.uuid4())
        now = self._now()

        effective_threshold = self._effective_threshold(prediction_threshold)

        with self.lock:
            self.jobs[job_id] = {
                "job_id": job_id,
                "status": "queued",
                "stage": "queued",
                "progress_percent": 0,
                "message": "Prediction job is queued",
                "repo_url": repo_url,
                "commit_sha": commit_sha,
                "prediction_threshold": effective_threshold,
                "clone_mode": "pat_temporary" if use_personal_access_token else "local_cache",
                "created_at": now,
                "updated_at": now,
                "result": None,
                "error": None,
            }

        self.executor.submit(
            self._run_job,
            job_id,
            repo_url,
            commit_sha,
            prediction_threshold,
            use_personal_access_token,
            github_token
        )

        return self.get_job(job_id)

    def get_job(self, job_id: str) -> dict:
        with self.lock:
            job = self.jobs.get(job_id)

            if not job:
                return None

            return job.copy()

    def _run_job(
        self,
        job_id: str,
        repo_url: str,
        commit_sha: str,
        prediction_threshold: float = None,
        use_personal_access_token: bool = False,
        github_token: str = None
    ):
        try:
            self._update_job(
                job_id,
                status="running",
                stage="starting",
                progress_percent=5,
                message="Starting prediction job"
            )

            def progress_callback(stage: str, percent: int, message: str):
                self._update_job(
                    job_id,
                    status="running",
                    stage=stage,
                    progress_percent=percent,
                    message=message
                )

            result = self.pipeline.run(
                repo_url=repo_url,
                commit_sha=commit_sha,
                prediction_threshold=prediction_threshold,
                use_personal_access_token=use_personal_access_token,
                github_token=github_token,
                progress_callback=progress_callback
            )

            prediction_response = {
                "repo_url": repo_url,
                "commit_sha": commit_sha,
                "prediction_threshold": self._effective_threshold(prediction_threshold),
                "clone_mode": "pat_temporary" if use_personal_access_token else "local_cache",
                "total_files_scanned": len(result),
                "results": result
            }
            history_id = None

            if self.history_service:
                history_id = self.history_service.save_prediction(prediction_response)

            self._update_job(
                job_id,
                status="completed",
                stage="completed",
                progress_percent=100,
                message="Prediction completed",
                result=prediction_response,
                history_id=history_id
            )
        except Exception as e:
            self._update_job(
                job_id,
                status="failed",
                stage="failed",
                progress_percent=100,
                message="Prediction failed",
                error=str(e)
            )

    def _update_job(self, job_id: str, **updates):
        with self.lock:
            job = self.jobs.get(job_id)

            if not job:
                return

            job.update(updates)
            job["updated_at"] = self._now()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _effective_threshold(self, prediction_threshold: float = None) -> float:
        if prediction_threshold is not None:
            return float(prediction_threshold)

        return float(self.pipeline.prediction_service.prediction_threshold)
