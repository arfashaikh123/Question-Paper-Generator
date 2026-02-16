
import os
import re
import json
from PyPDF2 import PdfReader
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from collections import Counter

# --- 1. Text Extraction (OCR / PDF Reading) ---

import fitz  # PyMuPDF
from PIL import Image
from transformers import AutoModelForCausalLM, AutoProcessor
import torch

# Global model cache
ocr_model = None
ocr_processor = None

def load_ocr_model():
    """Loads the Nanonets OCR model (Small 1.5B version)."""
    global ocr_model, ocr_processor
    if ocr_model is None:
        # User requested "only small model". 1.5B is the smallest in this family.
        model_id = "nanonets/Nanonets-OCR2-1.5B-exp" 
        print(f"Loading OCR Model: {model_id}...")
        try:
            ocr_processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
            ocr_model = AutoModelForCausalLM.from_pretrained(
                model_id,
                trust_remote_code=True,
                torch_dtype=torch.float32, # CPU for compatibility
                device_map="auto"
            )
            print("OCR Model Loaded.")
        except Exception as e:
            print(f"Failed to load OCR model: {e}")
            return None, None
    return ocr_model, ocr_processor

def ocr_page(image, model, processor):
    """Runs OCR on a single PIL Image."""
    if not model or not processor:
        return ""
    
    # Standard prompt for Nanonets/Qwen-VL based OCR
    prompt = "<|image|>Extract the text from this document accurately into markdown format."
    
    # Check if chat template is available or manually construct
    messages = [
        {"role": "user", "content": [{"type": "image", "image": image}, {"type": "text", "text": "Extract the text from this document accurately into markdown format."}]}
    ]
    
    try:
        # Use processor to format inputs
        text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = processor(text=[text], images=[image], padding=True, return_tensors="pt")
        
        # Generate
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=1024,
            do_sample=False
        )
        
        # Decode
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        # Cleanup response (remove prompt if echoed)
        # Qwen-VL based models often echo or have specific splitters
        return generated_text.split("markdown format.")[-1].strip()
        
    except Exception as e:
        return f"[OCR Error: {e}]"

def extract_text_from_pdf(pdf_file, api_key=None, use_ocr_fallback=True) -> str:
    """
    Extracts text. Tries PyPDF2 first. If garbled, falls back to Local Nanonets 1.5B OCR.
    """
    # 1. Try PyPDF2
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
            
        # Check for garbled text
        if len(text) < 50 or (len(text) > 0 and text.count('/') > len(text) * 0.1):
            print("Detected garbled text. Falling back to Local OCR...")
            raise Exception("Garbled Text")
            
        return text
    except Exception as e:
        if not use_ocr_fallback:
            return f"Error reading PDF (OCR disabled): {e}"
            
    # 2. Fallback to Local OCR
    print("Starting Local OCR extraction...")
    try:
        if hasattr(pdf_file, "read"):
            pdf_file.seek(0)
            file_bytes = pdf_file.read()
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        else:
            doc = fitz.open(pdf_file)
            
        model, processor = load_ocr_model()
        if not model:
            return "Error: Could not load OCR model. Check RAM/Disk space."
            
        full_text = ""
        for page_num, page in enumerate(doc):
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            ocr_text = ocr_page(img, model, processor)
            full_text += f"--- Page {page_num + 1} ---\n{ocr_text}\n\n"
            
        return full_text
    except Exception as e:
        return f"OCR Failed: {e}"

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

def parse_syllabus_modules(text: str, api_key: str = None) -> dict:
    """
    Parses syllabus text to find 'Module: Hours' mapping.
    1. Tries Regex first (fast).
    2. If Regex fails and api_key is provided, uses LLM (smart).
    """
    modules = {}
    lines = text.split('\n')
    
    # 1. Regex Approach
    for line in lines:
        match = re.search(r'(\d+)\s*(?:Hours|Hrs)', line, re.IGNORECASE)
        if match:
            hours = int(match.group(1))
            topic_part = line[:match.start()].strip()
            topic_name = re.sub(r'^[\d\.\s]+', '', topic_part)
            
            if len(topic_name) > 3 and hours > 0:
                modules[topic_name] = hours
    
    # 2. LLM Fallback
    if not modules and api_key:
        try:
            llm = ChatGroq(temperature=0, model_name="llama-3.3-70b-versatile", api_key=api_key)
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful assistant that extracts structured data."),
                ("human", """Extract the Syllabus Modules and their allocated Hours from the text below.
                
                **Text:**
                {text}
                
                **Output Format:**
                Return ONLY a JSON object where keys are Module Names and values are Integer Hours.
                Example: {{"Introduction": 4, "Data Structures": 10}}
                If no hours are explicitly mentioned, estimate based on content length or return empty {{}}.
                """)
            ])
            chain = prompt | llm
            response = chain.invoke({"text": text[:15000]})
            content = response.content.strip()
            # Extract JSON from potential markdown code blocks
            if "```" in content:
                content = content.split("```")[1].replace("json", "").strip()
            modules = json.loads(content)
        except Exception as e:
            print(f"LLM Syllabus Parsing failed: {e}")
            
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
