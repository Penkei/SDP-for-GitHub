import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/home";
import Basic from "./pages/sec_basic/Basic";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/basic" element={<Basic />} />
        
      </Routes>
    </BrowserRouter>
  );
}

export default App;