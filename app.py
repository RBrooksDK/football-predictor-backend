import os
from flask import Flask, jsonify # Import jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file (if it exists)
# We'll create .env later for API keys etc.
load_dotenv()

# Initialize the Flask application
app = Flask(__name__)

# Enable CORS for all routes and all origins by default for development.
# For production, you might want to restrict origins.
CORS(app)

# A simple configuration for now (can be expanded later)
# Example: Secret key for session management (though we aren't using sessions yet)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'a_super_secret_default_key_for_dev')

# --- API Routes ---

@app.route('/') # This is the root route for basic testing
def index():
    return jsonify(message="Welcome to the Football Predictor API! Version 1.0")

@app.route('/api/hello') # A sample API endpoint
def hello_api():
    return jsonify(greeting="Hello from the API!", status="success")

# --- Main execution block ---
if __name__ == '__main__':
    # debug=True enables auto-reloading when code changes and provides helpful error messages.
    # port=5001 to avoid conflict if your frontend dev server uses port 5000.
    # host='0.0.0.0' makes the server accessible from other devices on your network (optional for now).
    app.run(debug=True, port=5001)