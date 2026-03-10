import streamlit as st
import re
import sys
import os
from collections import defaultdict
from langchain_community.document_loaders import PyPDFLoader
from fpdf import FPDF

# Add project root to path so we can import llm_providers
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from llm_providers import PROVIDERS, DEFAULT_PROVIDER, get_openai_client, get_default_model

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(page_title="Explainable AI QP Generator", layout="wide")

st.title("📊 Explainable Algorithmic Question Paper Generator")
st.markdown("Priority = 0.6 × Syllabus Weight + 0.4 × PYQ Frequency")

# =====================================================
# SIDEBAR INPUTS – LLM Configuration
# =====================================================

st.sidebar.header("🤖 LLM Configuration")

provider_options = {v["name"]: k for k, v in PROVIDERS.items()
                   if k != "local_transformers"}  # Exclude in-process model loading (not HTTP-based)
selected_provider_name = st.sidebar.selectbox(
    "LLM Provider",
    list(provider_options.keys()),
    help=(
        "Choose the language model backend. "
        "Groq is a fast cloud option; Ollama lets you run models locally; "
        "Hugging Face Hub allows using your fine-tuned models from HF Hub; "
        "the custom option works with any OpenAI-compatible server."
    ),
)
provider = provider_options[selected_provider_name]
provider_config = PROVIDERS[provider]

st.sidebar.caption(provider_config["description"])

# API Key
api_key = ""
if provider_config["requires_api_key"]:
    key_label = (
        "Hugging Face Token"
        if provider == "huggingface_hub"
        else f"{selected_provider_name} API Key"
    )
    api_key = st.sidebar.text_input(key_label, type="password")
    env_var = (
        "GROQ_API_KEY" if provider == "groq"
        else "HF_TOKEN" if provider == "huggingface_hub"
        else "LLM_API_KEY"
    )
    if not api_key and env_var in os.environ:
        api_key = os.environ[env_var]
else:
    api_key = st.sidebar.text_input(
        "API Key (optional)", type="password",
        help="Leave blank if the server does not require authentication."
    )

# Base URL (for providers that expose a configurable endpoint)
if provider in ("ollama", "openai_compatible"):
    base_url = st.sidebar.text_input(
        "Base URL",
        value=provider_config["base_url"],
    )
elif provider == "huggingface_hub":
    base_url = provider_config["base_url"]
else:
    base_url = provider_config["base_url"]

# Model
if provider == "groq":
    model = st.sidebar.selectbox("Model", provider_config["models"])
elif provider == "huggingface_hub":
    model = st.sidebar.text_input(
        "HF Model ID",
        help="e.g. 'username/my-finetuned-llama'",
    )
else:
    model = st.sidebar.text_input(
        "Model Name",
        value=provider_config["default_model"],
    )

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

    for i in range(len(lines) - 2):

        # Pattern:
        # Module number
        # Topic
        # Hours

        if lines[i].isdigit():  # Module number

            topic = lines[i + 1]
            hrs_line = lines[i + 2]

            if hrs_line.isdigit():

                hours = int(hrs_line)

                # Accept realistic hour range
                if 4 <= hours <= 12 and len(topic) > 5:
                    topics[topic] = hours

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

    if provider_config["requires_api_key"] and not api_key:
        st.error(f"Enter {selected_provider_name} API Key / Token")
        st.stop()

    if not model:
        st.error("Enter a model name or ID to proceed.")
        st.stop()

    if not syllabus_text_input:
        st.error("Paste syllabus text")
        st.stop()

    if not pyq_pdfs:
        st.error("Upload previous year papers")
        st.stop()

    # Build a provider-agnostic OpenAI-compatible client
    client = get_openai_client(provider=provider, api_key=api_key, base_url=base_url)
    selected_model = get_default_model(provider=provider, model=model)

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
                        model=selected_model,
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
                model=selected_model,
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
