import React, { useState } from "react";
import "./repo_input.css";

interface RepoInputProps {
  onContinue: (repoUrl: string, pat: string) => void;
}

const RepoInput: React.FC<RepoInputProps> = ({ onContinue }) => {
  const [repositoryUrl, setRepositoryUrl] = useState("");
  const [pat, setPat] = useState("");
  const [showPat, setShowPat] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onContinue(repositoryUrl, pat);
  };

  return (
    <div className="page-container section-fade">
      <div className="repo-input-card glass-card form-shell">
        <h2 className="repo-input-title">Repository Input</h2>
        <p className="repo-input-description">
          Enter your GitHub repository URL and Personal Access Token (PAT) to
          allow the system to retrieve repository data for defect prediction analysis.
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
              Paste the full GitHub repository link that you want to scan. For example:
              <span className="example-text"> https://github.com/facebook/react</span>
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
              A Personal Access Token is used to securely access GitHub repository data.
            </p>
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