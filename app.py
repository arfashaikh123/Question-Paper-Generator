
import streamlit as st
import tempfile
import os
import json
from utils import (
    extract_text_from_pdf,
    extract_pattern_from_text,
    parse_syllabus_modules,
    calculate_topic_weights,
    generate_question_paper
)
from llm_providers import PROVIDERS, DEFAULT_PROVIDER

# Page Config
st.set_page_config(page_title="Smart Question Paper Generator", layout="wide")

st.title("📄 Smart Question Paper Generator")
st.markdown("""
Generate a university-standard question paper by analyzing:
1. **Syllabus** (for topic hours)
2. **Previous Year Questions** (for frequency)
3. **Sample Question Paper** (for exam pattern)
""")

# ---------------------------------------------------------------------------
# Sidebar: LLM Provider Configuration
# ---------------------------------------------------------------------------
st.sidebar.header("LLM Configuration")

provider_options = {v["name"]: k for k, v in PROVIDERS.items()}
selected_provider_name = st.sidebar.selectbox(
    "LLM Provider",
    list(provider_options.keys()),
    help="Choose where to run the language model. Groq is a fast cloud option; "
         "Ollama lets you run models locally; the custom option works with any "
         "OpenAI-compatible fine-tuned model server.",
)
provider = provider_options[selected_provider_name]
provider_config = PROVIDERS[provider]

st.sidebar.caption(provider_config["description"])

# API Key (only shown for providers that need one)
api_key = ""
if provider_config["requires_api_key"]:
    key_label = (
        "Hugging Face Token"
        if provider == "huggingface_hub"
        else f"{selected_provider_name} API Key"
    )
    api_key = st.sidebar.text_input(key_label, type="password")
    env_var = "GROQ_API_KEY" if provider == "groq" else "HF_TOKEN" if provider == "huggingface_hub" else "LLM_API_KEY"
    if not api_key and env_var in os.environ:
        api_key = os.environ[env_var]
    if not api_key:
        st.sidebar.warning(f"Please enter your {key_label} to proceed.")
else:
    # Providers like Ollama and custom servers may optionally require a key
    api_key = st.sidebar.text_input(
        "API Key (optional)", type="password",
        help="Leave blank if the server does not require authentication."
    )

# Model / path input
if provider == "local_transformers":
    # Local transformers needs a model path or HF model ID, not a base URL
    base_url = None
    model = st.sidebar.text_input(
        "Model Path or HF Model ID",
        value="",
        help=(
            "Path to your fine-tuned model folder on disk "
            "(e.g. /models/my-llm) **or** a Hugging Face model ID "
            "(e.g. username/my-finetuned-llama). "
            "The model must be compatible with the 🤗 text-generation pipeline."
        ),
    )
    if not model:
        st.sidebar.warning("Enter a local model path or HF model ID to proceed.")

elif provider in ("ollama", "openai_compatible"):
    base_url = st.sidebar.text_input(
        "Base URL",
        value=provider_config["base_url"],
        help="The base URL of the model server (e.g., http://localhost:11434/v1).",
    )
    model = st.sidebar.text_input(
        "Model Name",
        value=provider_config["default_model"],
        help="Enter the exact model name supported by your server "
             "(e.g., llama3.2, mistral, or your fine-tuned model name).",
    )

elif provider == "huggingface_hub":
    base_url = provider_config["base_url"]  # Fixed HF endpoint
    model = st.sidebar.text_input(
        "HF Model ID",
        value="",
        help=(
            "The full Hugging Face model ID, e.g. 'username/my-finetuned-llama'. "
            "Must be a model that supports text generation and is accessible "
            "with your HF token."
        ),
    )
    if not model:
        st.sidebar.warning("Enter your Hugging Face model ID to proceed.")

else:  # groq
    base_url = provider_config["base_url"]
    model = st.sidebar.selectbox(
        "Model",
        provider_config["models"],
        index=0,
        help="Select the model to use for generation.",
    )

# ---------------------------------------------------------------------------
# Sidebar: Custom Model Setup Guide
# ---------------------------------------------------------------------------
with st.sidebar.expander("📋 How to use your custom model", expanded=False):
    st.markdown("""
**Option 1 – Hugging Face Hub** *(easiest for cloud-hosted fine-tunes)*

1. Fine-tune your model and push it to HF Hub with `model.push_to_hub("username/my-model")`.
2. Get an access token from [hf.co/settings/tokens](https://huggingface.co/settings/tokens).
3. Select **Hugging Face Hub** above and enter your token + model ID.

---

**Option 2 – Local Transformers** *(no server, load weights directly)*

1. Save your fine-tuned model to disk: `model.save_pretrained("/path/to/model")`.
2. Install dependencies: `pip install langchain-huggingface transformers torch`.
3. Select **Local Custom Model (Transformers)** and enter the path.

---

**Option 3 – Ollama** *(easiest for local inference)*

1. Install [Ollama](https://ollama.com).
2. Import your GGUF model: `ollama create my-model -f Modelfile`.
3. Select **Ollama (Local)** and enter the model name.

---

**Option 4 – vLLM / LM Studio / llama.cpp** *(OpenAI-compatible server)*

1. Start your server, e.g. `vllm serve username/my-finetuned-llama`.
2. Select **Custom OpenAI-Compatible API**, enter the server URL and model name.
""")

