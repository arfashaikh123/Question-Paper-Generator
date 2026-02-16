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
