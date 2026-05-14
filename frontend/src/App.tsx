import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import HomePage from "./pages/HomePage";
import RepositoryInputPage from "./pages/RepositoryInputPage";
import PredictionResultPage from "./pages/PredictionResultPage";
import HowItWorksPage from "./pages/HowItWorksPage";
import PredictionHistoryPage from "./pages/PredictionHistoryPage";

function App() {
  return (
    <BrowserRouter>
      <Navbar />

      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/repository-input" element={<RepositoryInputPage />} />
        <Route path="/prediction-result" element={<PredictionResultPage />} />
        <Route path="/how-it-works" element={<HowItWorksPage />} />
        <Route path="/prediction-history" element={<PredictionHistoryPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
