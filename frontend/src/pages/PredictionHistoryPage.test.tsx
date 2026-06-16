import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import PredictionHistoryPage, { isHistoryDeleteEnabled } from "./PredictionHistoryPage";
import { fetchPredictionHistory } from "../services/api";

vi.mock("../services/api", () => ({
  fetchPredictionHistory: vi.fn(),
  fetchPredictionHistoryDetail: vi.fn(),
  deletePredictionHistoryItem: vi.fn(),
  getApiErrorMessage: vi.fn((_error: unknown, fallbackMessage: string) => fallbackMessage),
}));

const mockedFetchPredictionHistory = vi.mocked(fetchPredictionHistory);

const historyResponse = {
  history: [
    {
      id: "history-1",
      repo_url: "https://github.com/sclorg/s2i-python-container.git",
      commit_sha: "1234567890abcdef1234567890abcdef12345678",
      prediction_threshold: 0.5,
      scanned_at: "2026-06-16T08:00:00.000Z",
      total_files_scanned: 12,
      high_risk_count: 3,
      medium_risk_count: 4,
      low_risk_count: 5,
      defective_count: 7,
      average_risk_probability: 0.61,
    },
  ],
};

const renderHistoryPage = () =>
  render(
    <MemoryRouter>
      <PredictionHistoryPage />
    </MemoryRouter>
  );

describe("PredictionHistoryPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedFetchPredictionHistory.mockResolvedValue(historyResponse);
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("shows saved prediction history returned by the backend", async () => {
    renderHistoryPage();

    expect(await screen.findByText("sclorg/s2i-python-container")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Open Result" })).toBeInTheDocument();
  });

  it("hides the delete button when deployment disables history deletion", async () => {
    vi.stubEnv("VITE_ENABLE_HISTORY_DELETE", "false");

    expect(isHistoryDeleteEnabled()).toBe(false);
    renderHistoryPage();

    await waitFor(() => expect(mockedFetchPredictionHistory).toHaveBeenCalled());
    expect(screen.queryByRole("button", { name: "Delete" })).not.toBeInTheDocument();
  });
});

