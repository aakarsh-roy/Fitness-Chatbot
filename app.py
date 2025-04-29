import os
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
from datetime import datetime
from functools import wraps
import time
import logging

# Configure logging
logging.basicConfig(
    filename='chatbot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default-secret-key")

# Create the model configuration
generation_config = {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 8192,
}

# Create safety settings
safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
]

# Define system prompt
SYSTEM_PROMPT = """You are a professional fitness, diet advisor and cooking recipe chatbot. Only respond to queries related to:
- Diet and nutrition advice
- Workout and exercise recommendations
- Fitness goals and planning
- Health and wellness in the context of fitness
- BMI and body composition
- Meal planning and dietary requirements
- Exercise form and technique
- Recovery and rest
- Sports nutrition

If a user asks questions unrelated to fitness, diet, or health, politely redirect them to ask fitness/diet-related questions only.

Always provide evidence-based information and include disclaimers when necessary. Avoid giving medical advice and suggest consulting healthcare professionals for medical concerns."""

# Rate limiting configuration
RATE_LIMIT = 30  # Maximum requests per minute
rate_limit_data = {}

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_ip = request.remote_addr
        current_time = time.time()
        
        # Clean up old entries
        rate_limit_data.clear()
        
        # Check rate limit
        if user_ip in rate_limit_data:
            timestamps = rate_limit_data[user_ip]
            timestamps = [ts for ts in timestamps if current_time - ts < 60]
            
            if len(timestamps) >= RATE_LIMIT:
                return jsonify({
                    "error": "Rate limit exceeded. Please wait a moment before sending more messages."
                }), 429
                
            rate_limit_data[user_ip] = timestamps + [current_time]
        else:
            rate_limit_data[user_ip] = [current_time]
            
        return f(*args, **kwargs)
    return decorated_function

# Create the generative model
try:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    # Initialize chat history with system prompt
    chat = model.start_chat(history=[])
    chat.send_message(SYSTEM_PROMPT)
except Exception as e:
    logging.error(f"Error initializing Gemini model: {str(e)}")
    raise



@app.route('/')
def index():
    if 'chat_history' not in session:
        session['chat_history'] = []
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
@rate_limit
def chat_response():
    try:
        message = request.json.get('message', '').strip()
        
        if not message:
            return jsonify({"error": "Message cannot be empty"}), 400
            
        # Initialize chat history if not exists
        if 'chat_history' not in session:
            session['chat_history'] = []
            
        # Add user message to history
        session['chat_history'].append({
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'is_user': True
        })
        
        # Send the message to the chat session and get the response
        response = chat.send_message(message)
        
        # Remove Markdown formatting
        response_text = response.text
        response_text = response_text.replace('*', '')  # Remove asterisks
        response_text = response_text.replace('**', '')  # Remove double asterisks
        response_text = response_text.replace('_', '')   # Remove underscores
        response_text = response_text.replace('__', '')  # Remove double underscores
        response_text = response_text.replace('\n', '<br>')  # Convert newlines to HTML breaks
        
        # Add bot response to history
        session['chat_history'].append({
            'message': response_text,
            'timestamp': datetime.now().isoformat(),
            'is_user': False
        })
        
        session.modified = True
        
        # Log the interaction
        logging.info(f"User message: {message}")
        logging.info(f"Bot response: {response_text}")
        
        return jsonify({"response": response_text})
        
    except Exception as e:
        logging.error(f"Error in chat_response: {str(e)}")
        return jsonify({
            "error": "An error occurred while processing your request. Please try again."
        }), 500

@app.route('/clear-session', methods=['POST'])
def clear_session():
    try:
        session.clear()
        # Reinitialize chat with system prompt
        global chat
        chat = model.start_chat(history=[])
        chat.send_message(SYSTEM_PROMPT)
        return jsonify({"status": "success"})
    except Exception as e:
        logging.error(f"Error clearing session: {str(e)}")
        return jsonify({"error": "Failed to clear chat history"}), 500

@app.route('/export-history', methods=['GET'])
def export_history():
    try:
        if 'chat_history' not in session:
            return jsonify({"error": "No chat history found"}), 404
            
        chat_history = session['chat_history']
        return jsonify({"history": chat_history})
    except Exception as e:
        logging.error(f"Error exporting history: {str(e)}")
        return jsonify({"error": "Failed to export chat history"}), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run()