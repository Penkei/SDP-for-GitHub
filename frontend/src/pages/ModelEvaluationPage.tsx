import { useEffect, useMemo, useState } from "react";
import { fetchModelTransparency } from "../services/api";
import type {
  FeatureImportanceItem,
  ModelComparisonItem,
  ModelTransparencyResponse,
} from "../types/prediction";

const formatMetric = (value?: number) => {
  const parsed = Number(value || 0);
  return parsed.toFixed(3);
};

const formatPercent = (value?: number) => `${(Number(value || 0) * 100).toFixed(1)}%`;

const metricNotes = [
  {
    label: "Accuracy",
    text: "Overall correctness across both defective and non-defective rows.",
  },
  {
    label: "Precision",
    text: "How often a file predicted as risky is actually linked to a defect label.",
  },
  {
    label: "Recall",
    text: "How many defective examples the model successfully catches.",
  },
  {
    label: "F1",
    text: "Balance between precision and recall, useful for imbalanced datasets.",
  },
  {
    label: "PR-AUC",
    text: "Quality of ranking when focusing on the defective class.",
  },
];

const featureMeaning: Record<string, string> = {
  nosi: "Static invocation signal",
  dit: "Inheritance depth",
  cbo: "Dependency coupling",
  rfc: "Method interaction complexity",
  loc: "File size",
  comparisonsQty: "Conditional decision count",
  returnQty: "Return path count",
  wmc: "Weighted method complexity",
  lcom: "Cohesion weakness",
  totalMethods: "Detected method count",
  file_change_count: "Historical file changes",
  file_bug_fix_count: "Previous bug-fix activity",
  recent_file_change_count: "Recent file changes",
  days_since_last_change: "Age since previous change",
  last_change_lines_added: "Previous added lines",
  last_change_lines_deleted: "Previous deleted lines",
  last_change_churn: "Previous code churn",
  last_change_file_count: "Previous commit size",
  author_file_change_count: "Author history with this file",
};

function getBestModel(items: ModelComparisonItem[]) {
  if (!items.length) {
    return null;
  }

  return [...items].sort((a, b) => Number(b.f1 || 0) - Number(a.f1 || 0))[0];
}

function getConfusionValue(
  rows: Array<Record<string, number | string>> | undefined,
  rowName: string,
  columnName: string
) {
  if (!rows?.length) {
    return 0;
  }

  const row = rows.find((item) =>
    Object.values(item).some((value) => String(value) === rowName)
  );

  return Number(row?.[columnName] || 0);
}

