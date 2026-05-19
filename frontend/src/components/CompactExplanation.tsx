interface CompactExplanationProps {
  explanation: string;
}

const keywordLabels = [
  "Method interaction complexity",
  "Number of conditional checks",
  "Static method usage",
  "Class cohesion complexity",
  "Number of methods",
  "File size",
  "Dependency between classes",
  "Overall method complexity",
  "Number of return paths",
  "Inheritance depth",
];

const displayNameMap: Record<string, string> = {
  "Method interaction complexity": "Method interactions",
  "Number of conditional checks": "Conditional checks",
  "Static method usage": "Static calls",
  "Class cohesion complexity": "Cohesion complexity",
  "Number of methods": "Methods",
  "File size": "File size",
  "Dependency between classes": "Class dependencies",
  "Overall method complexity": "Method complexity",
  "Number of return paths": "Return paths",
  "Inheritance depth": "Inheritance depth",
};

function extractValue(sentence: string): string {
  const match = sentence.match(/\(([^=]+)=([^)]+)\)/);

  if (!match) {
    return "";
  }

  return match[2];
}

function CompactExplanation({ explanation }: CompactExplanationProps) {
  const sentences = explanation
    .split(".")
    .map((sentence) => sentence.trim())
    .filter(Boolean);

  const items = sentences
    .map((sentence) => {
      const keyword = keywordLabels.find((label) =>
        sentence.startsWith(label)
      );

      if (!keyword) {
        return null;
      }

      return {
        keyword: displayNameMap[keyword],
        value: extractValue(sentence),
      };
    })
    .filter(Boolean) as { keyword: string; value: string }[];

  if (items.length === 0) {
    return <span>{explanation}</span>;
  }

  return (
    <div className="compact-explanation-list">
      {items.map((item) => (
        <div className="compact-explanation-item" key={item.keyword}>
          <span className="compact-explanation-keyword">{item.keyword}</span>
          <span className="compact-explanation-value">{item.value}</span>
        </div>
      ))}
    </div>
  );
}

export default CompactExplanation;