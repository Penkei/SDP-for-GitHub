import React, { useEffect, useState } from "react";
import "./select_commit.css";

interface BranchItem {
  name: string;
}

interface CommitItem {
  sha: string;
  message: string;
  author: string;
  date: string;
}

interface SelectCommitProps {
  repoUrl: string;
  pat: string;
}

const SelectCommit: React.FC<SelectCommitProps> = ({ repoUrl, pat }) => {
  const [branches, setBranches] = useState<BranchItem[]>([]);
  const [selectedBranch, setSelectedBranch] = useState("");
  const [commits, setCommits] = useState<CommitItem[]>([]);
  const [selectedCommit, setSelectedCommit] = useState("");
  const [selectedCommitDetails, setSelectedCommitDetails] = useState<CommitItem | null>(null);
  const [manualSha, setManualSha] = useState("");
  const [loadingBranches, setLoadingBranches] = useState(false);
  const [loadingCommits, setLoadingCommits] = useState(false);
  const [loadingSha, setLoadingSha] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [shaError, setShaError] = useState("");
  const commitsPerPage = 20;
  const startCommitNumber = (currentPage - 1) * commitsPerPage + 1;
  const endCommitNumber = (currentPage - 1) * commitsPerPage + commits.length;

  useEffect(() => {
    if (repoUrl && pat) {
      fetchBranches();
    }
  }, [repoUrl, pat]);

  const fetchBranches = async () => {
    try {
      setLoadingBranches(true);
      setErrorMessage("");

      const response = await fetch("http://127.0.0.1:8000/api/repository/branches", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          repoUrl,
          pat
        })
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        setErrorMessage(result.detail || result.message || "Failed to load branches.");
        return;
      }

      const fetchedBranches = result.data.branches || [];
      setBranches(fetchedBranches);

      if (fetchedBranches.length > 0) {
        const firstBranch = fetchedBranches[0].name;
        setSelectedBranch(firstBranch);
        fetchCommits(firstBranch, 1);
      }
    } catch {
      setErrorMessage("Unable to connect to backend.");
    } finally {
      setLoadingBranches(false);
    }
  };

  const fetchCommits = async (branch: string, page: number = 1) => {
    try {
      setLoadingCommits(true);
      setErrorMessage("");
      setSelectedCommit("");
      setSelectedCommitDetails(null);
      setManualSha("");

      const response = await fetch("http://127.0.0.1:8000/api/repository/commits", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          repoUrl,
          pat,
          branch,
          page,
          per_page: commitsPerPage
        })
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        setErrorMessage(result.detail || result.message || "Failed to load commits.");
        return;
      }

      setCommits(result.data.commits || []);
      setCurrentPage(page);
    } catch {
      setErrorMessage("Unable to connect to backend.");
    } finally {
      setLoadingCommits(false);
    }
  };

  const handleBranchChange = async (event: React.ChangeEvent<HTMLSelectElement>) => {
    const branch = event.target.value;
    setSelectedBranch(branch);
    setCurrentPage(1);
    await fetchCommits(branch, 1);
  };

  const handleCommitSelect = (commit: CommitItem) => {
    setSelectedCommit(commit.sha);
    setSelectedCommitDetails(commit);
    setManualSha("");
  };

  const handleManualShaSelect = async () => {
    const trimmedSha = manualSha.trim();

    if (!trimmedSha) {
      setShaError("Please enter a commit SHA.");
      return;
    }

    if (!/^[a-fA-F0-9]{7,40}$/.test(trimmedSha)) {
      setShaError("Invalid SHA format.");
      return;
    }

    try {
      setLoadingSha(true);
      setErrorMessage("");
      setShaError("");
      setSelectedCommitDetails(null);

      const response = await fetch("http://127.0.0.1:8000/api/repository/commit-by-sha", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          repoUrl,
          pat,
          sha: trimmedSha
        })
    });

    const result = await response.json();

    if (!response.ok || !result.success) {
      setShaError(`No commit found for SHA: "${trimmedSha}"`);
      return;
    }

    setSelectedCommit(result.data.sha);
    setSelectedCommitDetails(result.data);
  } catch {
    setShaError("Unable to validate commit SHA.");
  } finally {
    setLoadingSha(false);
  }
};

  const handleScan = () => {
    if (!selectedCommit || !selectedCommitDetails) {
      alert("Please select a commit or enter a valid commit SHA.");
      return;
    }

    console.log("Selected branch:", selectedBranch);
    console.log("Selected commit:", selectedCommitDetails);

    alert("Commit selected successfully. Next step: Analysis Running.");
  };

  return (
    <div className="page-container section-fade">
      <div className="select-commit-card glass-card form-shell">
        <h2 className="select-commit-title">Select Commit to Scan</h2>
        <p className="select-commit-description">
          Choose a branch first, then select a commit from the list or paste an exact commit SHA.
        </p>

        {errorMessage && <div className="error-box">{errorMessage}</div>}

        <div className="select-commit-section">
          <label className="form-label" htmlFor="branchSelect">
            Branch
          </label>
          <select
            id="branchSelect"
            className="form-select"
            value={selectedBranch}
            onChange={handleBranchChange}
            disabled={loadingBranches || branches.length === 0}
          >
            {branches.length === 0 ? (
              <option value="">No branches available</option>
            ) : (
              branches.map((branch) => (
                <option key={branch.name} value={branch.name}>
                  {branch.name}
                </option>
              ))
            )}
          </select>
          {loadingBranches && <p className="loading-text">Loading branches...</p>}
        </div>

        <div className="select-commit-section">
          <label htmlFor="manualSha" className="form-label">
            Enter Commit SHA Manually
          </label>

          <div className="manual-sha-row">
            <input
              id="manualSha"
              type="text"
              className="form-input"
              placeholder="Paste full commit SHA here"
              value={manualSha}
              onChange={(e) => setManualSha(e.target.value)}
            />

            <button
              type="button"
              className="secondary-btn"
              onClick={handleManualShaSelect}
              disabled={loadingSha}
            >
              {loadingSha ? "Checking..." : "Use SHA"}
            </button>
          </div>

          <p className="input-help-text">
            If you already know the commit SHA, paste it here and the system will validate it.
          </p>
        </div>

        {(selectedCommitDetails || shaError) && (
          <div className={`selected-commit-box ${shaError ? "error" : ""}`}>
            <div className="selected-commit-title-text">
              {shaError ? "Commit Not Found" : "Selected Commit"}
            </div>

            {shaError ? (
              <div className="selected-commit-error">
                {shaError}
              </div>
            ) : (
              <>
                <div className="selected-commit-message">
                  {selectedCommitDetails?.message}
                </div>

                <div className="selected-commit-meta">
                  <span><strong>SHA:</strong> {selectedCommitDetails?.sha}</span>
                  <span><strong>Author:</strong> {selectedCommitDetails?.author}</span>
                  <span>
                    <strong>Date:</strong>{" "}
                    {new Date(selectedCommitDetails!.date).toLocaleString()}
                  </span>
                </div>
              </>
            )}
          </div>
        )}

        <div className="select-commit-section">
          <label className="form-label">Commit List</label>

          {loadingCommits ? (
            <p className="loading-text">Loading commits...</p>
          ) : commits.length === 0 ? (
            <div className="empty-box">No commits found for this branch.</div>
          ) : (
            <>
              <div className="commit-list">
                {commits.map((commit) => (
                  <label
                    key={commit.sha}
                    className={`commit-item ${
                      selectedCommit === commit.sha ? "selected" : ""
                    }`}
                  >
                    <input
                      type="radio"
                      name="selectedCommit"
                      value={commit.sha}
                      checked={selectedCommit === commit.sha}
                      onChange={() => handleCommitSelect(commit)}
                    />

                    <div className="commit-content">
                      <div className="commit-message">{commit.message}</div>
                      <div className="commit-meta">
                        <span>
                          <strong>SHA:</strong> {commit.sha.substring(0, 7)}
                        </span>
                        <span>
                          <strong>Author:</strong> {commit.author}
                        </span>
                        <span>
                          <strong>Date:</strong> {new Date(commit.date).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </label>
                ))}
              </div>

              <div className="pagination">
                <button
                  disabled={currentPage === 1}
                  onClick={() => fetchCommits(selectedBranch, currentPage - 1)}
                >
                  Prev
                </button>

                <span className="pagination-range">
                  {commits.length > 0
                    ? `Showing commits ${startCommitNumber}–${endCommitNumber}`
                    : "No commits"}
                </span>

                <button
                  disabled={commits.length < commitsPerPage}
                  onClick={() => fetchCommits(selectedBranch, currentPage + 1)}
                >
                  Next
                </button>
              </div>
            </>
          )}
        </div>

        <div className="button-row">
          <button
            type="button"
            className="submit-btn"
            onClick={handleScan}
            disabled={!selectedCommitDetails}
          >
            Scan Selected Commit
          </button>
        </div>
      </div>
    </div>
  );
};

export default SelectCommit;