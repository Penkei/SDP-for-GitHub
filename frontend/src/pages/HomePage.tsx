import { Link } from "react-router-dom";

function HomePage() {
  return (
    <div className="page">
      <section className="hero home-hero">
        <span className="home-eyebrow">Software Defect Prediction</span>
        <h1>Understand GitHub code risk before review</h1>

        <p>
          SDP for GitHub checks Java, Python, and C++ files in a selected
          repository commit. It estimates which files may be more likely to
          contain defects, explains the important metrics behind the result, and
          helps developers decide what to review first.
        </p>

        <div className="hero-actions">
          <Link to="/repository-input" className="primary-button">
            Start Prediction
          </Link>

          <Link to="/how-it-works" className="secondary-home-link">
            How It Works
          </Link>
        </div>
      </section>

      <section className="home-intro-grid" aria-label="Application overview">
        <div className="home-intro-panel">
          <h2>What the application does</h2>
          <p>
            The app reads source files from a GitHub commit, extracts code and
            commit-history metrics, then sends those metrics into a trained
            machine learning model.
          </p>
          <p>
            The output is not a final bug report. It is a risk estimate that
            helps developers focus review time on files that deserve more
            attention.
          </p>
        </div>

        <div className="home-intro-panel">
          <h2>What you get back</h2>
          <ul>
            <li>Risk probability for each supported file.</li>
            <li>High, medium, or low risk category.</li>
            <li>Plain-language explanation of why the file was marked risky.</li>
            <li>Dashboard charts, filtering, selection, and export options.</li>
          </ul>
        </div>
      </section>

      <section className="card-grid home-card-grid">
        <div className="card home-step-card">
          <span>1</span>
          <h3>Choose Repository</h3>
          <p>
            Enter a GitHub repository URL, select a branch, tag, or commit, then
            run prediction on the selected version of the code.
          </p>
        </div>

        <div className="card home-step-card">
          <span>2</span>
          <h3>Extract Metrics</h3>
          <p>
            The backend measures file size, complexity, conditional checks,
            method structure, and commit-history activity for supported files.
          </p>
        </div>

        <div className="card home-step-card">
          <span>3</span>
          <h3>Review Risk</h3>
          <p>
            The model predicts file-level defect risk and shows which metric
            values influenced the result, so the output is easier to understand.
          </p>
        </div>
      </section>

      <section className="home-concept-grid" aria-label="Key concepts">
        <div className="home-concept">
          <h3>Risk probability</h3>
          <p>
            A percentage showing how strongly the model thinks a file matches
            patterns seen in defective files during training.
          </p>
        </div>

        <div className="home-concept">
          <h3>Prediction threshold</h3>
          <p>
            The cut-off used to decide whether a file is labelled defective. For
            example, a 36% threshold means files at or above 36% are marked as
            defective by the app.
          </p>
        </div>

        <div className="home-concept">
          <h3>SHAP explanation</h3>
          <p>
            SHAP helps explain a model decision by showing which metrics pushed
            the prediction higher or lower for a specific file.
          </p>
        </div>
      </section>
    </div>
  );
}

export default HomePage;
