import type { CommitItem } from "../types/prediction";

interface CommitSidePanelProps {
  isOpen: boolean;
  loading: boolean;
  commits: CommitItem[];
  errorMessage: string;
  currentPage: number;
  pageSize: number;
  hasNextPage: boolean;
  onClose: () => void;
  onSelectCommit: (commit: CommitItem) => void;
  onNextPage: () => void;
  onPreviousPage: () => void;
}

const splitCommitMessage = (message: string) => {
  const normalizedMessage = message.replace(/\s+/g, " ").trim();
  const sentenceBreak = normalizedMessage.search(/(?<=\.)\s/);
  const subjectBreak = sentenceBreak > 0 ? sentenceBreak : normalizedMessage.indexOf(" -- ");
  const splitIndex =
    subjectBreak > 0 && subjectBreak < 140 ? subjectBreak : 110;

  if (normalizedMessage.length <= splitIndex) {
    return {
      subject: normalizedMessage,
      details: "",
    };
  }

  return {
    subject: `${normalizedMessage.slice(0, splitIndex).trim()}...`,
    details: normalizedMessage.slice(splitIndex).trim(),
  };
};

function CommitSidePanel({
  isOpen,
  loading,
  commits,
  errorMessage,
  currentPage,
  pageSize,
  hasNextPage,
  onClose,
  onSelectCommit,
  onNextPage,
  onPreviousPage,
}: CommitSidePanelProps) {
  if (!isOpen) {
    return null;
  }

  const startNumber = (currentPage - 1) * pageSize + 1;
  const endNumber = startNumber + commits.length - 1;

  return (
    <div className="side-panel-overlay">
      <div className="side-panel">
        <div className="side-panel-sticky-header">
          <div className="side-panel-header">
            <div>
              <h2>Select Commit</h2>
              <p>
                Showing commits {commits.length > 0 ? startNumber : 0}
                {commits.length > 0 ? ` - ${endNumber}` : ""}.
              </p>
            </div>

            <button className="close-button" onClick={onClose}>
              ×
            </button>
          </div>

          <div className="commit-pagination">
            <button
              className="small-button"
              onClick={onPreviousPage}
              disabled={loading || currentPage === 1}
            >
              Previous
            </button>

            <span>Page {currentPage}</span>

            <button
              className="small-button"
              onClick={onNextPage}
              disabled={loading || !hasNextPage}
            >
              Next
            </button>
          </div>
        </div>

        <div className="side-panel-scroll-body">
          {loading && (
            <div className="loading-section">
              <div className="progress-bar">
                <div className="progress-bar-fill"></div>
              </div>
              <p>Loading commits from GitHub...</p>
            </div>
          )}

          {errorMessage && <div className="error-box">{errorMessage}</div>}

          {!loading && commits.length > 0 && (
            <div className="commit-list">
              {commits.map((commit) => {
                const commitMessage = splitCommitMessage(commit.message);

                return (
                  <div key={commit.sha} className="commit-item">
                    <div className="commit-top-row">
                      <span className="commit-sha">{commit.short_sha}</span>
                      <span className="commit-date">
                        {new Date(commit.date).toLocaleDateString()}
                      </span>
                    </div>

                    <div className="commit-message" title={commit.message}>
                      {commitMessage.subject}
                    </div>

                    {commitMessage.details && (
                      <details className="commit-details">
                        <summary>Show full message</summary>
                        <p>{commit.message}</p>
                      </details>
                    )}

                    <div className="commit-footer-row">
                      <div className="commit-author">By {commit.author}</div>
                      <button
                        className="select-commit-button"
                        onClick={() => onSelectCommit(commit)}
                      >
                        Select
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {!loading && commits.length === 0 && !errorMessage && (
            <div className="empty-box">No commits found.</div>
          )}
        </div>
      </div>
    </div>
  );
}

export default CommitSidePanel;
