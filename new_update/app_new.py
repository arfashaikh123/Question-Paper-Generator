import streamlit as st
import os
import re
import numpy as np
from collections import Counter
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.vectorstores import FAISS
from huggingface_hub import InferenceClient

# --- Model Setup ---
HF_TOKEN = os.environ.get("HF_TOKEN", "")
client = InferenceClient(token=HF_TOKEN)

st.set_page_config(page_title="AI Question Paper Generator", layout="wide")

st.title("📄 AI Question Paper Generator Pro (Priority-Aware)")

# Sidebar
st.sidebar.header("⚙️ Configuration")

syllabus_file = st.sidebar.file_uploader("Upload Syllabus PDF", type=["pdf"])
pyq_files = st.sidebar.file_uploader("Upload PYQ PDFs", type=["pdf"], accept_multiple_files=True)

num_sets = st.sidebar.slider("Number of Sets", 1, 3, 1)

mcq_count = st.sidebar.slider("MCQs", 0, 20, 5)
short_count = st.sidebar.slider("Short Questions", 0, 15, 3)
long_count = st.sidebar.slider("Long Questions", 0, 10, 2)

generate = st.sidebar.button("✨ Generate Question Paper")

# ------------------------------
# Helper Functions
# ------------------------------

def load_pdf_text(pdf_file):
    with open(f"/tmp/{pdf_file.name}", "wb") as f:
        f.write(pdf_file.read())
    loader = PyPDFLoader(f"/tmp/{pdf_file.name}")
    pages = loader.load()
    return " ".join([p.page_content for p in pages])


def extract_topics(syllabus_text):
    # Simple heuristic: treat bullet lines / numbered lines as topics
    lines = syllabus_text.split("\n")
    topics = []
    for line in lines:
        line = line.strip()
        if len(line) > 5 and (
            line.startswith("-") or 
            re.match(r"^\d+[\.\)]", line)
        ):
            topics.append(re.sub(r"^\d+[\.\)]\s*", "", line))
    return list(set(topics))


def calculate_frequency(topics, pyq_text):
    freq = {}
    for topic in topics:
        freq[topic] = pyq_text.lower().count(topic.lower())
    return freq


def normalize(values_dict):
    values = np.array(list(values_dict.values()))
    max_val = max(values) if max(values) != 0 else 1
    normalized = {k: v / max_val for k, v in values_dict.items()}
    return normalized


def compute_priority(topics, syllabus_text, pyq_text):
    # Approximate syllabus weight using topic length frequency
    syllabus_counts = {t: syllabus_text.lower().count(t.lower()) for t in topics}
    freq_counts = calculate_frequency(topics, pyq_text)

    S_norm = normalize(syllabus_counts)
    F_norm = normalize(freq_counts)

    priority = {}
    for t in topics:
        priority[t] = 0.6 * S_norm[t] + 0.4 * F_norm[t]

    # Sort by priority
    sorted_topics = sorted(priority.items(), key=lambda x: x[1], reverse=True)

    return sorted_topics[:8]  # Top 8 important topics


# ------------------------------
# Main Generation Logic
# ------------------------------

def generate_question_paper():
    if not syllabus_file:
        st.error("Upload syllabus PDF.")
        return

    if not HF_TOKEN:
        st.error("HF_TOKEN not set.")
        return

    with st.spinner("📘 Reading syllabus..."):
        syllabus_text = load_pdf_text(syllabus_file)

    pyq_text = ""
    if pyq_files:
        with st.spinner("📚 Reading PYQs..."):
            for f in pyq_files:
                pyq_text += load_pdf_text(f)

    topics = extract_topics(syllabus_text)

    if len(topics) == 0:
        st.warning("Could not extract topics automatically.")
        return

    important_topics = compute_priority(topics, syllabus_text, pyq_text)

    st.subheader("🔥 Top Important Topics (AI Selected)")
    for topic, score in important_topics:
        st.write(f"{topic} — Score: {round(score,2)}")

    topic_list = "\n".join([t[0] for t in important_topics])

    outputs = []

    for set_num in range(1, num_sets + 1):
        prompt = f"""
You are an expert examiner.

IMPORTANT TOPICS (High Priority):
{topic_list}

Generate Question Paper - SET {set_num}

MCQs: {mcq_count}
Short: {short_count}
Long: {long_count}

Ensure:
- More questions from higher priority topics
- Balanced coverage
- Formal exam format
"""

        response = client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model="meta-llama/Llama-3.2-3B-Instruct",
            max_tokens=2000,
            temperature=0.7,
        )

        outputs.append(response.choices[0].message.content)

    return "\n\n" + "="*80 + "\n\n".join(outputs)


# ------------------------------
# Output
# ------------------------------

if generate:
    result = generate_question_paper()
    if result:
        st.success("✅ Generation Complete!")
        st.markdown(result)
