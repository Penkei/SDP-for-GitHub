import type { PredictionResult } from "../types/prediction";

interface PredictionTableProps {
  results: PredictionResult[];
}

function PredictionTable({ results }: PredictionTableProps) {
  if (results.length === 0) {
    return (
      <div className="form-card">
        <p>No Java files found for prediction.</p>
      </div>
    );
  }

  return (
    <div className="table-card">
      <table>
        <thead>
          <tr>
            <th>File Path</th>
            <th>Prediction</th>
            <th>Risk Probability</th>
            <th>Risk Level</th>
            <th>Recommendation</th>
            <th>Explanation</th>
          </tr>
        </thead>

        <tbody>
          {results.map((item, index) => (
            <tr key={index}>
              <td>{item.file_path}</td>
              <td>
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
              <td>{(item.defect_risk_probability * 100).toFixed(2)}%</td>
              <td>
                <span className={`badge ${item.risk_level.toLowerCase()}`}>
                  {item.risk_level}
                </span>
              </td>
              <td>{item.recommendation}</td>
              <td className="explanation-cell">
                {item.top_contributing_metrics}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default PredictionTable;