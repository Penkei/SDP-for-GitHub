# SDP for GitHub

Software Defect Prediction for GitHub is a final year project that analyzes a
GitHub repository at a selected commit and predicts file-level defect risk using
static code metrics and a trained machine learning model.

The application has three main parts:

- `backend/` - FastAPI backend for GitHub access, metric extraction, prediction,
  progress tracking, report export, and model transparency.
- `frontend/` - React + Vite user interface.
- `ml_workspace/` - model training scripts, datasets, trained model artifacts,
  and evaluation results.

## Current Features

- Select a GitHub repository, branch/tag, and commit.
- Predict defect risk for Java, Python, and C++ source files.
- Track prediction progress by backend stage.
- View a risk dashboard with high/medium/low counts, average risk, highest-risk
  file, riskiest folder, and language breakdown.
- Search and filter prediction results by file path, language, risk level,
  prediction label, and probability range.
- Export prediction results as a CSV report.
- View model transparency details, including model comparison, feature
  importance, selected features, dataset summary, and limitations.
- Cache repository metadata and local repository mirrors to reduce repeated
  GitHub cloning.

## Requirements

- Python 3.10 or newer
- Node.js 20 or newer
- Git

## Backend Setup

From the project root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r "backend requirements.txt"
uvicorn main:app --reload
```

The backend runs at:

```text
http://127.0.0.1:8000
```

If PowerShell blocks script activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Frontend Setup

From the project root:

```powershell
cd frontend
npm install
npm run dev
```

The frontend runs at:

```text
http://127.0.0.1:5173
```

For a production build:

```powershell
npm run build
```

## How To Use

1. Start the backend.
2. Start the frontend.
3. Open the frontend URL in a browser.
4. Go to Repository Input.
5. Enter a public GitHub repository URL.
6. Load branches or tags.
7. Load commits for the selected branch/tag.
8. Select a commit and run prediction.
9. Review the progress status, risk dashboard, result table, and explanations.
10. Export the report if needed.

## Backend API Summary

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/` | Backend health message |
| `POST` | `/prediction-jobs` | Start an async prediction job |
| `GET` | `/prediction-jobs/{job_id}` | Poll job progress/result |
| `POST` | `/predict` | Run legacy synchronous prediction |
| `POST` | `/branches` | List repository branches |
| `POST` | `/tags` | List repository tags |
| `POST` | `/commits` | List commits for a branch/tag |
| `POST` | `/export-report` | Export prediction response as CSV |
| `GET` | `/model-transparency` | Return model and dataset transparency data |

## Supported Source Languages

The live extractor currently scans:

- Java: `.java`
- Python: `.py`
- C++: `.cpp`, `.cc`, `.cxx`, `.hpp`, `.h`, `.hh`

The model uses a shared feature set:

- `nosi`
- `dit`
- `cbo`
- `rfc`
- `loc`
- `comparisonsQty`
- `returnQty`
- `wmc`
- `lcom`
- `totalMethods`

Python and C++ metrics are approximated into this shared feature set. For the
best accuracy, rebuild the dataset and retrain the model with representative
repositories from all target languages.

## Model Training

Training scripts are stored in:

```text
ml_workspace/scripts/
```

Typical workflow:

```powershell
cd ml_workspace
python scripts/build_multi_repo_dataset.py
python scripts/train_github_dataset_model.py
```

Generated artifacts are saved under:

```text
ml_workspace/models/
ml_workspace/results/
```

## Cache Behavior

The backend stores temporary repository mirrors and working copies under:

```text
temp_repos/
```

This directory is ignored by Git. Metadata such as branches, tags, and commit
pages is cached in memory for a short period to reduce repeated Git operations.

## Notes And Limitations

- The project currently targets public GitHub repositories.
- Static metrics cannot capture runtime behavior, test quality, or production
  incidents.
- SHAP explanations describe model feature influence, not guaranteed root cause.
- Model quality depends on the training dataset and how closely it matches the
  analyzed repository.
