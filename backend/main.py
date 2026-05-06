from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models.request_models import PredictionRequest, CommitListRequest, GitRefListRequest
from services.defect_prediction_pipeline import DefectPredictionPipeline


app = FastAPI(
    title="SDP for GitHub Backend",
    description="Backend API for GitHub-based software defect prediction",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = DefectPredictionPipeline()


@app.get("/")
def root():
    return {
        "message": "SDP for GitHub Backend is running"
    }


@app.post("/predict")
def predict_defect(request: PredictionRequest):
    try:
        result = pipeline.run(
            repo_url=request.repo_url,
            commit_sha=request.commit_sha
        )

        return {
            "repo_url": request.repo_url,
            "commit_sha": request.commit_sha,
            "total_files_scanned": len(result),
            "results": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/commits")
def get_commits(request: CommitListRequest):
    try:
        commits = pipeline.github_service.get_commit_list(
            repo_url=request.repo_url,
            git_ref=request.git_ref,
            max_commits=request.max_commits,
            skip=request.skip
        )

        return {
            "repo_url": request.repo_url,
            "git_ref": request.git_ref,
            "skip": request.skip,
            "max_commits": request.max_commits,
            "total_commits": len(commits),
            "commits": commits
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/branches")
def get_branches(request: GitRefListRequest):
    try:
        branches = pipeline.github_service.get_branch_list(
            repo_url=request.repo_url
        )

        return {
            "repo_url": request.repo_url,
            "total_branches": len(branches),
            "branches": branches
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tags")
def get_tags(request: GitRefListRequest):
    try:
        tags = pipeline.github_service.get_tag_list(
            repo_url=request.repo_url
        )

        return {
            "repo_url": request.repo_url,
            "total_tags": len(tags),
            "tags": tags
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))