function ModelEvaluationPage() {
  const [modelInfo, setModelInfo] = useState<ModelTransparencyResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const loadEvaluation = async () => {
      try {
        const response = await fetchModelTransparency();
        setModelInfo(response);
      } catch (error) {
        setErrorMessage("Unable to load model evaluation evidence from the backend.");
      } finally {
        setLoading(false);
      }
    };

    loadEvaluation();
  }, []);

  const bestModel = useMemo(
    () => getBestModel(modelInfo?.model_comparison || []),
    [modelInfo]
  );

  const topFeatures = useMemo(
    () => (modelInfo?.feature_importance || []).slice(0, 10),
    [modelInfo]
  );

  const maxImportance = Math.max(
    ...topFeatures.map((item: FeatureImportanceItem) => Number(item.importance || 0)),
    0.01
  );

  const hasConfusionMatrix = Boolean(modelInfo?.confusion_matrix?.length);

  const trueNegative = getConfusionValue(
    modelInfo?.confusion_matrix,
    "actual_non_defective",
    "predicted_non_defective"
  );
  const falsePositive = getConfusionValue(
    modelInfo?.confusion_matrix,
    "actual_non_defective",
    "predicted_defective"
  );
  const falseNegative = getConfusionValue(
    modelInfo?.confusion_matrix,
    "actual_defective",
    "predicted_non_defective"
  );
  const truePositive = getConfusionValue(
    modelInfo?.confusion_matrix,
    "actual_defective",
    "predicted_defective"
  );

  return (
    <div className="page evaluation-page">
      <section className="evaluation-hero">
        <div>
          <span className="evaluation-kicker">Training Evidence</span>
          <h1>Model Evaluation</h1>
          <p>
            Review the dataset, model comparison, selected features, and validation
            evidence used to justify the deployed defect prediction model.
          </p>
        </div>
        <div className="evaluation-hero-card">
          <span>Active Model</span>
          <strong>{modelInfo?.model_name || "Not loaded"}</strong>
          <small>
            Threshold {formatMetric(modelInfo?.training_metadata?.prediction_threshold)}
          </small>
        </div>
      </section>

      {loading && <div className="evaluation-message">Loading evaluation evidence...</div>}
      {errorMessage && <div className="evaluation-message error">{errorMessage}</div>}

      {modelInfo && (
        <>
          <section className="evaluation-stat-grid">
            <div className="evaluation-stat">
              <span>Dataset Rows</span>
              <strong>{modelInfo.dataset_summary.total_rows}</strong>
              <small>Training examples</small>
            </div>
            <div className="evaluation-stat">
              <span>Defective Rows</span>
              <strong>{modelInfo.dataset_summary.defective_rows}</strong>
              <small>Positive class</small>
            </div>
            <div className="evaluation-stat">
              <span>Non-defective Rows</span>
              <strong>{modelInfo.dataset_summary.non_defective_rows}</strong>
              <small>Negative class</small>
            </div>
            <div className="evaluation-stat">
              <span>Repositories</span>
              <strong>{modelInfo.dataset_summary.repositories}</strong>
              <small>Source projects</small>
            </div>
          </section>

          <section className="evaluation-grid">
            <div className="evaluation-panel wide-panel">
              <div className="panel-heading">
                <div>
                  <h2>Model Comparison</h2>
                  <p>
                    Models are compared using held-out evaluation metrics. The best
                    model is selected by F1 because defect data is usually imbalanced.
                  </p>
                </div>
                {bestModel && <span className="model-pill">Best: {bestModel.model}</span>}
              </div>

              <div className="evaluation-table-scroll">
                <table className="evaluation-table">
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
                      <tr
                        key={item.model}
                        className={item.model === bestModel?.model ? "best-row" : ""}
                      >
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

            <div className="evaluation-panel">
              <h2>Metric Guide</h2>
              <div className="metric-note-list">
                {metricNotes.map((note) => (
                  <div className="metric-note" key={note.label}>
                    <strong>{note.label}</strong>
                    <p>{note.text}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="evaluation-grid">
            <div className="evaluation-panel">
              <h2>Confusion Matrix</h2>
              <p className="panel-copy">
                This shows how the best model behaved on the test split. It appears
                after retraining with the latest script.
              </p>
              {hasConfusionMatrix ? (
                <div className="confusion-grid">
                  <div className="confusion-cell correct">
                    <span>True Negative</span>
                    <strong>{trueNegative}</strong>
                    <small>Correctly safe</small>
                  </div>
                  <div className="confusion-cell warning">
                    <span>False Positive</span>
                    <strong>{falsePositive}</strong>
                    <small>Extra review</small>
                  </div>
                  <div className="confusion-cell danger">
                    <span>False Negative</span>
                    <strong>{falseNegative}</strong>
                    <small>Missed risk</small>
                  </div>
                  <div className="confusion-cell correct">
                    <span>True Positive</span>
                    <strong>{truePositive}</strong>
                    <small>Correctly risky</small>
                  </div>
                </div>
              ) : (
                <div className="missing-evidence">
                  Retrain the model to generate `results/github_confusion_matrix.csv`.
                </div>
              )}
            </div>

            <div className="evaluation-panel">
              <h2>Dataset Balance</h2>
              <p className="panel-copy">
                Defect datasets are rarely perfectly balanced. Precision, recall, F1,
                and PR-AUC are more informative than accuracy alone.
              </p>
              <div className="balance-chart">
                <div
                  className="balance-segment safe"
                  style={{
                    width: formatPercent(
                      modelInfo.dataset_summary.non_defective_rows /
                        Math.max(modelInfo.dataset_summary.total_rows, 1)
                    ),
                  }}
                />
                <div
                  className="balance-segment risky"
                  style={{
                    width: formatPercent(
                      modelInfo.dataset_summary.defective_rows /
                        Math.max(modelInfo.dataset_summary.total_rows, 1)
                    ),
                  }}
                />
              </div>
              <div className="balance-legend">
                <span>Non-defective {modelInfo.dataset_summary.non_defective_rows}</span>
                <span>Defective {modelInfo.dataset_summary.defective_rows}</span>
              </div>
            </div>
          </section>

          <section className="evaluation-grid">
            <div className="evaluation-panel wide-panel">
              <div className="panel-heading">
                <div>
                  <h2>Top Feature Importance</h2>
                  <p>
                    Importance explains the model globally. Individual predictions
                    can still depend on different features.
                  </p>
                </div>
              </div>
              <div className="feature-rank-list">
                {topFeatures.map((item) => {
                  const width = `${(Number(item.importance || 0) / maxImportance) * 100}%`;
                  return (
                    <div className="feature-rank" key={item.feature}>
                      <div>
                        <strong>{item.feature}</strong>
                        <span>{featureMeaning[item.feature] || "Model feature"}</span>
                      </div>
                      <div className="feature-rank-bar">
                        <span style={{ width }} />
                      </div>
                      <small>{formatPercent(item.importance)}</small>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="evaluation-panel">
              <h2>Training Configuration</h2>
              <div className="config-list">
                <div>
                  <span>Optimization</span>
                  <strong>
                    {modelInfo.training_metadata?.optimization ||
                      "Randomized search with validation threshold tuning"}
                  </strong>
                </div>
                <div>
                  <span>Random Seed</span>
                  <strong>{modelInfo.training_metadata?.random_state ?? 42}</strong>
                </div>
                <div>
                  <span>Selected Features</span>
                  <strong>{modelInfo.selected_features.length}</strong>
                </div>
                <div>
                  <span>Languages</span>
                  <strong>{modelInfo.dataset_summary.languages.join(", ")}</strong>
                </div>
              </div>
            </div>
          </section>

          <section className="evaluation-panel">
            <h2>Evaluation Interpretation</h2>
            <div className="interpretation-grid">
              <div>
                <strong>What this evidence supports</strong>
                <p>
                  The model has been compared against alternatives and selected
                  using measurable validation performance, not chosen arbitrarily.
                </p>
              </div>
              <div>
                <strong>What this evidence does not prove</strong>
                <p>
                  It does not guarantee that every high-risk file contains a defect.
                  The output should guide review priority, testing effort, and
                  investigation.
                </p>
              </div>
              <div>
                <strong>Why process metrics matter</strong>
                <p>
                  Commit history captures change frequency, previous bug-fix
                  activity, and churn, which are common signals in software defect
                  prediction research.
                </p>
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  );
}

export default ModelEvaluationPage;
