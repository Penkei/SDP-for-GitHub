import { useEffect, useMemo, useState } from "react";
import { fetchModelTransparency } from "../services/api";
import type {
  FeatureImportanceItem,
  ModelComparisonItem,
  ModelTransparencyResponse,
} from "../types/prediction";

type HowSection = "guide" | "evaluation";

const formatMetric = (value?: number) => Number(value || 0).toFixed(3);
const formatPercent = (value?: number) => `${(Number(value || 0) * 100).toFixed(1)}%`;

const codeMetricDescriptions = [
  {
    name: "loc",
    meaning: "File size",
    detail: "A larger file usually takes longer to understand, review, and test.",
  },
  {
    name: "wmc",
    meaning: "Logic complexity",
    detail: "More branches and methods mean there are more paths where mistakes can hide.",
  },
  {
    name: "rfc",
    meaning: "Method interaction",
    detail: "A file that calls many methods can be harder to change safely.",
  },
  {
    name: "cbo",
    meaning: "Coupling",
    detail: "More dependency connections can make one file affect more parts of the project.",
  },
  {
    name: "comparisonsQty",
    meaning: "Decision checks",
    detail: "Many comparisons often mean more conditions to test.",
  },
  {
    name: "returnQty",
    meaning: "Return paths",
    detail: "Many return points can make edge cases easier to miss.",
  },
  {
    name: "file_change_count",
    meaning: "Past file changes",
    detail: "A file changed many times may be unstable or important to the system.",
  },
  {
    name: "file_bug_fix_count",
    meaning: "Past bug fixes",
    detail: "A file fixed many times before may deserve closer review.",
  },
  {
    name: "recent_file_change_count",
    meaning: "Recent activity",
    detail: "Files changing frequently in recent commits may carry more risk.",
  },
  {
    name: "last_change_churn",
    meaning: "Previous code churn",
    detail: "Large recent edits can increase the chance of missed side effects.",
  },
];

const evaluationMetricNotes = [
  {
    label: "Accuracy",
    text: "The percentage of total predictions that were correct. Useful, but not enough by itself when the dataset is imbalanced.",
  },
  {
    label: "Precision",
    text: "When the model says a file is defective, precision tells how often that warning is correct.",
  },
  {
    label: "Recall",
    text: "Recall tells how many truly defective examples the model manages to catch.",
  },
  {
    label: "F1",
    text: "F1 balances precision and recall. It is a useful score when both false alarms and missed defects matter.",
  },
  {
    label: "PR-AUC",
    text: "PR-AUC focuses on how well the model ranks the defective class, which is important for defect prediction.",
  },
];

const featureMeaning: Record<string, string> = {
  nosi: "Static call usage",
  dit: "Inheritance depth",
  cbo: "Coupling",
  rfc: "Method interaction",
  loc: "File size",
  comparisonsQty: "Decision checks",
  returnQty: "Return paths",
  wmc: "Logic complexity",
  lcom: "Cohesion weakness",
  totalMethods: "Method count",
  file_change_count: "Past file changes",
  file_bug_fix_count: "Past bug fixes",
  recent_file_change_count: "Recent file changes",
  days_since_last_change: "Age since previous change",
  last_change_lines_added: "Previous added lines",
  last_change_lines_deleted: "Previous deleted lines",
  last_change_churn: "Previous code churn",
  last_change_file_count: "Previous commit size",
  author_file_change_count: "Author history with file",
};

const getFeatureMeaning = (feature: string) =>
  featureMeaning[feature] || "Model input feature";

const getBestModel = (items: ModelComparisonItem[]) => {
  if (!items.length) {
    return null;
  }

  return [...items].sort((a, b) => Number(b.f1 || 0) - Number(a.f1 || 0))[0];
};

const getConfusionValue = (
  rows: Array<Record<string, number | string>> | undefined,
  rowName: string,
  columnName: string
) => {
  if (!rows?.length) {
    return 0;
  }

  const row = rows.find((item) =>
    Object.values(item).some((value) => String(value) === rowName)
  );

  return Number(row?.[columnName] || 0);
};

