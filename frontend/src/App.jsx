import { useState } from 'react';
import BackgroundCanvas from './components/BackgroundCanvas';
import Loader from './components/Loader';
import HomePage from './pages/HomePage';
import AboutPage from './pages/AboutPage';
import UploadPage from './pages/UploadPage';
import StudioPage from './pages/StudioPage';

export default function App() {
  const [currentPage, setCurrentPage] = useState('home');
  const [loaderVisible, setLoaderVisible] = useState(false);
  const [loaderText, setLoaderText] = useState('Processing...');

  // Shared state passed from Upload → Studio
  const [apiKey, setApiKey] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);
  const [currentPattern, setCurrentPattern] = useState(null);

  const navigate = (page) => {
    setCurrentPage(page);
    window.scrollTo(0, 0);
  };

  const showLoader = (text) => {
    setLoaderText(text);
    setLoaderVisible(true);
  };

  const hideLoader = () => {
    setLoaderVisible(false);
  };

  const handleAnalysisComplete = ({ apiKey: key, analysisData: data, currentPattern: pattern }) => {
    setApiKey(key);
    setAnalysisData(data);
    setCurrentPattern(pattern);
    navigate('studio');
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'home':
        return <HomePage onNavigate={navigate} />;
      case 'about':
        return <AboutPage onNavigate={navigate} />;
      case 'upload':
        return (
          <UploadPage
            onNavigate={navigate}
            onAnalysisComplete={handleAnalysisComplete}
            showLoader={showLoader}
            hideLoader={hideLoader}
          />
        );
      case 'studio':
        return (
          <StudioPage
            apiKey={apiKey}
            analysisData={analysisData}
            initialPattern={currentPattern}
            onNavigate={navigate}
            showLoader={showLoader}
            hideLoader={hideLoader}
          />
        );
      default:
        return <HomePage onNavigate={navigate} />;
    }
  };

  return (
    <>
      <BackgroundCanvas />
      {renderPage()}
      <Loader visible={loaderVisible} text={loaderText} />
    </>
  );
}
