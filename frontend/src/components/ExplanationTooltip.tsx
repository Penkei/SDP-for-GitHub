interface ExplanationTooltipProps {
  explanation: string;
}

const keywordDescriptions: Record<string, string> = {
  "Method interaction complexity":
    "This means the file has many method calls or interactions. More interactions can make the file harder to understand and test.",

  "Number of conditional checks":
    "This means the file contains many if, else, switch, or comparison conditions. More conditions usually mean more decision paths.",

  "Static method usage":
    "This means the file uses many static method calls. High static usage may increase dependency or coupling between code parts.",

  "Class cohesion complexity":
    "This means the methods in the class may not be strongly related to each other. Low cohesion can make the class harder to maintain.",

  "Number of methods":
    "This means the file contains many methods. More methods may increase responsibility and maintenance difficulty.",

  "File size":
    "This means the file has many lines of code. Larger files are usually harder to review and maintain.",

  "Dependency between classes":
    "This means the file depends on many other classes. Higher dependency can increase the chance of side effects.",

  "Overall method complexity":
    "This means the file has more complex method logic, such as loops and condition branches.",

  "Number of return paths":
    "This means the file has many return statements. Many return paths can make logic flow harder to trace.",

  "Inheritance depth":
    "This means the class is deeper in the inheritance hierarchy. Deeper inheritance can make behavior harder to understand.",
};

function ExplanationTooltip({ explanation }: ExplanationTooltipProps) {
  const sentences = explanation
    .split(".")
    .map((sentence) => sentence.trim())
    .filter(Boolean);

  const getKeyword = (sentence: string) => {
    return Object.keys(keywordDescriptions).find((keyword) =>
      sentence.startsWith(keyword)
    );
  };

  return (
    <div className="explanation-list">
      {sentences.map((sentence, index) => {
        const keyword = getKeyword(sentence);

        if (!keyword) {
          return (
            <div key={index} className="explanation-item">
              {sentence}.
            </div>
          );
        }

        const remainingText = sentence.replace(keyword, "").trim();

        return (
          <div key={index} className="explanation-item">
            <span className="tooltip-keyword">
              {keyword}
              <span className="tooltip-box">
                {keywordDescriptions[keyword]}
              </span>
            </span>
            <span> {remainingText}.</span>
          </div>
        );
      })}
    </div>
  );
}

export default ExplanationTooltip;