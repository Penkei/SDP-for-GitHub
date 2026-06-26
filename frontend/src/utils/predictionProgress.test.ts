import { describe, expect, it } from "vitest";
import {
  formatEstimatedTime,
  MAX_SOURCE_FILES_PER_RUN,
} from "./predictionProgress";

describe("prediction progress utility", () => {
  it("calculates decreasing estimated time for prediction progress", () => {
    expect(MAX_SOURCE_FILES_PER_RUN).toBe(500);
    expect(formatEstimatedTime(0)).toBe("5 minutes");
    expect(formatEstimatedTime(25)).toBe("4 minutes");
    expect(formatEstimatedTime(50)).toBe("3 minutes");
    expect(formatEstimatedTime(100)).toBe("less than 1 minute");
    expect(formatEstimatedTime(120)).toBe("less than 1 minute");
  });
});
