import React from "react";
import "./BasicNavbar.css";

type BasicStep =
  | "repository-input"
  | "select-commit"
  | "analysis-running"
  | "prediction-result";

interface BasicNavbarProps {
  currentStep: BasicStep;
  onStepChange?: (step: BasicStep) => void;
}

const steps: { key: BasicStep; label: string }[] = [
  { key: "repository-input", label: "Repository Input" },
  { key: "select-commit", label: "Select Commit to Scan" },
  { key: "analysis-running", label: "Analysis Running" },
  { key: "prediction-result", label: "Prediction Result" },
];

const BasicNavbar: React.FC<BasicNavbarProps> = ({
  currentStep,
  onStepChange,
}) => {
  return (
    <nav className="basic-navbar">
      <div className="basic-navbar__title">Basic Usage</div>

      <div className="basic-navbar__steps">
        {steps.map((step, index) => (
          <React.Fragment key={step.key}>
            <button
              type="button"
              className={`basic-navbar__item ${
                currentStep === step.key ? "active" : ""
              }`}
              onClick={() => onStepChange?.(step.key)}
            >
              {step.label}
            </button>

            {index < steps.length - 1 && (
              <span className="basic-navbar__divider">/</span>
            )}
          </React.Fragment>
        ))}
      </div>
    </nav>
  );
};

export default BasicNavbar;
export type { BasicStep };