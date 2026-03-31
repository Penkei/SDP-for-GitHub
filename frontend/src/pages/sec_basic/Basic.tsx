import React, { useState } from "react";
import BasicNavbar, { type BasicStep } from "./BasicNavbar";
import RepoInput from "./repo_input";
import SelectCommit from "./select_commit";

const Basic: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<BasicStep>("repository-input");
  const [repoUrl, setRepoUrl] = useState("");
  const [pat, setPat] = useState("");

  return (
    <div className="section-fade">
      <BasicNavbar currentStep={currentStep} onStepChange={setCurrentStep} />

      {currentStep === "repository-input" && (
        <RepoInput
          onContinue={(repositoryUrlValue: string, patValue: string) => {
            setRepoUrl(repositoryUrlValue);
            setPat(patValue);
            setCurrentStep("select-commit");
          }}
        />
      )}

      {currentStep === "select-commit" && (
        <SelectCommit repoUrl={repoUrl} pat={pat} />
      )}

      {currentStep === "analysis-running" && <div>Analysis Running Section</div>}
      {currentStep === "prediction-result" && <div>Prediction Result Section</div>}
    </div>
  );
};

export default Basic;