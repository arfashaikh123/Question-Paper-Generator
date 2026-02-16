from groq import Groq

import random

def generate_paper_content(allocation, api_key, paper_pattern=None, priority_scores=None):
    """
    Generates question paper.
    If paper_pattern is provided, follows that structure.
    Otherwise uses topic allocation.
    """
    client = Groq(api_key=api_key)
    final_questions = []

    # MODE 1: Strict Pattern Matching (Reference Paper)
    if paper_pattern and priority_scores:
        sorted_topics = sorted(priority_scores.items(), key=lambda x: x[1], reverse=True)
        top_topics = [t[0] for t in sorted_topics if t[1] > 0]
        
        for section_name, details in paper_pattern.items():
            count = details.get('questions_to_attempt', details.get('total_questions', 5))
            desc = details.get('description', '')
            marks = details.get('marks_per_question', 1)
            
            # Select topics for this section (weighted random to favor high priority)
            # Simple approach: Cycle through top topics or pick random from top 50%
            section_content = f"## {section_name} ({desc} - {marks} Marks each)\n"
            
            # Generate in batches or single prompt
            prompt = f"""
            Generate {count} exam questions for **{section_name}**.
            
            **Structure**: {desc}
            **Marks per Question**: {marks}
            **Topics to Cover**: {', '.join(top_topics[:min(len(top_topics), 10)])}... (Focus on these)
            
            **Rules**:
            1. Strictly follow the question type (MCQ, Short, Long) implied by the description.
            2. Use the provided topics.
            3. Format clearly.
            """
            
            try:
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=1000
                )
                section_content += response.choices[0].message.content + "\n\n"
                final_questions.append(section_content)
            except Exception as e:
                final_questions.append(f"## {section_name}\n[Error: {e}]\n")
                
        return "\n".join(final_questions)

    # MODE 2: Default Allocation (Original)
    for topic, count in allocation.items():
        if count > 0:
            prompt = f"""
            Generate {count} new exam questions for topic: {topic}

            Rules:
            - Avoid repeating past patterns
            - Create new structure
            - Maintain academic difficulty
            - Professional formatting
            - Include marks for each question
            """

            try:
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=800
                )
                final_questions.append(f"## Topic: {topic}\n" + response.choices[0].message.content)
            except Exception as e:
                final_questions.append(f"## Topic: {topic}\n[Error generating questions: {e}]")

    return "\n\n".join(final_questions)
