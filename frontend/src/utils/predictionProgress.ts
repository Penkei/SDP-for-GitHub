export const MAX_SOURCE_FILES_PER_RUN = 500;
const ESTIMATED_TOTAL_SECONDS = 300;

export const formatEstimatedTime = (percent: number) => {
  if (percent >= 100) {
    return "less than 1 minute";
  }

  const remainingPercent = Math.max(0, 100 - percent);
  const remainingSeconds = Math.max(
    30,
    Math.ceil((remainingPercent / 100) * ESTIMATED_TOTAL_SECONDS)
  );
  const minutes = Math.max(1, Math.ceil(remainingSeconds / 60));

  return `${minutes} minute${minutes === 1 ? "" : "s"}`;
};
