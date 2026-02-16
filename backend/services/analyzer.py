import re
import os
from collections import defaultdict
from langchain_community.document_loaders import PyPDFLoader
from groq import Groq

def parse_and_clean_syllabus(raw_text):
    """
    Parses raw syllabus text to extract Topic -> Hours mapping.
    Expects format: Module No -> Topic -> Hours (on separate lines)
    """
    topics = {}
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]

    for i in range(len(lines) - 2):
        if lines[i].isdigit():  # Module number check
            topic = lines[i + 1]
            hrs_line = lines[i + 2]
            if hrs_line.isdigit():
                hours = int(hrs_line)
                # Filtering logic
                if 2 <= hours <= 20 and len(topic) > 3:
                     topics[topic] = hours
    return topics

def extract_text_from_pdf(file_path):
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    return "\n".join([p.page_content for p in pages])

def compute_priority_scores(syllabus_topics, frequency_dict):
    if not syllabus_topics:
        return {}
        
    max_hours = max(syllabus_topics.values())
    max_freq = max(frequency_dict.values()) if frequency_dict else 1

    priority_scores = {}

    for topic in syllabus_topics:
        H_norm = syllabus_topics[topic] / max_hours
        F_norm = frequency_dict.get(topic, 0) / max_freq
        priority = 0.6 * H_norm + 0.4 * F_norm
        priority_scores[topic] = round(priority, 3)

    return priority_scores

def calculate_allocation(priority_scores, total_questions=10):
    total_priority = sum(priority_scores.values())
    allocation = {}
    if total_priority == 0:
        return {k: 1 for k in priority_scores} # Fallback
        
    for topic, score in priority_scores.items():
        # Ensure at least 1 question if score is decent, else proportional
        count = int((score / total_priority) * total_questions)
        allocation[topic] = max(1, count) if score > 0.1 else 0
        
    return allocation

def analyze_syllabus_and_pyqs(syllabus_text, pyq_paths, api_key):
    client = Groq(api_key=api_key)
    
    # 1. Parse Syllabus
    syllabus_topics = parse_and_clean_syllabus(syllabus_text)
    if not syllabus_topics:
        raise ValueError("Could not parse syllabus. Format expected: ModuleNum \n Topic \n Hours")

    # 2. Analyze PYQs
    frequency = defaultdict(int)
    
    for pdf_path in pyq_paths:
        pyq_text = extract_text_from_pdf(pdf_path)
        # Naive splitting by '?'
        questions = pyq_text.split("?")
        
        topic_list_str = ", ".join(syllabus_topics.keys())
        
        # Batch processing would be better but keeping it simple per logic
        # We will process a subset to save time/tokens if needed, or all.
        # Let's process valid looking questions.
        
        for q in questions:
            if len(q.strip()) > 30:
                prompt = f"""
                Classify the following question into one of these topics:
                {topic_list_str}

                Question:
                {q}

                Respond ONLY with the exact topic name from the list.
                """
                
                try:
                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0,
                        max_tokens=60
                    )
                    topic = response.choices[0].message.content.strip()
                    
                    # Fuzzy match or direct check
                    # We'll check if the returned string contains a topic key
                    matched = False
                    for t in syllabus_topics:
                        if t.lower() in topic.lower():
                            frequency[t] += 1
                            matched = True
                            break
                except Exception as e:
                    print(f"Error classifying question: {e}")
                    continue

    # 3. Compute Priority
    priority_scores = compute_priority_scores(syllabus_topics, frequency)
    
    # 4. Default Allocation (can be overridden by UI later, but good to return)
    # logic ported from app_new.py
    default_allocation = calculate_allocation(priority_scores)

    return {
        "syllabus_topics": syllabus_topics,
        "frequency": frequency,
        "priority_scores": priority_scores,
        "default_allocation": default_allocation
    }
