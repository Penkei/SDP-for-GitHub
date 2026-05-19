import { useEffect, useState } from "react";
import { fetchModelTransparency } from "../services/api";
import type { ModelTransparencyResponse } from "../types/prediction";

const formatMetric = (value: number) => Number(value).toFixed(3);
const formatImportance = (value: number) => `${(Number(value) * 100).toFixed(1)}%`;

const metricDescriptions = [
  {
    name: "dit",
    meaning: "Inheritance depth",
    detail: "Deeper inheritance can make behavior harder to trace.",
  },
  {
    name: "nosi",
    meaning: "Static calls",
    detail: "Frequent static calls can signal tight utility or global-style coupling.",
  },
  {
    name: "loc",
    meaning: "File size",
    detail: "Large files are usually harder to review and test thoroughly.",
  },
  {
    name: "wmc",
    meaning: "Logic complexity",
    detail: "More branches and methods can make behavior harder to reason about.",
  },
  {
    name: "rfc",
    meaning: "Method interaction",
    detail: "More calls between methods can increase the impact of a change.",
  },
  {
    name: "cbo",
    meaning: "Dependency coupling",
    detail: "Files connected to many dependencies may be more fragile.",
  },
  {
    name: "comparisonsQty",
    meaning: "Decision checks",
    detail: "Many comparisons often indicate more conditional paths to test.",
  },
  {
    name: "returnQty",
    meaning: "Return paths",
    detail: "Multiple exits can make edge cases easier to miss.",
  },
];

const modelMetricDescriptions = [
  {
    name: "Recall",
    detail: "How many truly risky files the model catches. High recall is useful because missed risky files are costly.",
  },
  {
    name: "Precision",
    detail: "How often a risky prediction is correct. Moderate precision means some files are flagged for extra review even if they are not defective.",
  },
  {
    name: "F1",
    detail: "A balance between precision and recall. This is a good overall score when both false alarms and missed risks matter.",
  },
  {
    name: "ROC-AUC",
    detail: "How well the model separates risky and non-risky files across thresholds.",
  },
  {
    name: "PR-AUC",
    detail: "How well the model performs when focusing on the risky/defective class.",
  },
];

const getMetricDescription = (featureName: string) =>
  metricDescriptions.find((metric) => metric.name === featureName) || {
    name: featureName,
    meaning: featureName,
    detail: "This feature is one of the numeric code signals used by the model.",
  };

