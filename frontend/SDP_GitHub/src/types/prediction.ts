export interface PredictionRequest {
  repo_url: string;
  commit_sha: string;
}

export interface PredictionResult {
  file_path: string;
  prediction_label: string;
  defect_risk_probability: number;
  risk_level: string;
  recommendation: string;
  top_contributing_metrics: string;
}

export interface PredictionResponse {
  repo_url: string;
  commit_sha: string;
  total_files_scanned: number;
  results: PredictionResult[];
}

export interface CommitItem {
  sha: string;
  short_sha: string;
  message: string;
  author: string;
  date: string;
}

export interface CommitListResponse {
  repo_url: string;
  git_ref: string;
  skip: number;
  max_commits: number;
  total_commits: number;
  commits: CommitItem[];
}

export interface GitRefItem {
  name: string;
  type: "branch" | "tag";
}

export interface BranchListResponse {
  repo_url: string;
  total_branches: number;
  branches: GitRefItem[];
}

export interface TagListResponse {
  repo_url: string;
  total_tags: number;
  tags: GitRefItem[];
}