# --- SECTION 1: DATA UPLOAD ---
st.header("1. Upload Documents")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Details from Syllabus")
    syllabus_file = st.file_uploader("Upload Syllabus (PDF)", type=["pdf"])

with col2:
    st.subheader("Frequency from PYQs")
    pyq_files = st.file_uploader("Upload Previous Papers (PDF)", type=["pdf"], accept_multiple_files=True)

with col3:
    st.subheader("Pattern from Sample")
    pattern_file = st.file_uploader("Upload Sample Paper (PDF)", type=["pdf"])

# Store extracted data in session state to persist between reruns
if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = {}

# --- SECTION 2: ANALYSIS ---
if st.button("🔍 Analyze Inputs"):
    if provider_config["requires_api_key"] and not api_key:
        st.error(f"API Key is required for {selected_provider_name}!")
    elif provider == "local_transformers" and not model:
        st.error("Please enter a model path or Hugging Face model ID.")
    elif provider == "huggingface_hub" and not model:
        st.error("Please enter your Hugging Face model ID.")
    elif not syllabus_file or not pyq_files or not pattern_file:
        st.error("Please upload all required documents.")
    else:
        with st.spinner("Analyzing documents..."):
            try:
                # 1. Parse Syllabus
                syllabus_text = extract_text_from_pdf(syllabus_file)
                
                # Debug: Show extracted text
                with st.expander("Debug: Extracted Syllabus Text"):
                    st.text(syllabus_text[:2000] + "..." if len(syllabus_text) > 2000 else syllabus_text)
                
                modules = parse_syllabus_modules(
                    syllabus_text, api_key,
                    provider=provider, model=model, base_url=base_url,
                )
                
                # 2. Parse PYQs
                pyq_text = ""
                for pyq in pyq_files:
                    pyq_text += extract_text_from_pdf(pyq) + "\n"
                    
                # 3. Parse Pattern
                pattern_text = extract_text_from_pdf(pattern_file)
                extracted_pattern = extract_pattern_from_text(
                    pattern_text, api_key,
                    provider=provider, model=model, base_url=base_url,
                )
                
                # 4. Calculate Weights
                final_weights = {} # init
                if modules:
                    # Helper function calc
                    # Need to implement the weight calculation inside utils or here
                    # Using the imported function
                    # But first we need the 'frequency' which happens inside calculate_topic_weights
                    # So we pass syllabus modules and PYQ text to it
                    
                    # We might want to separate frequency count for display, but for now just get weights
                    # Actually, we need to pass the modules dict to calculate_topic_weights
                    pass 
                
                # Store in session state
                st.session_state.extracted_data = {
                    "syllabus_text": syllabus_text,
                    "modules": modules,
                    "pyq_text": pyq_text,
                    "pattern_desc": extracted_pattern,
                    # We calc weights later or now? Let's do it now.
                    "weights": calculate_topic_weights(modules, pyq_text)
                }
                
                st.success("Analysis Complete!")
                
            except Exception as e:
                st.error(f"An error occurred during analysis: {e}")

# --- SECTION 3: VERIFICATION & GENERATION ---

if "extracted_data" in st.session_state and st.session_state.extracted_data:
    data = st.session_state.extracted_data
    
    st.header("2. Review Extracted Information")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Extracted Pattern")
        # Allow user to edit the pattern if extraction was imperfect
        pattern_input = st.text_area("Exam Pattern Instructions", value=data["pattern_desc"], height=300)
    
    with col_b:
        st.subheader("Topic Weightage")
        if data["modules"]:
            # Display weights
            weights = data["weights"]
            # Convert to list for display
            weight_list = [{"Topic": k, "Weight": f"{v:.2f}"} for k, v in weights.items()]
            st.table(weight_list)
        else:
            st.warning("No specific modules/hours detected in Syllabus. Using equal weights.")
            
    # --- SECTION 4: GENERATION ---
    st.header("3. Generate Question Paper")
    
    if st.button("✨ Generate Paper"):
        with st.spinner("Generating Question Paper..."):
            final_paper = generate_question_paper(
                pattern_description=pattern_input,
                weighted_topics=data["weights"],
                syllabus_text=data["syllabus_text"],
                api_key=api_key,
                provider=provider,
                model=model,
                base_url=base_url,
            )
            
            st.session_state.final_paper = final_paper
            st.success("Generation Successful!")

# --- SECTION 5: OUTPUT ---
if "final_paper" in st.session_state:
    st.markdown("---")
    st.subheader("Generated Question Paper")
    
    st.markdown(st.session_state.final_paper)
    
    st.download_button(
        label="📥 Download Markdown",
        data=st.session_state.final_paper,
        file_name="generated_question_paper.md",
        mime="text/markdown"
    )
