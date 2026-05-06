from pydantic import BaseModel


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