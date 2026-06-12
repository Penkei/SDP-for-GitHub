import csv
import json
import os
from io import StringIO

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from config import settings

from models.request_models import (
    PredictionRequest,
    CommitListRequest,
    GitRefListRequest,
    ExportReportRequest,
    FeedbackRequest,
)
from services.defect_prediction_pipeline import DefectPredictionPipeline
from services.feedback_service import FeedbackService
from services.prediction_job_service import PredictionJobService
from services.prediction_history_service import PredictionHistoryService


app = FastAPI(
    title="SDP for GitHub Backend",
    description="Backend API for GitHub-based software defect prediction",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prediction_history = PredictionHistoryService()
feedback_service = FeedbackService(prediction_history.db_path)
pipeline = DefectPredictionPipeline()
prediction_jobs = PredictionJobService(pipeline, prediction_history)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
ML_WORKSPACE_DIR = settings.ml_workspace_dir


@app.get("/")
def root():
    return {
        "message": "SDP for GitHub Backend is running"
    }


@app.get("/health")
def health_check():
    required_model_files = {
        "model": pipeline.prediction_service.model_path,
        "features": pipeline.prediction_service.features_path,
        "threshold": pipeline.prediction_service.threshold_path,
        "feature_transform_stats": pipeline.prediction_service.transform_stats_path,
    }
    model_files = {
        name: os.path.exists(path)
        for name, path in required_model_files.items()
    }

    return {
        "status": "ok" if all(model_files.values()) else "degraded",
        "model_files": model_files,
        "history_storage": prediction_history.db_path,
        "local_cache_mode_enabled": settings.allow_local_cache_mode,
        "max_source_files_per_run": settings.max_source_files_per_run,
    }


@app.post("/predict")
def predict_defect(request: PredictionRequest):
    try:
        _validate_clone_mode(request.use_personal_access_token)
        result = pipeline.run(
            repo_url=request.repo_url,
            commit_sha=request.commit_sha,
            prediction_threshold=request.prediction_threshold,
            use_personal_access_token=request.use_personal_access_token,
            github_token=request.github_token
        )

        response = {
            "repo_url": request.repo_url,
            "commit_sha": request.commit_sha,
            "prediction_threshold": _effective_prediction_threshold(
                request.prediction_threshold
            ),
            "clone_mode": "pat_temporary"
            if request.use_personal_access_token
            else "local_cache",
            "total_files_scanned": len(result),
            "results": result
        }

        prediction_history.save_prediction(response)
        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/prediction-jobs")
def start_prediction_job(request: PredictionRequest):
    try:
        _validate_clone_mode(request.use_personal_access_token)
        return prediction_jobs.start_job(
            repo_url=request.repo_url,
            commit_sha=request.commit_sha,
            prediction_threshold=request.prediction_threshold,
            use_personal_access_token=request.use_personal_access_token,
            github_token=request.github_token
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/prediction-jobs/{job_id}")
def get_prediction_job(job_id: str):
    job = prediction_jobs.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Prediction job not found")

    return job


@app.get("/prediction-history")
def list_prediction_history():
    return {
        "history": prediction_history.list_predictions()
    }


@app.get("/prediction-history/{history_id}")
def get_prediction_history_item(history_id: str):
    prediction = prediction_history.get_prediction(history_id)

    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction history item not found")

    return prediction


@app.delete("/prediction-history/{history_id}")
def delete_prediction_history_item(history_id: str):
    deleted = prediction_history.delete_prediction(history_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Prediction history item not found")

    return {
        "deleted": True,
        "history_id": history_id
    }


@app.get("/feedback")
def list_feedback():
    return {
        "feedback": feedback_service.list_feedback()
    }


@app.post("/feedback")
def create_feedback(request: FeedbackRequest):
    try:
        feedback = feedback_service.create_feedback(
            name=request.name,
            role=request.role,
            rating=request.rating,
            message=request.message
        )

        return {
            "feedback": feedback
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

@app.post("/export-report")
def export_report(request: ExportReportRequest):
    output = StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Repository URL",
        request.repo_url
    ])
    writer.writerow([
        "Commit SHA",
        request.commit_sha
    ])
    writer.writerow([
        "Prediction Threshold",
        request.prediction_threshold if request.prediction_threshold is not None else "Model default"
    ])
    writer.writerow([
        "Total Files Scanned",
        request.total_files_scanned
    ])
    writer.writerow([])

    writer.writerow([
        "File Path",
        "Language",
        "Prediction",
        "Risk Probability",
        "Risk Level",
        "Recommendation",
        "File Change Count",
        "File Bug-fix Count",
        "Recent File Change Count",
        "Days Since Last Change",
        "Previous Change Churn",
        "Author File Change Count",
        "Top Contributing Metrics",
        "Readable Explanation",
        "Confidence Warning",
        "Potential Test File",
        "Test File Reason"
    ])

    for result in request.results:
        writer.writerow([
            result.file_path,
            result.language,
            result.prediction_label,
            result.defect_risk_probability,
            result.risk_level,
            result.recommendation,
            result.file_change_count,
            result.file_bug_fix_count,
            result.recent_file_change_count,
            result.days_since_last_change,
            result.last_change_churn,
            result.author_file_change_count,
            result.top_contributing_metrics,
            result.readable_explanation,
            result.confidence_warning,
            result.is_potential_test_file,
            result.test_file_reason
        ])

    filename = f"defect_prediction_report_{request.commit_sha[:8]}.csv"

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@app.get("/model-transparency")
def get_model_transparency():
    comparison_path = os.path.join(
        ML_WORKSPACE_DIR,
        "results",
        "github_model_comparison.csv"
    )
    feature_importance_path = os.path.join(
        ML_WORKSPACE_DIR,
        "results",
        "github_feature_importance.csv"
    )
    dataset_path = os.path.join(
        ML_WORKSPACE_DIR,
        "data",
        "github_defect_dataset.csv"
    )
    metadata_path = os.path.join(
        ML_WORKSPACE_DIR,
        "results",
        "github_training_metadata.json"
    )
    confusion_matrix_path = os.path.join(
        ML_WORKSPACE_DIR,
        "results",
        "github_confusion_matrix.csv"
    )
    classification_report_path = os.path.join(
        ML_WORKSPACE_DIR,
        "results",
        "github_classification_report.txt"
    )

    model_comparison = _read_csv_records(comparison_path)
    feature_importance = _read_csv_records(feature_importance_path)
    dataset_summary = _build_dataset_summary(dataset_path)
    training_metadata = _read_json(metadata_path)
    confusion_matrix = _read_csv_records(confusion_matrix_path)
    classification_report = _read_text(classification_report_path)

    best_model = None

    if model_comparison:
        best_model = max(
            model_comparison,
            key=lambda row: float(row.get("f1", 0) or 0)
        )

    return {
        "model_name": best_model.get("model") if best_model else "Unknown",
        "selected_features": pipeline.prediction_service.feature_names,
        "model_comparison": model_comparison,
        "feature_importance": feature_importance,
        "dataset_summary": dataset_summary,
        "training_metadata": training_metadata,
        "confusion_matrix": confusion_matrix,
        "classification_report": classification_report,
        "limitations": [
            "Metrics combine static code approximations with Git commit-history process metrics, but still may not capture runtime behavior.",
            "Python and C++ support maps language-specific patterns into the existing shared feature set.",
            "Prediction quality depends on how representative the training dataset is for the analyzed repository.",
            "Generated explanations identify influential metrics, not guaranteed root causes."
        ]
    }
    
@app.post("/commits")
def get_commits(request: CommitListRequest):
    try:
        _validate_clone_mode(request.use_personal_access_token)
        commits = pipeline.github_service.get_commit_list(
            repo_url=request.repo_url,
            git_ref=request.git_ref,
            max_commits=request.max_commits,
            skip=request.skip,
            use_personal_access_token=request.use_personal_access_token,
            github_token=request.github_token
        )

        return {
            "repo_url": request.repo_url,
            "git_ref": request.git_ref,
            "skip": request.skip,
            "max_commits": request.max_commits,
            "total_commits": len(commits),
            "commits": commits
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/branches")
def get_branches(request: GitRefListRequest):
    try:
        _validate_clone_mode(request.use_personal_access_token)
        branches = pipeline.github_service.get_branch_list(
            repo_url=request.repo_url,
            use_personal_access_token=request.use_personal_access_token,
            github_token=request.github_token
        )

        return {
            "repo_url": request.repo_url,
            "total_branches": len(branches),
            "branches": branches
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tags")
def get_tags(request: GitRefListRequest):
    try:
        _validate_clone_mode(request.use_personal_access_token)
        tags = pipeline.github_service.get_tag_list(
            repo_url=request.repo_url,
            use_personal_access_token=request.use_personal_access_token,
            github_token=request.github_token
        )

        return {
            "repo_url": request.repo_url,
            "total_tags": len(tags),
            "tags": tags
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _read_csv_records(path: str) -> list:
    if not os.path.exists(path):
        return []

    return pd.read_csv(path).fillna("").to_dict(orient="records")


def _read_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def _read_text(path: str) -> str:
    if not os.path.exists(path):
        return ""

    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def _effective_prediction_threshold(prediction_threshold: float = None) -> float:
    if prediction_threshold is not None:
        return float(prediction_threshold)

    return float(pipeline.prediction_service.prediction_threshold)




def _validate_clone_mode(use_personal_access_token: bool):
    if not use_personal_access_token and not settings.allow_local_cache_mode:
        raise HTTPException(
            status_code=403,
            detail=(
                "Local cache mode is disabled on this deployment. "
                "Use Personal Token request mode instead."
            )
        )


def _build_dataset_summary(path: str) -> dict:
    if not os.path.exists(path):
        return {
            "total_rows": 0,
            "defective_rows": 0,
            "non_defective_rows": 0,
            "repositories": 0,
            "languages": []
        }

    df = pd.read_csv(path)
    defective_rows = int((df["defect"] == 1).sum()) if "defect" in df else 0
    non_defective_rows = int((df["defect"] == 0).sum()) if "defect" in df else 0
    repositories = int(df["repo_url"].nunique()) if "repo_url" in df else 0
    languages = sorted(df["language"].dropna().unique().tolist()) if "language" in df else ["Java"]

    return {
        "total_rows": int(len(df)),
        "defective_rows": defective_rows,
        "non_defective_rows": non_defective_rows,
        "repositories": repositories,
        "languages": languages
    }
