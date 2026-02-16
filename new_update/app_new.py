import streamlit as st
import pdfplumber
import re

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(page_title="Advanced PDF Extractor", layout="wide")

st.title("📄 Advanced Exam PDF Extraction & Cleaning System")
st.markdown("Watermark Removal • Question Formatting • Table Structuring")

# =====================================================
# FILE UPLOAD
# =====================================================

pdf_files = st.file_uploader(
    "Upload Exam PDF(s)",
    type=["pdf"],
    accept_multiple_files=True
)

# =====================================================
# CLEAN WATERMARK / HEADER / FOOTER
# =====================================================

def clean_text(text):

    # Remove long hexadecimal watermark strings
    text = re.sub(r"\b[A-F0-9]{20,}\b", "", text)

    # Remove page number formats like: 28560 Page 1 of 2
    text = re.sub(r"\b\d+\s*Page\s*\d+\s*of\s*\d+\b", "", text, flags=re.IGNORECASE)

    # Remove subject header repetition
    text = re.sub(r"Paper\s*/\s*Subject\s*Code:.*?\n", "", text)

    # Remove Total Marks / Hours header
    text = re.sub(r"\(.*?Hours\).*?Total\s*Marks\s*\d+", "", text)

    # Remove NB instructions block
    text = re.sub(r"\bNB\b.*?(?=Q\d)", "", text, flags=re.DOTALL)

    # Remove excessive whitespace
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = re.sub(r"\s{2,}", " ", text)

    return text.strip()


# =====================================================
# FORMAT QUESTIONS PROPERLY
# =====================================================

def format_questions(text):

    # Separate main questions (Q1, Q2...)
    text = re.sub(r"(Q\d+)", r"\n\n\1", text)

    # Separate sub-parts like a), b), c)
    text = re.sub(r"\s([a-d]\))", r"\n   \1", text)

    # Separate roman numeral parts i), ii), iii)
    text = re.sub(r"\s(i{1,3}\))", r"\n      \1", text)

    return text.strip()


# =====================================================
# FORMAT NUMERIC TABLES
# =====================================================

def format_numeric_tables(text):

    # Detect patterns like: 2 10 4 20 6 25 8 30
    pattern = r"(\d+\s+\d+(?:\s+\d+\s+\d+)+)"

    matches = re.findall(pattern, text)

    for match in matches:
        numbers = match.split()
        if len(numbers) % 2 == 0:
            formatted = "\n"
            for i in range(0, len(numbers), 2):
                formatted += f"{numbers[i]}  |  {numbers[i+1]}\n"
            text = text.replace(match, formatted)

    return text


# =====================================================
# EXTRACT TEXT + TABLES PER PDF
# =====================================================

def extract_pdf_content(pdf_file):

    extracted_text = ""
    extracted_tables = []

    with pdfplumber.open(pdf_file) as pdf:

        for page in pdf.pages:

            # Extract page text
            page_text = page.extract_text()
            if page_text:
                extracted_text += page_text + "\n\n"

            # Extract tables
            tables = page.extract_tables()
            for table in tables:
                extracted_tables.append(table)

    return extracted_text, extracted_tables


# =====================================================
# MAIN PROCESSING
# =====================================================

if pdf_files:

    for pdf in pdf_files:

        st.header(f"📘 Processing: {pdf.name}")

        with st.spinner("Extracting and cleaning content..."):

            # Step 1: Raw extraction
            raw_text, tables = extract_pdf_content(pdf)

            # Step 2: Cleaning
            cleaned_text = clean_text(raw_text)

            # Step 3: Format questions
            formatted_text = format_questions(cleaned_text)

            # Step 4: Format numeric tables
            final_text = format_numeric_tables(formatted_text)

        # =====================================================
        # DISPLAY CLEANED TEXT
        # =====================================================

        st.subheader("📄 Cleaned & Structured Text")
        st.text_area(
            "Extracted Content",
            final_text,
            height=500
        )

        # =====================================================
        # DISPLAY TABLES (if detected)
        # =====================================================

        if tables:
            st.subheader("📊 Extracted Tables")
            for idx, table in enumerate(tables):
                st.write(f"Table {idx + 1}")
                st.table(table)
        else:
            st.info("No structured tables detected.")

else:
    st.info("Upload a PDF to begin extraction.")
