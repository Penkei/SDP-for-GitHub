import { useMemo, useState } from "react";
import { useLocation, Link } from "react-router-dom";
import type { PredictionResponse, PredictionResult } from "../types/prediction";
import PredictionTable from "../components/PredictionTable";
import MetricGuide from "../components/MetricGuide";

export type ProbabilitySortDirection = "desc" | "asc";

function PredictionResultPage() {
  const location = useLocation();

  const predictionResponse = location.state?.predictionResponse as
    | PredictionResponse
    | undefined;

  const [probabilitySortDirection, setProbabilitySortDirection] =
    useState<ProbabilitySortDirection>("desc");

  const [isMetricGuideOpen, setIsMetricGuideOpen] = useState(false);

  const sortedResults = useMemo(() => {
    if (!predictionResponse) {
      return [];
    }

    const copiedResults: PredictionResult[] = [...predictionResponse.results];

    copiedResults.sort((a, b) => {
      if (probabilitySortDirection === "desc") {
        return b.defect_risk_probability - a.defect_risk_probability;
      }

      return a.defect_risk_probability - b.defect_risk_probability;
    });

    return copiedResults;
  }, [predictionResponse, probabilitySortDirection]);

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
              Total Java Files Scanned:{" "}
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