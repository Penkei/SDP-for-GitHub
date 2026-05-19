from pydantic import BaseModel
from pydantic import validator
from typing import List, Optional
from urllib.parse import urlparse


def normalize_github_repo_url(repo_url: str) -> str:
    cleaned_url = repo_url.strip()
    parsed_url = urlparse(cleaned_url)

    if parsed_url.scheme not in {"http", "https"}:
        raise ValueError("Repository URL must start with http:// or https://.")

    if parsed_url.netloc.lower() != "github.com":
        raise ValueError("Only github.com repository URLs are supported.")

    path_parts = [part for part in parsed_url.path.strip("/").split("/") if part]

    if len(path_parts) != 2:
        raise ValueError("Repository URL must use the format https://github.com/owner/repository.")

    owner, repo = path_parts

    if not owner or not repo:
        raise ValueError("Repository URL must include both owner and repository name.")

    repo = repo.removesuffix(".git")

    if not repo:
        raise ValueError("Repository name cannot be empty.")

    return f"https://github.com/{owner}/{repo}.git"


class GitHubRepoRequest(BaseModel):
    repo_url: str

    @validator("repo_url")
    def validate_repo_url(cls, value: str) -> str:
        return normalize_github_repo_url(value)


class PredictionRequest(GitHubRepoRequest):
    commit_sha: str
<<<<<<< HEAD
=======
    prediction_threshold: Optional[float] = None

    @validator("prediction_threshold")
    def validate_prediction_threshold(cls, value: Optional[float]) -> Optional[float]:
        if value is None:
            return value

        if value < 0.05 or value > 0.95:
            raise ValueError("Prediction threshold must be between 0.05 and 0.95.")

        return value
>>>>>>> Refinement


class CommitListRequest(GitHubRepoRequest):
    git_ref: str
    max_commits: int = 20
    skip: int = 0


class GitRefListRequest(GitHubRepoRequest):
    pass


class PredictionResultForExport(BaseModel):
    file_path: str
    language: Optional[str] = ""
    prediction_label: str
    defect_risk_probability: float
    risk_level: str
    recommendation: str
<<<<<<< HEAD
=======
    file_change_count: Optional[int] = 0
    file_bug_fix_count: Optional[int] = 0
    recent_file_change_count: Optional[int] = 0
    days_since_last_change: Optional[int] = 0
    last_change_churn: Optional[int] = 0
    author_file_change_count: Optional[int] = 0
>>>>>>> Refinement
    top_contributing_metrics: str
    readable_explanation: Optional[str] = ""


class ExportReportRequest(GitHubRepoRequest):
    commit_sha: str
<<<<<<< HEAD
=======
    prediction_threshold: Optional[float] = None
>>>>>>> Refinement
    total_files_scanned: int
    results: List[PredictionResultForExport]
