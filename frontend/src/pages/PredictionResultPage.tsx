import { useMemo, useState } from "react";
import { useLocation, Link } from "react-router-dom";
import type { PredictionResponse, PredictionResult } from "../types/prediction";
import PredictionTable from "../components/PredictionTable";
import MetricGuide from "../components/MetricGuide";

export type ProbabilitySortDirection = "desc" | "asc";
type RiskFilter = "All" | "High" | "Medium" | "Low";
type PredictionFilter = "All" | "Defective" | "Non-defective";

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
              Total Supported Files Scanned:{" "}
              <strong>{predictionResponse.total_files_scanned}</strong>
            </p>
          </div>

          <button
            className="metric-guide-open-button"
            onClick={() => setIsMetricGuideOpen(true)}
          >
            Metric Explanation Guide
          </button>
        </div>
      </div>

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
