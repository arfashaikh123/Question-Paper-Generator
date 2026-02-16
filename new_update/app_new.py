import streamlit as st
from groq import Groq
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.vectorstores import FAISS

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(page_title="PDF Text Retrieval System", layout="wide")

st.title("📄 Intelligent PDF Text Retrieval System")
st.markdown("Groq Ready • FAISS Vector Search • FastEmbed Embeddings")

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.header("🔐 Groq API Key (Optional for Now)")

api_key = st.sidebar.text_input(
    "Enter Groq API Key",
    type="password",
    help="Not used yet. Reserved for generation step."
)

st.sidebar.header("📄 Upload PDF Files")

pdf_files = st.sidebar.file_uploader(
    "Upload one or more PDFs",
    type=["pdf"],
    accept_multiple_files=True
)

st.sidebar.header("🔍 Retrieval Query")

query = st.sidebar.text_area(
    "Enter search query",
    value="Important concepts and key topics",
    height=100
)

search_button = st.sidebar.button("🚀 Extract & Retrieve")

# =====================================================
# MAIN FUNCTION
# =====================================================

def extract_and_retrieve():

    if not pdf_files:
        st.error("❌ Please upload at least one PDF.")
        return

    # Optional Groq initialization (for future use)
    if api_key:
        try:
            client = Groq(api_key=api_key)
            st.success("✅ Groq API Initialized Successfully (Ready for next step).")
        except Exception as e:
            st.warning(f"⚠️ Groq Initialization Failed: {str(e)}")

    # Load PDFs
    with st.spinner("📄 Loading PDFs..."):
        all_pages = []

        for pdf in pdf_files:
            temp_path = f"/tmp/{pdf.name}"
            with open(temp_path, "wb") as f:
                f.write(pdf.read())

            loader = PyPDFLoader(temp_path)
            pages = loader.load()
            all_pages.extend(pages)

        if not all_pages:
            st.error("❌ No text could be extracted.")
            return

    # Split into chunks
    with st.spinner("✂️ Splitting text into chunks..."):
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        chunks = splitter.split_documents(all_pages)

    # Create vector store
    with st.spinner("🧠 Generating embeddings & building vector store..."):
        embeddings = FastEmbedEmbeddings()
        vector_store = FAISS.from_documents(chunks, embeddings)

    # Retrieve relevant content
    with st.spinner("🔍 Retrieving relevant content..."):
        retriever = vector_store.as_retriever(
            search_kwargs={"k": min(8, len(chunks))}
        )

        results = retriever.invoke(query)

    retrieved_text = "\n\n".join([doc.page_content for doc in results])

    st.success("✅ Retrieval Complete!")

    st.subheader("📄 Retrieved Text")
    st.markdown(f"**Query:** {query}")
    st.markdown("---")
    st.write(retrieved_text)


# =====================================================
# TRIGGER
# =====================================================

if search_button:
    extract_and_retrieve()
