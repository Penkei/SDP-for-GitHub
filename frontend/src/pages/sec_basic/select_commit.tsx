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
  const [loadingBranches, setLoadingBranches] = useState(false);
  const [loadingCommits, setLoadingCommits] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

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
        fetchCommits(firstBranch);
      }
    } catch (error) {
      setErrorMessage("Unable to connect to backend.");
    } finally {
      setLoadingBranches(false);
    }
  };

  const fetchCommits = async (branch: string) => {
    try {
      setLoadingCommits(true);
      setErrorMessage("");
      setSelectedCommit("");
      setCommits([]);

      const response = await fetch("http://127.0.0.1:8000/api/repository/commits", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          repoUrl,
          pat,
          branch
        })
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        setErrorMessage(result.detail || result.message || "Failed to load commits.");
        return;
      }

      setCommits(result.data.commits || []);
    } catch (error) {
      setErrorMessage("Unable to connect to backend.");
    } finally {
      setLoadingCommits(false);
    }
  };

  const handleBranchChange = async (event: React.ChangeEvent<HTMLSelectElement>) => {
    const branch = event.target.value;
    setSelectedBranch(branch);
    await fetchCommits(branch);
  };

  const handleScan = () => {
    if (!selectedCommit) {
      alert("Please select a commit to scan.");
      return;
    }

    const commitData = commits.find((commit) => commit.sha === selectedCommit);
    console.log("Selected branch:", selectedBranch);
    console.log("Selected commit:", commitData);

    alert("Commit selected successfully. Next step: Analysis Running.");
  };

  return (
    <div className="page-container section-fade">
      <div className="select-commit-card glass-card form-shell">
        <h2 className="select-commit-title">Select Commit to Scan</h2>
        <p className="select-commit-description">
          Choose a branch first, then select the commit you want to scan for defect prediction.
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
          <label className="form-label">Commit List</label>

          {loadingCommits ? (
            <p className="loading-text">Loading commits...</p>
          ) : commits.length === 0 ? (
            <div className="empty-box">No commits found for this branch.</div>
          ) : (
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
                    onChange={() => setSelectedCommit(commit.sha)}
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
          )}
        </div>

        <div className="button-row">
          <button
            type="button"
            className="submit-btn"
            onClick={handleScan}
            disabled={!selectedCommit}
          >
            Scan Selected Commit
          </button>
        </div>
      </div>
    </div>
  );
};

export default SelectCommit;