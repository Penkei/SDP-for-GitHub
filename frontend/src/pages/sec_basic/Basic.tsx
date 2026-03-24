import React, { useState } from "react";
import BasicNavbar, { type BasicStep } from "./BasicNavbar";
import RepoInput from "./repo_input";

const Basic: React.FC = () => {
  const [currentStep, setCurrentStep] =
    useState<BasicStep>("repository-input");

  return (
    <div className="section-fade">
      <BasicNavbar currentStep={currentStep} onStepChange={setCurrentStep} />

      {currentStep === "repository-input" && <RepoInput />}
      {currentStep === "select-commit" && <div>Select Commit to Scan Section</div>}
      {currentStep === "analysis-running" && <div>Analysis Running Section</div>}
      {currentStep === "prediction-result" && <div>Prediction Result Section</div>}
    </div>
  );
};

export default Basic;