// ==========================================
// APP LOGIC & API
// ==========================================
let analysisData = null;
const apiBase = "https://question-paper-generator-jg4p.onrender.com/api"; // Render Backend

// DOM Elements
const analyzeBtn = document.getElementById('analyzeBtn');
const generateBtn = document.getElementById('generateBtn');
const downloadPdfBtn = document.getElementById('downloadPdfBtn');
const resultsSection = document.getElementById('resultsSection');
const loader = document.getElementById('loader');
const loadingText = document.getElementById('loadingText');
const paperOutput = document.getElementById('paperOutput');
const paperContent = document.getElementById('paperContent');
const collegeNameInput = document.getElementById('collegeName');



// 1. Analyze Handler
analyzeBtn.addEventListener('click', async () => {
    const apiKey = document.getElementById('apiKey').value;
    const syllabusText = document.getElementById('syllabusText').value;
    const pyqFiles = document.getElementById('pyqFiles').files;
    const referenceFile = document.getElementById('referenceFile').files[0];

    if (!apiKey || !syllabusText || pyqFiles.length === 0) {
        alert("Please fill in all fields (API Key, Syllabus, PYQs).");
        return;
    }

    // UI Updates
    loader.classList.remove('hidden');
    resultsSection.classList.add('hidden');
    loadingText.textContent = referenceFile ? "Parsing Pattern & Analyzing..." : "Analyzing Syllabus & PYQs...";

    // Prepare Data
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
        const response = await fetch(`${apiBase}/analyze`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.error) throw new Error(data.error);

        analysisData = data;

        // Update UI
        document.getElementById('topicCount').textContent = Object.keys(data.syllabus_topics).length;
        // Check if pattern was detected
        if (data.paper_pattern) {
            document.getElementById('priorityCount').innerHTML = `<span style="color:#00f3ff">Pattern Detected</span>`;
        } else {
            document.getElementById('priorityCount').textContent = Object.keys(data.priority_scores).length + " Priorities";
        }

        if (data.paper_pattern) {
            document.getElementById('priorityCount').innerHTML = `<span style="color:#00f3ff">Pattern Detected</span>`;
        } else {
            document.getElementById('priorityCount').textContent = Object.keys(data.priority_scores).length + " Priorities";
        }

        resultsSection.classList.remove('hidden');
    } catch (err) {
        alert("Analysis Failed: " + err.message);
    } finally {
        loader.classList.add('hidden');
    }
});

// 2. Generate Handler
generateBtn.addEventListener('click', async () => {
    if (!analysisData) return;

    loader.classList.remove('hidden');
    loadingText.textContent = "Generating Question Paper...";

    // Use analyzed pattern
    const finalPattern = analysisData.paper_pattern;

    try {
        const response = await fetch(`${apiBase}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                api_key: document.getElementById('apiKey').value,
                allocation: analysisData.default_allocation,
                paper_pattern: finalPattern,
                priority_scores: analysisData.priority_scores
            })
        });

        const data = await response.json();
        if (data.error) throw new Error(data.error);

        paperContent.textContent = data.paper_text;
        paperOutput.classList.remove('hidden');

    } catch (err) {
        alert("Generation Failed: " + err.message);
    } finally {
        loader.classList.add('hidden');
    }
});

// 3. Download PDF Handler
downloadPdfBtn.addEventListener('click', async () => {
    const text = paperContent.textContent;
    if (!text) return;

    const collegeName = collegeNameInput.value.trim();

    try {
        const response = await fetch(`${apiBase}/download-pdf`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text_content: text,
                college_name: collegeName
            })
        });

        if (!response.ok) throw new Error("Download failed");

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = "Question_Paper.pdf";
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);

    } catch (err) {
        alert(err.message);
    }
});

// ==========================================
// CHATBOT LOGIC
// ==========================================
const chatContainer = document.getElementById('chatContainer');
const chatTriggerBtn = document.getElementById('chatTriggerBtn');
const closeChatBtn = document.getElementById('closeChatBtn');
const chatInput = document.getElementById('chatInput');
const sendMessageBtn = document.getElementById('sendMessageBtn');
const chatHistory = document.getElementById('chatHistory');

// Toggle Chat
function toggleChat() {
    chatContainer.classList.toggle('closed');
}

chatTriggerBtn.addEventListener('click', toggleChat);
closeChatBtn.addEventListener('click', toggleChat);

// Append Message
function appendMessage(text, sender) {
    const div = document.createElement('div');
    div.className = `chat-msg ${sender}`;
    div.textContent = text;
    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// Send Message
async function sendChatMessage() {
    const message = chatInput.value.trim();
    if (!message) return;

    if (!analysisData) {
        alert("Please analyze a syllabus first so I have context!");
        return;
    }

    const apiKey = document.getElementById('apiKey').value;

    // UI Update
    appendMessage(message, 'user');
    chatInput.value = '';
    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'chat-msg bot';
    loadingMsg.textContent = "Thinking...";
    chatHistory.appendChild(loadingMsg);

    try {
        const response = await fetch(`${apiBase}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                api_key: apiKey,
                message: message,
                context: {
                    syllabus_topics: analysisData.syllabus_topics,
                    paper_pattern: analysisData.paper_pattern,
                    priority_scores: analysisData.priority_scores
                }
            })
        });

        const data = await response.json();
        chatHistory.removeChild(loadingMsg);

        if (data.error) throw new Error(data.error);

        appendMessage(data.reply, 'bot');

        // Handle Actions (Future)
        if (data.action === 'regenerate_suggestion') {
            appendMessage("💡 Tip: You can click 'Generate Paper' again to see changes if I've updated the config (not yet implemented).", 'bot');
        }

    } catch (err) {
        chatHistory.removeChild(loadingMsg);
        appendMessage("Error: " + err.message, 'bot');
    }
}

sendMessageBtn.addEventListener('click', sendChatMessage);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendChatMessage();
});

// Show Chat Button after analysis
const originalAnalyze = analyzeBtn.onclick;
// Note: We use addEventListener, so we can just add another listener
analyzeBtn.addEventListener('click', () => {
    // Show chat button once analysis starts/completes
    chatTriggerBtn.classList.remove('hidden');
});
