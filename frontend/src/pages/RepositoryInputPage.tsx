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

type ThresholdMode = "balanced" | "aggressive" | "conservative" | "custom";

type ActiveGuide = "repo-url" | "pat" | null;

//This flag keeps public deployments on request based cloning
const ENABLE_LOCAL_CACHE_MODE = import.meta.env.VITE_ENABLE_LOCAL_CACHE_MODE !== "false";

const thresholdOptions: Array<{
  mode: ThresholdMode;
  label: string;
  value: number | null;
  description: string;
}> = [
  {
    mode: "balanced",
    label: "Balanced",
    value: null,
    description: "Use trained model threshold",
  },
  {
    mode: "aggressive",
    label: "Aggressive",
    value: 0.35,
    description: "Flag more files",
  },
  {
    mode: "conservative",
    label: "Conservative",
    value: 0.65,
    description: "Flag fewer files",
  },
  {
    mode: "custom",
    label: "Custom",
    value: null,
    description: "Choose threshold",
  },
];

const validateGitHubRepositoryUrl = (value: string) => {
  const trimmedUrl = value.trim();

  if (!trimmedUrl) {
    return "Please enter a GitHub repository URL first.";
  }

  let parsedUrl: URL;

  try {
    parsedUrl = new URL(trimmedUrl);
  } catch {
    return "Repository URL is not valid. Use https://github.com/owner/repository.";
  }

  if (!["http:", "https:"].includes(parsedUrl.protocol)) {
    return "Repository URL must start with http:// or https://.";
  }

  if (parsedUrl.hostname.toLowerCase() !== "github.com") {
    return "Only github.com repository URLs are supported.";
  }

  const pathParts = parsedUrl.pathname
    .replace(/\/$/, "")
    .split("/")
    .filter(Boolean);

  if (pathParts.length !== 2) {
    return "Repository URL must use the format https://github.com/owner/repository.";
  }

  const repositoryName = pathParts[1].replace(/\.git$/, "");

  if (!pathParts[0] || !repositoryName) {
    return "Repository URL must include both owner and repository name.";
  }

  return "";
};

