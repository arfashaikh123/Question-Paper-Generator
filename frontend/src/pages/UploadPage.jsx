import { useState, useRef } from 'react';
import Navbar from '../components/Navbar';

const API_BASE = 'https://question-paper-generator-jg4p.onrender.com/api';

const TEMPLATES = {
  auto: {
    label: 'Auto-detect from Reference PDF',
    pattern: null,
  },
  ese_mu: {
    label: 'ESE — Mumbai University (60 / 100 Marks)',
    pattern: {
      'Q1': {
        description: 'Two sub-questions (a & b) of 10 marks each',
        marks_per_question: 20,
        total_questions: 1,
        questions_to_attempt: 1,
      },
      'Q2': {
        description: 'Two sub-questions (a & b) of 10 marks each',
        marks_per_question: 20,
        total_questions: 1,
        questions_to_attempt: 1,
      },
      'Q3': {
        description: 'Two sub-questions (a & b) of 10 marks each',
        marks_per_question: 20,
        total_questions: 1,
        questions_to_attempt: 1,
      },
      'Q4': {
        description: 'Two sub-questions (a & b) of 10 marks each',
        marks_per_question: 20,
        total_questions: 1,
        questions_to_attempt: 1,
      },
      'Q5': {
        description: 'Two sub-questions (a & b) of 10 marks each',
        marks_per_question: 20,
        total_questions: 1,
        questions_to_attempt: 1,
      },
    },
    info: 'Total: 100 marks on paper · Attempt any 3 question sets = 60 marks',
  },
  default: {
    label: 'Standard 3-Section (ABC)',
    pattern: {
      'Section A': { description: 'Brief Answer', marks_per_question: 5, total_questions: 4, questions_to_attempt: 4 },
      'Section B': { description: 'Short Answer', marks_per_question: 5, total_questions: 6, questions_to_attempt: 4 },
      'Section C': { description: 'Long Answer', marks_per_question: 10, total_questions: 4, questions_to_attempt: 2 },
    },
  },
};

export default function UploadPage({ onNavigate, onAnalysisComplete, showLoader, hideLoader }) {
  const [syllabusText, setSyllabusText] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('ese_mu');
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
    formData.append('api_key', '');
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

      // Use template pattern, or auto-detected from backend, or default
      let pattern;
      if (selectedTemplate === 'auto') {
        pattern = data.paper_pattern || TEMPLATES.default.pattern;
      } else {
        pattern = TEMPLATES[selectedTemplate]?.pattern || TEMPLATES.default.pattern;
      }

      onAnalysisComplete({
        apiKey: '',
        analysisData: data,
        currentPattern: pattern,
      });
    } catch (err) {
      alert(err.message);
    } finally {
      hideLoader();
    }
  };

  const currentTemplate = TEMPLATES[selectedTemplate];

  return (
    <div className="landing-container">
      <Navbar activePage="upload" onNavigate={onNavigate} />

      <div className="hero-section">
        <h2 className="hero-title">Design Intelligent Question Papers.</h2>
        <p className="hero-subtitle">Upload your syllabus and let AI architect the perfect exam.</p>

        <div className="upload-card">

          {/* Template Selector */}
          <div className="input-group">
            <label>Exam Template</label>
            <select
              className="glass-input"
              value={selectedTemplate}
              onChange={(e) => setSelectedTemplate(e.target.value)}
            >
              {Object.entries(TEMPLATES).map(([key, tmpl]) => (
                <option key={key} value={key}>{tmpl.label}</option>
              ))}
            </select>
          </div>

          {currentTemplate?.pattern && (
            <div style={{ padding: '0.6rem 0' }}>
              <div style={{
                display: 'flex',
                gap: '0.5rem',
                flexWrap: 'wrap',
              }}>
                {Object.entries(currentTemplate.pattern).map(([name, d]) => (
                  <span key={name} style={{
                    background: 'rgba(0, 243, 255, 0.1)',
                    border: '1px solid rgba(0, 243, 255, 0.25)',
                    color: '#00f3ff',
                    padding: '4px 10px',
                    borderRadius: '6px',
                    fontSize: '0.75rem',
                  }}>
                    {name}: {d.marks_per_question}m × {d.questions_to_attempt}
                  </span>
                ))}
              </div>
              {currentTemplate.info && (
                <div style={{
                  color: '#888',
                  fontSize: '0.8rem',
                  marginTop: '0.5rem',
                }}>
                  {currentTemplate.info}
                </div>
              )}
            </div>
          )}

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
