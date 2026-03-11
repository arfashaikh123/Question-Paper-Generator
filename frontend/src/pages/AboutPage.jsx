import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function AboutPage({ onNavigate }) {
  return (
    <div className="page-container">
      <Navbar activePage="about" onNavigate={onNavigate} />

      <div className="about-content">
        <div className="about-hero">
          <div className="home-badge">📖 Technical Overview</div>
          <h2 className="home-title" style={{ fontSize: '2.5rem' }}>Algorithms &amp; Architecture</h2>
          <p className="home-subtitle">
            A deep dive into how NeuroGen Studio analyses question papers,
            generates new questions, and leverages the RAG model approach.
          </p>
        </div>

        {/* SECTION 1: Paper Analysis */}
        <section className="about-section">
          <div className="about-section-header">
            <span className="about-section-icon">🔍</span>
            <h3>Paper Analysis Algorithms</h3>
          </div>
          <p className="about-section-intro">
            NeuroGen employs a multi-stage analysis pipeline to understand your syllabus and
            previous year question (PYQ) papers before generating anything.
          </p>

          <div className="algo-cards">
            <div className="algo-card">
              <h4>📄 PDF Text Extraction</h4>
              <p>
                Uploaded PDFs are parsed using <strong>PyPDF2</strong> and <strong>PyMuPDF (fitz)</strong>.
                Both libraries are used in tandem: PyMuPDF handles scanned/image PDFs with better
                layout fidelity, while PyPDF2 handles digital PDFs. Raw text is cleaned, normalised,
                and passed downstream.
              </p>
              <div className="algo-tags">
                <span className="algo-tag">PyPDF2</span>
                <span className="algo-tag">PyMuPDF</span>
                <span className="algo-tag">Text Normalisation</span>
              </div>
            </div>

            <div className="algo-card">
              <h4>🏷️ Topic Extraction &amp; Classification</h4>
              <p>
                Extracted text is sent to a <strong>Groq LLM (llama-3.1-8b-instant)</strong> with a
                structured prompt that instructs the model to identify and classify syllabus topics
                by module. The LLM returns a structured JSON mapping of module names to their topics,
                which is then stored for downstream use.
              </p>
              <div className="algo-tags">
                <span className="algo-tag">Groq LLM</span>
                <span className="algo-tag">Structured Prompting</span>
                <span className="algo-tag">JSON Extraction</span>
              </div>
            </div>

            <div className="algo-card">
              <h4>📊 Priority Scoring Algorithm</h4>
              <p>
                Each topic is scored by analysing its <strong>frequency of appearance</strong> across
                all uploaded PYQ papers. The algorithm counts how many times related terms appear
                within each PYQ, normalises these counts, and produces a <em>priority score</em>
                between 0 and 1. High-priority topics receive a larger share of questions in the
                generated paper.
              </p>
              <div className="algo-steps">
                <div className="algo-step"><span className="step-dot"></span>Term frequency counting per PYQ</div>
                <div className="algo-step"><span className="step-dot"></span>Cross-paper aggregation</div>
                <div className="algo-step"><span className="step-dot"></span>Min-max normalisation → priority score</div>
                <div className="algo-step"><span className="step-dot"></span>Score-based topic allocation</div>
              </div>
            </div>

            <div className="algo-card">
              <h4>🗂️ Pattern Recognition</h4>
              <p>
                If a reference question paper PDF is provided, the LLM parses its structure and
                infers the exam pattern: section names, marks per question, number of questions,
                and questions to attempt. The header (institution name, exam year, subject, etc.)
                is also extracted and pre-filled in the Studio for convenience.
              </p>
              <div className="algo-tags">
                <span className="algo-tag">Structural Parsing</span>
                <span className="algo-tag">LLM Inference</span>
                <span className="algo-tag">Header Extraction</span>
              </div>
            </div>
          </div>
        </section>

        {/* SECTION 2: RAG Model */}
        <section className="about-section">
          <div className="about-section-header">
            <span className="about-section-icon">🧠</span>
            <h3>RAG Model Approach</h3>
          </div>
          <p className="about-section-intro">
            NeuroGen Studio is built on <strong>Retrieval-Augmented Generation (RAG)</strong> — a
            technique that grounds LLM outputs in your actual documents rather than relying solely
            on the model's parametric knowledge.
          </p>

          <div className="rag-pipeline">
            <div className="rag-stage">
              <div className="rag-stage-icon">📥</div>
              <div className="rag-stage-label">Ingest</div>
              <div className="rag-stage-desc">PDFs are parsed into clean text chunks and stored in memory as a retrieval corpus.</div>
            </div>
            <div className="rag-arrow">→</div>
            <div className="rag-stage">
              <div className="rag-stage-icon">🔎</div>
              <div className="rag-stage-label">Retrieve</div>
              <div className="rag-stage-desc">When generating questions, relevant topic passages are retrieved from the PYQ corpus using keyword and semantic matching.</div>
            </div>
            <div className="rag-arrow">→</div>
            <div className="rag-stage">
              <div className="rag-stage-icon">🔗</div>
              <div className="rag-stage-label">Augment</div>
              <div className="rag-stage-desc">Retrieved passages are injected into the LLM prompt as grounding context, anchoring generation to real exam content.</div>
            </div>
            <div className="rag-arrow">→</div>
            <div className="rag-stage">
              <div className="rag-stage-icon">✨</div>
              <div className="rag-stage-label">Generate</div>
              <div className="rag-stage-desc">The LLM produces novel, contextually grounded questions that reflect true exam style and topic distribution.</div>
            </div>
          </div>

          <div className="algo-cards" style={{ marginTop: '2rem' }}>
            <div className="algo-card">
              <h4>Why RAG over pure LLM generation?</h4>
              <p>
                A standalone LLM generates questions based on training data alone, which may not
                reflect the specific style, difficulty, or topic distribution of your institution's
                exams. RAG anchors generation in <em>your</em> documents, producing questions that
                are more relevant, diverse, and appropriately levelled.
              </p>
            </div>
            <div className="algo-card">
              <h4>LangChain Integration</h4>
              <p>
                The retrieval and prompt-chaining pipeline is orchestrated using
                <strong> LangChain</strong>. LangChain manages document loading, text splitting,
                prompt templates, and LLM chains, providing a modular pipeline that is easy to
                extend and maintain.
              </p>
              <div className="algo-tags">
                <span className="algo-tag">LangChain</span>
                <span className="algo-tag">Prompt Templates</span>
                <span className="algo-tag">LLM Chains</span>
              </div>
            </div>
            <div className="algo-card">
              <h4>Chat Agent (Conversational RAG)</h4>
              <p>
                The Studio's chat interface uses a <strong>conversational RAG agent</strong> that
                maintains a context window containing the current syllabus topics and exam pattern.
                Each user message is augmented with this context before being sent to the LLM,
                enabling coherent, multi-turn dialogue about the paper structure.
              </p>
              <div className="algo-tags">
                <span className="algo-tag">Conversational Context</span>
                <span className="algo-tag">Multi-turn Dialogue</span>
                <span className="algo-tag">Pattern Updates</span>
              </div>
            </div>
          </div>
        </section>

        {/* SECTION 3: Question Generation */}
        <section className="about-section">
          <div className="about-section-header">
            <span className="about-section-icon">📐</span>
            <h3>Question Generation Algorithms</h3>
          </div>
          <p className="about-section-intro">
            Once topics are analysed and the exam pattern is defined, NeuroGen orchestrates
            a multi-step generation pipeline to produce a complete, balanced question paper.
          </p>

          <div className="algo-cards">
            <div className="algo-card">
              <h4>📋 Topic-Based Allocation</h4>
              <p>
                Questions are allocated to topics proportionally based on their
                <strong> priority scores</strong> and the total number of questions required by
                the pattern. Topics with higher priority scores receive more questions,
                while every topic in the syllabus receives at least one question to ensure
                full coverage.
              </p>
              <div className="algo-steps">
                <div className="algo-step"><span className="step-dot"></span>Compute priority-weighted question counts</div>
                <div className="algo-step"><span className="step-dot"></span>Floor allocation + remainder distribution</div>
                <div className="algo-step"><span className="step-dot"></span>Guarantee minimum 1 question per topic</div>
              </div>
            </div>

            <div className="algo-card">
              <h4>⚖️ Marks Distribution</h4>
              <p>
                Each section's marks-per-question and question count are respected strictly.
                The generator verifies that the sum of attempted questions × marks equals the
                expected section total, raising an error if the pattern is inconsistent
                before proceeding.
              </p>
              <div className="algo-tags">
                <span className="algo-tag">Pattern Validation</span>
                <span className="algo-tag">Constraint Satisfaction</span>
              </div>
            </div>

            <div className="algo-card">
              <h4>🎓 Bloom's Taxonomy Integration</h4>
              <p>
                Questions are generated across multiple cognitive levels to ensure a
                pedagogically balanced paper. Short-answer questions target
                <em> Remember / Understand</em> levels, while long-answer questions target
                <em> Apply / Analyse / Evaluate / Create</em> levels, guided by the
                LLM prompt design.
              </p>
              <div className="algo-tags">
                <span className="algo-tag">Remember</span>
                <span className="algo-tag">Understand</span>
                <span className="algo-tag">Apply</span>
                <span className="algo-tag">Analyse</span>
                <span className="algo-tag">Evaluate</span>
                <span className="algo-tag">Create</span>
              </div>
            </div>

            <div className="algo-card">
              <h4>🌀 Diversity Optimisation</h4>
              <p>
                To avoid repetitive questions, each generation prompt includes the previously
                generated questions as negative examples. The LLM is instructed to produce
                questions that are semantically distinct, ensuring variety in phrasing,
                scope, and assessed skill.
              </p>
              <div className="algo-tags">
                <span className="algo-tag">Negative Prompting</span>
                <span className="algo-tag">Semantic Diversity</span>
              </div>
            </div>
          </div>
        </section>

        {/* SECTION 4: Tech Stack */}
        <section className="about-section">
          <div className="about-section-header">
            <span className="about-section-icon">🛠️</span>
            <h3>Technology Stack</h3>
          </div>
          <div className="tech-grid">
            <div className="tech-item"><span className="tech-name">Groq API</span><span className="tech-desc">Ultra-fast LLM inference (llama-3.1-8b-instant)</span></div>
            <div className="tech-item"><span className="tech-name">LangChain</span><span className="tech-desc">RAG pipeline, prompt templates &amp; LLM chains</span></div>
            <div className="tech-item"><span className="tech-name">Flask</span><span className="tech-desc">Python REST API backend</span></div>
            <div className="tech-item"><span className="tech-name">PyMuPDF</span><span className="tech-desc">High-fidelity PDF text extraction</span></div>
            <div className="tech-item"><span className="tech-name">fpdf2</span><span className="tech-desc">Programmatic PDF generation</span></div>
            <div className="tech-item"><span className="tech-name">React + Vite</span><span className="tech-desc">Fast, modern frontend</span></div>
            <div className="tech-item"><span className="tech-name">GSAP</span><span className="tech-desc">Smooth UI animations</span></div>
            <div className="tech-item"><span className="tech-name">Netlify + Render</span><span className="tech-desc">Frontend &amp; backend hosting</span></div>
          </div>
        </section>
      </div>

      <Footer
        onNavigate={onNavigate}
        links={[
          { page: 'home', label: 'Home' },
          { page: 'upload', label: 'Get Started' },
        ]}
      />
    </div>
  );
}
