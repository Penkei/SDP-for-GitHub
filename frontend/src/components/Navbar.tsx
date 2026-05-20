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
        <Link to="/" className="nav-link home-link">Home</Link>
        <Link to="/repository-input" className="nav-link scan-link">
          Scan a Repository
        </Link>
        <Link to="/prediction-history" className="nav-link history-link">
          Prediction History
        </Link>
        <Link to="/how-it-works" className="nav-link works-link">
          How It Works
        </Link>
      </div>
    </nav>
  );
}

export default Navbar;
