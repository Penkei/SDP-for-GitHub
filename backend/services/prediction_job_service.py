import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import RLock


class PredictionJobService:
    def __init__(self, pipeline, max_workers: int = 2):
        self.pipeline = pipeline
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.jobs = {}
        self.lock = RLock()

    def start_job(self, repo_url: str, commit_sha: str) -> dict:
        job_id = str(uuid.uuid4())
        now = self._now()

        with self.lock:
            self.jobs[job_id] = {
                "job_id": job_id,
                "status": "queued",
                "stage": "queued",
                "progress_percent": 0,
                "message": "Prediction job is queued",
                "repo_url": repo_url,
                "commit_sha": commit_sha,
                "created_at": now,
                "updated_at": now,
                "result": None,
                "error": None,
            }

        self.executor.submit(self._run_job, job_id, repo_url, commit_sha)

        return self.get_job(job_id)

    def get_job(self, job_id: str) -> dict:
        with self.lock:
            job = self.jobs.get(job_id)

            if not job:
                return None

            return job.copy()

    def _run_job(self, job_id: str, repo_url: str, commit_sha: str):
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
                progress_callback=progress_callback
            )

            self._update_job(
                job_id,
                status="completed",
                stage="completed",
                progress_percent=100,
                message="Prediction completed",
                result={
                    "repo_url": repo_url,
                    "commit_sha": commit_sha,
                    "total_files_scanned": len(result),
                    "results": result
                }
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
