import axios from "axios";
import type { 
  PredictionRequest, 
  PredictionResponse,
  PredictionJobStatus,
  CommitListResponse,
  BranchListResponse,
  TagListResponse,
  ModelTransparencyResponse,
  PredictionHistoryListResponse,
  PredictionHistoryDetail,
} from "../types/prediction";


const API_BASE_URL = "http://127.0.0.1:8000";


export const getApiErrorMessage = (
  error: unknown,
  fallbackMessage: string
) => {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 404) {
      return "The requested backend resource was not found. If this happened during prediction, the backend may have restarted while the job was running.";
    }

    const detail = error.response?.data?.detail;

    if (typeof detail === "string" && detail.trim()) {
      if (
        detail.toLowerCase().includes("personal access token") ||
        detail.toLowerCase().includes("github authentication failed")
      ) {
        return detail;
      }

      return detail;
    }

    if (Array.isArray(detail) && detail.length > 0) {
      return detail
        .map((item) => item.msg || JSON.stringify(item))
        .join(" ");
    }

    if (error.message) {
      return error.message;
    }
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return fallbackMessage;
};


export const predictDefects = async (
  request: PredictionRequest
): Promise<PredictionResponse> => {
  const response = await axios.post<PredictionResponse>(
    `${API_BASE_URL}/predict`,
    request
  );

  return response.data;
};

export const startPredictionJob = async (
  request: PredictionRequest
): Promise<PredictionJobStatus> => {
  const response = await axios.post<PredictionJobStatus>(
    `${API_BASE_URL}/prediction-jobs`,
    request
  );

  return response.data;
};

export const fetchPredictionJob = async (
  jobId: string
): Promise<PredictionJobStatus> => {
  const response = await axios.get<PredictionJobStatus>(
    `${API_BASE_URL}/prediction-jobs/${jobId}`
  );

  return response.data;
};

export const exportPredictionReport = async (
  predictionResponse: PredictionResponse
): Promise<Blob> => {
  const response = await axios.post(
    `${API_BASE_URL}/export-report`,
    predictionResponse,
    {
      responseType: "blob",
    }
  );

  return response.data;
};

export const fetchModelTransparency =
  async (): Promise<ModelTransparencyResponse> => {
    const response = await axios.get<ModelTransparencyResponse>(
      `${API_BASE_URL}/model-transparency`
    );

    return response.data;
  };

export const fetchPredictionHistory =
  async (): Promise<PredictionHistoryListResponse> => {
    const response = await axios.get<PredictionHistoryListResponse>(
      `${API_BASE_URL}/prediction-history`
    );

    return response.data;
  };

export const fetchPredictionHistoryDetail = async (
  historyId: string
): Promise<PredictionHistoryDetail> => {
  const response = await axios.get<PredictionHistoryDetail>(
    `${API_BASE_URL}/prediction-history/${historyId}`
  );

  return response.data;
};

export const deletePredictionHistoryItem = async (
  historyId: string
): Promise<void> => {
  await axios.delete(`${API_BASE_URL}/prediction-history/${historyId}`);
};

export const fetchBranches = async (
  repoUrl: string,
  usePersonalAccessToken: boolean = false,
  githubToken: string = ""
): Promise<BranchListResponse> => {
  const response = await axios.post<BranchListResponse>(
    `${API_BASE_URL}/branches`,
    {
      repo_url: repoUrl,
      use_personal_access_token: usePersonalAccessToken,
      github_token: githubToken || null,
    }
  );

  return response.data;
};


export const fetchTags = async (
  repoUrl: string,
  usePersonalAccessToken: boolean = false,
  githubToken: string = ""
): Promise<TagListResponse> => {
  const response = await axios.post<TagListResponse>(
    `${API_BASE_URL}/tags`,
    {
      repo_url: repoUrl,
      use_personal_access_token: usePersonalAccessToken,
      github_token: githubToken || null,
    }
  );

  return response.data;
};

export const fetchCommits = async (
  repoUrl: string,
  gitRef: string,
  maxCommits: number = 20,
  skip: number = 0,
  usePersonalAccessToken: boolean = false,
  githubToken: string = ""
): Promise<CommitListResponse> => {
  const response = await axios.post<CommitListResponse>(
    `${API_BASE_URL}/commits`,
    {
      repo_url: repoUrl,
      git_ref: gitRef,
      max_commits: maxCommits,
      skip: skip,
      use_personal_access_token: usePersonalAccessToken,
      github_token: githubToken || null,
    }
  );

  return response.data;
};
