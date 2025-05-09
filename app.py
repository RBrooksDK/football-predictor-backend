import os
from flask import Flask, jsonify, request # Keep jsonify
from flask_sqlalchemy import SQLAlchemy # <-- ADDED IMPORT
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash # <-- ADDED IMPORT for password hashing

load_dotenv()
app = Flask(__name__)
CORS(app)

# --- Database Configuration ---
# Determine the base directory of the Flask application
basedir = os.path.abspath(os.path.dirname(__file__)) # <-- ADDED: Gets the directory where app.py is located
# Configure the SQLAlchemy database URI for SQLite
# It will create a file named 'predictions.db' in an 'instance' folder
# The 'instance' folder is a good place for instance-specific files not in version control.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'predictions.db') # <-- MODIFIED/ADDED
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Optional: Disables a feature that signals application on every change in the database
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'a_super_secret_default_key_for_dev')

db = SQLAlchemy(app) # <-- ADDED: Initialize SQLAlchemy with the Flask app

# --- Database Models ---
class User(db.Model): # <-- ADDED User Model
    __tablename__ = 'users' # Optional: Explicitly names the table 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False) # Increased length for longer hashes

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self): # Optional: A nice representation for debugging
        return f'<User {self.username}>'

# TODO: Add other models later: League, Team, Prediction, ActualStanding, UserScore

# --- API Routes ---
@app.route('/')
def index():
    return jsonify(message="Welcome to the Football Predictor API! DB Setup in progress.")

@app.route('/api/hello')
def hello_api():
    return jsonify(greeting="Hello from the API!", status="success")

# NEW REGISTRATION ROUTE
@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json() # Get JSON data from the request body

    if not data:
        return jsonify(message="No input data provided"), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify(message="Username and password are required"), 400

    if len(password) < 6: # Example: basic password length validation
        return jsonify(message="Password must be at least 6 characters long"), 400

    # Check if user already exists
    if User.query.filter_by(username=username).first():
        return jsonify(message="Username already exists"), 409 # 409 Conflict

    # Create new user
    new_user = User(username=username)
    new_user.set_password(password) # Hashes the password

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify(message="User registered successfully", user_id=new_user.id), 201 # 201 Created
    except Exception as e:
        db.session.rollback() # Rollback in case of error
        # Log the error for debugging (in a real app, use proper logging)
        print(f"Error during registration: {e}")
        return jsonify(message="An error occurred during registration. Please try again."), 500

# NEW LOGIN ROUTE
@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json()

    if not data:
        return jsonify(message="No input data provided"), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify(message="Username and password are required"), 400

    # Find user by username
    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        # Login successful
        # TODO: In a real app, generate and return an authentication token (e.g., JWT) here
        return jsonify(message="Login successful", user_id=user.id, username=user.username), 200
    else:
        # Invalid credentials
        return jsonify(message="Invalid username or password"), 401 # 401 Unauthorized

# --- Helper function to create database tables ---
def create_db_tables(): # <-- ADDED helper function
    # Ensure the instance folder exists
    instance_folder_path = os.path.join(basedir, 'instance')
    if not os.path.exists(instance_folder_path):
        os.makedirs(instance_folder_path)
        print(f"Created instance folder at {instance_folder_path}")

    with app.app_context(): # Creates an application context for db operations
        db.create_all() # Creates database tables for all models defined
    print("Database tables created (if they didn't exist).")

# --- Main execution block ---
if __name__ == '__main__':
    # Call the function to create tables before running the app
    # This is okay for development. For production, you'd typically use migrations (e.g., Flask-Migrate).
    create_db_tables() # <-- ADDED call to create tables

    app.run(debug=True, port=5001)
