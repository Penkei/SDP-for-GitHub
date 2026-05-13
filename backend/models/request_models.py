from pydantic import BaseModel
from typing import List, Optional


class PredictionRequest(BaseModel):
    repo_url: str
    commit_sha: str


class CommitListRequest(BaseModel):
    repo_url: str
    git_ref: str
    max_commits: int = 20
    skip: int = 0


class GitRefListRequest(BaseModel):
    repo_url: str


class PredictionResultForExport(BaseModel):
    file_path: str
    language: Optional[str] = ""
    prediction_label: str
    defect_risk_probability: float
    risk_level: str
    recommendation: str
    top_contributing_metrics: str
    readable_explanation: Optional[str] = ""


class ExportReportRequest(BaseModel):
    repo_url: str
    commit_sha: str
    total_files_scanned: int
    results: List[PredictionResultForExport]