function HowItWorksPage() {
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
          "Model evidence could not be loaded. The guide is still available."
        );
      } finally {
        setLoading(false);
      }
    };

    loadModelInfo();
  }, []);

  return (
    <div className="page">
      <section className="how-hero">
        <div>
          <h1>How It Works</h1>
          <p>
            SDP for GitHub scans a selected commit, extracts code metrics, and
            highlights files that may deserve earlier review.
          </p>
        </div>
      </section>

      <section className="developer-flow">
        <div className="flow-step">
          <span>1</span>
          <h2>Select Repository</h2>
          <p>Choose a public GitHub repository, branch or tag, and commit.</p>
        </div>
        <div className="flow-step">
          <span>2</span>
          <h2>Extract Metrics</h2>
          <p>The backend scans Java, Python, and C++ files for code patterns.</p>
        </div>
        <div className="flow-step">
          <span>3</span>
          <h2>Predict Risk</h2>
          <p>The trained model estimates defect risk for each supported file.</p>
        </div>
        <div className="flow-step">
          <span>4</span>
          <h2>Review First</h2>
          <p>Use high-risk files and explanations to prioritize code review.</p>
        </div>
      </section>

      <section className="how-grid">
        <div className="how-card">
          <h2>What Defect Risk Means</h2>
          <p>
            A high-risk result does not prove that a file has a bug. It means the
            file has code patterns similar to files that were historically linked
            with defect-fixing commits.
          </p>
          <div className="risk-meaning-list">
            <div>
              <strong>High</strong>
              <span>Review before release or merge.</span>
            </div>
            <div>
              <strong>Medium</strong>
              <span>Check important logic and recent changes.</span>
            </div>
            <div>
              <strong>Low</strong>
              <span>Lower priority unless the file is part of active work.</span>
            </div>
          </div>
        </div>

        <div className="how-card">
          <h2>How Developers Should Use It</h2>
          <ul className="how-list">
            <li>Start with high-risk files in the dashboard.</li>
            <li>Read the explanation to see which metrics influenced the result.</li>
            <li>Use the prediction as review guidance, not as final proof.</li>
            <li>Export the report when documenting review decisions.</li>
          </ul>
        </div>
      </section>

      <section className="how-card">
          <h2>Code Metrics In Plain Language</h2>
          <p className="section-intro">
            The model does not read code like a human. It counts structural
            signals that often make code harder to review, test, or change.
          </p>
        <div className="metric-explainer-grid">
          {metricDescriptions.map((metric) => (
            <div className="metric-explainer" key={metric.name}>
              <span>{metric.name}</span>
              <strong>{metric.meaning}</strong>
              <p>{metric.detail}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="how-grid">
        <div className="how-card">
          <h2>Supported Files</h2>
          <p>
            The current extractor supports Java, Python, and C++ source files.
            Language-specific patterns are mapped into a shared metric set so the
            prediction workflow stays consistent.
          </p>
          <div className="feature-chip-list">
            {(modelInfo?.dataset_summary.languages || ["Java", "Python", "C++"]).map(
              (language) => (
                <span className="feature-chip" key={language}>
                  {language}
                </span>
              )
            )}
          </div>
        </div>

        <div className="how-card">
          <h2>Important Limits</h2>
          <ul className="how-list">
            {(modelInfo?.limitations || [
              "Static metrics cannot understand runtime behavior.",
              "Commit-message labels can be noisy.",
              "Predictions are advisory and should support human review.",
            ]).map((limitation) => (
              <li key={limitation}>{limitation}</li>
            ))}
          </ul>
        </div>
      </section>

      <section className="how-card">
        <div className="evidence-header">
          <div>
            <h2>Model Evidence</h2>
            <p>
              The application compares multiple algorithms during training and
              deploys the strongest validated model.
            </p>
          </div>
          {modelInfo && <strong>{modelInfo.model_name}</strong>}
        </div>

        {loading && <p className="how-muted">Loading model evidence...</p>}
        {errorMessage && <div className="info-box">{errorMessage}</div>}

        {modelInfo && (
          <>
            <div className="evidence-summary-grid">
              <div className="evidence-stat-card">
                <span>Dataset Rows</span>
                <strong>{modelInfo.dataset_summary.total_rows}</strong>
                <small>Total labeled file examples</small>
              </div>
              <div className="evidence-stat-card">
                <span>Defective Rows</span>
                <strong>{modelInfo.dataset_summary.defective_rows}</strong>
                <small>Examples linked to fixes</small>
              </div>
              <div className="evidence-stat-card">
                <span>Non-defective Rows</span>
                <strong>{modelInfo.dataset_summary.non_defective_rows}</strong>
                <small>Examples from normal changes</small>
              </div>
              <div className="evidence-stat-card">
                <span>Repositories</span>
                <strong>{modelInfo.dataset_summary.repositories}</strong>
                <small>Projects used for training</small>
              </div>
            </div>

            <div className="model-metric-guide">
              {modelMetricDescriptions.map((metric) => (
                <div className="model-metric-card" key={metric.name}>
                  <strong>{metric.name}</strong>
                  <p>{metric.detail}</p>
                </div>
              ))}
            </div>

            <div className="evidence-table-scroll">
              <table className="evidence-table">
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
          </>
        )}
      </section>

      {modelInfo && (
        <section className="how-grid">
          <div className="how-card">
            <h2>Feature Importance</h2>
            <p className="section-intro">
              These bars show which code metrics influenced the trained model
              most overall. They do not mean every prediction depends on the same
              metric.
            </p>
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

          <div className="how-card">
            <h2>Selected Features</h2>
            <p className="section-intro">
              These are the inputs given to the model for every scanned file.
            </p>
            <div className="selected-feature-grid">
              {modelInfo.selected_features.map((feature) => (
                <div className="selected-feature-card" key={feature}>
                  <span>{feature}</span>
                  <strong>{getMetricDescription(feature).meaning}</strong>
                  <p>{getMetricDescription(feature).detail}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}
    </div>
  );
}

export default HowItWorksPage;
