import { Link } from "react-router-dom";
import logoUrl from "../../assets/logo.png";

function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <img src={logoUrl} alt="SDP for GitHub" className="navbar-logo" />
        <div className="navbar-title">SDP for GitHub</div>
      </div>

      <div className="navbar-links">
        <Link to="/">Home</Link>
        <Link to="/repository-input">Repository Input</Link>
        <Link to="/prediction-history">Prediction History</Link>
        <Link to="/how-it-works">How It Works</Link>
<<<<<<< HEAD
=======
        <Link to="/model-evaluation">Model Evaluation</Link>
>>>>>>> Refinement
      </div>
    </nav>
  );
}

export default Navbar;
