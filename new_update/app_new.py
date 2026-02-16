import streamlit as st
from groq import Groq
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.vectorstores import FAISS

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(page_title="AI Question Paper Generator (Groq)", layout="wide")

st.title("📄 AI Question Paper Generator")
st.markdown("Powered by Groq • Llama 3")

# =====================================================
# SIDEBAR - GROQ API INPUT
# =====================================================

st.sidebar.header("🔐 Groq API Configuration")

groq_api_key = st.sidebar.text_input(
    "Enter Groq API Key",
    type="password",
    help="Get your key from https://console.groq.com"
)

# =====================================================
# SIDEBAR - FILE UPLOAD
# =====================================================

st.sidebar.header("📄 Upload PDFs")

pdf_files = st.sidebar.file_uploader(
    "Upload Study Material PDFs (Max 5)",
    type=["pdf"],
    accept_multiple_files=True
)

# =====================================================
# SIDEBAR - QUESTION SETTINGS
# =====================================================

st.sidebar.header("⚙️ Question Configuration")

num_sets = st.sidebar.slider("Number of Sets", 1, 3, 1)

st.sidebar.subheader("MCQs")
mcq_difficulty = st.sidebar.radio("MCQ Difficulty", ["Easy", "Medium", "Hard"], index=1)
mcq_count = st.sidebar.slider("Number of MCQs", 0, 20, 5)

st.sidebar.subheader("Short Questions")
short_difficulty = st.sidebar.radio("Short Difficulty", ["Easy", "Medium", "Hard"], index=1)
short_count = st.sidebar.slider("Number of Short Questions", 0, 15, 3)

st.sidebar.subheader("Long Questions")
long_difficulty = st.sidebar.radio("Long Difficulty", ["Easy", "Medium", "Hard"], index=1)
long_count = st.sidebar.slider("Number of Long Questions", 0, 10, 2)

generate_button = st.sidebar.button("🚀 Generate Question Paper")

# =====================================================
# MAIN FUNCTION
# =====================================================

def generate_question_paper():

    if not groq_api_key:
        st.error("❌ Please enter Groq API key.")
        return

    if not pdf_files:
        st.error("❌ Please upload at least one PDF.")
        return

    if len(pdf_files) > 5:
        st.error("❌ Maximum 5 PDFs allowed.")
        return

    total_questions = mcq_count + short_count + long_count
    if total_questions == 0:
        st.error("❌ Please select at least one question.")
        return

    # Initialize Groq client
    try:
        client = Groq(api_key=groq_api_key)
    except Exception as e:
        st.error(f"❌ Invalid Groq API Key: {str(e)}")
        return

    # -------------------------------------------------
    # Load PDFs
    # -------------------------------------------------

    with st.spinner("📄 Loading PDFs..."):

        all_pages = []

        for pdf in pdf_files:
            temp_path = f"/tmp/{pdf.name}"
            with open(temp_path, "wb") as f:
                f.write(pdf.read())

            loader = PyPDFLoader(temp_path)
            pages = loader.load()
            all_pages.extend(pages)

    # -------------------------------------------------
    # Split Text
    # -------------------------------------------------

    with st.spinner("✂️ Splitting text into chunks..."):

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        chunks = splitter.split_documents(all_pages)

    # -------------------------------------------------
    # Create Vector Store
    # -------------------------------------------------

    with st.spinner("🧠 Creating vector database..."):

        embeddings = FastEmbedEmbeddings()
        vector_store = FAISS.from_documents(chunks, embeddings)

    # -------------------------------------------------
    # Retrieve Important Context
    # -------------------------------------------------

    with st.spinner("🔍 Retrieving important concepts..."):

        retriever = vector_store.as_retriever(search_kwargs={"k": 10})
        context_docs = retriever.invoke("Key concepts and important topics")
        context_text = "\n\n".join([doc.page_content for doc in context_docs])

    outputs = []

    # -------------------------------------------------
    # Generate Question Papers
    # -------------------------------------------------

    for set_num in range(1, num_sets + 1):

        prompt = f"""
You are an expert academic examiner.

CONTEXT:
{context_text}

Create QUESTION PAPER - SET {set_num}

MCQs: {mcq_count} ({mcq_difficulty})
Short Questions: {short_count} ({short_difficulty})
Long Questions: {long_count} ({long_difficulty})

Rules:
- Professional formatting
- Number all questions properly
- Include answer key for MCQs
- Do not add explanations outside exam format
"""

        with st.spinner(f"✍️ Generating Set {set_num}..."):

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are an expert academic examiner."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1200,
            )

            generated_text = response.choices[0].message.content
            outputs.append(generated_text)

    st.success("✅ Question Paper Generated Successfully!")

    final_output = "\n\n" + "="*100 + "\n\n".join(outputs)
    st.markdown(final_output)


# =====================================================
# RUN
# =====================================================

if generate_button:
    generate_question_paper()
