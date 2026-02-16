from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
from werkzeug.utils import secure_filename
from services.analyzer import analyze_syllabus_and_pyqs, extract_text_from_pdf
from services.generator import generate_paper_content
from services.pdf_maker import create_pdf
from services.chat_agent import ChatAgent

chat_agent = ChatAgent()

# --- CONFIGURATION ---
# TODO: Replace with your actual Groq API Key
GROQ_API_KEY = "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" 

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        data = request.form
        syllabus_text = data.get('syllabus_text')
        # Use provided key or fallback to hardcoded key
        api_key = data.get('api_key') or GROQ_API_KEY
        
        if not syllabus_text or not api_key:
            return jsonify({"error": "Missing syllabus text or API key"}), 400
        
        pyq_files = request.files.getlist('pyq_files')
        reference_file = request.files.get('reference_file') # New input
        
        # Save PYQs temporarily
        temp_pyq_paths = []
        if pyq_files:
            for file in pyq_files:
                if file.filename:
                    filename = secure_filename(file.filename)
                    # Use abspath to avoid potential issues with relative paths or mixed slashes
                    temp_path = os.path.abspath(os.path.join(tempfile.gettempdir(), filename))
                    file.save(temp_path)
                    temp_pyq_paths.append(temp_path)
        
        # Handle Reference File
        reference_text = None
        if reference_file and reference_file.filename:
            filename = secure_filename(reference_file.filename)
            ref_path = os.path.abspath(os.path.join(tempfile.gettempdir(), filename))
            reference_file.save(ref_path)
            try:
                reference_text = extract_text_from_pdf(ref_path)
            finally:
                if os.path.exists(ref_path):
                    os.remove(ref_path)

        # Analyze
        result = analyze_syllabus_and_pyqs(syllabus_text, temp_pyq_paths, api_key, reference_text)
        
        # Cleanup temp files
        for path in temp_pyq_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except:
                pass
                
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        api_key = data.get('api_key') or GROQ_API_KEY
        allocation = data.get('allocation')
        # New optional params
        paper_pattern = data.get('paper_pattern')
        priority_scores = data.get('priority_scores')
        
        if not api_key:
            return jsonify({"error": "Missing API key"}), 400
            
        # Generate Text Content
        paper_text = generate_paper_content(allocation, api_key, paper_pattern, priority_scores)
        
        return jsonify({"paper_text": paper_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/download-pdf', methods=['POST'])
def download_pdf():
    try:
        data = request.json
        text_content = data.get('text_content')
        college_name = data.get('college_name', 'COLLEGE OF ENGINEERING') # Default if empty
        college_name = data.get('college_name', 'COLLEGE OF ENGINEERING') # Default if empty
        header_image_data = data.get('header_image') # Base64 string
        header_text_raw = data.get('header_text_raw') # New input
        
        if not text_content:
            return jsonify({"error": "No content provided"}), 400
            
        # Refine Header if provided
        polished_header = None
        if header_text_raw:
            # Use the ChatAgent to perfect the header
             # We need a key for this agent interaction. Use global or from request.
            api_key = GROQ_API_KEY 
            polished_header = chat_agent.refine_header_text(header_text_raw, api_key)

        # Handle Header Image
        temp_img_path = None
        if header_image_data:
            import base64
            try:
                # Remove header if present (e.g., "data:image/png;base64,")
                if "," in header_image_data:
                    header_image_data = header_image_data.split(",")[1]
                
                img_bytes = base64.b64decode(header_image_data)
                temp_img_path = os.path.join(tempfile.gettempdir(), "header_logo.png")
                with open(temp_img_path, "wb") as f:
                    f.write(img_bytes)
            except Exception as e:
                print(f"Error decoding image: {e}")
                temp_img_path = None

        pdf_bytes = create_pdf(text_content, college_name, header_image_path=temp_img_path, header_text=polished_header)
        
        # Cleanup Image
        if temp_img_path and os.path.exists(temp_img_path):
            os.remove(temp_img_path)
        
        # Save to temp file to send
        temp_pdf_path = os.path.join(tempfile.gettempdir(), "generated_paper.pdf")
        with open(temp_pdf_path, "wb") as f:
            f.write(pdf_bytes)
            
        return send_file(
            temp_pdf_path,
            as_attachment=True,
            download_name="question_paper.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        api_key = data.get('api_key') or GROQ_API_KEY
        message = data.get('message')
        context = data.get('context', {})
        
        if not api_key or not message:
            return jsonify({"error": "Missing API key or message"}), 400
            
        response = chat_agent.process_message(message, context, api_key)
        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
