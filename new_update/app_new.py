import streamlit as st
import re
import numpy as np
from groq import Groq
from langchain_community.document_loaders import PyPDFLoader

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(page_title="AI Question Paper Generator", layout="wide")

st.title("📄 AI Question Paper Generator (Hybrid Intelligent)")
st.markdown("Priority-Aware • PYQ Analysis • Powered by Groq Llama3")

# =====================================================
# SIDEBAR – GROQ API INPUT
# =====================================================

st.sidebar.header("🔐 Groq API Configuration")

api_key = st.sidebar.text_input(
    "Enter Groq API Key",
    type="password",
    help="Get your API key from https://console.groq.com"
)

if not api_key:
    st.warning("⚠️ Please enter your Groq API key in the sidebar to continue.")
    st.stop()

client = Groq(api_key=api_key)

# =====================================================
# SIDEBAR – FILE UPLOAD
# =====================================================

st.sidebar.header("📘 Upload Files")

syllabus_file = st.sidebar.file_uploader("Upload Syllabus PDF", type=["pdf"])
pyq_files = st.sidebar.file_uploader(
    "Upload Previous Year Papers (Optional)",
    type=["pdf"],
    accept_multiple_files=True
)

# =====================================================
# SIDEBAR – EXAM STRUCTURE
# =====================================================

st.sidebar.header("⚙️ Exam Structure")

num_sets = st.sidebar.slider("Number of Sets", 1, 3, 1)
mcq_count = st.sidebar.slider("MCQs", 0, 20, 5)
short_count = st.sidebar.slider("Short Questions", 0, 15, 3)
long_count = st.sidebar.slider("Long Questions", 0, 10, 2)

generate_btn = st.sidebar.button("✨ Generate Question Paper")

# =====================================================
# HELPER FUNCTIONS
# =====================================================

def load_pdf_text(pdf_file):
    temp_path = f"/tmp/{pdf_file.name}"
    with open(temp_path, "wb") as f:
        f.write(pdf_file.read())

    loader = PyPDFLoader(temp_path)
    pages = loader.load()
    return " ".join([p.page_content for p in pages])


def extract_topics(syllabus_text):
    lines = syllabus_text.split("\n")
    topics = []

    for line in lines:
        line = line.strip()
        if len(line) > 5 and (
            line.startswith("-") or
            re.match(r"^\d+[\.\)]", line)
        ):
            topic = re.sub(r"^\d+[\.\)]\s*", "", line)
            topics.append(topic)

    return list(set(topics))


def normalize(dictionary):
    values = np.array(list(dictionary.values()))
    max_val = max(values) if max(values) != 0 else 1
    return {k: v / max_val for k, v in dictionary.items()}


def compute_priority(topics, syllabus_text, pyq_text):
    syllabus_counts = {t: syllabus_text.lower().count(t.lower()) for t in topics}
    pyq_counts = {t: pyq_text.lower().count(t.lower()) for t in topics}

    S_norm = normalize(syllabus_counts)
    F_norm = normalize(pyq_counts)

    priority_scores = {}

    for t in topics:
        priority_scores[t] = 0.6 * S_norm[t] + 0.4 * F_norm[t]

    sorted_topics = sorted(priority_scores.items(), key=lambda x: x[1], reverse=True)

    return sorted_topics[:8]  # top 8 topics


def generate_with_groq(prompt):
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": "You are an expert university examiner."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=2000,
    )
    return response.choices[0].message.content


# =====================================================
# MAIN GENERATION FUNCTION
# =====================================================

def generate_question_paper():

    if not syllabus_file:
        st.error("❌ Please upload syllabus PDF.")
        return None

    with st.spinner("📘 Reading syllabus..."):
        syllabus_text = load_pdf_text(syllabus_file)

    pyq_text = ""
    if pyq_files:
        with st.spinner("📚 Reading Previous Year Papers..."):
            for f in pyq_files:
                pyq_text += load_pdf_text(f)

    topics = extract_topics(syllabus_text)

    if len(topics) == 0:
        st.error("❌ Could not extract topics automatically.")
        return None

    important_topics = compute_priority(topics, syllabus_text, pyq_text)

    st.subheader("🔥 AI-Selected Important Topics")

    for topic, score in important_topics:
        st.write(f"**{topic}** — Score: {round(score, 2)}")

    topic_list = "\n".join([f"- {t[0]}" for t in important_topics])

    outputs = []

    for set_num in range(1, num_sets + 1):

        st.info(f"Generating Set {set_num}/{num_sets}...")

        prompt = f"""
Create a formal university question paper.

IMPORTANT HIGH-PRIORITY TOPICS:
{topic_list}

Exam Structure:
- MCQs: {mcq_count}
- Short Questions: {short_count}
- Long Questions: {long_count}

Rules:
- Allocate more questions to higher priority topics.
- Maintain balanced coverage.
- Professional formatting.
- Include answer key for MCQs.
- Start with "QUESTION PAPER - SET {set_num}"
- Do not add explanations outside exam format.
"""

        paper = generate_with_groq(prompt)
        outputs.append(paper)

    return "\n\n" + "="*100 + "\n\n".join(outputs)


# =====================================================
# OUTPUT SECTION
# =====================================================

if generate_btn:
    with st.spinner("🤖 Generating Question Paper..."):
        result = generate_question_paper()

    if result:
        st.success("✅ Question Paper Generated Successfully!")
        st.markdown(result)
