import { useState, useRef } from 'react';
import Navbar from '../components/Navbar';

const API_BASE = 'https://question-paper-generator-jg4p.onrender.com/api';

function getDefaultPattern() {
  return {
    'Section A': { description: 'Brief Answer', marks_per_question: 5, total_questions: 4, questions_to_attempt: 4 },
    'Section B': { description: 'Short Answer', marks_per_question: 5, total_questions: 6, questions_to_attempt: 4 },
    'Section C': { description: 'Long Answer', marks_per_question: 10, total_questions: 4, questions_to_attempt: 2 },
  };
}

export default function UploadPage({ onNavigate, onAnalysisComplete, showLoader, hideLoader }) {
  const [apiKey, setApiKey] = useState('');
  const [syllabusText, setSyllabusText] = useState('');
  const pyqRef = useRef(null);
  const refRef = useRef(null);

  const handleAnalyze = async () => {
    const pyqFiles = pyqRef.current?.files;
    const referenceFile = refRef.current?.files?.[0];

    if (!syllabusText || !pyqFiles || pyqFiles.length === 0) {
      alert('Please fill in Syllabus and at least one PYQ PDF.');
      return;
    }

    showLoader('Initializing Neural Analysis...');

    const formData = new FormData();
    formData.append('api_key', apiKey);
    formData.append('syllabus_text', syllabusText);
    for (let i = 0; i < pyqFiles.length; i++) {
      formData.append('pyq_files', pyqFiles[i]);
    }
    if (referenceFile) {
      formData.append('reference_file', referenceFile);
    }

    try {
      const response = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (data.error) throw new Error(data.error);

      const pattern = data.paper_pattern || getDefaultPattern();

      onAnalysisComplete({
        apiKey,
        analysisData: data,
        currentPattern: pattern,
      });
    } catch (err) {
      alert(err.message);
    } finally {
      hideLoader();
    }
  };

  return (
    <div className="landing-container">
      <Navbar activePage="upload" onNavigate={onNavigate} />

      <div className="hero-section">
        <h2 className="hero-title">Design Intelligent Question Papers.</h2>
        <p className="hero-subtitle">Upload your syllabus and let AI architect the perfect exam.</p>

        <div className="upload-card">
          <div className="input-group">
            <label>Groq API Key</label>
            <input
              type="password"
              placeholder="Optional if set in backend (sk-...)"
              className="glass-input"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
          </div>

          <div className="input-group">
            <label>Syllabus Text</label>
            <textarea
              placeholder="Paste module-wise syllabus..."
              className="glass-input"
              value={syllabusText}
              onChange={(e) => setSyllabusText(e.target.value)}
            />
          </div>

          <div className="file-drop-zone">
            <div className="input-group">
              <label>PYQs (PDF)</label>
              <input type="file" multiple accept=".pdf" className="glass-input file-input" ref={pyqRef} />
            </div>
            <div className="input-group">
              <label>Reference Pattern (PDF)</label>
              <input type="file" accept=".pdf" className="glass-input file-input" ref={refRef} />
            </div>
          </div>

          <button className="neon-btn huge-btn" onClick={handleAnalyze}>
            Start Designing <span className="arrow">→</span>
          </button>
        </div>
      </div>
    </div>
  );
}
