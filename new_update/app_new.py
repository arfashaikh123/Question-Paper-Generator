import streamlit as st
import numpy as np
from groq import Groq
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.vectorstores import FAISS
from sklearn.metrics.pairwise import cosine_similarity
import re
from collections import defaultdict

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(page_title="Explainable AI QP Generator", layout="wide")
st.title("📊 Explainable Algorithmic Question Paper Generator")

# ============================================================
# SIDEBAR INPUTS
# ============================================================

st.sidebar.header("🔐 Groq API Key")
groq_key = st.sidebar.text_input("Enter Groq API Key", type="password")

st.sidebar.header("📄 Upload Files")

syllabus_pdf = st.sidebar.file_uploader("Upload Syllabus PDF", type=["pdf"])
pyq_pdfs = st.sidebar.file_uploader(
    "Upload Previous Year Papers",
    type=["pdf"],
    accept_multiple_files=True
)

st.sidebar.header("⚙️ Question Configuration")
total_questions = st.sidebar.slider("Total Questions", 5, 30, 10)
generate_button = st.sidebar.button("🚀 Generate Question Paper")

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def extract_text_from_pdf(pdf_file):
    temp_path = f"/tmp/{pdf_file.name}"
    with open(temp_path, "wb") as f:
        f.write(pdf_file.read())
    loader = PyPDFLoader(temp_path)
    pages = loader.load()
    return "\n".join([p.page_content for p in pages])

def extract_topics_from_syllabus(text):

    topics = {}
    lines = text.split("\n")

    for i in range(len(lines)):
        line = lines[i].strip()

        # Detect module number at beginning
        if re.match(r"^\d+\s", line):

            parts = re.split(r"\s{2,}", line)

            if len(parts) >= 2:
                topic_part = parts[1]

                # Try to extract hours from next lines
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    hrs_match = re.search(r"\b(\d+)\b", next_line)

                    if hrs_match:
                        topics[topic_part.strip()] = int(hrs_match.group(1))

    return topics


def classify_question_topic(client, question, topics):
    topic_list = ", ".join(topics.keys())

    prompt = f"""
Classify the following question into one of these topics:
{topic_list}

Question:
{question}

Respond ONLY with topic name.
"""

    response = client.chat.completions.create(
        model="llama-3.3-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=50,
        temperature=0
    )

    return response.choices[0].message.content.strip()


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
        allocation[topic] = int((score / total_priority) * total_q)

    return allocation


# ============================================================
# MAIN GENERATION PIPELINE
# ============================================================

if generate_button:

    if not groq_key:
        st.error("Enter Groq API Key")
        st.stop()

    if not syllabus_pdf or not pyq_pdfs:
        st.error("Upload syllabus and previous year papers")
        st.stop()

    client = Groq(api_key=groq_key)

    # ========================================================
    # PHASE 1: Extract Syllabus Topics
    # ========================================================

    with st.spinner("📘 Extracting syllabus topics..."):
        syllabus_text = extract_text_from_pdf(syllabus_pdf)
        syllabus_topics = extract_topics_from_syllabus(syllabus_text)

    if not syllabus_topics:
        st.error("Could not extract topics automatically. Adjust syllabus format.")
        st.stop()

    st.subheader("📚 Extracted Syllabus Topics")
    st.json(syllabus_topics)

    # ========================================================
    # PHASE 2: Analyse PYQs
    # ========================================================

    with st.spinner("📄 Analysing Previous Year Papers..."):
        frequency = defaultdict(int)

        for pdf in pyq_pdfs:
            pyq_text = extract_text_from_pdf(pdf)
            questions = pyq_text.split("?")

            for q in questions:
                if len(q.strip()) > 20:
                    topic = classify_question_topic(client, q, syllabus_topics)
                    if topic in syllabus_topics:
                        frequency[topic] += 1

    st.subheader("📊 PYQ Frequency Analysis")
    st.json(frequency)

    # ========================================================
    # PHASE 3: Compute Priority Scores
    # ========================================================

    priority_scores = compute_priority_scores(syllabus_topics, frequency)

    st.subheader("🔥 Computed Priority Scores")
    st.json(priority_scores)

    # ========================================================
    # PHASE 4: Allocate Questions
    # ========================================================

    allocation = allocate_questions(priority_scores, total_questions)

    st.subheader("🧮 Question Allocation Per Topic")
    st.json(allocation)

    # ========================================================
    # PHASE 5: Controlled Generation
    # ========================================================

    final_questions = []

    for topic, count in allocation.items():
        if count > 0:
            prompt = f"""
Generate {count} new exam questions for topic: {topic}

Avoid repeating patterns seen in previous exams.
Ensure conceptual depth and new structure.
"""

            response = client.chat.completions.create(
                model="llama-3.3-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=800
            )

            final_questions.append(response.choices[0].message.content)

    st.subheader("📝 Generated Question Paper")
    st.markdown("\n\n".join(final_questions))
