from groq import Groq
import json

class ChatAgent:
    def __init__(self):
        pass

    def process_message(self, user_message, context, api_key):
        """
        Processes the user's message and returns a reply and potential action.
        
        Args:
            user_message (str): The user's input.
            context (dict): Current analysis state (syllabus, pattern, etc).
            api_key (str): Groq API Key.
            
        Returns:
            dict: {"reply": str, "action": str|None}
        """
        client = Groq(api_key=api_key)
        
        # Construct System Prompt
        system_prompt = f"""
        You are an Expert Exam Setter Assistant for a Question Paper Generator App.
        
        **Context:**
        - Syllabus Topics: {list(context.get('syllabus_topics', {}).keys())}
        - Current Pattern: {json.dumps(context.get('paper_pattern', {}), indent=2)}
        - User Goal: Create a high-quality question paper.
        
        **Your Capabilities:**
        1. Answer questions about the syllabus or analyzed topics.
        2. Suggest questions for specific modules.
        3. Help refine the paper pattern (e.g. "Make Section A harder").
        
        **Rules:**
        - Be concise and professional.
        - If the user asks to change the pattern or regenerate, acknowledge it and suggest they use the UI controls or say "I can't do that directy yet, but here is a suggestion...".
        - (Future: You will be able to trigger actions).
        
        Answer the user's message based on the context.
        """
        
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            reply = response.choices[0].message.content
            
            # Simple Intent Detection (for future actions)
            action = None
            if "regenerate" in user_message.lower() or "create new" in user_message.lower():
                action = "regenerate_suggestion"
            
            return {"reply": reply, "action": action}
            
        except Exception as e:
            return {"reply": f"Error interacting with AI: {str(e)}", "action": None}
