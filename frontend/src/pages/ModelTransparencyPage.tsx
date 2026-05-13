import { useEffect, useState } from "react";
import { fetchModelTransparency } from "../services/api";
import type { ModelTransparencyResponse } from "../types/prediction";

const formatMetric = (value: number) => Number(value).toFixed(3);
const formatImportance = (value: number) => `${(Number(value) * 100).toFixed(1)}%`;

function ModelTransparencyPage() {
  const [modelInfo, setModelInfo] = useState<ModelTransparencyResponse | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const loadModelInfo = async () => {
      try {
        const response = await fetchModelTransparency();
        setModelInfo(response);
      } catch (error) {
        setErrorMessage(
          "Failed to load model transparency details. Please check the backend server."
        );
      } finally {
        setLoading(false);
      }
    };

    loadModelInfo();
  }, []);

  if (loading) {
    return (
      <div className="page">
        <div className="transparency-card">
          <h1>Model Transparency</h1>
          <p className="transparency-muted">Loading model details...</p>
        </div>
      </div>
    );
  }

  if (!modelInfo || errorMessage) {
    return (
      <div className="page">
        <div className="transparency-card">
          <h1>Model Transparency</h1>
          <div className="error-box">{errorMessage}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <section className="transparency-hero">
        <div>
          <h1>Model Transparency</h1>
          <p>
            Current production model: <strong>{modelInfo.model_name}</strong>
          </p>
        </div>
      </section>

      <section className="transparency-summary-grid">
        <div className="transparency-stat-card">
          <span>Dataset Rows</span>
          <strong>{modelInfo.dataset_summary.total_rows}</strong>
        </div>
        <div className="transparency-stat-card">
          <span>Defective Rows</span>
          <strong>{modelInfo.dataset_summary.defective_rows}</strong>
        </div>
        <div className="transparency-stat-card">
          <span>Non-defective Rows</span>
          <strong>{modelInfo.dataset_summary.non_defective_rows}</strong>
        </div>
        <div className="transparency-stat-card">
          <span>Repositories</span>
          <strong>{modelInfo.dataset_summary.repositories}</strong>
        </div>
      </section>

      <section className="transparency-grid">
        <div className="transparency-card">
          <h2>Model Comparison</h2>
          <div className="transparency-table-scroll">
            <table className="transparency-table">
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Accuracy</th>
                  <th>Precision</th>
                  <th>Recall</th>
                  <th>F1</th>
                  <th>ROC-AUC</th>
                  <th>PR-AUC</th>
                </tr>
              </thead>
              <tbody>
                {modelInfo.model_comparison.map((item) => (
                  <tr key={item.model}>
                    <td>{item.model}</td>
                    <td>{formatMetric(item.accuracy)}</td>
                    <td>{formatMetric(item.precision)}</td>
                    <td>{formatMetric(item.recall)}</td>
                    <td>{formatMetric(item.f1)}</td>
                    <td>{formatMetric(item.roc_auc)}</td>
                    <td>{formatMetric(item.pr_auc)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="transparency-card">
          <h2>Selected Features</h2>
          <div className="feature-chip-list">
            {modelInfo.selected_features.map((feature) => (
              <span className="feature-chip" key={feature}>
                {feature}
              </span>
            ))}
          </div>
        </div>
      </section>

      <section className="transparency-grid">
        <div className="transparency-card">
          <h2>Feature Importance</h2>
          <div className="importance-list">
            {modelInfo.feature_importance.map((item) => (
              <div className="importance-row" key={item.feature}>
                <div>
                  <strong>{item.feature}</strong>
                  <span>{formatImportance(item.importance)}</span>
                </div>
                <div className="importance-bar">
                  <span style={{ width: formatImportance(item.importance) }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="transparency-card">
          <h2>Supported Training Languages</h2>
          <div className="feature-chip-list">
            {modelInfo.dataset_summary.languages.map((language) => (
              <span className="feature-chip" key={language}>
                {language}
              </span>
            ))}
          </div>

          <h2 className="transparency-subheading">Limitations</h2>
          <ul className="limitations-list">
            {modelInfo.limitations.map((limitation) => (
              <li key={limitation}>{limitation}</li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  );
}

export default ModelTransparencyPage;
