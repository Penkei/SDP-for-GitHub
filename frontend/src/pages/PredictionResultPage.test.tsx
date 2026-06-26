import { describe, expect, it } from "vitest";
import type {
  PredictionResponse,
  PredictionResult,
} from "../types/prediction";
import {
  buildPdfReportHtml,
  filterPredictionResults,
} from "./PredictionResultPage";

const results: PredictionResult[] = [
  {
    file_path: "src/main.py",
    language: "Python",
    prediction_label: "Defective",
    defect_risk_probability: 0.82,
    risk_level: "High",
    recommendation: "Review immediately before release",
    top_contributing_metrics: "conditional checks",
  },
  {
    file_path: "src/helper.py",
    language: "Python",
    prediction_label: "Non-defective",
    defect_risk_probability: 0.31,
    risk_level: "Low",
    recommendation: "Low priority",
    top_contributing_metrics: "file size",
  },
  {
    file_path: "src/Worker.java",
    language: "Java",
    prediction_label: "Defective",
    defect_risk_probability: 0.64,
    risk_level: "Medium",
    recommendation: "Review during normal testing",
    top_contributing_metrics: "method count",
  },
];

describe("PredictionResultPage helpers", () => {
  it("filters prediction results by path and risk level", () => {
    const filtered = filterPredictionResults(results, {
      fileSearch: "main",
      languageFilter: "All",
      riskFilter: "High",
      predictionFilter: "All",
      minProbability: "",
      maxProbability: "",
    });

    expect(filtered).toHaveLength(1);
    expect(filtered[0].file_path).toBe("src/main.py");

    const restored = filterPredictionResults(results, {
      fileSearch: "",
      languageFilter: "All",
      riskFilter: "All",
      predictionFilter: "All",
      minProbability: "",
      maxProbability: "",
    });

    expect(restored).toHaveLength(3);
  });

  it("builds a PDF report containing only selected results", () => {
    const response: PredictionResponse = {
      repo_url: "https://github.com/sclorg/s2i-python-container.git",
      commit_sha: "1234567890abcdef1234567890abcdef12345678",
      prediction_threshold: 0.5,
      total_files_scanned: 1,
      results: [results[0]],
    };

    const reportHtml = buildPdfReportHtml(response, [results[0]]);

    expect(reportHtml).toContain("src/main.py");
    expect(reportHtml).not.toContain("src/helper.py");
    expect(reportHtml).toContain("Exported Files</span><strong>1");
  });
});
