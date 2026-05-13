import { Link } from "react-router-dom";

function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-title">SDP for GitHub</div>

      <div className="navbar-links">
        <Link to="/">Home</Link>
        <Link to="/repository-input">Repository Input</Link>
        <Link to="/prediction-history">Prediction History</Link>
        <Link to="/model-transparency">Model Transparency</Link>
      </div>
    </nav>
  );
}

export default Navbar;
