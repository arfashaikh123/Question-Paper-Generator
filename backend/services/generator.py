from groq import Groq

def generate_paper_content(allocation, api_key):
    """
    Generates the final question paper text based on topic allocation.
    """
    client = Groq(api_key=api_key)
    final_questions = []

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
