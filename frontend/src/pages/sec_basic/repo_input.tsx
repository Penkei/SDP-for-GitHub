import React, { useState } from "react";
import "./repo_input.css";

const RepoInput: React.FC = () => {
  const [repositoryUrl, setRepositoryUrl] = useState("");
  const [pat, setPat] = useState("");
  const [showPat, setShowPat] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    console.log("Repository URL:", repositoryUrl);
    console.log("PAT:", pat);

    // Later you can replace this with API call or parent callback
    alert("Repository information submitted.");
  };

  return (
 <div className="page-container section-fade">
    <div className="repo-input-card glass-card form-shell">
        <h2 className="repo-input-title">Repository Input</h2>
        <p className="repo-input-description">
          Enter your GitHub repository URL and Personal Access Token (PAT) to
          allow the system to retrieve repository data for defect prediction
          analysis.
        </p>

        <form onSubmit={handleSubmit} className="repo-input-form">
          <div className="form-group">
            <label htmlFor="repositoryUrl" className="form-label">
              Repository URL
            </label>
            <input
              id="repositoryUrl"
              type="text"
              className="form-input"
              placeholder="Example: https://github.com/owner/repository-name"
              value={repositoryUrl}
              onChange={(e) => setRepositoryUrl(e.target.value)}
              required
            />
            <p className="input-help-text">
              Paste the full GitHub repository link that you want to scan. For
              example:{" "}
              <span className="example-text">
                https://github.com/facebook/react
              </span>
            </p>
          </div>

          <div className="form-group">
            <label htmlFor="pat" className="form-label">
              GitHub Personal Access Token (PAT)
            </label>

            <div className="password-input-wrapper">
              <input
                id="pat"
                type={showPat ? "text" : "password"}
                className="form-input"
                placeholder="Enter your GitHub Personal Access Token"
                value={pat}
                onChange={(e) => setPat(e.target.value)}
                required
              />
              <button
                type="button"
                className="toggle-btn"
                onClick={() => setShowPat(!showPat)}
              >
                {showPat ? "Hide" : "Show"}
              </button>
            </div>

            <p className="input-help-text">
              A Personal Access Token is used to securely access GitHub API data
              from your account. This helps the system read repository
              information, especially for private repositories or when API rate
              limits apply.
            </p>

            <div className="pat-info-box">
              <h4>How to create a GitHub PAT</h4>
              <ol>
                <li>Log in to your GitHub account.</li>
                <li>Go to Settings.</li>
                <li>Open Developer settings.</li>
                <li>Select Personal access tokens.</li>
                <li>Generate a new token.</li>
                <li>
                  Choose the required permissions, then copy and paste the token
                  here.
                </li>
              </ol>
              <p className="pat-note">
                Recommended: use a token with only the minimum permissions
                needed for repository reading.
              </p>
            </div>

            <div className="tutorial-image-section">
              <h4>PAT Tutorial Images</h4>
              <p className="input-help-text">
                You can place step-by-step tutorial screenshots here to guide
                users visually.
              </p>

              <div className="tutorial-image-placeholder">
                <span>Image Placeholder 1</span>
              </div>
              <div className="tutorial-image-placeholder">
                <span>Image Placeholder 2</span>
              </div>
            </div>
          </div>

          <div className="button-row">
            <button type="submit" className="submit-btn">
              Continue
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RepoInput;