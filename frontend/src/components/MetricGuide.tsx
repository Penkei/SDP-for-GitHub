interface MetricGuideProps {
  isOpen: boolean;
  onClose: () => void;
}

const metricGuides = [
  {
    title: "Method interaction complexity",
    metric: "RFC",
    description:
      "Shows how many method calls or interactions exist in the file. Higher value may mean the file is harder to understand, test, and debug.",
  },
  {
    title: "Number of conditional checks",
    metric: "comparisonsQty",
    description:
      "Shows how many decision checks exist, such as if conditions and comparisons. Higher value may mean more possible logic paths.",
  },
  {
    title: "Static method usage",
    metric: "NOSI",
    description:
      "Shows how many static method calls are used. Higher value may indicate stronger dependency between code parts.",
  },
  {
    title: "Class cohesion complexity",
    metric: "LCOM",
    description:
      "Shows whether methods in the class are closely related. Higher value may suggest weaker cohesion and harder maintenance.",
  },
  {
    title: "Number of methods",
    metric: "totalMethods",
    description:
      "Shows how many methods are in the file. More methods may mean the file has more responsibilities.",
  },
  {
    title: "File size",
    metric: "LOC",
    description:
      "Shows the number of lines of code. Larger files are usually harder to review, test, and maintain.",
  },
  {
    title: "Dependency between classes",
    metric: "CBO",
    description:
      "Shows how much the file depends on other classes. Higher dependency may increase side-effect risk.",
  },
  {
    title: "Overall method complexity",
    metric: "WMC",
    description:
      "Shows the complexity of methods, including branches and loops. Higher value may mean more complex logic.",
  },
  {
    title: "Number of return paths",
    metric: "returnQty",
    description:
      "Shows how many return statements exist. Many return paths can make program flow harder to trace.",
  },
  {
    title: "Inheritance depth",
    metric: "DIT",
    description:
      "Shows how deep the class is in the inheritance hierarchy. Deeper inheritance may make behavior harder to understand.",
  },
];

function MetricGuide({ isOpen, onClose }: MetricGuideProps) {
  if (!isOpen) {
    return null;
  }

  return (
    <div className="metric-modal-overlay">
      <div className="metric-guide-modal">
        <div className="metric-guide-modal-header">
          <div>
            <h2>Metric Explanation Guide</h2>
            <p>
              These metrics explain why a file may have higher or lower defect
              risk.
            </p>
          </div>

          <button className="metric-modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="metric-guide-modal-grid">
          {metricGuides.map((item) => (
            <div className="metric-guide-modal-item" key={item.metric}>
              <div className="metric-guide-modal-title-row">
                <h3>{item.title}</h3>
                <span>{item.metric}</span>
              </div>

              <p>{item.description}</p>
            </div>
          ))}
        </div>

        <div className="metric-guide-modal-footer">
          <button className="primary-button" onClick={onClose}>
            Got it
          </button>
        </div>
      </div>
    </div>
  );
}

export default MetricGuide;