export interface PredictionRequest {
  repo_url: string;
  commit_sha: string;
}

export interface PredictionResult {
  file_path: string;
  language: string;
  prediction_label: string;
  defect_risk_probability: number;
  risk_level: string;
  recommendation: string;
  top_contributing_metrics: string;
  readable_explanation?: string;
}

export interface PredictionResponse {
  repo_url: string;
  commit_sha: string;
  total_files_scanned: number;
  results: PredictionResult[];
}

export interface PredictionJobStatus {
  job_id: string;
  status: "queued" | "running" | "completed" | "failed";
  stage: string;
  progress_percent: number;
  message: string;
  repo_url: string;
  commit_sha: string;
  created_at: string;
  updated_at: string;
  result: PredictionResponse | null;
  error: string | null;
  history_id?: string | null;
}

export interface PredictionHistorySummary {
  id: string;
  repo_url: string;
  commit_sha: string;
  scanned_at: string;
  total_files_scanned: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  defective_count: number;
  average_risk_probability: number;
}

export interface PredictionHistoryListResponse {
  history: PredictionHistorySummary[];
}

export interface PredictionHistoryDetail extends PredictionResponse {
  history_id: string;
  scanned_at: string;
}

export interface ModelComparisonItem {
  model: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  roc_auc: number;
  pr_auc: number;
}

export interface FeatureImportanceItem {
  feature: string;
  importance: number;
}

export interface DatasetSummary {
  total_rows: number;
  defective_rows: number;
  non_defective_rows: number;
  repositories: number;
  languages: string[];
}

export interface ModelTransparencyResponse {
  model_name: string;
  selected_features: string[];
  model_comparison: ModelComparisonItem[];
  feature_importance: FeatureImportanceItem[];
  dataset_summary: DatasetSummary;
  limitations: string[];
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
