// ==========================================
// STATE MANAGEMENT
// ==========================================
const state = {
    apiKey: null,
    syllabusText: null,
    pyqFiles: null,
    referenceFile: null,
    analysisData: null,
    currentPattern: null, // { "Section A": { ... } }
    generatedPaperText: null
};

const apiBase = "https://question-paper-generator-jg4p.onrender.com/api";
// const apiBase = "http://127.0.0.1:5000/api"; // Local Debug

// DOM Elements
const landingPage = document.getElementById('landingPage');
const studioPage = document.getElementById('studioPage');
const loader = document.getElementById('loader');
const loadingText = document.getElementById('loadingText');

// ==========================================
// 1. LANDING PAGE LOGIC
// ==========================================
document.getElementById('analyzeBtn').addEventListener('click', async () => {
    const apiKey = document.getElementById('apiKey').value;
    const syllabusText = document.getElementById('syllabusText').value;
    const pyqFiles = document.getElementById('pyqFiles').files;
    const referenceFile = document.getElementById('referenceFile').files[0];

    // API Key is optional if set in backend
    // if (!apiKey) { ... } 

    if (!syllabusText || pyqFiles.length === 0) {
        alert("Please fill in Syllabus and at least one PYQ PDF.");
        return;
    }

    state.apiKey = apiKey;
    state.syllabusText = syllabusText;
    state.pyqFiles = pyqFiles;
    state.referenceFile = referenceFile;

    showLoader("Initializing Neural Analysis...");

    const formData = new FormData();
    formData.append('api_key', apiKey); // Can be empty
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

        state.analysisData = data;
        state.currentPattern = data.paper_pattern || getDefaultPattern();

        // Transition to Studio
        landingPage.classList.add('hidden');
        studioPage.classList.remove('hidden');

        // Init Studio
        initStudio();

    } catch (err) {
        alert(err.message);
    } finally {
        hideLoader();
    }
});

function getDefaultPattern() {
    return {
        "Section A": { description: "Brief Answer", marks_per_question: 5, total_questions: 4, questions_to_attempt: 4 },
        "Section B": { description: "Short Answer", marks_per_question: 5, total_questions: 6, questions_to_attempt: 4 },
        "Section C": { description: "Long Answer", marks_per_question: 10, total_questions: 4, questions_to_attempt: 2 }
    };
}

// ==========================================
// 2. STUDIO LOGIC
// ==========================================
function initStudio() {
    // Update Stats
    document.getElementById('topicCount').innerText = Object.keys(state.analysisData.syllabus_topics).length;
    document.getElementById('priorityCount').innerText = Object.keys(state.analysisData.priority_scores).length;

    // Render Initial View
    renderBlueprint();

    // Add Initial Bot Message
    if (!state.analysisData.paper_pattern) {
        addChatMessage("I analyzed the syllabus but didn't find a reference pattern. I've created a standard template for you.", 'bot');
    }
}

// Tab Switching
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('active'));

        btn.classList.add('active');
        document.getElementById(`${btn.dataset.tab}View`).classList.add('active');
    });
});

document.getElementById('backToHomeBtn').addEventListener('click', () => {
    if (confirm("Exit Studio? All progress will be lost.")) {
        studioPage.classList.add('hidden');
        landingPage.classList.remove('hidden');
    }
});

// ==========================================
// 3. BLUEPRINT VISUALIZER
// ==========================================
function renderBlueprint() {
    const canvas = document.getElementById('patternCanvas');
    canvas.innerHTML = '';

    if (!state.currentPattern) return;

    Object.entries(state.currentPattern).forEach(([sectionName, details]) => {
        const totalMarks = details.marks_per_question * details.questions_to_attempt;

        const card = document.createElement('div');
        card.className = 'pattern-card';
        card.innerHTML = `
            <div class="card-header">${sectionName}</div>
            <div class="card-meta">${details.description}</div>
            <div style="display:flex; gap:5px; flex-wrap:wrap;">
                <span class="card-tag">Marks/Q: ${details.marks_per_question}</span>
                <span class="card-tag">Total Qs: ${details.total_questions}</span>
                <span class="card-tag">Attempt: ${details.questions_to_attempt}</span>
                <span class="card-tag" style="border-color:var(--neon-purple); color:var(--neon-purple)">Total: ${totalMarks}</span>
            </div>
        `;
        canvas.appendChild(card);
    });
}

