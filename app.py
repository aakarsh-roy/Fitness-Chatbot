import os
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Initialize the Flask app
app = Flask(__name__)

# Create the model configuration for diet plan generation
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Create the generative model
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

# Route to render the main page
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle form submission and fetch diet plan
@app.route('/get_diet_plan', methods=['POST'])
def get_diet_plan():
    height = request.form['height']
    weight = request.form['weight']
    goal = request.form['goal']
    age= request.form['age']
    meal_preference= request.form['meal_preference']
    
    # Start a new chat session with an empty history
    chat_session = model.start_chat(history=[])
    
    # Construct the message to send to the model
    prompt = f'''
    DO NOT INCLUDE ANY BOLD WORDS IN YOUR RESPONSE
    
    Please suggest a diet plan for a person living in India with the following details:
    - Height: {height} cm
    - Weight: {weight} kg
    - Age: {age}
    - Fitness Goal: {goal}
    - Meal Preference: {meal_preference}

    Provide the plan in the following format:
    - Breakfast: Details
    - Mid Morning Snack: Details
    - Lunch: Details
    - Evening Snack: Details
    - Dinner: Details
    '''
    
    # Send the message to the chat session and get the response
    response = chat_session.send_message(prompt)
    
    # Format the description for line breaks
    description = response.text
    description_with_line_breaks = '<br>- '.join(description.split('-'))
    
    
    # Return the diet plan as a JSON response
    return jsonify({"diet_plan": description_with_line_breaks})

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
