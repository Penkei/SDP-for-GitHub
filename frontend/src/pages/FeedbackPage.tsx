import { useEffect, useState } from "react";
import { fetchFeedback, getApiErrorMessage, submitFeedback } from "../services/api";
import type { FeedbackEntry } from "../types/prediction";

const roleOptions = ["Student", "Developer", "Evaluator", "Other"];

const formatDate = (value: string) => {
  if (!value) {
    return "Unknown date";
  }

  return new Date(value).toLocaleString();
};

function FeedbackPage() {
  const [feedbackItems, setFeedbackItems] = useState<FeedbackEntry[]>([]);
  const [name, setName] = useState("");
  const [role, setRole] = useState("Student");
  const [rating, setRating] = useState(5);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const loadFeedback = async () => {
    setLoading(true);
    setErrorMessage("");

    try {
      const response = await fetchFeedback();
      setFeedbackItems(response.feedback);
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(error, "Feedback could not be loaded from the backend.")
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFeedback();
  }, []);

  const handleSubmit = async () => {
    const cleanedMessage = message.trim();

    if (!cleanedMessage) {
      setErrorMessage("Please write your feedback before submitting.");
      return;
    }

    setSubmitting(true);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const response = await submitFeedback({
        name: name.trim(),
        role,
        rating,
        message: cleanedMessage,
      });

      setFeedbackItems((current) => [response.feedback, ...current]);
      setName("");
      setRole("Student");
      setRating(5);
      setMessage("");
      setSuccessMessage("Thank you. Your feedback is now visible on this page.");
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(error, "Feedback could not be submitted.")
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page feedback-page">
      <section className="feedback-hero">
        <span>Public Feedback</span>
        <h1>Share feedback about SDP for GitHub</h1>
        <p>
          This page helps collect real user feedback for the project. Submitted
          feedback is public and can be viewed by anyone who opens this page.
        </p>
      </section>

      <section className="feedback-layout">
        <div className="feedback-form-card">
          <h2>Leave Feedback</h2>
          <p className="feedback-note">
            Please do not include passwords, GitHub tokens, private repository
            details, or other sensitive information.
          </p>

          <label>Name</label>
          <input
            type="text"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Optional"
            maxLength={80}
          />

          <label>Role</label>
          <select value={role} onChange={(event) => setRole(event.target.value)}>
            {roleOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>

          <label>Rating</label>
          <div className="rating-row" aria-label="Feedback rating">
            {[1, 2, 3, 4, 5].map((value) => (
              <button
                key={value}
                type="button"
                className={rating === value ? "active" : ""}
                onClick={() => setRating(value)}
              >
                {value}
              </button>
            ))}
          </div>

          <label>Feedback</label>
          <textarea
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="What worked well? What was confusing? What should be improved?"
            maxLength={1200}
            rows={6}
          />
          <div className="feedback-character-count">
            {message.length}/1200 characters
          </div>

          {successMessage && <div className="success-box">{successMessage}</div>}
          {errorMessage && <div className="error-box">{errorMessage}</div>}

          <button
            type="button"
            className="primary-button full-width"
            onClick={handleSubmit}
            disabled={submitting}
          >
            {submitting ? "Submitting..." : "Submit Feedback"}
          </button>
        </div>

        <div className="feedback-list-card">
          <div className="feedback-list-header">
            <div>
              <h2>Public Feedback</h2>
              <p>Newest responses appear first.</p>
            </div>
            <button type="button" className="secondary-button" onClick={loadFeedback}>
              {loading ? "Loading..." : "Refresh"}
            </button>
          </div>

          {loading ? (
            <div className="empty-feedback">Loading feedback...</div>
          ) : feedbackItems.length === 0 ? (
            <div className="empty-feedback">
              No feedback has been submitted yet.
            </div>
          ) : (
            <div className="feedback-list">
              {feedbackItems.map((item) => (
                <article className="feedback-item" key={item.id}>
                  <div className="feedback-item-header">
                    <div>
                      <strong>{item.name || "Anonymous"}</strong>
                      <span>{item.role || "User"}</span>
                    </div>
                    <div className="feedback-rating">
                      {item.rating}/5
                    </div>
                  </div>
                  <p>{item.message}</p>
                  <time>{formatDate(item.submitted_at)}</time>
                </article>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

export default FeedbackPage;