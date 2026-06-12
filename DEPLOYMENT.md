# Deployment Guide

This guide explains how to deploy SDP for GitHub as a real public demo application.

The frontend can run on Vercel because it is a static React and Vite application. The backend must run on a server platform such as Render because it needs Python, Git, machine learning packages, model files, temporary clone storage, and SQLite history storage.

## Recommended Architecture

| Part | Platform | Reason |
| --- | --- | --- |
| Frontend | Vercel | Hosts the built React application and serves it through HTTPS. |
| Backend | Render | Runs FastAPI with Python, Git, ML dependencies, temp repository cloning, and persistent SQLite storage. |
| Prediction History | Render persistent disk | Stores the shared demo SQLite database outside the container filesystem. |

## Backend Deployment On Render

1. Push the repository to GitHub.
2. Create a new Render Web Service.
3. Choose Docker as the environment.
4. Use the repository root as the Docker build context.
5. Confirm the health check path is `/health`.
6. Add a persistent disk:

```text
Mount path: /var/data
Size: 1 GB
```

7. Add these environment variables:

```text
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app
ALLOW_LOCAL_CACHE_MODE=false
MAX_SOURCE_FILES_PER_RUN=500
SDP_TEMP_REPO_DIR=/tmp/sdp_github_temp_repos
PREDICTION_HISTORY_DB_PATH=/var/data/prediction_history.db
```

8. Deploy the backend.
9. Open this URL after deployment:

```text
https://your-render-backend.onrender.com/health
```

The response should show `status` as `ok` when all required model files are available.

## Frontend Deployment On Vercel

1. Create a new Vercel project from the same GitHub repository.
2. Set the root directory to:

```text
frontend
```

3. Use the default Vite build command:

```text
npm run build
```

4. Use this output directory:

```text
dist
```

5. Add these environment variables:

```text
VITE_API_BASE_URL=https://your-render-backend.onrender.com
VITE_ENABLE_LOCAL_CACHE_MODE=false
```

6. Deploy the frontend.
7. Update the Render `ALLOWED_ORIGINS` value with the final Vercel URL.
8. Redeploy the backend after changing `ALLOWED_ORIGINS`.

## Public Demo Safety Settings

Use these settings for a public FYP demo:

| Setting | Recommended value | Purpose |
| --- | --- | --- |
| `ALLOW_LOCAL_CACHE_MODE` | `false` | Prevents reusable repository mirror caches on the server. |
| `MAX_SOURCE_FILES_PER_RUN` | `500` | Prevents very large repositories from overloading the demo server. |
| `ALLOWED_ORIGINS` | Vercel URL only | Prevents unrelated websites from calling the backend in browsers. |
| `PREDICTION_HISTORY_DB_PATH` | `/var/data/prediction_history.db` | Keeps SQLite history on persistent disk. |

## Personal Access Token Handling

The deployed app asks users for a GitHub Personal Access Token so GitHub API requests are less likely to hit rate limits. The token is sent to the backend for the current request only.

The backend should not save the token in SQLite history, API responses, or error messages. Private repository prediction is not part of this deployment scope.

## Deployment Smoke Test

After deployment, test these actions:

1. Open the Vercel frontend.
2. Enter a public GitHub repository URL.
3. Enter a GitHub Personal Access Token.
4. Load branches.
5. Load commits.
6. Select a commit.
7. Run prediction.
8. Confirm the progress bar completes.
9. Open Prediction History and confirm the completed run is saved.
10. Export CSV and PDF from the result page.
11. Open the backend `/health` endpoint.

## Troubleshooting

| Problem | Likely cause | Fix |
| --- | --- | --- |
| Frontend cannot reach backend | Wrong `VITE_API_BASE_URL` | Check the deployed Render URL and redeploy Vercel. |
| Browser CORS error | Wrong `ALLOWED_ORIGINS` | Put the exact Vercel URL in Render and redeploy backend. |
| `/health` is degraded | Missing model artifacts | Confirm `ml_workspace/models` is included in the deployed repository. |
| Prediction history disappears | No persistent disk | Add a Render disk and set `PREDICTION_HISTORY_DB_PATH`. |
| Large repo takes too long | Demo file limit or server size | Use a smaller repository or lower `MAX_SOURCE_FILES_PER_RUN`. |