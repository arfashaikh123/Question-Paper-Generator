// ==========================================
// THREE.JS SETUP
// ==========================================
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });

renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
document.getElementById('canvas-container').appendChild(renderer.domElement);

// Lighting
const ambientLight = new THREE.AmbientLight(0x404040, 2);
scene.add(ambientLight);

const pointLight = new THREE.PointLight(0x00f3ff, 1, 100);
pointLight.position.set(10, 10, 10);
scene.add(pointLight);

// ==========================================
// NEURAL NETWORK VISUALIZATION
// ==========================================
const nodes = [];
const connections = [];
const particleCount = 60;
const connectionDistance = 3.5;

// Geometry for Nodes
const nodeGeometry = new THREE.IcosahedronGeometry(0.15, 0);
const nodeMaterial = new THREE.MeshBasicMaterial({ color: 0x00f3ff, transparent: true, opacity: 0.8 });

// Create Nodes
for (let i = 0; i < particleCount; i++) {
    const node = new THREE.Mesh(nodeGeometry, nodeMaterial.clone());

    // Random Position
    node.position.x = (Math.random() - 0.5) * 15;
    node.position.y = (Math.random() - 0.5) * 15;
    node.position.z = (Math.random() - 0.5) * 15;

    // Velocity for movement
    node.velocity = new THREE.Vector3(
        (Math.random() - 0.5) * 0.02,
        (Math.random() - 0.5) * 0.02,
        (Math.random() - 0.5) * 0.02
    );

    scene.add(node);
    nodes.push(node);
}

// Lines Material
const lineMaterial = new THREE.LineBasicMaterial({ color: 0x00f3ff, transparent: true, opacity: 0.15 });

// Animation Loop
const animate = () => {
    requestAnimationFrame(animate);

    // Update Nodes
    nodes.forEach(node => {
        node.position.add(node.velocity);

        // Boundary Check (Bounce back)
        if (Math.abs(node.position.x) > 8) node.velocity.x *= -1;
        if (Math.abs(node.position.y) > 8) node.velocity.y *= -1;
        if (Math.abs(node.position.z) > 8) node.velocity.z *= -1;

        // Rotation for effect
        node.rotation.x += 0.01;
        node.rotation.y += 0.01;
    });

    // Update Connections (Dynamic Lines)
    // Clear old lines
    connections.forEach(line => scene.remove(line));
    connections.length = 0;

    for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
            const dist = nodes[i].position.distanceTo(nodes[j].position);

            if (dist < connectionDistance) {
                const geometry = new THREE.BufferGeometry().setFromPoints([
                    nodes[i].position,
                    nodes[j].position
                ]);
                const line = new THREE.Line(geometry, lineMaterial);
                scene.add(line);
                connections.push(line);
            }
        }
    }

    // Camera Movement
    camera.position.x += (mouseX - camera.position.x) * 0.05;
    camera.position.y += (-mouseY - camera.position.y) * 0.05;
    camera.lookAt(scene.position);

    renderer.render(scene, camera);
};

// Mouse Interaction
let mouseX = 0;
let mouseY = 0;

document.addEventListener('mousemove', (event) => {
    mouseX = (event.clientX - window.innerWidth / 2) * 0.001;
    mouseY = (event.clientY - window.innerHeight / 2) * 0.001;
});

// Resize Handler
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

// Initial Camera Position
camera.position.z = 10;
animate();


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
const patternContainer = document.getElementById('patternContainer');
const addSectionBtn = document.getElementById('addSectionBtn');
const collegeNameInput = document.getElementById('collegeName');

// ==========================================
// PATTERN MANAGEMENT
// ==========================================
function createPatternRow(data = {}) {
    const div = document.createElement('div');
    div.className = 'pattern-row';
    div.innerHTML = `
        <input type="text" placeholder="Section Name (e.g. Section A)" value="${data.name || ''}" class="p-name">
        <input type="text" placeholder="Description (e.g. 10 MCQs)" value="${data.desc || ''}" class="p-desc">
        <input type="number" placeholder="Marks/Q" value="${data.marks || ''}" class="p-marks">
        <input type="number" placeholder="Total Qs" value="${data.total || ''}" class="p-total">
        <input type="number" placeholder="Attempt" value="${data.attempt || ''}" class="p-attempt">
        <button class="remove-btn" onclick="this.parentElement.remove()">×</button>
    `;
    patternContainer.appendChild(div);
}

addSectionBtn.addEventListener('click', () => createPatternRow());

function getPatternFromUI() {
    const rows = patternContainer.querySelectorAll('.pattern-row');
    if (rows.length === 0) return null;

    const pattern = {};
    rows.forEach(row => {
        const name = row.querySelector('.p-name').value.trim();
        if (name) {
            pattern[name] = {
                description: row.querySelector('.p-desc').value.trim(),
                marks_per_question: parseInt(row.querySelector('.p-marks').value) || 1,
                total_questions: parseInt(row.querySelector('.p-total').value) || 1,
                questions_to_attempt: parseInt(row.querySelector('.p-attempt').value) || 1
            };
        }
    });
    return Object.keys(pattern).length > 0 ? pattern : null;
}

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

    // Boost Node Activity (Visualizing Processing)
    nodes.forEach(n => {
        n.material.color.setHex(0xff00ff); // Turn Magenta
        n.velocity.multiplyScalar(3);
    });

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

            // Populate Form
            patternContainer.innerHTML = '';
            for (const [section, details] of Object.entries(data.paper_pattern)) {
                createPatternRow({
                    name: section,
                    desc: details.description,
                    marks: details.marks_per_question,
                    total: details.total_questions,
                    attempt: details.questions_to_attempt
                });
            }
        } else {
            document.getElementById('priorityCount').textContent = Object.keys(data.priority_scores).length + " Priorities";
            // Clear or add default? Let's clear
            patternContainer.innerHTML = '';
        }

        resultsSection.classList.remove('hidden');
    } catch (err) {
        alert("Analysis Failed: " + err.message);
    } finally {
        loader.classList.add('hidden');
        // Reset Nodes
        nodes.forEach(n => {
            n.material.color.setHex(0x00f3ff); // Back to Cyan
            n.velocity.multiplyScalar(0.33);
        });
    }
});

// 2. Generate Handler
generateBtn.addEventListener('click', async () => {
    if (!analysisData) return;

    loader.classList.remove('hidden');
    loadingText.textContent = "Generating Question Paper...";

    // Get Pattern from UI (overrides analysis data)
    const uiPattern = getPatternFromUI();
    const finalPattern = uiPattern || analysisData.paper_pattern;

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
