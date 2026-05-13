import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  fetchBranches,
  fetchCommits,
  fetchPredictionJob,
  fetchTags,
  getApiErrorMessage,
  startPredictionJob,
} from "../services/api";
import type {
  CommitItem,
  GitRefItem,
} from "../types/prediction";
import CommitSidePanel from "../components/CommitSidePanel";
import GitRefSidePanel from "../components/GitRefSidePanel";

function RepositoryInputPage() {
  const navigate = useNavigate();

  const [repoUrl, setRepoUrl] = useState("");
  const [selectedGitRef, setSelectedGitRef] = useState("");
  const [selectedGitRefType, setSelectedGitRefType] = useState("");
  const [commitSha, setCommitSha] = useState("");

  const [loadingPrediction, setLoadingPrediction] = useState(false);
  const [loadingCommits, setLoadingCommits] = useState(false);
  const [loadingRefs, setLoadingRefs] = useState(false);
  const [predictionProgress, setPredictionProgress] = useState({
    percent: 0,
    stage: "idle",
    message: "",
  });

  const [errorMessage, setErrorMessage] = useState("");
  const [commitErrorMessage, setCommitErrorMessage] = useState("");
  const [refErrorMessage, setRefErrorMessage] = useState("");

  const [isCommitPanelOpen, setIsCommitPanelOpen] = useState(false);
  const [isRefPanelOpen, setIsRefPanelOpen] = useState(false);

  const [refPanelTitle, setRefPanelTitle] = useState("Select Branch / Tag");
  const [commits, setCommits] = useState<CommitItem[]>([]);
  const [refs, setRefs] = useState<GitRefItem[]>([]);

  const [commitPage, setCommitPage] = useState(1);
  const [hasNextCommitPage, setHasNextCommitPage] = useState(false);

  const commitPageSize = 20;

  const validateRepoUrl = () => {
    if (!repoUrl.trim()) {
      setErrorMessage("Please enter a GitHub repository URL first.");
      return false;
    }

    return true;
  };

  const validateGitRef = () => {
    if (!selectedGitRef.trim()) {
      setErrorMessage("Please select a branch or tag first.");
      return false;
    }

    return true;
  };

  const handleLoadBranches = async () => {
    if (!validateRepoUrl()) {
      return;
    }

    setErrorMessage("");
    setRefErrorMessage("");
    setRefs([]);
    setRefPanelTitle("Select Branch");
    setIsRefPanelOpen(true);
    setLoadingRefs(true);

    try {
      const response = await fetchBranches(repoUrl.trim());
      setRefs(response.branches);
    } catch (error) {
      setRefErrorMessage(
        getApiErrorMessage(
          error,
          "Failed to load branches. Please check the repository URL or backend server."
        )
      );
    } finally {
      setLoadingRefs(false);
    }
  };

  const handleLoadTags = async () => {
    if (!validateRepoUrl()) {
      return;
    }

    setErrorMessage("");
    setRefErrorMessage("");
    setRefs([]);
    setRefPanelTitle("Select Tag");
    setIsRefPanelOpen(true);
    setLoadingRefs(true);

    try {
      const response = await fetchTags(repoUrl.trim());
      setRefs(response.tags);
    } catch (error) {
      setRefErrorMessage(
        getApiErrorMessage(
          error,
          "Failed to load tags. Please check the repository URL or backend server."
        )
      );
    } finally {
      setLoadingRefs(false);
    }
  };

  const handleSelectRef = (ref: GitRefItem) => {
    setSelectedGitRef(ref.name);
    setSelectedGitRefType(ref.type);
    setCommitSha("");
    setCommits([]);
    setCommitPage(1);
    setHasNextCommitPage(false);
    setIsRefPanelOpen(false);
  };

  const loadCommitPage = async (page: number) => {
    if (!validateRepoUrl() || !validateGitRef()) {
      return;
    }

    const skip = (page - 1) * commitPageSize;

    setErrorMessage("");
    setCommitErrorMessage("");
    setCommits([]);
    setIsCommitPanelOpen(true);
    setLoadingCommits(true);

    try {
      const response = await fetchCommits(
        repoUrl.trim(),
        selectedGitRef.trim(),
        commitPageSize,
        skip
      );

      setCommits(response.commits);
      setCommitPage(page);
      setHasNextCommitPage(response.commits.length === commitPageSize);
    } catch (error) {
      setCommitErrorMessage(
        getApiErrorMessage(
          error,
          "Failed to load commits for the selected branch/tag. Please check the repository URL or backend server."
        )
      );
    } finally {
      setLoadingCommits(false);
    }
  };

  const handleLoadCommits = async () => {
    await loadCommitPage(1);
  };

  const handleNextCommitPage = async () => {
    await loadCommitPage(commitPage + 1);
  };

  const handlePreviousCommitPage = async () => {
    if (commitPage > 1) {
      await loadCommitPage(commitPage - 1);
    }
  };

  const handleSelectCommit = (commit: CommitItem) => {
    setCommitSha(commit.sha);
    setIsCommitPanelOpen(false);
  };

  const handleRunPrediction = async () => {
    if (!repoUrl.trim() || !commitSha.trim()) {
      setErrorMessage(
        "Please enter repository URL, select a branch/tag, and select a commit."
      );
      return;
    }

    setLoadingPrediction(true);
    setErrorMessage("");
    setPredictionProgress({
      percent: 0,
      stage: "queued",
      message: "Submitting prediction job",
    });

    try {
      const startedJob = await startPredictionJob({
        repo_url: repoUrl.trim(),
        commit_sha: commitSha.trim(),
      });

      setPredictionProgress({
        percent: startedJob.progress_percent,
        stage: startedJob.stage,
        message: startedJob.message,
      });

      let currentJob = startedJob;

      while (
        currentJob.status !== "completed" &&
        currentJob.status !== "failed"
      ) {
        await new Promise((resolve) => setTimeout(resolve, 900));
        currentJob = await fetchPredictionJob(currentJob.job_id);

        setPredictionProgress({
          percent: currentJob.progress_percent,
          stage: currentJob.stage,
          message: currentJob.message,
        });
      }

      if (currentJob.status === "failed" || !currentJob.result) {
        throw new Error(currentJob.error || "Prediction failed");
      }

      navigate("/prediction-result", {
        state: {
          predictionResponse: currentJob.result,
        },
      });
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Prediction failed. Please check the backend server and input values."
        )
      );
    } finally {
      setLoadingPrediction(false);
    }
  };

  return (
    <div className="page">
      <div className="form-card">
        <h1>Repository Input</h1>

        <p className="page-description">
          Enter a GitHub repository URL, select a branch or tag, then load and
          select a commit for defect prediction.
        </p>

        <label>GitHub Repository URL</label>
        <input
          type="text"
          value={repoUrl}
          onChange={(e) => {
            setRepoUrl(e.target.value);
            setSelectedGitRef("");
            setSelectedGitRefType("");
            setCommitSha("");
            setCommits([]);
          }}
          placeholder="https://github.com/apache/commons-lang.git"
        />

        <div className="button-row two-columns">
          <button
            className="secondary-button"
            onClick={handleLoadBranches}
            disabled={loadingRefs || loadingCommits || loadingPrediction}
          >
            Load Branches
          </button>

          <button
            className="secondary-button"
            onClick={handleLoadTags}
            disabled={loadingRefs || loadingCommits || loadingPrediction}
          >
            Load Tags
          </button>
        </div>

        <label>Selected Branch / Tag</label>
        <input
          type="text"
          value={
            selectedGitRef
              ? `${selectedGitRefType}: ${selectedGitRef}`
              : ""
          }
          readOnly
          placeholder="Select a branch or tag first"
        />

        <button
          className="secondary-button full-width"
          onClick={handleLoadCommits}
          disabled={
            loadingRefs ||
            loadingCommits ||
            loadingPrediction ||
            !selectedGitRef
          }
        >
          {loadingCommits ? "Loading Commits..." : "Load Commits from Selected Branch/Tag"}
        </button>

        <label>Selected Commit SHA</label>
        <input
          type="text"
          value={commitSha}
          onChange={(e) => setCommitSha(e.target.value)}
          placeholder="Select commit from the right-side panel"
        />

        {errorMessage && <div className="error-box">{errorMessage}</div>}

        <button
          className="primary-button full-width"
          onClick={handleRunPrediction}
          disabled={loadingPrediction || loadingCommits || loadingRefs}
        >
          {loadingPrediction ? "Analyzing Repository..." : "Run Prediction"}
        </button>

        {loadingPrediction && (
          <div className="loading-box">
            <div className="progress-status-header">
              <strong>{predictionProgress.message}</strong>
              <span>{predictionProgress.percent}%</span>
            </div>
            <div className="progress-bar">
              <div
                className="progress-bar-fill determinate"
                style={{ width: `${predictionProgress.percent}%` }}
              ></div>
            </div>
            <ol className="progress-steps">
              <li className={predictionProgress.percent >= 5 ? "active" : ""}>
                Starting
              </li>
              <li className={predictionProgress.percent >= 15 ? "active" : ""}>
                Cloning
              </li>
              <li className={predictionProgress.percent >= 40 ? "active" : ""}>
                Extracting Metrics
              </li>
              <li className={predictionProgress.percent >= 65 ? "active" : ""}>
                Predicting
              </li>
              <li className={predictionProgress.percent >= 82 ? "active" : ""}>
                Explaining
              </li>
              <li className={predictionProgress.percent >= 100 ? "active" : ""}>
                Complete
              </li>
            </ol>
          </div>
        )}
      </div>

      <GitRefSidePanel
        isOpen={isRefPanelOpen}
        title={refPanelTitle}
        loading={loadingRefs}
        refs={refs}
        errorMessage={refErrorMessage}
        onClose={() => setIsRefPanelOpen(false)}
        onSelectRef={handleSelectRef}
      />

      <CommitSidePanel
        isOpen={isCommitPanelOpen}
        loading={loadingCommits}
        commits={commits}
        errorMessage={commitErrorMessage}
        currentPage={commitPage}
        pageSize={commitPageSize}
        hasNextPage={hasNextCommitPage}
        onClose={() => setIsCommitPanelOpen(false)}
        onSelectCommit={handleSelectCommit}
        onNextPage={handleNextCommitPage}
        onPreviousPage={handlePreviousCommitPage}
      />
    </div>
  );
}

export default RepositoryInputPage;
