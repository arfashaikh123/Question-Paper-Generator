export default function Footer({ onNavigate, links }) {
  return (
    <footer className="home-footer">
      <span>🧠 NeuroGen Studio</span>
      <span className="footer-links">
        {links.map((link) => (
          <a
            key={link.page}
            href="#"
            className="footer-link"
            onClick={(e) => { e.preventDefault(); onNavigate(link.page); }}
          >
            {link.label}
          </a>
        ))}
      </span>
      <span className="text-muted">Built with Groq · LangChain · Flask · Vite</span>
    </footer>
  );
}
