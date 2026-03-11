import React from 'react';
import Navbar from '../components/Navbar';

const HomePage = ({ onNavigate }) => {
    return (
        <div className="page-container">
            <Navbar activePage="home" onNavigate={onNavigate} />

            <div className="home-hero">
                <div className="home-badge">✨ Powered by Intelligent AI Analysis</div>
                <h2 className="home-title">Design Intelligent<br />Question Papers.</h2>
                <p className="home-subtitle">
                    Upload your syllabus and previous year questions. Our AI analyses topic priorities,
                    learns exam patterns, and architects the perfect exam — in seconds.
                </p>
                <div className="home-cta-group">
                    <button className="neon-btn huge-btn" onClick={() => onNavigate('landing')}>Get Started →</button>
                    <button className="ghost-btn" onClick={() => onNavigate('about')}>Learn How It Works</button>
                </div>
            </div>

            <div className="features-section">
                <h3 className="section-heading">What Makes NeuroGen Intelligent?</h3>
                <div className="features-grid">
                    {[
                        { icon: '🔍', title: 'RAG-Powered Analysis', desc: 'Retrieval-Augmented Generation extracts topic priorities and patterns from your uploaded PDFs with deep contextual understanding.' },
                        { icon: '📐', title: 'Smart Pattern Design', desc: 'Adaptive algorithms distribute marks across Bloom\'s Taxonomy levels, ensuring balanced and pedagogically sound question papers.' },
                        { icon: '💬', title: 'Chat-Driven Customisation', desc: 'Converse with an AI agent to refine sections, adjust mark distribution, and regenerate specific parts — all in natural language.' },
                        { icon: '📄', title: 'One-Click PDF Export', desc: 'Generate a professionally formatted, print-ready PDF with your institution\'s header and logo in a single click.' },
                        { icon: '🎯', title: 'Priority Scoring', desc: 'Frequency analysis of previous year questions surfaces high-priority topics, ensuring your paper reflects real exam trends.' },
                        { icon: '🔒', title: 'Secure & Private', desc: 'Your data is processed securely. We don\'t store your syllabus or generated papers on third-party servers.' },
                    ].map((feature, index) => (
                        <div key={index} className="feature-card">
                            <div className="feature-icon">{feature.icon}</div>
                            <h4>{feature.title}</h4>
                            <p>{feature.desc}</p>
                        </div>
                    ))}
                </div>
            </div>

            <div className="how-it-works">
                <h3 className="section-heading">How It Works</h3>
                <div className="steps-row">
                    {[
                        { step: '01', title: 'Upload Documents', desc: 'Provide your syllabus text, previous year question PDFs, and an optional reference pattern.' },
                        { step: '02', title: 'AI Analyses', desc: 'The RAG pipeline extracts topics, scores priorities, and detects the exam pattern from your files.' },
                        { step: '03', title: 'Design & Refine', desc: 'Use the Blueprint Studio and AI chat to customise sections, marks, and topic coverage.' },
                        { step: '04', title: 'Generate & Export', desc: 'Generate the final paper and download a polished, institution-ready PDF.' },
                    ].map((step, index) => (
                        <React.Fragment key={index}>
                            <div className="step-card">
                                <div className="step-number">{step.step}</div>
                                <h4>{step.title}</h4>
                                <p>{step.desc}</p>
                            </div>
                            {index < 3 && <div className="step-arrow">→</div>}
                        </React.Fragment>
                    ))}
                </div>
            </div>

            <footer className="home-footer">
                <span>🧠 NeuroGen Studio</span>
                <span className="footer-links">
                    <a href="#" className="footer-link" onClick={(e) => { e.preventDefault(); onNavigate('about'); }}>About & Algorithms</a>
                    <a href="#" className="footer-link" onClick={(e) => { e.preventDefault(); onNavigate('landing'); }}>Get Started</a>
                </span>
                <span className="text-muted">Built with LangChain · Flask · Vite</span>
            </footer>
        </div>
    );
};

export default HomePage;
