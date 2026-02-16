
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

# Page Config
st.set_page_config(page_title="Smart Question Paper Generator", layout="wide")

st.title("📄 Smart Question Paper Generator")
st.markdown("""
Generate a university-standard question paper by analyzing:
1. **Syllabus** (for topic hours)
2. **Previous Year Questions** (for frequency)
3. **Sample Question Paper** (for exam pattern)
""")

# Sidebar: API Key
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Groq API Key", type="password")

if not api_key and "GROQ_API_KEY" in os.environ:
    api_key = os.environ["GROQ_API_KEY"]

if not api_key:
    st.sidebar.warning("Please enter your Groq API Key to proceed.")

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
    if not api_key:
        st.error("API Key is required!")
    elif not syllabus_file or not pyq_files or not pattern_file:
        st.error("Please upload all required documents.")
    else:
        with st.spinner("Analyzing documents... (This may take time if OCR is required)"):
            try:
                # 0. Pre-load OCR model if needed (optional optimization)
                # For now, let it lazy load inside utils
                
                # 1. Parse Syllabus
                syllabus_text = extract_text_from_pdf(syllabus_file)
                
                # Debug: Show extracted text
                with st.expander("Debug: Extracted Syllabus Text"):
                    st.text(syllabus_text[:2000] + "..." if len(syllabus_text) > 2000 else syllabus_text)
                
                modules = parse_syllabus_modules(syllabus_text, api_key)
                
                # 2. Parse PYQs
                pyq_text = ""
                for pyq in pyq_files:
                    pyq_text += extract_text_from_pdf(pyq) + "\n"
                    
                # 3. Parse Pattern
                pattern_text = extract_text_from_pdf(pattern_file)
                extracted_pattern = extract_pattern_from_text(pattern_text, api_key)
                
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
        with st.spinner("Generating Question Paper using Groq..."):
            final_paper = generate_question_paper(
                pattern_description=pattern_input,
                weighted_topics=data["weights"],
                syllabus_text=data["syllabus_text"],
                api_key=api_key
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
