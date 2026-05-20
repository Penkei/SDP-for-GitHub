interface CompactExplanationProps {
  explanation: string;
}

const metricLabelMap: Record<string, string> = {
  rfc: "Method interactions",
  comparisonsQty: "Conditional checks",
  nosi: "Static calls",
  lcom: "Cohesion complexity",
  totalMethods: "Methods",
  loc: "File size",
  cbo: "Class dependencies",
  wmc: "Method complexity",
  returnQty: "Return paths",
  dit: "Inheritance depth",
  file_change_count: "File changes",
  file_bug_fix_count: "Bug-fix history",
  recent_file_change_count: "Recent changes",
  days_since_last_change: "Days since change",
  last_change_lines_added: "Last added lines",
  last_change_lines_deleted: "Last deleted lines",
  last_change_churn: "Last churn",
  last_change_file_count: "Files changed together",
  author_file_change_count: "Author file changes",
};

function formatMetricValue(value: string): string {
  const numericValue = Number(value);

  if (Number.isNaN(numericValue)) {
    return value.trim();
  }

  return Number.isInteger(numericValue)
    ? String(numericValue)
    : numericValue.toFixed(2);
}

function extractMetricItems(explanation: string) {
  const metricPattern = /\(([A-Za-z_][A-Za-z0-9_]*)=([^)]+)\)/g;
  const items: {
    keyword: string;
    value: string;
    rawMetric: string;
    direction: "higher" | "lower" | "neutral";
  }[] = [];
  const seenMetrics = new Set<string>();
  const sentences = explanation
    .split(".")
    .map((sentence) => sentence.trim())
    .filter(Boolean);

  sentences.forEach((sentence) => {
    const sentenceDirection = sentence.toLowerCase().includes("score higher")
      ? "higher"
      : sentence.toLowerCase().includes("score lower")
        ? "lower"
        : "neutral";

    for (const match of sentence.matchAll(metricPattern)) {
      const rawMetric = match[1];

      if (seenMetrics.has(rawMetric)) {
        continue;
      }

      seenMetrics.add(rawMetric);
      items.push({
        keyword: metricLabelMap[rawMetric] || rawMetric,
        value: formatMetricValue(match[2]),
        rawMetric,
        direction: sentenceDirection,
      });
    }
  });

  return items;
}

function CompactExplanation({ explanation }: CompactExplanationProps) {
  const items = extractMetricItems(explanation);

  if (items.length === 0) {
    return (
      <span className="compact-explanation-empty" title={explanation}>
        No metric values available
      </span>
    );
  }

  return (
    <div className="compact-explanation-list">
      {items.map((item) => (
        <div
          className={`compact-explanation-item ${item.direction}`}
          key={item.rawMetric}
          title={item.rawMetric}
        >
          <span className="compact-explanation-keyword">
            <span className="compact-explanation-direction">
              {item.direction === "higher"
                ? "Increases score"
                : item.direction === "lower"
                  ? "Lowers score"
                  : "Model signal"}
            </span>
            {item.keyword}
          </span>
          <span className="compact-explanation-value">{item.value}</span>
        </div>
      ))}
    </div>
  );
}

export default CompactExplanation;
