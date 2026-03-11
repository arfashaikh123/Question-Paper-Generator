import React from 'react';
import Navbar from '../components/Navbar';

const AboutPage = ({ onNavigate }) => {
    return (
        <div className="page-container">
            <Navbar activePage="about" onNavigate={onNavigate} />

            <div className="about-content">
                <div className="about-hero">
                    <div className="home-badge">📖 Technical Overview</div>
                    <h2 className="home-title" style={{ fontSize: '2.5rem' }}>Algorithms & Architecture</h2>
                    <p className="home-subtitle">
                        A deep dive into how NeuroGen Studio analyses question papers,
                        generates new questions, and leverages the RAG model approach.
                    </p>
                </div>

                <section className="about-section">
                    <div className="about-section-header">
                        <span className="about-section-icon">🔍</span>
                        <h3>Paper Analysis Algorithms</h3>
                    </div>
                    <p className="about-section-intro">
                        NeuroGen employs a multi-stage analysis pipeline to understand your syllabus and
                        previous year question (PYQ) papers before generating anything.
                    </p>
                    <div className="algo-cards">
                        <div className="algo-card">
                            <h4>📄 PDF Text Extraction</h4>
                            <p>Direct parsing using PyPDF2 and PyMuPDF for high fidelity.</p>
                        </div>
                        <div className="algo-card">
                            <h4>🏷️ Topic Extraction</h4>
                            <p>Structured JSON extraction via Advanced Large Language Models (LLMs).</p>
                        </div>
                    </div>
                </section>

                <section className="about-section">
                    <div className="about-section-header">
                        <span className="about-section-icon">🧠</span>
                        <h3>RAG Model Approach</h3>
                    </div>
                    <p className="about-section-intro">
                        Using Retrieval-Augmented Generation to ground AI outputs in your documents.
                    </p>
                </section>
            </div>

            <footer className="home-footer">
                <span>🧠 NeuroGen Studio</span>
                <span className="footer-links">
                    <a href="#" className="footer-link" onClick={() => onNavigate('home')}>Home</a>
                    <a href="#" className="footer-link" onClick={() => onNavigate('landing')}>Get Started</a>
                </span>
                <span className="text-muted">Built with LangChain · Flask · Vite</span>
            </footer>
        </div>
    );
};

export default AboutPage;