function RepositoryInputPage() {
  const navigate = useNavigate();

  const [repoUrl, setRepoUrl] = useState("");
  const [selectedGitRef, setSelectedGitRef] = useState("");
  const [selectedGitRefType, setSelectedGitRefType] = useState("");
  const [commitSha, setCommitSha] = useState("");
  const [thresholdMode, setThresholdMode] = useState<ThresholdMode>("balanced");
  const [customThreshold, setCustomThreshold] = useState("0.50");
  const [usePersonalAccessToken, setUsePersonalAccessToken] = useState(true);
  const [githubToken, setGithubToken] = useState("");
  const [activeGuide, setActiveGuide] = useState<ActiveGuide>(null);

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
    const validationMessage = validateGitHubRepositoryUrl(repoUrl);

    if (validationMessage) {
      setErrorMessage(validationMessage);
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

  const validatePersonalAccessToken = () => {
    if (!usePersonalAccessToken) {
      if (!ENABLE_LOCAL_CACHE_MODE) {
        setErrorMessage("Local cache mode is disabled on this deployment. Use Personal Token request mode instead.");
        return false;
      }

      return true;
    }

    if (!githubToken.trim()) {
      setErrorMessage(
        "Please enter a GitHub Personal Access Token, or switch to local cache mode."
      );
      return false;
    }

    return true;
  };

  const getPredictionThreshold = () => {
    if (thresholdMode === "balanced") {
      return null;
    }

    if (thresholdMode === "custom") {
      const parsedThreshold = Number(customThreshold);

      if (
        Number.isNaN(parsedThreshold) ||
        parsedThreshold < 0.05 ||
        parsedThreshold > 0.95
      ) {
        setErrorMessage("Custom threshold must be between 0.05 and 0.95.");
        return undefined;
      }

      return parsedThreshold;
    }

    const selectedOption = thresholdOptions.find(
      (option) => option.mode === thresholdMode
    );

    return selectedOption?.value ?? null;
  };

  const handleLoadBranches = async () => {
    if (!validateRepoUrl() || !validatePersonalAccessToken()) {
      return;
    }

    setErrorMessage("");
    setRefErrorMessage("");
    setRefs([]);
    setRefPanelTitle("Select Branch");
    setIsRefPanelOpen(true);
    setLoadingRefs(true);

    try {
      const response = await fetchBranches(
        repoUrl.trim(),
        usePersonalAccessToken,
        githubToken.trim()
      );
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
    if (!validateRepoUrl() || !validatePersonalAccessToken()) {
      return;
    }

    setErrorMessage("");
    setRefErrorMessage("");
    setRefs([]);
    setRefPanelTitle("Select Tag");
    setIsRefPanelOpen(true);
    setLoadingRefs(true);

    try {
      const response = await fetchTags(
        repoUrl.trim(),
        usePersonalAccessToken,
        githubToken.trim()
      );
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
    if (!validateRepoUrl() || !validateGitRef() || !validatePersonalAccessToken()) {
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
        skip,
        usePersonalAccessToken,
        githubToken.trim()
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

    if (!validatePersonalAccessToken()) {
      return;
    }

    const predictionThreshold = getPredictionThreshold();

    if (predictionThreshold === undefined) {
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
        prediction_threshold: predictionThreshold,
        use_personal_access_token: usePersonalAccessToken,
        github_token: usePersonalAccessToken ? githubToken.trim() : null,
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

        <div
          className={
            usePersonalAccessToken
              ? "clone-mode-panel pat-mode"
              : "clone-mode-panel"
          }
        >
          <div className="clone-mode-content">
            <div className="clone-mode-heading">
              <strong>
                {usePersonalAccessToken
                  ? "Hosted Token Cloning"
                  : "Local Cache Repository Input"}
              </strong>
              <span>
                {usePersonalAccessToken ? "Temporary server clone" : "Reusable cache"}
              </span>
            </div>

            <p>
              {usePersonalAccessToken
                ? "The application sends the repository URL to the hosted server. The server creates a temporary clone to read the selected commit and generate the prediction results."
                : "Use this when you want a reusable repository mirror stored in your local machine for faster repeated repository operations."}
            </p>

            <div className="clone-storage-list">
              {!usePersonalAccessToken && (
                <div>
                  <span>Stored in your local machine</span>
                  <code>%TEMP%\sdp_github_temp_repos\repo_cache</code>
                </div>
              )}
              <div>
                <span>Server work area</span>
                <code>Temporary folder on the hosted server</code>
              </div>
              <div>
                <span>Cleanup behavior</span>
                <code>
                  {usePersonalAccessToken
                    ? "Cleaned after use. PAT is not saved"
                    : "Worktree cleaned after prediction"}
                </code>
              </div>
            </div>
          </div>

          {ENABLE_LOCAL_CACHE_MODE && (
            <div className="clone-mode-action">
            <span>
              {usePersonalAccessToken
                ? "Prefer faster repeated runs with a reusable local cache?"
                : "Switch back to request-only cloning with no reusable cache."}
            </span>
            <button
              type="button"
              className="clone-mode-toggle"
              onClick={() => {
                setUsePersonalAccessToken((current) => !current);
                setErrorMessage("");
                setRefErrorMessage("");
                setCommitErrorMessage("");
                setSelectedGitRef("");
                setSelectedGitRefType("");
                setCommitSha("");
                setCommits([]);
              }}
              disabled={loadingRefs || loadingCommits || loadingPrediction}
            >
              {usePersonalAccessToken
                ? "Use local cache"
                : "Use Personal Token"}
            </button>
          </div>
          )}
        </div>

        <div className="field-label-row">
          <label>GitHub Repository URL</label>
          <button
            type="button"
            className="field-help-button"
            aria-label="Open GitHub repository URL guide"
            onClick={() => setActiveGuide("repo-url")}
          >
            ?
          </button>
        </div>
        <input
          type="text"
          value={repoUrl}
          onChange={(e) => {
            setRepoUrl(e.target.value);
            setErrorMessage("");
            setRefErrorMessage("");
            setCommitErrorMessage("");
            setSelectedGitRef("");
            setSelectedGitRefType("");
            setCommitSha("");
            setCommits([]);
          }}
          placeholder="https://github.com/apache/commons-lang.git"
        />
        <p className="input-hint">
          Use a public GitHub repository URL, for example
          https://github.com/owner/repository.
        </p>

        {usePersonalAccessToken && (
          <>
            <div className="field-label-row">
              <label>GitHub Personal Access Token</label>
              <button
                  type="button"
                  className="field-help-button"
                  aria-label="Open GitHub PAT guide"
                  onClick={() => setActiveGuide("pat")}
                >
                  ?
                </button>
            </div>
            <input
              type="password"
              value={githubToken}
              onChange={(event) => {
                setGithubToken(event.target.value);
                setErrorMessage("");
                setRefErrorMessage("");
                setCommitErrorMessage("");
              }}
              placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
              autoComplete="off"
            />
            <p className="input-hint">
              A GitHub Personal Access Token helps the hosted server request repository data from GitHub more reliably. The token is used only during the current request and is not saved in prediction history.
            </p>
          </>
        )}

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

        <div className="field-label-row">
          <label>Selected Commit SHA</label>
          <span className="help-tooltip">
            <button type="button" aria-label="Commit SHA guide">
              ?
            </button>
            <span className="help-tooltip-content">
              You can select a commit from the commit panel, or copy a commit
              SHA from GitHub and paste it here. On GitHub, open the repository,
              go to Commits, click a commit, then copy the long SHA from the
              commit page URL or copy button.
            </span>
          </span>
        </div>
        <input
          type="text"
          value={commitSha}
          onChange={(e) => setCommitSha(e.target.value)}
          placeholder="Select from commit panel or paste commit SHA from GitHub"
        />
        <p className="input-hint">
          Or copy from GitHub and paste a commit SHA manually. A full 40-character
          SHA is recommended for the most accurate checkout.
        </p>

        <div className="field-label-row">
          <label>Prediction Sensitivity</label>
          <span className="help-tooltip">
            <button type="button" aria-label="Prediction sensitivity guide">
              ?
            </button>
            <span className="help-tooltip-content">
              This controls the cutoff for labelling a file as defective. A
              lower cutoff marks more files as defective, which is more cautious
              but may include more false alarms. A higher cutoff marks fewer
              files, but may miss some risky files.
            </span>
          </span>
        </div>
        <div className="threshold-control">
          {thresholdOptions.map((option) => (
            <button
              key={option.mode}
              type="button"
              className={
                thresholdMode === option.mode
                  ? "threshold-option active"
                  : "threshold-option"
              }
              onClick={() => {
                setThresholdMode(option.mode);
                setErrorMessage("");
              }}
              disabled={loadingPrediction}
            >
              <strong>{option.label}</strong>
              <span>{option.description}</span>
            </button>
          ))}
        </div>

        {thresholdMode === "custom" && (
          <div className="threshold-custom-row">
            <input
              type="number"
              min="0.05"
              max="0.95"
              step="0.01"
              value={customThreshold}
              onChange={(event) => {
                setCustomThreshold(event.target.value);
                setErrorMessage("");
              }}
              disabled={loadingPrediction}
            />
            <span>
              {(Number(customThreshold || 0) * 100).toFixed(0)}% cutoff
            </span>
          </div>
        )}

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
              <li className={predictionProgress.percent >= 55 ? "active" : ""}>
                Process Metrics
              </li>
              <li className={predictionProgress.percent >= 72 ? "active" : ""}>
                Predicting
              </li>
              <li className={predictionProgress.percent >= 86 ? "active" : ""}>
                Explaining
              </li>
              <li className={predictionProgress.percent >= 100 ? "active" : ""}>
                Complete
              </li>
            </ol>
          </div>
        )}
      </div>
      {activeGuide && (
        <div
          className="guide-modal-backdrop"
          role="presentation"
          onClick={() => setActiveGuide(null)}
        >
          <section
            className="guide-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="guide-modal-title"
            onClick={(event) => event.stopPropagation()}
          >
            <button
              type="button"
              className="guide-modal-close"
              aria-label="Close guide"
              onClick={() => setActiveGuide(null)}
            >
              x
            </button>

            {activeGuide === "repo-url" ? (
              <>
                <div className="guide-modal-header">
                  <span>GitHub Repository URL Guide</span>
                  <h2 id="guide-modal-title">Copy the repository HTTPS URL</h2>
                  <p>
                    Use the repository URL from GitHub so the app can load branches,
                    commits, and source files for prediction.
                  </p>
                </div>

                <div className="guide-step-list">
                  <article className="guide-step-card">
                    <div className="guide-step-copy">
                      <strong>Step 1</strong>
                      <p>Open the repository page on GitHub and click the green Code button.</p>
                    </div>
                    <img
                      src="/github-url-guide-1.png"
                      alt="GitHub page with Code button"
                    />
                  </article>

                  <div className="guide-down-arrow" aria-hidden="true"></div>

                  <article className="guide-step-card">
                    <div className="guide-step-copy">
                      <strong>Step 2</strong>
                      <p>Select HTTPS and click the copy icon beside the repository URL.</p>
                    </div>
                    <img
                      src="/github-url-guide-2.png"
                      alt="GitHub HTTPS clone URL copy area"
                    />
                  </article>
                </div>
              </>
            ) : (
              <>
                <div className="guide-modal-header">
                  <span>GitHub PAT Guide</span>
                  <h2 id="guide-modal-title">Create a Personal Access Token</h2>
                  <p>
                    Create a GitHub token so the app can request repository branches
                    and commits without hitting public rate limits too quickly.
                  </p>
                </div>

                <div className="guide-step-list">
                  <article className="guide-step-card">
                    <div className="guide-step-copy">
                      <strong>Step 1</strong>
                      <p>Open GitHub Profile settings.</p>
                    </div>
                    <img
                      src="/pat-guide-1.png"
                      alt="GitHub Developer settings page"
                    />
                  </article>

                  <div className="guide-down-arrow" aria-hidden="true"></div>

                  <article className="guide-step-card">
                    <div className="guide-step-copy">
                      <strong>Step 2</strong>
                      <p>Go to Developer settings.</p>
                    </div>
                    <img
                      src="/pat-guide-2.png"
                      alt="GitHub create Personal Access Token page"
                    />
                  </article>

                  <div className="guide-down-arrow" aria-hidden="true"></div>

                  <article className="guide-step-card">
                    <div className="guide-step-copy">
                      <strong>Step 3</strong>
                      <p>Create a new fine grained Personal Access Token and copy the generated token and paste it into the PAT field.</p>
                    </div>
                    <img
                      src="/pat-guide-3.png"
                      alt="GitHub generated Personal Access Token copy screen"
                    />
                  </article>
                </div>
              </>
            )}
          </section>
        </div>
      )}


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


