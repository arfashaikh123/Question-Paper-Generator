import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function HomePage({ onNavigate }) {
  return (
    <div className="page-container">
      <Navbar activePage="home" onNavigate={onNavigate} />

      <div className="home-hero">
        <div className="home-badge">✨ Powered by Groq + LangChain RAG</div>
        <h2 className="home-title">Design Intelligent<br />Question Papers.</h2>
        <p className="home-subtitle">
          Upload your syllabus and previous year questions. Our AI analyses topic priorities,
          learns exam patterns, and architects the perfect exam — in seconds.
        </p>
        <div className="home-cta-group">
          <button className="neon-btn huge-btn" onClick={() => onNavigate('upload')}>
            Get Started →
          </button>
          <button
            className="ghost-btn"
            onClick={() => {
              document.getElementById('featuresSection')?.scrollIntoView({ behavior: 'smooth' });
            }}
          >
            Learn How It Works
          </button>
        </div>
      </div>

      <div className="features-section" id="featuresSection">
        <h3 className="section-heading">What Makes NeuroGen Intelligent?</h3>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">🔍</div>
            <h4>RAG-Powered Analysis</h4>
            <p>Retrieval-Augmented Generation extracts topic priorities and patterns from your uploaded PDFs with deep contextual understanding.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📐</div>
            <h4>Smart Pattern Design</h4>
            <p>Adaptive algorithms distribute marks across Bloom's Taxonomy levels, ensuring balanced and pedagogically sound question papers.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">💬</div>
            <h4>Chat-Driven Customisation</h4>
            <p>Converse with an AI agent to refine sections, adjust mark distribution, and regenerate specific parts — all in natural language.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📄</div>
            <h4>One-Click PDF Export</h4>
            <p>Generate a professionally formatted, print-ready PDF with your institution's header and logo in a single click.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🎯</div>
            <h4>Priority Scoring</h4>
            <p>Frequency analysis of previous year questions surfaces high-priority topics, ensuring your paper reflects real exam trends.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🔒</div>
            <h4>Bring Your Own Key</h4>
            <p>Use your own Groq API key for full control. Your data stays with you — no third-party storage of your syllabus or papers.</p>
          </div>
        </div>
      </div>

      <div className="how-it-works">
        <h3 className="section-heading">How It Works</h3>
        <div className="steps-row">
          <div className="step-card">
            <div className="step-number">01</div>
            <h4>Upload Documents</h4>
            <p>Provide your syllabus text, previous year question PDFs, and an optional reference pattern.</p>
          </div>
          <div className="step-arrow">→</div>
          <div className="step-card">
            <div className="step-number">02</div>
            <h4>AI Analyses</h4>
            <p>The RAG pipeline extracts topics, scores priorities, and detects the exam pattern from your files.</p>
          </div>
          <div className="step-arrow">→</div>
          <div className="step-card">
            <div className="step-number">03</div>
            <h4>Design &amp; Refine</h4>
            <p>Use the Blueprint Studio and AI chat to customise sections, marks, and topic coverage.</p>
          </div>
          <div className="step-arrow">→</div>
          <div className="step-card">
            <div className="step-number">04</div>
            <h4>Generate &amp; Export</h4>
            <p>Generate the final paper and download a polished, institution-ready PDF.</p>
          </div>
        </div>
      </div>

      <Footer
        onNavigate={onNavigate}
        links={[
          { page: 'about', label: 'About & Algorithms' },
          { page: 'upload', label: 'Get Started' },
        ]}
      />
    </div>
  );
}
