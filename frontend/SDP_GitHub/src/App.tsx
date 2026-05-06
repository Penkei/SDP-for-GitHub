import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import HomePage from "./pages/HomePage";
import RepositoryInputPage from "./pages/RepositoryInputPage";
import PredictionResultPage from "./pages/PredictionResultPage";

function App() {
  return (
    <BrowserRouter>
      <Navbar />

      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/repository-input" element={<RepositoryInputPage />} />
        <Route path="/prediction-result" element={<PredictionResultPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;