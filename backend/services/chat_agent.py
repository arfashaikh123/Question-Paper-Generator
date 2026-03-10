from services.llm_client import get_client, get_model, DEFAULT_PROVIDER
import json

class ChatAgent:
    def __init__(self):
        pass

    def process_message(self, user_message, context, api_key,
                        provider=DEFAULT_PROVIDER, model=None, base_url=None):
        """
        Processes the user's message and returns a reply and potential action.
        
        Args:
            user_message (str): The user's input.
            context (dict):     Current analysis state (syllabus, pattern, etc).
            api_key (str):      API key for the chosen LLM provider.
            provider (str):     LLM provider ('groq', 'ollama', or 'openai_compatible').
            model (str):        Model name; falls back to the provider's default.
            base_url (str):     Override the provider's base URL for custom deployments.
            
        Returns:
            dict: {"reply": str, "action": str|None}
        """
        client = get_client(provider=provider, api_key=api_key, base_url=base_url)
        selected_model = get_model(provider=provider, model=model)
        
        # Construct System Prompt
        system_prompt = f"""
        You are an Expert Exam Setter Assistant for a Question Paper Generator App.
        
        **Context:**
        - Syllabus Topics: {list(context.get('syllabus_topics', {}).keys())}
        - Current Pattern: {json.dumps(context.get('paper_pattern', {}), indent=2)}
        - User Goal: Create a high-quality question paper.
        
        **Your Capabilities:**
        1. Answer questions about the syllabus.
        2. MODIFY the "Current Pattern" if the user requests changes (e.g., "Add Section C", "Change Marks").
        
        **RESPONSE FORMAT:**
        You must return a valid JSON object with the following structure:
        {{
            "reply": "Your conversational response here.",
            "action": "update_pattern" or null,
            "data": {{ ...new pattern object... }} or null
        }}
        
        **RULES:**
        - If the user asks to change the pattern, you MUST return `action: "update_pattern"` and the FULL updated pattern object in `data`.
        - The pattern object keys are Section Names (e.g. "Section A"). Values have `description`, `marks_per_question`, `total_questions`, `questions_to_attempt`.
        - If no change is needed, set `action` to null.
        - Be concise and professional.
        """
        
        try:
            response = client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1, # Lower temperature for JSON reliability
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON response from LLM
            content = response.choices[0].message.content
            parsed_response = json.loads(content)
            
            return parsed_response
            
        except Exception as e:
            return {"reply": f"Error interacting with AI: {str(e)}", "action": None}

    def refine_header_text(self, raw_text, api_key,
                           provider=DEFAULT_PROVIDER, model=None, base_url=None):
        """
        Refines raw header text into a professional exam header using LLM.
        """
        client = get_client(provider=provider, api_key=api_key, base_url=base_url)
        selected_model = get_model(provider=provider, model=model)
        
        system_prompt = """
        You are an expert academic typesetter. 
        Format the following text into a professional exam header (3-4 lines max).
        Center align implies the content, but you just return the text lines.
        Use standard terminology (e.g. "DEPARTMENT OF...", "EXAMINATION - 202X").
        Return ONLY the formatted text, no markdown, no quotes, no conversational filler.
        """
        
        try:
            response = client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Refine this header info: {raw_text}"}
                ],
                temperature=0.1,
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Header refinement failed: {e}")
            return raw_text # Fallback to raw text
