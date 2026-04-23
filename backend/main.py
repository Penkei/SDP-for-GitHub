from urllib.parse import urlparse

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GITHUB_API_URL = "https://api.github.com"


class RepoRequest(BaseModel):
    repoUrl: str
    pat: str


class CommitRequest(BaseModel):
    repoUrl: str
    pat: str
    branch: str
    page: int = 1
    per_page: int = 20


class CommitShaRequest(BaseModel):
    repoUrl: str
    pat: str
    sha: str


def parse_repo_url(repo_url: str):
    try:
        parsed = urlparse(repo_url)

        if "github.com" not in parsed.netloc:
            raise ValueError("Only GitHub repository URLs are supported.")

        path_parts = [part for part in parsed.path.split("/") if part]

        if len(path_parts) < 2:
            raise ValueError("Invalid GitHub repository URL.")

        owner = path_parts[0]
        repo = path_parts[1].replace(".git", "")

        return owner, repo
    except Exception:
        raise ValueError("Invalid repository URL format.")


def get_headers(pat: str):
    return {
        "Authorization": f"Bearer {pat}",
        "Accept": "application/vnd.github+json"
    }


@app.get("/")
def root():
    return {"message": "GitHub backend API is running."}


@app.post("/api/repository/branches")
def get_repository_branches(request: RepoRequest):
    try:
        owner, repo = parse_repo_url(request.repoUrl)

        response = requests.get(
            f"{GITHUB_API_URL}/repos/{owner}/{repo}/branches",
            headers=get_headers(request.pat)
        )
        response.raise_for_status()

        branches_data = response.json()
        branches = [{"name": branch["name"]} for branch in branches_data]

        return {
            "success": True,
            "data": {
                "owner": owner,
                "repo": repo,
                "branches": branches
            }
        }

    except requests.HTTPError as e:
        message = "Failed to fetch branches."
        if e.response is not None:
            try:
                message = e.response.json().get("message", message)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=message)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/repository/commits")
def get_repository_commits(request: CommitRequest):
    try:
        owner, repo = parse_repo_url(request.repoUrl)

        response = requests.get(
            f"{GITHUB_API_URL}/repos/{owner}/{repo}/commits",
            headers=get_headers(request.pat),
            params={
                "sha": request.branch,
                "per_page": request.per_page,
                "page": request.page
            }
        )
        response.raise_for_status()

        commits_data = response.json()

        commits = [
            {
                "sha": commit["sha"],
                "message": commit["commit"]["message"],
                "author": commit["commit"]["author"]["name"] if commit["commit"]["author"] else "Unknown",
                "date": commit["commit"]["author"]["date"] if commit["commit"]["author"] else "Unknown"
            }
            for commit in commits_data
        ]

        return {
            "success": True,
            "data": {
                "owner": owner,
                "repo": repo,
                "branch": request.branch,
                "page": request.page,
                "per_page": request.per_page,
                "commits": commits
            }
        }

    except requests.HTTPError as e:
        message = "Failed to fetch commits."
        if e.response is not None:
            try:
                message = e.response.json().get("message", message)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=message)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/repository/commit-by-sha")
def get_commit_by_sha(request: CommitShaRequest):
    try:
        owner, repo = parse_repo_url(request.repoUrl)
        sha = request.sha.strip()

        response = requests.get(
            f"{GITHUB_API_URL}/repos/{owner}/{repo}/commits/{sha}",
            headers=get_headers(request.pat)
        )
        response.raise_for_status()

        commit = response.json()

        commit_data = {
            "sha": commit["sha"],
            "message": commit["commit"]["message"],
            "author": commit["commit"]["author"]["name"] if commit["commit"]["author"] else "Unknown",
            "date": commit["commit"]["author"]["date"] if commit["commit"]["author"] else "Unknown"
        }

        return {
            "success": True,
            "data": commit_data
        }

    except requests.HTTPError as e:
        message = "Failed to find commit SHA."
        status_code = 500

        if e.response is not None:
            status_code = e.response.status_code
            try:
                message = e.response.json().get("message", message)
            except Exception:
                pass

        if status_code == 404:
            raise HTTPException(status_code=404, detail="Commit SHA not found in this repository.")

        raise HTTPException(status_code=500, detail=message)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))