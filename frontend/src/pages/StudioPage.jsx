import { useState, useRef, useEffect } from 'react';

const API_BASE = 'https://question-paper-generator-jg4p.onrender.com/api';

export default function StudioPage({ apiKey, analysisData, initialPattern, onNavigate, showLoader, hideLoader }) {
  const [currentPattern, setCurrentPattern] = useState(initialPattern);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [activeTab, setActiveTab] = useState('blueprint');
  const [generatedPaperText, setGeneratedPaperText] = useState(null);
  const [previewHtml, setPreviewHtml] = useState('');
  const [headerDetails, setHeaderDetails] = useState('');
  const headerImageRef = useRef(null);
  const chatHistoryRef = useRef(null);

  // Initialize on mount
  useEffect(() => {
    const initMessages = [];

    initMessages.push({
      sender: 'bot',
      html: `Analysis Complete! I've extracted the topics. You can now:
        <ul><li>Ask to add sections</li><li>Change marks distribution</li><li>Generate the paper</li></ul>`,
    });

    if (!analysisData.paper_pattern) {
      initMessages.push({
        sender: 'bot',
        html: "I analyzed the syllabus but didn't find a reference pattern. I've created a standard template for you.",
      });
    }

    if (analysisData.extracted_header) {
      setHeaderDetails(analysisData.extracted_header);
      initMessages.push({
        sender: 'bot',
        html: "<i>I've extracted the exam header from your PYQ. You can check it in the 'Manual Actions' panel.</i>",
      });
    }

    setChatMessages(initMessages);
  }, [analysisData]);

  // Auto-scroll chat
  useEffect(() => {
    if (chatHistoryRef.current) {
      chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight;
    }
  }, [chatMessages]);

  const addMessage = (html, sender) => {
    setChatMessages((prev) => [...prev, { sender, html }]);
  };

  // Chat
  const handleSendMessage = async () => {
    const msg = chatInput.trim();
    if (!msg) return;

    addMessage(msg, 'user');
    setChatInput('');
    addMessage('Thinking...', 'bot');

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key: apiKey,
          message: msg,
          context: {
            syllabus_topics: analysisData.syllabus_topics,
            paper_pattern: currentPattern,
          },
        }),
      });
      const data = await response.json();

      // Remove "Thinking..." message
      setChatMessages((prev) => prev.slice(0, -1));

      addMessage(data.reply, 'bot');

      if (data.action === 'update_pattern' && data.data) {
        setCurrentPattern(data.data);
        addMessage("<i>I've updated the pattern blueprint based on your request.</i>", 'bot');
      }
    } catch (err) {
      setChatMessages((prev) => prev.slice(0, -1));
      addMessage('Error: ' + err.message, 'bot');
    }
  };

  // Generate Paper
  const handleGenerate = async () => {
    showLoader('Generating Question Paper...');

    try {
      const response = await fetch(`${API_BASE}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key: apiKey,
          allocation: analysisData.default_allocation,
          paper_pattern: currentPattern,
          priority_scores: analysisData.priority_scores,
        }),
      });

      const data = await response.json();
      if (data.error) throw new Error(data.error);

      setGeneratedPaperText(data.paper_text);
      setActiveTab('preview');

      // Read header image for preview
      const imageFile = headerImageRef.current?.files?.[0];
      if (imageFile) {
        const reader = new FileReader();
        reader.onload = (e) => buildPreviewHtml(data.paper_text, e.target.result);
        reader.readAsDataURL(imageFile);
      } else {
        buildPreviewHtml(data.paper_text, null);
      }
    } catch (err) {
      alert(err.message);
    } finally {
      hideLoader();
    }
  };

  const buildPreviewHtml = (text, imageUrl) => {
    const header = headerDetails || 'COLLEGE OF ENGINEERING\nEXAMINATION - 202X';
    let imageHtml = '';
    if (imageUrl) {
      imageHtml = `<div style="text-align:center; margin-bottom:10px;"><img src="${imageUrl}" style="max-height:80px;"></div>`;
    }
    const headerLines = header.split('\n').map((line) => `<div>${line.toUpperCase()}</div>`).join('');
    let html = `
      ${imageHtml}
      <div style="text-align:center; margin-bottom: 2rem; font-weight:bold; font-size:14pt; line-height:1.4">
        ${headerLines}
        <div style="border-bottom: 1px solid #000; margin-top:10px; width:100%"></div>
      </div>
      <div style="white-space: pre-wrap; font-family: 'Times New Roman'; line-height: 1.5;">${text}</div>
    `;
    html = html.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
    html = html.replace(/Section [A-Z]/g, '<br><h4 style="margin:10px 0; text-decoration:underline">$&</h4>');
    setPreviewHtml(html);
  };

  // Download PDF
  const handleDownloadPdf = async () => {
    if (!generatedPaperText) return;

    try {
      let base64Image = null;
      const imageFile = headerImageRef.current?.files?.[0];
      if (imageFile) {
        base64Image = await new Promise((resolve) => {
          const reader = new FileReader();
          reader.onload = (e) => resolve(e.target.result);
          reader.readAsDataURL(imageFile);
        });
      }

      showLoader('Refining Header & Generating PDF...');

      const response = await fetch(`${API_BASE}/download-pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text_content: generatedPaperText,
          header_text_raw: headerDetails,
          header_image: base64Image,
        }),
      });

      hideLoader();

      if (!response.ok) throw new Error('Download failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'Question_Paper.pdf';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
    } catch (err) {
      hideLoader();
      alert(err.message);
    }
  };

  const topicCount = analysisData.syllabus_topics ? Object.keys(analysisData.syllabus_topics).length : 0;
  const priorityCount = analysisData.priority_scores ? Object.keys(analysisData.priority_scores).length : 0;

  return (
    <div className="studio-container">
      {/* LEFT PANEL: Chat & Controls */}
      <aside className="studio-left">
        <div className="studio-header">
          <div className="logo-small">🧠 NeuroGen</div>
          <button
            className="icon-btn"
            onClick={() => {
              if (window.confirm('Exit Studio? All progress will be lost.')) {
                onNavigate('home');
              }
            }}
          >
            🏠
          </button>
        </div>

        {/* Chat Interface */}
        <div className="chat-interface">
          <div className="chat-history" ref={chatHistoryRef}>
            {chatMessages.map((msg, i) => (
              <div
                key={i}
                className={`chat-msg ${msg.sender}`}
                dangerouslySetInnerHTML={{ __html: msg.html }}
              />
            ))}
          </div>
          <div className="chat-input-wrapper">
            <input
              type="text"
              placeholder="Type instructions..."
              className="glass-input"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') handleSendMessage(); }}
            />
            <button className="send-btn" onClick={handleSendMessage}>➤</button>
          </div>
        </div>

        {/* Manual Controls */}
        <div className="manual-controls">
          <div className="input-group">
            <label>Header Details (AI Formatted)</label>
            <textarea
              placeholder="e.g. ABC College, Mid Term 2025, CS Dept"
              className="glass-input compact"
              rows="3"
              value={headerDetails}
              onChange={(e) => setHeaderDetails(e.target.value)}
            />
          </div>
          <div className="input-group">
            <label>Header Logo/Image</label>
            <input type="file" accept="image/*" className="glass-input compact" ref={headerImageRef} />
          </div>
          <button className="neon-btn full-width" onClick={handleGenerate}>
            Generate Paper Result
          </button>
        </div>
      </aside>

      {/* RIGHT PANEL: Visualization & Preview */}
      <main className="studio-right">
        {/* Tabs */}
        <div className="studio-tabs">
          <button
            className={`tab-btn ${activeTab === 'blueprint' ? 'active' : ''}`}
            onClick={() => setActiveTab('blueprint')}
          >
            📐 Pattern Blueprint
          </button>
          <button
            className={`tab-btn ${activeTab === 'preview' ? 'active' : ''}`}
            onClick={() => setActiveTab('preview')}
          >
            📄 Paper Preview
          </button>
        </div>

        {/* Blueprint View */}
        <div className={`view-panel ${activeTab === 'blueprint' ? 'active' : ''}`}>
          <div className="blueprint-canvas">
            <div className="stats-bar">
              <div className="stat-item">Topics: <span>{topicCount}</span></div>
              <div className="stat-item">Priorities: <span>{priorityCount}</span></div>
            </div>
            <div className="pattern-grid">
              {currentPattern ? (
                Object.entries(currentPattern).map(([sectionName, details]) => {
                  const totalMarks = details.marks_per_question * details.questions_to_attempt;
                  return (
                    <div className="pattern-card" key={sectionName}>
                      <div className="card-header">{sectionName}</div>
                      <div className="card-meta">{details.description}</div>
                      <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                        <span className="card-tag">Marks/Q: {details.marks_per_question}</span>
                        <span className="card-tag">Total Qs: {details.total_questions}</span>
                        <span className="card-tag">Attempt: {details.questions_to_attempt}</span>
                        <span className="card-tag" style={{ borderColor: 'var(--neon-purple)', color: 'var(--neon-purple)' }}>
                          Total: {totalMarks}
                        </span>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="empty-state">
                  No pattern defined yet. Ask AI to "Create a standard pattern".
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Preview View */}
        <div className={`view-panel ${activeTab === 'preview' ? 'active' : ''}`}>
          <div className="paper-stage">
            <div className="a4-page" dangerouslySetInnerHTML={{ __html: previewHtml }} />
          </div>
          <div className="preview-actions">
            <button className="neon-btn" onClick={handleDownloadPdf}>Download PDF</button>
          </div>
        </div>
      </main>
    </div>
  );
}
