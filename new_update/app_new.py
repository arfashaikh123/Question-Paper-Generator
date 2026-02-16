import streamlit as st
import re
from collections import defaultdict
from groq import Groq
from langchain_community.document_loaders import PyPDFLoader
from fpdf import FPDF

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(page_title="Explainable AI QP Generator", layout="wide")

st.title("📊 Explainable Algorithmic Question Paper Generator")
st.markdown("Priority = 0.6 × Syllabus Weight + 0.4 × PYQ Frequency")

# =====================================================
# SIDEBAR INPUTS
# =====================================================

st.sidebar.header("🔐 Groq API Key")
groq_key = st.sidebar.text_input("Enter Groq API Key", type="password")

st.sidebar.header("📚 Paste Syllabus Text")

syllabus_text_input = st.sidebar.text_area(
    "Paste syllabus topics (hours must be mentioned)",
    height=250,
    placeholder="""
Introduction to Statistics
6
Data Collection & Sampling Methods
6
Introduction to Regression
8
Introduction to Multiple Linear Regression
8
Statistical inference
6
Tests of hypotheses
5
"""
)

st.sidebar.header("📄 Upload Previous Year Papers")
pyq_pdfs = st.sidebar.file_uploader(
    "Upload PYQs",
    type=["pdf"],
    accept_multiple_files=True
)

st.sidebar.header("⚙️ Configuration")
total_questions = st.sidebar.slider("Total Questions", 5, 30, 10)
generate_button = st.sidebar.button("🚀 Generate Paper")

# =====================================================
# STRICT SYLLABUS PARSER
# =====================================================

def parse_and_clean_syllabus(raw_text):

    topics = {}
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]

    ignore_words = ["module", "content", "hrs", "hr", "hours"]

    for i in range(len(lines) - 1):

        line = lines[i]
        next_line = lines[i + 1]

        # Skip structural words
        if any(word in line.lower() for word in ignore_words):
            continue

        # Skip if line is numeric (serial number)
        if line.isdigit():
            continue

        # Next line must be numeric
        if next_line.isdigit():

            hours = int(next_line)

            # Accept realistic teaching hours only
            if 4 <= hours <= 12:

                if len(line) > 5 and any(c.isalpha() for c in line):
                    topics[line] = hours

    return topics

# =====================================================
# PDF TEXT EXTRACTION
# =====================================================

def extract_text_from_pdf(pdf_file):
    temp_path = f"/tmp/{pdf_file.name}"
    with open(temp_path, "wb") as f:
        f.write(pdf_file.read())
    loader = PyPDFLoader(temp_path)
    pages = loader.load()
    return "\n".join([p.page_content for p in pages])

# =====================================================
# PRIORITY CALCULATION
# =====================================================

def compute_priority_scores(syllabus_topics, frequency_dict):

    max_hours = max(syllabus_topics.values())
    max_freq = max(frequency_dict.values()) if frequency_dict else 1

    priority_scores = {}

    for topic in syllabus_topics:
        H_norm = syllabus_topics[topic] / max_hours
        F_norm = frequency_dict.get(topic, 0) / max_freq
        priority = 0.6 * H_norm + 0.4 * F_norm
        priority_scores[topic] = round(priority, 3)

    return priority_scores

def allocate_questions(priority_scores, total_q):

    total_priority = sum(priority_scores.values())
    allocation = {}

    for topic, score in priority_scores.items():
        allocation[topic] = max(1, int((score / total_priority) * total_q))

    return allocation

# =====================================================
# PDF GENERATOR
# =====================================================

def generate_pdf(text):

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    for line in text.split("\n"):
        pdf.multi_cell(0, 8, line)

    return pdf.output(dest="S").encode("latin-1")

# =====================================================
# MAIN PIPELINE
# =====================================================

if generate_button:

    if not groq_key:
        st.error("Enter Groq API Key")
        st.stop()

    if not syllabus_text_input:
        st.error("Paste syllabus text")
        st.stop()

    if not pyq_pdfs:
        st.error("Upload previous year papers")
        st.stop()

    client = Groq(api_key=groq_key)

    # -----------------------------
    # Phase 1: Parse Syllabus
    # -----------------------------
    syllabus_topics = parse_and_clean_syllabus(syllabus_text_input)

    if not syllabus_topics:
        st.error("Could not detect topics automatically. Check syllabus format.")
        st.stop()

    st.subheader("📚 Extracted Syllabus Topics")
    st.json(syllabus_topics)

    # -----------------------------
    # Phase 2: Analyse PYQs
    # -----------------------------
    frequency = defaultdict(int)

    with st.spinner("📄 Analysing Previous Year Papers..."):
        for pdf in pyq_pdfs:
            pyq_text = extract_text_from_pdf(pdf)
            questions = pyq_text.split("?")

            for q in questions:
                if len(q.strip()) > 30:

                    topic_list = ", ".join(syllabus_topics.keys())

                    prompt = f"""
Classify the following question into one of these topics:
{topic_list}

Question:
{q}

Respond ONLY with topic name.
"""

                    response = client.chat.completions.create(
                        model="llama-3.3-8b-instant",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0,
                        max_tokens=50
                    )

                    topic = response.choices[0].message.content.strip()

                    if topic in syllabus_topics:
                        frequency[topic] += 1

    st.subheader("📊 PYQ Frequency")
    st.json(frequency)

    # -----------------------------
    # Phase 3: Compute Priority
    # -----------------------------
    priority_scores = compute_priority_scores(syllabus_topics, frequency)

    st.subheader("🔥 Priority Scores")
    st.json(priority_scores)

    # -----------------------------
    # Phase 4: Allocate Questions
    # -----------------------------
    allocation = allocate_questions(priority_scores, total_questions)

    st.subheader("🧮 Question Allocation")
    st.json(allocation)

    # -----------------------------
    # Phase 5: Controlled Generation
    # -----------------------------
    st.subheader("📝 Generated Question Paper")

    final_questions = []

    for topic, count in allocation.items():
        if count > 0:

            prompt = f"""
Generate {count} new exam questions for topic: {topic}

Rules:
- Avoid repeating past patterns
- Create new structure
- Maintain academic difficulty
- Professional formatting
"""

            response = client.chat.completions.create(
                model="llama-3.3-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=800
            )

            final_questions.append(response.choices[0].message.content)

    final_output = "\n\n".join(final_questions)

    st.markdown(final_output)

    # -----------------------------
    # Download Buttons
    # -----------------------------
    st.download_button(
        label="📥 Download as TXT",
        data=final_output,
        file_name="Generated_Question_Paper.txt",
        mime="text/plain"
    )

    pdf_data = generate_pdf(final_output)

    st.download_button(
        label="📥 Download as PDF",
        data=pdf_data,
        file_name="Generated_Question_Paper.pdf",
        mime="application/pdf"
    )
