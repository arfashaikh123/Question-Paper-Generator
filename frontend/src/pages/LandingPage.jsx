import React, { useState } from 'react';
import Navbar from '../components/Navbar';

const LandingPage = ({ onNavigate, onAnalyze }) => {
    const [syllabusText, setSyllabusText] = useState('');
    const [pyqFiles, setPyqFiles] = useState([]);
    const [referenceFile, setReferenceFile] = useState(null);

    const handleAnalyze = () => {
        onAnalyze({ syllabusText, pyqFiles, referenceFile });
    };

    return (
        <div className="landing-container">
            <Navbar activePage="landing" onNavigate={onNavigate} />

            <div className="hero-section">
                <h2 className="hero-title">Design Intelligent Question Papers.</h2>
                <p className="hero-subtitle">Upload your syllabus and let AI architect the perfect exam.</p>

                <div className="upload-card">

                    <div className="input-group">
                        <label>Syllabus Text</label>
                        <textarea
                            className="glass-input"
                            placeholder="Paste module-wise syllabus..."
                            value={syllabusText}
                            onChange={(e) => setSyllabusText(e.target.value)}
                        />
                    </div>

                    <div className="file-drop-zone">
                        <div className="input-group">
                            <label>PYQs (PDF)</label>
                            <input
                                type="file"
                                className="glass-input file-input"
                                multiple
                                accept=".pdf"
                                onChange={(e) => setPyqFiles(e.target.files)}
                            />
                        </div>
                        <div className="input-group">
                            <label>Reference Pattern (PDF)</label>
                            <input
                                type="file"
                                className="glass-input file-input"
                                accept=".pdf"
                                onChange={(e) => setReferenceFile(e.target.files[0])}
                            />
                        </div>
                    </div>

                    <button className="neon-btn huge-btn" onClick={handleAnalyze}>
                        Start Designing <span className="arrow">→</span>
                    </button>
                </div>
            </div>
        </div>
    );
};

export default LandingPage;
