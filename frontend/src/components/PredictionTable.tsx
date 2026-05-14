import type { PredictionResult } from "../types/prediction";
import type { ProbabilitySortDirection } from "../pages/PredictionResultPage";
import sortIconUrl from "../../assets/24967-200.png";
import CompactExplanation from "./CompactExplanation";

interface PredictionTableProps {
  results: PredictionResult[];
  probabilitySortDirection: ProbabilitySortDirection;
  onToggleProbabilitySort: () => void;
}

function PredictionTable({
  results,
  probabilitySortDirection,
  onToggleProbabilitySort,
}: PredictionTableProps) {
  if (results.length === 0) {
    return (
      <div className="form-card">
        <p>No supported Java, Python, or C++ files found for prediction.</p>
      </div>
    );
  }

  const sortLabel =
    probabilitySortDirection === "desc" ? "High to Low" : "Low to High";

  return (
    <div className="table-card">
      <div className="table-scroll-box">
        <table className="prediction-table">
          <thead>
            <tr>
              <th className="col-no">No.</th>
              <th className="col-file">File Path</th>
              <th className="col-language">Language</th>
              <th className="col-prediction">Prediction</th>

              <th className="col-probability">
                <div className="probability-header">
                  <span>Risk Probability</span>

                  <button
                    className="sort-icon-button"
                    onClick={onToggleProbabilitySort}
                    title={`Sort probability: ${sortLabel}`}
                  >
                    <img
                      src={sortIconUrl}
                      alt="Sort"
                      className={
                        probabilitySortDirection === "desc"
                          ? "sort-table-icon"
                          : "sort-table-icon rotate-up"
                      }
                    />
                    <span>{sortLabel}</span>
                  </button>
                </div>
              </th>

              <th className="col-risk">Risk Level</th>
              <th className="col-recommendation">Recommendation</th>
              <th className="col-metrics">Metric Values</th>
              <th className="col-readable-explanation">Explanation</th>
            </tr>
          </thead>

          <tbody>
            {results.map((item, index) => (
              <tr key={`${item.file_path}-${index}`}>
                <td className="col-no">{index + 1}</td>

                <td className="col-file file-path-cell">{item.file_path}</td>

                <td className="col-language">{item.language || "Unknown"}</td>

                <td className="col-prediction">
                  <span
                    className={
                      item.prediction_label === "Defective"
                        ? "badge danger"
                        : "badge success"
                    }
                  >
                    {item.prediction_label}
                  </span>
                </td>

                <td className="col-probability probability-cell">
                  {(item.defect_risk_probability * 100).toFixed(2)}%
                </td>

                <td className="col-risk">
                  <span className={`badge ${item.risk_level.toLowerCase()}`}>
                    {item.risk_level}
                  </span>
                </td>

                <td className="col-recommendation">{item.recommendation}</td>

                <td className="col-metrics explanation-cell">
                  <CompactExplanation explanation={item.top_contributing_metrics} />
                </td>

                <td className="col-readable-explanation readable-explanation-cell">
                  {item.readable_explanation ||
                    "The model detected code patterns that may affect defect risk."}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default PredictionTable;
