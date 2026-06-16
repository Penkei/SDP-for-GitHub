import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import FeedbackPage from "./FeedbackPage";
import { fetchFeedback, submitFeedback } from "../services/api";

vi.mock("../services/api", () => ({
  fetchFeedback: vi.fn(),
  submitFeedback: vi.fn(),
  getApiErrorMessage: vi.fn((_error: unknown, fallbackMessage: string) => fallbackMessage),
}));

const mockedFetchFeedback = vi.mocked(fetchFeedback);
const mockedSubmitFeedback = vi.mocked(submitFeedback);

describe("FeedbackPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedFetchFeedback.mockResolvedValue({ feedback: [] });
  });

  it("shows public feedback returned by the backend", async () => {
    mockedFetchFeedback.mockResolvedValue({
      feedback: [
        {
          id: "fb-1",
          name: "Student Tester",
          role: "Student",
          rating: 5,
          message: "The prediction dashboard is easy to understand.",
          submitted_at: "2026-06-16T08:00:00.000Z",
        },
      ],
    });

    render(<FeedbackPage />);

    expect(await screen.findByText("The prediction dashboard is easy to understand.")).toBeInTheDocument();
    expect(screen.getByText("Student Tester")).toBeInTheDocument();
    expect(screen.getByText("5/5")).toBeInTheDocument();
  });

  it("blocks blank feedback before sending a request", async () => {
    const user = userEvent.setup();

    render(<FeedbackPage />);

    await waitFor(() => expect(mockedFetchFeedback).toHaveBeenCalled());
    await user.click(screen.getByRole("button", { name: "Submit Feedback" }));

    expect(screen.getByText("Please write your feedback before submitting.")).toBeInTheDocument();
    expect(mockedSubmitFeedback).not.toHaveBeenCalled();
  });

  it("adds submitted feedback to the public list", async () => {
    const user = userEvent.setup();
    mockedSubmitFeedback.mockResolvedValue({
      feedback: {
        id: "fb-2",
        name: "Developer Tester",
        role: "Developer",
        rating: 4,
        message: "The repository input guide is helpful.",
        submitted_at: "2026-06-16T09:00:00.000Z",
      },
    });

    render(<FeedbackPage />);

    await waitFor(() => expect(mockedFetchFeedback).toHaveBeenCalled());
    await user.type(screen.getByLabelText("Name"), "Developer Tester");
    await user.type(screen.getByLabelText("Feedback"), "The repository input guide is helpful.");
    await user.click(screen.getByRole("button", { name: "Submit Feedback" }));

    expect(await screen.findByText("Thank you. Your feedback is now visible on this page.")).toBeInTheDocument();
    expect(screen.getByText("The repository input guide is helpful.")).toBeInTheDocument();
  });
});
