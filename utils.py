
import os
import re
import json
from PyPDF2 import PdfReader
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from collections import Counter

# --- 1. Text Extraction (OCR / PDF Reading) ---

def extract_text_from_pdf(pdf_file) -> str:
    """
    Extracts text from a PDF file. 
    Tries PyPDF2 first (fast). If text is too short, assumes scanned and would ideally use OCR.
    For this implementation, we will stick to PyPDF2 for speed unless user explicitly aids setup.
    """
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error reading PDF: {e}"

# --- 2. Pattern Extraction (LLM Based) ---

def extract_pattern_from_text(text: str, api_key: str) -> str:
    """
    Uses Groq to analyze the sample paper text and extract the exam structure.
    Returns a markdown description of the pattern.
    """
    if not api_key:
        return "Error: API Key missing."

    llm = ChatGroq(temperature=0, model_name="llama-3.3-70b-versatile", api_key=api_key)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert exam analyzer."),
        ("human", """Analyze the following text from a sample question paper and extract the detailed exam pattern.
        
        **Sample Paper Text:**
        {text}
        
        **Output Requirements:**
        Identify:
        1. Total Marks
        2. Duration
        3. Section-wise breakdown (e.g., Q1: Compulsory, Q2-Q6: Solve any 3).
        4. Question Types (MCQ, Short Note, Long Answer).
        
        Return a concise MARKDOWN summary of this pattern that can be used as instructions for generating a new paper.
        """)
    ])
    
    chain = prompt | llm
    try:
        response = chain.invoke({"text": text[:15000]}) # Truncate to fit context
        return response.content
    except Exception as e:
        return f"Error extracting pattern: {e}"

# --- 3. Syllabus Parsing ---

def parse_syllabus_modules(text: str) -> dict:
    """
    Parses syllabus text to find 'Module: Hours' mapping.
    """
    modules = {}
    lines = text.split('\n')
    
    for line in lines:
        # Regex for "Module Name ... 10 Hours"
        # Heuristic: Find digits followed by 'Hours' or 'Hrs'
        match = re.search(r'(\d+)\s*(?:Hours|Hrs)', line, re.IGNORECASE)
        if match:
            hours = int(match.group(1))
            # Rough attempt to get topic name: text before the hours
            topic_part = line[:match.start()].strip()
            # Cleanup: remove leading numbers/dots (e.g. "1. Introduction")
            topic_name = re.sub(r'^[\d\.\s]+', '', topic_part)
            
            if len(topic_name) > 3 and hours > 0:
                modules[topic_name] = hours
    
    return modules

# --- 4. Weightage Calculation ---

def calculate_topic_weights(syllabus_modules: dict, pyq_text: str) -> dict:
    """
    Combines Syllabus Hours (50%) and PYQ Frequency (50%) to determine topic weights.
    """
    if not syllabus_modules:
        return {}

    # 1. Normalize Hour Weights
    total_hours = sum(syllabus_modules.values())
    hour_weights = {k: v/total_hours for k, v in syllabus_modules.items()}
    
    # 2. Calculate Frequency Weights from PYQs
    pyq_lower = pyq_text.lower()
    freq_counts = {}
    for topic in syllabus_modules.keys():
        # Simple keyword matching (first 2 significant words)
        words = [w for w in topic.split() if len(w) > 3]
        if not words:
            freq_counts[topic] = 0
            continue
            
        keywords = words[:2] 
        regex = r"|".join([re.escape(k.lower()) for k in keywords])
        count = len(re.findall(regex, pyq_lower))
        freq_counts[topic] = count
        
    total_freq = sum(freq_counts.values())
    freq_weights = {k: v/total_freq if total_freq > 0 else 0 for k, v in freq_counts.items()}
    
    # 3. Combine
    final_weights = {}
    for topic in syllabus_modules:
        w_h = hour_weights.get(topic, 0)
        w_f = freq_weights.get(topic, 0)
        final_weights[topic] = (w_h * 0.5) + (w_f * 0.5)
        
    return final_weights

# --- 5. Question Paper Generation ---

def generate_question_paper(
    pattern_description: str,
    weighted_topics: dict,
    syllabus_text: str,
    api_key: str
) -> str:
    """
    Generates the final question paper.
    """
    if not api_key:
        return "Error: API Key missing."
        
    # Prepare High Priority Topics String
    sorted_topics = sorted(weighted_topics.items(), key=lambda x: x[1], reverse=True)
    top_topics_str = "\n".join([f"- {t[0]} (Weight: {t[1]:.2f})" for t in sorted_topics[:5]])

    llm = ChatGroq(temperature=0.5, model_name="llama-3.3-70b-versatile", api_key=api_key)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert academic question paper setter."),
        ("human", """Create a comprehensive question paper based on the following instructions.

        **1. Exam Pattern (STRICTLY FOLLOW THIS):**
        {pattern}

        **2. Focus Topics (High Weightage - Prioritize these):**
        {top_topics}

        **3. Syllabus Context:**
        {syllabus_snippet}

        **Instructions:**
        - Ensure the paper is balanced but gives more weight to the Focus Topics.
        - Questions should be academic, clear, and unambiguous.
        - Output the final paper in clean Markdown format.
        """)
    ])
    
    chain = prompt | llm
    try:
        response = chain.invoke({
            "pattern": pattern_description,
            "top_topics": top_topics_str,
            "syllabus_snippet": syllabus_text[:10000] # Truncate
        })
        return response.content
    except Exception as e:
        return f"Error generating paper: {e}"
