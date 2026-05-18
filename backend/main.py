import csv
import json
import os
from io import BytesIO, StringIO

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from models.request_models import (
    PredictionRequest,
    CommitListRequest,
    GitRefListRequest,
    ExportReportRequest,
)
from services.defect_prediction_pipeline import DefectPredictionPipeline
from services.prediction_job_service import PredictionJobService
from services.prediction_history_service import PredictionHistoryService


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

prediction_history = PredictionHistoryService()
pipeline = DefectPredictionPipeline()
prediction_jobs = PredictionJobService(pipeline, prediction_history)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
ML_WORKSPACE_DIR = os.path.join(PROJECT_DIR, "ml_workspace")


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
            commit_sha=request.commit_sha,
            prediction_threshold=request.prediction_threshold
        )

        response = {
            "repo_url": request.repo_url,
            "commit_sha": request.commit_sha,
            "prediction_threshold": _effective_prediction_threshold(
                request.prediction_threshold
            ),
            "total_files_scanned": len(result),
            "results": result
        }

        prediction_history.save_prediction(response)
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/prediction-jobs")
def start_prediction_job(request: PredictionRequest):
    try:
        return prediction_jobs.start_job(
            repo_url=request.repo_url,
            commit_sha=request.commit_sha,
            prediction_threshold=request.prediction_threshold
        )

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
        "Readable Explanation"
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
            result.readable_explanation
        ])

    filename = f"defect_prediction_report_{request.commit_sha[:8]}.csv"

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@app.post("/export-report/pdf")
def export_report_pdf(request: ExportReportRequest):
    pdf_bytes = _build_prediction_pdf(request)
    filename = f"defect_prediction_report_{request.commit_sha[:8]}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
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


def _build_prediction_pdf(request: ExportReportRequest) -> bytes:
    lines = []
    lines.append("SDP for GitHub - Prediction Report")
    lines.append("")
    lines.append(f"Repository: {request.repo_url}")
    lines.append(f"Commit: {request.commit_sha}")
    threshold = (
        f"{request.prediction_threshold:.2f}"
        if request.prediction_threshold is not None
        else "Model default"
    )
    lines.append(f"Prediction Threshold: {threshold}")
    lines.append(f"Exported Files: {len(request.results)}")
    lines.append("")

    for index, result in enumerate(request.results, start=1):
        probability = f"{result.defect_risk_probability * 100:.2f}%"
        lines.append(f"{index}. {result.file_path}")
        lines.append(
            f"   Language: {result.language or 'Unknown'} | "
            f"Prediction: {result.prediction_label} | "
            f"Risk: {result.risk_level} | Probability: {probability}"
        )
        lines.append(f"   Recommendation: {result.recommendation}")

        if result.readable_explanation:
            lines.append(f"   Explanation: {result.readable_explanation}")

        if result.top_contributing_metrics:
            lines.append(f"   Contributing Metrics: {result.top_contributing_metrics}")

        lines.append("")

    return _render_simple_pdf(lines)


def _render_simple_pdf(lines: list[str]) -> bytes:
    page_width = 595
    page_height = 842
    margin_left = 44
    margin_top = 52
    line_height = 14
    max_chars = 96
    max_lines_per_page = 52

    wrapped_lines = []

    for line in lines:
        wrapped_lines.extend(_wrap_pdf_line(line, max_chars))

    pages = [
        wrapped_lines[index:index + max_lines_per_page]
        for index in range(0, len(wrapped_lines), max_lines_per_page)
    ] or [[]]

    objects = []

    def add_object(content: bytes) -> int:
        objects.append(content)
        return len(objects)

    font_object_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    page_object_ids = []

    for page_index, page_lines in enumerate(pages, start=1):
        text_commands = ["BT", "/F1 10 Tf", "12 TL"]
        current_y = page_height - margin_top
        text_commands.append(f"1 0 0 1 {margin_left} {current_y} Tm")

        for line_index, line in enumerate(page_lines):
            if line_index > 0:
                text_commands.append("T*")

            if page_index == 1 and line_index == 0:
                text_commands.append("/F1 16 Tf")
                text_commands.append(f"({_escape_pdf_text(line)}) Tj")
                text_commands.append("/F1 10 Tf")
            else:
                text_commands.append(f"({_escape_pdf_text(line)}) Tj")

        text_commands.append("ET")
        stream = "\n".join(text_commands).encode("latin-1", errors="replace")
        content_object_id = add_object(
            b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\n"
            b"stream\n" + stream + b"\nendstream"
        )
        page_object_id = add_object(
            (
                f"<< /Type /Page /Parent 0 0 R /MediaBox [0 0 {page_width} {page_height}] "
                f"/Resources << /Font << /F1 {font_object_id} 0 R >> >> "
                f"/Contents {content_object_id} 0 R >>"
            ).encode("ascii")
        )
        page_object_ids.append(page_object_id)

    kids = " ".join(f"{page_id} 0 R" for page_id in page_object_ids)
    pages_object_id = add_object(
        f"<< /Type /Pages /Kids [{kids}] /Count {len(page_object_ids)} >>".encode("ascii")
    )

    for page_object_id in page_object_ids:
        objects[page_object_id - 1] = objects[page_object_id - 1].replace(
            b"/Parent 0 0 R",
            f"/Parent {pages_object_id} 0 R".encode("ascii")
        )

    catalog_object_id = add_object(
        f"<< /Type /Catalog /Pages {pages_object_id} 0 R >>".encode("ascii")
    )

    output = BytesIO()
    output.write(b"%PDF-1.4\n")
    offsets = [0]

    for object_id, content in enumerate(objects, start=1):
        offsets.append(output.tell())
        output.write(f"{object_id} 0 obj\n".encode("ascii"))
        output.write(content)
        output.write(b"\nendobj\n")

    xref_offset = output.tell()
    output.write(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.write(b"0000000000 65535 f \n")

    for offset in offsets[1:]:
        output.write(f"{offset:010d} 00000 n \n".encode("ascii"))

    output.write(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_object_id} 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF"
        ).encode("ascii")
    )

    return output.getvalue()


def _wrap_pdf_line(line: str, max_chars: int) -> list[str]:
    if not line:
        return [""]

    words = line.split()
    wrapped = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()

        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            wrapped.append(current)

        current = word

    if current:
        wrapped.append(current)

    return wrapped or [""]


def _escape_pdf_text(text: str) -> str:
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
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