// ==========================================
// 4. GENERATION & PREVIEW
// ==========================================
document.getElementById('generateBtn').addEventListener('click', async () => {
    showLoader("Generating Question Paper...");

    try {
        const response = await fetch(`${apiBase}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                api_key: state.apiKey,
                allocation: state.analysisData.default_allocation,
                paper_pattern: state.currentPattern,
                priority_scores: state.analysisData.priority_scores
            })
        });

        const data = await response.json();
        if (data.error) throw new Error(data.error);

        state.generatedPaperText = data.paper_text;

        // Auto-switch to Preview Tab
        document.querySelector('[data-tab="preview"]').click();
        renderPaperPreview(data.paper_text);

    } catch (err) {
        alert(err.message);
    } finally {
        hideLoader();
    }
});

function renderPaperPreview(text) {
    const collegeName = document.getElementById('collegeName').value || "COLLEGE OF ENGINEERING";
    const container = document.getElementById('a4Page');

    // Simple conversion of text to HTML structure
    // We assume the text has markdown-like headers

    let html = `
        <div style="text-align:center; margin-bottom: 2rem;">
            <h2 style="margin:0; font-size:16pt">${collegeName.toUpperCase()}</h2>
            <h3 style="margin:5px 0; font-size:12pt; font-weight:normal">EXAMINATION - ${new Date().getFullYear()}</h3>
            <div style="border-bottom: 1px solid #000; margin-top:10px; width:100%"></div>
        </div>
        <div style="white-space: pre-wrap; font-family: 'Times New Roman'; line-height: 1.5;">${text}</div>
    `;

    // Bold replacement
    html = html.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
    html = html.replace(/Section [A-Z]/g, '<br><h4 style="margin:10px 0; text-decoration:underline">$&</h4>');

    container.innerHTML = html;
}

document.getElementById('downloadPdfBtn').addEventListener('click', async () => {
    if (!state.generatedPaperText) return;

    const collegeName = document.getElementById('collegeName').value;

    try {
        const response = await fetch(`${apiBase}/download-pdf`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text_content: state.generatedPaperText,
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
// 5. CHAT LOGIC
// ==========================================
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendMessageBtn');
const chatHistory = document.getElementById('chatHistory');

function addChatMessage(text, sender) {
    const div = document.createElement('div');
    div.className = `chat-msg ${sender}`;
    div.innerHTML = text; // Allow HTML in bot responses
    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

sendBtn.addEventListener('click', async () => {
    const msg = chatInput.value.trim();
    if (!msg) return;

    addChatMessage(msg, 'user');
    chatInput.value = '';

    const loaderId = 'chat-loader-' + Date.now();
    addChatMessage(`<span id="${loaderId}">Thinking...</span>`, 'bot');

    try {
        const response = await fetch(`${apiBase}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                api_key: state.apiKey,
                message: msg,
                context: {
                    syllabus_topics: state.analysisData.syllabus_topics,
                    paper_pattern: state.currentPattern
                }
            })
        });

        const data = await response.json();

        // Remove loader
        const loaderEl = document.getElementById(loaderId);
        if (loaderEl) loaderEl.parentElement.remove();

        addChatMessage(data.reply, 'bot');

        // Handle JSON Actions
        if (data.action === 'update_pattern' && data.data) {
            state.currentPattern = data.data;
            renderBlueprint();
            addChatMessage("<i>I've updated the pattern blueprint based on your request.</i>", 'bot');
        }

    } catch (err) {
        const loaderEl = document.getElementById(loaderId);
        if (loaderEl) loaderEl.parentElement.textContent = "Error: " + err.message;
    }
});

chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendBtn.click();
});

// Helpers
function showLoader(text) {
    loadingText.innerText = text;
    loader.classList.remove('hidden');
}
function hideLoader() {
    loader.classList.add('hidden');
}
