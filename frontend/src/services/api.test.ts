import { describe, expect, it } from "vitest";
import { getApiErrorMessage } from "./api";

describe("getApiErrorMessage", () => {
  it("explains network errors with Render free plan guidance", () => {
    const message = getApiErrorMessage(
      { isAxiosError: true },
      "Fallback message"
    );

    expect(message).toContain("Network error");
    expect(message).toContain("Render's free plan");
    expect(message).toContain("approximately 1 minute");
  });

  it("explains missing backend resources after restart", () => {
    const message = getApiErrorMessage(
      { isAxiosError: true, response: { status: 404, data: {} } },
      "Fallback message"
    );

    expect(message).toContain("backend resource was not found");
    expect(message).toContain("backend may have restarted");
  });

  it("shows authentication details returned by the backend", () => {
    const message = getApiErrorMessage(
      {
        isAxiosError: true,
        response: {
          status: 403,
          data: {
            detail: "GitHub authentication failed. Personal Access Token is invalid or out of access.",
          },
        },
      },
      "Fallback message"
    );

    expect(message).toContain("GitHub authentication failed");
    expect(message).toContain("Personal Access Token");
  });
});
