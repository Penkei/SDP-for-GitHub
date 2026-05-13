import axios from "axios";
import type { 
  PredictionRequest, 
  PredictionResponse,
  PredictionJobStatus,
  CommitListResponse,
  BranchListResponse,
  TagListResponse,
  ModelTransparencyResponse,
} from "../types/prediction";


const API_BASE_URL = "http://127.0.0.1:8000";


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

export const fetchBranches = async (
  repoUrl: string
): Promise<BranchListResponse> => {
  const response = await axios.post<BranchListResponse>(
    `${API_BASE_URL}/branches`,
    {
      repo_url: repoUrl,
    }
  );

  return response.data;
};


export const fetchTags = async (
  repoUrl: string
): Promise<TagListResponse> => {
  const response = await axios.post<TagListResponse>(
    `${API_BASE_URL}/tags`,
    {
      repo_url: repoUrl,
    }
  );

  return response.data;
};

export const fetchCommits = async (
  repoUrl: string,
  gitRef: string,
  maxCommits: number = 20,
  skip: number = 0
): Promise<CommitListResponse> => {
  const response = await axios.post<CommitListResponse>(
    `${API_BASE_URL}/commits`,
    {
      repo_url: repoUrl,
      git_ref: gitRef,
      max_commits: maxCommits,
      skip: skip,
    }
  );

  return response.data;
};
