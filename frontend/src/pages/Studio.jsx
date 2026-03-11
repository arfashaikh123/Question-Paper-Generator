import React, { useState } from 'react';

const Studio = ({ onNavigate, analysisData }) => {
    const [activeTab, setActiveTab] = useState('blueprint');
    const [chatMessages, setChatMessages] = useState([
        { text: "Analysis Complete! I've extracted the topics. You can now: Ask to add sections, Change marks distribution, or Generate the paper.", sender: 'bot' }
    ]);
    const [chatInput, setChatInput] = useState('');

    const handleSendMessage = () => {
        if (!chatInput.trim()) return;
        setChatMessages([...chatMessages, { text: chatInput, sender: 'user' }]);
        setChatInput('');
        // AI logic would go here
    };

    return (
        <div className="studio-container">
            {/* LEFT PANEL: Chat & Controls */}
            <aside className="studio-left">
                <div className="studio-header">
                    <div className="logo-small">🧠 NeuroGen</div>
                    <button className="icon-btn" onClick={() => onNavigate('home')}>🏠</button>
                </div>

                <div className="chat-interface">
                    <div className="chat-history">
                        {chatMessages.map((msg, i) => (
                            <div key={i} className={`chat-msg ${msg.sender}`}>
                                {msg.text}
                            </div>
                        ))}
                    </div>
                    <div className="chat-input-wrapper">
                        <input
                            type="text"
                            className="glass-input"
                            placeholder="Type instructions..."
                            value={chatInput}
                            onChange={(e) => setChatInput(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                        />
                        <button className="send-btn" onClick={handleSendMessage}>➤</button>
                    </div>
                </div>

                <div className="manual-controls">
                    <div className="input-group">
                        <label>Header Details (AI Formatted)</label>
                        <textarea className="glass-input compact" placeholder="e.g. ABC College, Mid Term 2025, CS Dept" rows="3" />
                    </div>
                    <div className="input-group">
                        <label>Header Logo/Image</label>
                        <input type="file" className="glass-input compact" accept="image/*" />
                    </div>
                    <button className="neon-btn full-width">Generate Paper Result</button>
                </div>
            </aside>

            {/* RIGHT PANEL: Visualization & Preview */}
            <main className="studio-right">
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

                {activeTab === 'blueprint' && (
                    <div className="view-panel active">
                        <div className="blueprint-canvas">
                            <div className="stats-bar">
                                <div className="stat-item">Topics: <span>{analysisData?.topics_data?.length || 0}</span></div>
                                <div className="stat-item">Priorities: <span>{analysisData?.priorities?.length || 0}</span></div>
                            </div>
                            <div className="pattern-grid">
                                {analysisData ? (
                                    <div className="blueprint-info">
                                        {/* Dynamic content here */}
                                        <p>Analysis data loaded. Ready to design.</p>
                                    </div>
                                ) : (
                                    <div className="empty-state">
                                        No pattern defined yet. Ask AI to "Create a standard pattern".
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'preview' && (
                    <div className="view-panel active">
                        <div className="paper-stage">
                            <div className="a4-page">
                                {/* Preview content */}
                                <p className="text-muted">Generate paper to see preview.</p>
                            </div>
                        </div>
                        <div className="preview-actions">
                            <button className="neon-btn">Download PDF</button>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
};

export default Studio;
