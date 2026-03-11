export default function Navbar({ activePage, onNavigate }) {
  return (
    <nav className="main-nav">
      <h1 className="logo">🧠 NeuroGen <span className="highlight">Studio</span></h1>
      <div className="nav-links">
        <a
          href="#"
          className={`nav-link ${activePage === 'home' ? 'active' : ''}`}
          onClick={(e) => { e.preventDefault(); onNavigate('home'); }}
        >
          Home
        </a>
        <a
          href="#"
          className={`nav-link ${activePage === 'about' ? 'active' : ''}`}
          onClick={(e) => { e.preventDefault(); onNavigate('about'); }}
        >
          About
        </a>
        <a
          href="#"
          className="nav-link nav-cta"
          onClick={(e) => { e.preventDefault(); onNavigate('upload'); }}
        >
          Get Started →
        </a>
      </div>
    </nav>
  );
}
