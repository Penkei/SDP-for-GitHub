import { useLocation, Link } from "react-router-dom";
import type { PredictionResponse } from "../types/prediction";
import PredictionTable from "../components/PredictionTable";

function PredictionResultPage() {
  const location = useLocation();

  const predictionResponse = location.state?.predictionResponse as
    | PredictionResponse
    | undefined;

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
        <h1>Prediction Result</h1>

        <p>
          Repository: <strong>{predictionResponse.repo_url}</strong>
        </p>

        <p>
          Commit / Branch: <strong>{predictionResponse.commit_sha}</strong>
        </p>

        <p>
          Total Java Files Scanned:{" "}
          <strong>{predictionResponse.total_files_scanned}</strong>
        </p>
      </div>

      <PredictionTable results={predictionResponse.results} />
    </div>
  );
}

export default PredictionResultPage;