function HowItWorksPage() {
  const [activeSection, setActiveSection] = useState<HowSection>("guide");
  const [modelInfo, setModelInfo] = useState<ModelTransparencyResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const loadModelInfo = async () => {
      try {
        const response = await fetchModelTransparency();
        setModelInfo(response);
      } catch (error) {
        setErrorMessage("Model evidence could not be loaded from the backend. This may happen because the application runs on Render's free plan. Please wait approximately 1 minutes and try again.");
      } finally {
        setLoading(false);
      }
    };

    loadModelInfo();
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
    <div className="page">
      <section className="how-hero">
        <div>
          <span className="how-kicker">Developer Guide</span>
          <h1>How It Works</h1>
          <p>
            SDP for GitHub checks the files changed in a selected commit, measures
            code and commit-history signals, then estimates which files deserve
            closer review.
          </p>
        </div>
        <div className="how-section-switch" aria-label="How It Works sections">
          <button
            className={activeSection === "guide" ? "active" : ""}
            onClick={() => setActiveSection("guide")}
          >
            How It Works
          </button>
          <button
            className={activeSection === "evaluation" ? "active" : ""}
            onClick={() => setActiveSection("evaluation")}
          >
            Model Evaluation
          </button>
        </div>
      </section>

      {loading && <div className="info-box">Loading model evidence... This may take approximately 1 minute when the Render free-plan server is waking up.</div>}
      {errorMessage && <div className="info-box">{errorMessage}</div>}

      {activeSection === "guide" ? (
        <>
          <section className="developer-flow">
            <div className="flow-step">
              <span>1</span>
              <h2>Select A Commit</h2>
              <p>Choose a public GitHub repository, branch or tag, then select a commit.</p>
            </div>
            <div className="flow-step">
              <span>2</span>
              <h2>Measure Files</h2>
              <p>The backend reads changed Java, Python, and C++ files and collects metrics.</p>
            </div>
            <div className="flow-step">
              <span>3</span>
              <h2>Predict Risk</h2>
              <p>The model compares those metrics with patterns learned from training data.</p>
            </div>
            <div className="flow-step">
              <span>4</span>
              <h2>Review Smarter</h2>
              <p>Use high-risk files as a priority list for review and testing.</p>
            </div>
          </section>

          <section className="how-grid">
            <div className="how-card">
              <h2>What The Prediction Means</h2>
              <p>
                The result is not saying, "this file definitely has a bug." It is
                saying, "this file looks similar to files that were risky in the
                training data." Treat it like a warning light, not a final verdict.
              </p>
              <div className="risk-meaning-list">
                <div>
                  <strong>High</strong>
                  <span>Review this file first, especially before merge or release.</span>
                </div>
                <div>
                  <strong>Medium</strong>
                  <span>Check important logic and recent changes when time allows.</span>
                </div>
                <div>
                  <strong>Low</strong>
                  <span>Lower priority, but still monitor it if the file keeps changing.</span>
                </div>
              </div>
            </div>

            <div className="how-card">
              <h2>How A Developer Should Use It</h2>
              <ul className="how-list">
                <li>Start with the highest-risk files in the dashboard.</li>
                <li>Read the explanation to see which metrics pushed the result.</li>
                <li>Use the result to decide where to review, test, or refactor first.</li>
                <li>Do not reject code only because the model marks it as high risk.</li>
              </ul>
            </div>
          </section>

          <section className="how-card">
            <h2>Metrics In Plain Language</h2>
            <p className="section-intro">
              The model does not understand code like a human. It uses numbers that
              often describe how difficult a file is to understand, change, or test.
            </p>
            <div className="metric-explainer-grid">
              {codeMetricDescriptions.map((metric) => (
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
                The current version supports Java, Python, and C++ source files.
                Different languages are mapped into a shared set of metrics so the
                prediction process stays consistent.
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
                <li>The model cannot see runtime crashes, user behavior, or production logs.</li>
                <li>Training labels come from GitHub commit history, so some labels may be noisy.</li>
                <li>A high score means "review this first," not "this is certainly broken."</li>
                <li>Results are better when training data is close to the project being analyzed.</li>
              </ul>
            </div>
          </section>
        </>
      ) : (
        <>
          <section className="how-card">
            <div className="evidence-header">
              <div>
                <h2>Model Evaluation</h2>
                <p>
                  This section explains how the model was checked before being used
                  for prediction. It is here to show that the selected model was
                  compared with alternatives instead of chosen randomly.
                </p>
              </div>
              {modelInfo && <strong>{modelInfo.model_name}</strong>}
            </div>

            {modelInfo && (
              <div className="evidence-summary-grid">
                <div className="evidence-stat-card">
                  <span>Dataset Rows</span>
                  <strong>{modelInfo.dataset_summary.total_rows}</strong>
                  <small>File examples used for training</small>
                </div>
                <div className="evidence-stat-card">
                  <span>Defective Rows</span>
                  <strong>{modelInfo.dataset_summary.defective_rows}</strong>
                  <small>Examples linked to bug-fix commits</small>
                </div>
                <div className="evidence-stat-card">
                  <span>Non-defective Rows</span>
                  <strong>{modelInfo.dataset_summary.non_defective_rows}</strong>
                  <small>Examples from normal changes</small>
                </div>
                <div className="evidence-stat-card">
                  <span>Repositories</span>
                  <strong>{modelInfo.dataset_summary.repositories}</strong>
                  <small>Projects included in the dataset</small>
                </div>
              </div>
            )}
          </section>

          {modelInfo && (
            <>
              <section className="how-grid evaluation-grid">
                <div className="how-card">
                  <div className="evidence-header compact">
                    <div>
                      <h2>Model Comparison</h2>
                      <p>
                        The training script tests several algorithms. The best model
                        is selected mainly by F1 score because defect data is usually
                        unbalanced.
                      </p>
                    </div>
                    {bestModel && <strong>Best: {bestModel.model}</strong>}
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

                <div className="how-card">
                  <h2>Metric Guide</h2>
                  <div className="model-metric-guide">
                    {evaluationMetricNotes.map((note) => (
                      <div className="model-metric-card" key={note.label}>
                        <strong>{note.label}</strong>
                        <p>{note.text}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </section>

              <section className="how-grid">
                <div className="how-card">
                  <h2>Confusion Matrix</h2>
                  <p className="section-intro">
                    This shows what the model got right and wrong on the test set.
                    It appears after retraining with the latest training script.
                  </p>
                  {hasConfusionMatrix ? (
                    <div className="confusion-grid">
                      <div className="confusion-cell correct">
                        <span>True Negative</span>
                        <strong>{trueNegative}</strong>
                        <small>Correctly predicted non-defective</small>
                      </div>
                      <div className="confusion-cell warning">
                        <span>False Positive</span>
                        <strong>{falsePositive}</strong>
                        <small>Flagged for review but not defective</small>
                      </div>
                      <div className="confusion-cell danger">
                        <span>False Negative</span>
                        <strong>{falseNegative}</strong>
                        <small>Defective example missed by model</small>
                      </div>
                      <div className="confusion-cell correct">
                        <span>True Positive</span>
                        <strong>{truePositive}</strong>
                        <small>Correctly predicted defective</small>
                      </div>
                    </div>
                  ) : (
                    <div className="missing-evidence">
                      Retrain the model to generate the confusion matrix file.
                    </div>
                  )}
                </div>

                <div className="how-card">
                  <h2>Dataset Balance</h2>
                  <p className="section-intro">
                    Defect datasets often have more normal examples than defective
                    examples. That is why recall, precision, F1, and PR-AUC matter.
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

              <section className="how-grid">
                <div className="how-card">
                  <h2>Top Feature Importance</h2>
                  <p className="section-intro">
                    Feature importance shows which inputs mattered most overall
                    during training. It does not mean every single prediction uses
                    the same reason.
                  </p>
                  <div className="feature-rank-list">
                    {topFeatures.map((item) => {
                      const width = `${(Number(item.importance || 0) / maxImportance) * 100}%`;
                      return (
                        <div className="feature-rank" key={item.feature}>
                          <div>
                            <strong>{item.feature}</strong>
                            <span>{getFeatureMeaning(item.feature)}</span>
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

                <div className="how-card">
                  <h2>Training Setup</h2>
                  <div className="selected-feature-grid">
                    <div className="selected-feature-card">
                      <span>Optimization</span>
                      <strong>
                        {modelInfo.training_metadata?.optimization ||
                          "Randomized search with validation threshold tuning"}
                      </strong>
                      <p>The script tries multiple settings and keeps the best result.</p>
                    </div>
                    <div className="selected-feature-card">
                      <span>Selected Features</span>
                      <strong>{modelInfo.selected_features.length}</strong>
                      <p>These are the numeric inputs given to the model.</p>
                    </div>
                    <div className="selected-feature-card">
                      <span>Languages</span>
                      <strong>{modelInfo.dataset_summary.languages.join(", ")}</strong>
                      <p>These languages appear in the current training dataset.</p>
                    </div>
                  </div>
                </div>
              </section>

            </>
          )}
        </>
      )}
    </div>
  );
}

export default HowItWorksPage;
