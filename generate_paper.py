
import os
import sys
from PyPDF2 import PdfReader
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

def extract_text_from_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return ""

def main():
    # Define paths
    qa_folder = "QA"
    syllabus_text = ""
    previous_papers_text = ""

    # Iterate through files in the QA folder
    if os.path.exists(qa_folder):
        for filename in os.listdir(qa_folder):
            file_path = os.path.join(qa_folder, filename)
            if filename.lower().endswith(".pdf"):
                print(f"Processing: {filename}")
                extracted_text = extract_text_from_pdf(file_path)
                
                # Simple logic to distinguish syllabus from question papers
                if "syllabus" in filename.lower():
                    syllabus_text += extracted_text
                    print("  -> Identified as Syllabus")
                else:
                    previous_papers_text += f"--- START OF PAPER: {filename} ---\n"
                    previous_papers_text += extracted_text
                    previous_papers_text += f"--- END OF PAPER: {filename} ---\n"
    else:
        print(f"Directory '{qa_folder}' not found. Please ensure the folder exists.")
        return

    print(f"\nSyllabus Length: {len(syllabus_text)} characters")
    print(f"Previous Papers Length: {len(previous_papers_text)} characters")

    # Initialize ChatGroq
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY environment variable not set.")
        return

    llm = ChatGroq(
        temperature=0.3,
        model_name="llama-3.3-70b-versatile",
        api_key=api_key
    )

    # Define the prompt template
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are an expert academician and question paper setter. Your task is to generate a comprehensive and balanced question paper based on the provided syllabus and reference from previous years' papers."),
        ("human", """Generate a new question paper for the subject based on the following inputs:

        **Syllabus Content:**
        {syllabus}

        **Previous Years' Question Papers (for pattern and difficulty reference):**
        {previous_papers}

        **Instructions:**
        1. Follow the standard university format (e.g., Duration: 3 Hours, Max Marks: 80/100).
        2. Ensure questions cover different cognitive levels (Recall, Understand, Apply, Analyze, Evaluate).
        3. Divide the paper into appropriate sections (e.g., Q1: Compulsory short notes, Q2-Q6: Detailed questions with internal choices).
        4. Do not copy questions directly from previous papers, but maintain a similar difficulty level and topic distribution.
        5. Output the result in clean Markdown format.
        
        Generate the Question Paper now:""")
    ])

    # Create the chain
    chain = prompt_template | llm

    print("Generating question paper...")
    try:
        response = chain.invoke({
            "syllabus": syllabus_text[:20000],  # Truncating to avoid token limits
            "previous_papers": previous_papers_text[:40000]
        })
        
        generated_paper = response.content
        print("Generation Complete!")
        
        output_file = "Generated_Question_Paper_Sample.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(generated_paper)
        print(f"Question paper saved to {output_file}")
        
    except Exception as e:
        print(f"Error during generation: {e}")

if __name__ == "__main__":
    main()
