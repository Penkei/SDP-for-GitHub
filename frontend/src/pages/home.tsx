import React from "react";
import { useNavigate } from "react-router-dom";
import "./Home.css";

const Home: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="container">
      <h1 className="title">Welcome to Defect Prediction Tool</h1>

      <p className="subtitle">
        Analyze your GitHub repository and predict potential defects using Machine Learning.
        Choose how you would like to proceed:
      </p>

      <div className="cardContainer">
        {/* Basic Usage */}
        <div className="card">
          <h2>Basic Usage</h2>
          <p>
            Use a pre-trained machine learning model to quickly analyze your repository
            and get defect predictions without any setup.
          </p>
          <button onClick={() => navigate("/basic")}>
            Start Basic Analysis
          </button>
        </div>

        {/* Advanced Usage */}
        <div className="card">
          <h2>Advanced Usage</h2>
          <p>
            For users familiar with machine learning. Customize and retrain the model
            using your own dataset for more tailored predictions.
          </p>
          <button onClick={() => navigate("/advanced")}>
            Start Advanced Analysis
          </button>
        </div>
      </div>
    </div>
  );
};

export default Home;