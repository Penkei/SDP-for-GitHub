import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  deletePredictionHistoryItem,
  fetchPredictionHistory,
  fetchPredictionHistoryDetail,
  getApiErrorMessage,
} from "../services/api";
import type { PredictionHistorySummary } from "../types/prediction";

const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`;

const getRepoName = (repoUrl: string) => {
  const cleanUrl = repoUrl.replace(/\.git$/, "");
  const parts = cleanUrl.split("/").filter(Boolean);
  return parts.slice(-2).join("/");
};

function PredictionHistoryPage() {
  const navigate = useNavigate();
  const [historyItems, setHistoryItems] = useState<PredictionHistorySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [openingId, setOpeningId] = useState("");
  const [deletingId, setDeletingId] = useState("");

  const loadHistory = async () => {
    setLoading(true);
    setErrorMessage("");

    try {
      const response = await fetchPredictionHistory();
      setHistoryItems(response.history);
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Failed to load prediction history. Please check the backend server."
        )
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleOpenHistory = async (historyId: string) => {
    setOpeningId(historyId);
    setErrorMessage("");

    try {
      const prediction = await fetchPredictionHistoryDetail(historyId);

      navigate("/prediction-result", {
        state: {
          predictionResponse: prediction,
        },
      });
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(error, "Failed to open the selected prediction.")
      );
    } finally {
      setOpeningId("");
    }
  };

  const handleDeleteHistory = async (historyId: string) => {
    setDeletingId(historyId);
    setErrorMessage("");

    try {
      await deletePredictionHistoryItem(historyId);
      setHistoryItems((currentItems) =>
        currentItems.filter((item) => item.id !== historyId)
      );
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(error, "Failed to delete the selected prediction.")
      );
    } finally {
      setDeletingId("");
    }
  };

  return (
    <div className="page">
      <section className="history-header">
        <div>
          <h1>Prediction History</h1>
          <p>Review previous prediction runs stored in SQLite.</p>
        </div>
        <button className="secondary-button" onClick={loadHistory} disabled={loading}>
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </section>

      {errorMessage && <div className="error-box history-error">{errorMessage}</div>}

      {loading && (
        <div className="history-card">
          <p className="history-muted">Loading prediction history...</p>
        </div>
      )}

      {!loading && historyItems.length === 0 && (
        <div className="history-card">
          <h2>No History Yet</h2>
          <p className="history-muted">
            Completed predictions will appear here automatically.
          </p>
        </div>
      )}

      {!loading && historyItems.length > 0 && (
        <div className="history-list">
          {historyItems.map((item) => (
            <article className="history-card" key={item.id}>
              <div className="history-card-main">
                <div>
                  <h2>{getRepoName(item.repo_url)}</h2>
                  <p className="history-muted">{item.repo_url}</p>
                </div>

                <div className="history-meta-grid">
                  <div>
                    <span>Commit</span>
                    <strong>{item.commit_sha.slice(0, 8)}</strong>
                  </div>
                  <div>
                    <span>Scanned</span>
                    <strong>{new Date(item.scanned_at).toLocaleString()}</strong>
                  </div>
                  <div>
                    <span>Files</span>
                    <strong>{item.total_files_scanned}</strong>
                  </div>
                  <div>
                    <span>Threshold</span>
                    <strong>
                      {item.prediction_threshold !== null &&
                      item.prediction_threshold !== undefined
                        ? formatPercent(item.prediction_threshold)
                        : "Default"}
                    </strong>
                  </div>
                  <div>
                    <span>Avg Risk</span>
                    <strong>{formatPercent(item.average_risk_probability)}</strong>
                  </div>
                </div>
              </div>

              <div className="history-risk-row">
                <span className="history-risk high">High {item.high_risk_count}</span>
                <span className="history-risk medium">
                  Medium {item.medium_risk_count}
                </span>
                <span className="history-risk low">Low {item.low_risk_count}</span>
                <span className="history-risk defective">
                  Defective {item.defective_count}
                </span>
              </div>

              <div className="history-actions">
                <button
                  className="primary-button"
                  onClick={() => handleOpenHistory(item.id)}
                  disabled={openingId === item.id || deletingId === item.id}
                >
                  {openingId === item.id ? "Opening..." : "Open Result"}
                </button>
                <button
                  className="history-delete-button"
                  onClick={() => handleDeleteHistory(item.id)}
                  disabled={openingId === item.id || deletingId === item.id}
                >
                  {deletingId === item.id ? "Deleting..." : "Delete"}
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}

export default PredictionHistoryPage;
