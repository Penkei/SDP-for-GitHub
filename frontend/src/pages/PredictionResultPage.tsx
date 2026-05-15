import { useMemo, useState } from "react";
import { useLocation, Link } from "react-router-dom";
import type { PredictionResponse, PredictionResult } from "../types/prediction";
import PredictionTable from "../components/PredictionTable";
import MetricGuide from "../components/MetricGuide";
import { exportPredictionReport } from "../services/api";

export type ProbabilitySortDirection = "desc" | "asc";
type RiskFilter = "All" | "High" | "Medium" | "Low";
type PredictionFilter = "All" | "Defective" | "Non-defective";

const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`;

const getTopLevelFolder = (filePath: string) => {
  const normalizedPath = filePath.replaceAll("\\", "/");
  const pathParts = normalizedPath.split("/").filter(Boolean);

  if (pathParts.length <= 1) {
    return "Repository root";
  }

  return pathParts[0];
};

function PredictionResultPage() {
  const location = useLocation();

  const predictionResponse = location.state?.predictionResponse as
    | PredictionResponse
    | undefined;

  const [probabilitySortDirection, setProbabilitySortDirection] =
    useState<ProbabilitySortDirection>("desc");

  const [isMetricGuideOpen, setIsMetricGuideOpen] = useState(false);
  const [fileSearch, setFileSearch] = useState("");
  const [languageFilter, setLanguageFilter] = useState("All");
  const [riskFilter, setRiskFilter] = useState<RiskFilter>("All");
  const [predictionFilter, setPredictionFilter] =
    useState<PredictionFilter>("All");
  const [minProbability, setMinProbability] = useState("");
  const [maxProbability, setMaxProbability] = useState("");
  const [exportingReport, setExportingReport] = useState(false);

  const availableLanguages = useMemo(() => {
    if (!predictionResponse) {
      return [];
    }

    return Array.from(
      new Set(
        predictionResponse.results
          .map((result) => result.language)
          .filter(Boolean)
      )
    ).sort();
  }, [predictionResponse]);

  const dashboardStats = useMemo(() => {
    const emptyStats = {
      totalFiles: 0,
      highRiskCount: 0,
      mediumRiskCount: 0,
      lowRiskCount: 0,
      defectiveCount: 0,
      averageProbability: 0,
      highestRiskFile: null as PredictionResult | null,
      riskiestFolder: "No folder",
      riskiestFolderAverage: 0,
      languageBreakdown: [] as Array<{
        language: string;
        count: number;
        averageProbability: number;
      }>,
      riskDistribution: [] as Array<{
        label: string;
        count: number;
        percent: number;
        className: string;
      }>,
    };

    if (!predictionResponse || predictionResponse.results.length === 0) {
      return emptyStats;
    }

    const folderStats = new Map<string, { count: number; probabilitySum: number }>();
    const languageStats = new Map<string, { count: number; probabilitySum: number }>();

    const stats = predictionResponse.results.reduce(
      (summary, result) => {
        const probability = result.defect_risk_probability;
        const folder = getTopLevelFolder(result.file_path);
        const language = result.language || "Unknown";

        if (result.risk_level === "High") {
          summary.highRiskCount += 1;
        } else if (result.risk_level === "Medium") {
          summary.mediumRiskCount += 1;
        } else {
          summary.lowRiskCount += 1;
        }

        if (result.prediction_label === "Defective") {
          summary.defectiveCount += 1;
        }

        summary.probabilitySum += probability;

        if (
          !summary.highestRiskFile ||
          probability > summary.highestRiskFile.defect_risk_probability
        ) {
          summary.highestRiskFile = result;
        }

        const folderItem = folderStats.get(folder) || {
          count: 0,
          probabilitySum: 0,
        };
        folderItem.count += 1;
        folderItem.probabilitySum += probability;
        folderStats.set(folder, folderItem);

        const languageItem = languageStats.get(language) || {
          count: 0,
          probabilitySum: 0,
        };
        languageItem.count += 1;
        languageItem.probabilitySum += probability;
        languageStats.set(language, languageItem);

        return summary;
      },
      {
        ...emptyStats,
        probabilitySum: 0,
      }
    );

    const sortedFolders = Array.from(folderStats.entries()).sort((a, b) => {
      const averageA = a[1].probabilitySum / a[1].count;
      const averageB = b[1].probabilitySum / b[1].count;

      return averageB - averageA;
    });

    const languageBreakdown = Array.from(languageStats.entries())
      .map(([language, item]) => ({
        language,
        count: item.count,
        averageProbability: item.probabilitySum / item.count,
      }))
      .sort((a, b) => b.count - a.count);

    const riskiestFolder = sortedFolders[0];

    const totalFiles = predictionResponse.results.length;
    const riskDistribution = [
      {
        label: "High",
        count: stats.highRiskCount,
        percent: totalFiles ? stats.highRiskCount / totalFiles : 0,
        className: "high",
      },
      {
        label: "Medium",
        count: stats.mediumRiskCount,
        percent: totalFiles ? stats.mediumRiskCount / totalFiles : 0,
        className: "medium",
      },
      {
        label: "Low",
        count: stats.lowRiskCount,
        percent: totalFiles ? stats.lowRiskCount / totalFiles : 0,
        className: "low",
      },
    ];

    return {
      totalFiles: predictionResponse.results.length,
      highRiskCount: stats.highRiskCount,
      mediumRiskCount: stats.mediumRiskCount,
      lowRiskCount: stats.lowRiskCount,
      defectiveCount: stats.defectiveCount,
      averageProbability: stats.probabilitySum / predictionResponse.results.length,
      highestRiskFile: stats.highestRiskFile,
      riskiestFolder: riskiestFolder ? riskiestFolder[0] : "No folder",
      riskiestFolderAverage: riskiestFolder
        ? riskiestFolder[1].probabilitySum / riskiestFolder[1].count
        : 0,
      languageBreakdown,
      riskDistribution,
    };
  }, [predictionResponse]);

  const riskDonutBackground = useMemo(() => {
    if (dashboardStats.totalFiles === 0) {
      return "#e5e7eb";
    }

    const highEnd = dashboardStats.riskDistribution[0].percent * 100;
    const mediumEnd =
      highEnd + dashboardStats.riskDistribution[1].percent * 100;

    return `conic-gradient(#dc2626 0 ${highEnd}%, #d97706 ${highEnd}% ${mediumEnd}%, #16a34a ${mediumEnd}% 100%)`;
  }, [dashboardStats]);

  const filteredResults = useMemo(() => {
    if (!predictionResponse) {
      return [];
    }

    const normalizedSearch = fileSearch.trim().toLowerCase();
    const parsedMinProbability =
      minProbability.trim() === "" ? null : Number(minProbability) / 100;
    const parsedMaxProbability =
      maxProbability.trim() === "" ? null : Number(maxProbability) / 100;

    return predictionResponse.results.filter((result) => {
      const matchesSearch =
        !normalizedSearch ||
        result.file_path.toLowerCase().includes(normalizedSearch);
      const matchesLanguage =
        languageFilter === "All" || result.language === languageFilter;
      const matchesRisk =
        riskFilter === "All" || result.risk_level === riskFilter;
      const matchesPrediction =
        predictionFilter === "All" ||
        result.prediction_label === predictionFilter;
      const matchesMinProbability =
        parsedMinProbability === null ||
        result.defect_risk_probability >= parsedMinProbability;
      const matchesMaxProbability =
        parsedMaxProbability === null ||
        result.defect_risk_probability <= parsedMaxProbability;

      return (
        matchesSearch &&
        matchesLanguage &&
        matchesRisk &&
        matchesPrediction &&
        matchesMinProbability &&
        matchesMaxProbability
      );
    });
  }, [
    predictionResponse,
    fileSearch,
    languageFilter,
    riskFilter,
    predictionFilter,
    minProbability,
    maxProbability,
  ]);

  const sortedResults = useMemo(() => {
    const copiedResults: PredictionResult[] = [...filteredResults];

    copiedResults.sort((a, b) => {
      if (probabilitySortDirection === "desc") {
        return b.defect_risk_probability - a.defect_risk_probability;
      }

      return a.defect_risk_probability - b.defect_risk_probability;
    });

    return copiedResults;
  }, [filteredResults, probabilitySortDirection]);

  const hasActiveFilters =
    fileSearch.trim() !== "" ||
    languageFilter !== "All" ||
    riskFilter !== "All" ||
    predictionFilter !== "All" ||
    minProbability.trim() !== "" ||
    maxProbability.trim() !== "";

  const resetFilters = () => {
    setFileSearch("");
    setLanguageFilter("All");
    setRiskFilter("All");
    setPredictionFilter("All");
    setMinProbability("");
    setMaxProbability("");
  };

  const handleExportReport = async () => {
    if (!predictionResponse) {
      return;
    }

    setExportingReport(true);

    try {
      const reportBlob = await exportPredictionReport(predictionResponse);
      const downloadUrl = URL.createObjectURL(reportBlob);
      const link = document.createElement("a");

      link.href = downloadUrl;
      link.download = `defect_prediction_report_${predictionResponse.commit_sha.slice(
        0,
        8
      )}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(downloadUrl);
    } finally {
      setExportingReport(false);
    }
  };

  if (!predictionResponse) {
    return (
      <div className="page">
        <div className="form-card">
          <h1>No Prediction Result</h1>
          <p>Please run a prediction first.</p>
          <Link to="/repository-input" className="primary-button">
            Go to Repository Input
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="result-header">
        <div className="result-header-top">
          <div>
            <h1>Prediction Result</h1>

            <p>
              Repository: <strong>{predictionResponse.repo_url}</strong>
            </p>

            <p>
              Commit: <strong>{predictionResponse.commit_sha}</strong>
            </p>

            <p>
              Prediction Threshold:{" "}
              <strong>
                {predictionResponse.prediction_threshold !== null &&
                predictionResponse.prediction_threshold !== undefined
                  ? formatPercent(predictionResponse.prediction_threshold)
                  : "Model default"}
              </strong>
            </p>

            <p>
              Total Supported Files Scanned:{" "}
              <strong>{predictionResponse.total_files_scanned}</strong>
            </p>
          </div>

          <div className="result-header-actions">
            <button
              className="export-report-button"
              onClick={handleExportReport}
              disabled={exportingReport}
            >
              {exportingReport ? "Exporting..." : "Export Report"}
            </button>

            <button
              className="metric-guide-open-button"
              onClick={() => setIsMetricGuideOpen(true)}
            >
              Metric Explanation Guide
            </button>
          </div>
        </div>
      </div>

      <section className="risk-dashboard" aria-label="Risk dashboard">
        <div className="dashboard-summary-grid">
          <div className="dashboard-stat high-risk-stat">
            <span>High Risk</span>
            <strong>{dashboardStats.highRiskCount}</strong>
            <small>{formatPercent(dashboardStats.riskDistribution[0]?.percent || 0)}</small>
          </div>

          <div className="dashboard-stat medium-risk-stat">
            <span>Medium Risk</span>
            <strong>{dashboardStats.mediumRiskCount}</strong>
            <small>{formatPercent(dashboardStats.riskDistribution[1]?.percent || 0)}</small>
          </div>

          <div className="dashboard-stat low-risk-stat">
            <span>Low Risk</span>
            <strong>{dashboardStats.lowRiskCount}</strong>
            <small>{formatPercent(dashboardStats.riskDistribution[2]?.percent || 0)}</small>
          </div>

          <div className="dashboard-stat defective-stat">
            <span>Defective</span>
            <strong>{dashboardStats.defectiveCount}</strong>
            <small>
              {formatPercent(
                dashboardStats.totalFiles
                  ? dashboardStats.defectiveCount / dashboardStats.totalFiles
                  : 0
              )}
            </small>
          </div>

          <div className="dashboard-stat average-risk-stat">
            <span>Average Risk</span>
            <strong>{formatPercent(dashboardStats.averageProbability)}</strong>
            <small>Mean probability</small>
          </div>
        </div>

        <div className="dashboard-detail-grid">
          <div className="risk-panel risk-distribution-panel">
            <div className="risk-panel-header">
              <h2>Risk Distribution</h2>
              <span>{dashboardStats.totalFiles} files</span>
            </div>

            <div className="risk-chart-layout">
              <div
                className="risk-donut"
                style={{ background: riskDonutBackground }}
                aria-hidden="true"
              >
                <div className="risk-donut-center">
                  <strong>{formatPercent(dashboardStats.averageProbability)}</strong>
                  <span>Avg risk</span>
                </div>
              </div>

              <div className="risk-breakdown-list">
                {dashboardStats.riskDistribution.map((item) => (
                  <div className="risk-breakdown-row" key={item.label}>
                    <span>
                      <i className={`legend-dot ${item.className}-dot`} />
                      {item.label}
                    </span>
                    <strong>{item.count}</strong>
                    <small>{formatPercent(item.percent)}</small>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="risk-panel">
            <div className="risk-panel-header">
              <h2>Highest Risk File</h2>
              <span>
                {dashboardStats.highestRiskFile
                  ? formatPercent(
                      dashboardStats.highestRiskFile.defect_risk_probability
                    )
                  : "0.0%"}
              </span>
            </div>

            <p className="dashboard-file-path">
              {dashboardStats.highestRiskFile?.file_path || "No file available"}
            </p>
            <p className="dashboard-muted">
              {dashboardStats.highestRiskFile?.language || "No language"} |{" "}
              {dashboardStats.highestRiskFile?.risk_level || "No risk"}
            </p>
          </div>

          <div className="risk-panel">
            <div className="risk-panel-header">
              <h2>Riskiest Folder</h2>
              <span>{formatPercent(dashboardStats.riskiestFolderAverage)}</span>
            </div>

            <p className="dashboard-file-path">{dashboardStats.riskiestFolder}</p>
            <p className="dashboard-muted">Average defect probability</p>
          </div>
        </div>

        {dashboardStats.languageBreakdown.length > 0 && (
          <div className="risk-panel language-chart-panel">
            <div className="risk-panel-header">
              <h2>Language Risk Overview</h2>
              <span>Count and average risk</span>
            </div>

            <div className="language-column-chart">
              {dashboardStats.languageBreakdown.map((item) => (
                <div className="language-column-item" key={item.language}>
                  <div className="language-column-bars">
                    <span
                      className="language-count-bar"
                      style={{
                        height: `${Math.max(
                          12,
                          (item.count / dashboardStats.totalFiles) * 100
                        )}%`,
                      }}
                    />
                    <span
                      className="language-risk-bar"
                      style={{
                        height: `${Math.max(12, item.averageProbability * 100)}%`,
                      }}
                    />
                  </div>
                  <div className="language-column-label">
                    <strong>{item.language}</strong>
                    <span>{item.count} files</span>
                    <small>{formatPercent(item.averageProbability)} avg</small>
                  </div>
                </div>
              ))}
            </div>

            <div className="chart-legend">
              <span>
                <i className="legend-line count-line" /> File volume
              </span>
              <span>
                <i className="legend-line risk-line" /> Average risk
              </span>
            </div>
          </div>
        )}
      </section>

      <div className="result-filters">
        <div className="filter-summary">
          <strong>{sortedResults.length}</strong> of{" "}
          <strong>{predictionResponse.results.length}</strong> files shown
        </div>

        <div className="filter-grid">
          <label className="filter-field filter-field-wide">
            <span>Search File Path</span>
            <input
              type="search"
              value={fileSearch}
              onChange={(event) => setFileSearch(event.target.value)}
              placeholder="Search by folder or file name"
            />
          </label>

          <label className="filter-field">
            <span>Language</span>
            <select
              value={languageFilter}
              onChange={(event) => setLanguageFilter(event.target.value)}
            >
              <option value="All">All languages</option>
              {availableLanguages.map((language) => (
                <option key={language} value={language}>
                  {language}
                </option>
              ))}
            </select>
          </label>

          <label className="filter-field">
            <span>Risk Level</span>
            <select
              value={riskFilter}
              onChange={(event) =>
                setRiskFilter(event.target.value as RiskFilter)
              }
            >
              <option value="All">All risks</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </label>

          <label className="filter-field">
            <span>Prediction</span>
            <select
              value={predictionFilter}
              onChange={(event) =>
                setPredictionFilter(event.target.value as PredictionFilter)
              }
            >
              <option value="All">All predictions</option>
              <option value="Defective">Defective</option>
              <option value="Non-defective">Non-defective</option>
            </select>
          </label>

          <label className="filter-field">
            <span>Min Probability %</span>
            <input
              type="number"
              value={minProbability}
              min="0"
              max="100"
              onChange={(event) => setMinProbability(event.target.value)}
              placeholder="0"
            />
          </label>

          <label className="filter-field">
            <span>Max Probability %</span>
            <input
              type="number"
              value={maxProbability}
              min="0"
              max="100"
              onChange={(event) => setMaxProbability(event.target.value)}
              placeholder="100"
            />
          </label>
        </div>

        <button
          className="filter-reset-button"
          onClick={resetFilters}
          disabled={!hasActiveFilters}
        >
          Reset Filters
        </button>
      </div>

      <PredictionTable
        results={sortedResults}
        probabilitySortDirection={probabilitySortDirection}
        onToggleProbabilitySort={() =>
          setProbabilitySortDirection((current) =>
            current === "desc" ? "asc" : "desc"
          )
        }
      />

      <MetricGuide
        isOpen={isMetricGuideOpen}
        onClose={() => setIsMetricGuideOpen(false)}
      />
    </div>
  );
}

export default PredictionResultPage;
