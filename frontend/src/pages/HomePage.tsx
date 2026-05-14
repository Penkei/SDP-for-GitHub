import { Link } from "react-router-dom";

function HomePage() {
  return (
    <div className="page">
      <section className="hero">
        <h1>Program Defect Prediction for GitHub</h1>

        <p>
          This system uses a machine learning model to analyze Java, Python, and
          C++ files from a GitHub repository and predict potential defect risk at
          file level.
        </p>

        <div className="hero-actions">
          <Link to="/repository-input" className="primary-button">
            Start Prediction
          </Link>
        </div>
      </section>

      <section className="card-grid">
        <div className="card">
          <h3>Repository Input</h3>
          <p>Enter a GitHub repository URL and commit SHA or branch name.</p>
        </div>

        <div className="card">
          <h3>ML Prediction</h3>
          <p>The backend extracts code metrics and predicts file defect risk.</p>
        </div>

        <div className="card">
          <h3>Explainability</h3>
          <p>SHAP explanation shows which metrics contributed to the prediction.</p>
        </div>
      </section>
    </div>
  );
}

export default HomePage;
