import React, { useState, useEffect } from 'react';
import Background from './components/Background';
import HomePage from './pages/HomePage';
import AboutPage from './pages/AboutPage';
import LandingPage from './pages/LandingPage';
import Studio from './pages/Studio'; // We'll create this next

function App() {
  const [currentPage, setCurrentPage] = useState('home');
  const [analysisData, setAnalysisData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingText, setLoadingText] = useState('Processing...');

  const navigate = (page) => {
    setCurrentPage(page);
  };

  const handleAnalyze = async (formData) => {
    setIsLoading(true);
    setLoadingText('Analyzing Documents...');

    const apiBase = 'http://localhost:5000'; // Adjust as needed
    const data = new FormData();
    data.append('syllabus_text', formData.syllabusText);
    for (let i = 0; i < formData.pyqFiles.length; i++) {
      data.append('pyq_files', formData.pyqFiles[i]);
    }
    if (formData.referenceFile) {
      data.append('reference_file', formData.referenceFile);
    }

    try {
      const response = await fetch(`${apiBase}/analyze`, {
        method: 'POST',
        body: data
      });
      const result = await response.json();
      if (result.error) throw new Error(result.error);

      setAnalysisData(result);
      setCurrentPage('studio');
    } catch (err) {
      alert(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <Background />
      {currentPage === 'home' && <HomePage onNavigate={navigate} />}
      {currentPage === 'about' && <AboutPage onNavigate={navigate} />}
      {currentPage === 'landing' && <LandingPage onNavigate={navigate} onAnalyze={handleAnalyze} />}
      {currentPage === 'studio' && <Studio onNavigate={navigate} analysisData={analysisData} />}

      {isLoading && (
        <div id="loader" className="loader">
          <div className="spinner"></div>
          <p>{loadingText}</p>
        </div>
      )}
    </>
  );
}

export default App;
