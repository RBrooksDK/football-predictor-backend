import os
from flask import Flask, jsonify, request # Keep jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

# <-- NEW IMPORTS FOR JWT (ALREADY PRESENT IN YOUR CODE, CONFIRMED) -->
from flask_jwt_extended import create_access_token
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from flask_jwt_extended import get_jwt_identity # To get user identity from token

load_dotenv()
app = Flask(__name__)
CORS(app)

# --- Configurations --- # Renamed from "Database Configuration" for clarity
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'predictions.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'a_super_secret_default_key_for_dev')

# <-- START JWT CONFIGURATION -->
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your_default_jwt_secret_key_here_CHANGE_ME') # IMPORTANT: Change default and use .env
jwt = JWTManager(app) # Initialize JWTManager
# <-- END JWT CONFIGURATION -->

db = SQLAlchemy(app)

# --- Database Models ---
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

# TODO: Add other models later: League, Team, Prediction, ActualStanding, UserScore

# --- API Routes ---
@app.route('/')
def index():
    # <-- MODIFIED message for clarity -->
    return jsonify(message="Welcome to the Football Predictor API! JWT Authentication enabled.")

@app.route('/api/hello') # This can remain an unprotected route
def hello_api():
    return jsonify(greeting="Hello from the API!", status="success")

# REGISTRATION ROUTE (No changes needed here for JWT setup itself)
@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json()

    if not data:
        return jsonify(message="No input data provided"), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify(message="Username and password are required"), 400

    if len(password) < 6:
        return jsonify(message="Password must be at least 6 characters long"), 400

    if User.query.filter_by(username=username).first():
        return jsonify(message="Username already exists"), 409

    new_user = User(username=username)
    new_user.set_password(password)

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify(message="User registered successfully", user_id=new_user.id), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error during registration: {e}")
        return jsonify(message="An error occurred during registration. Please try again."), 500

# LOGIN ROUTE
@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json()

    if not data:
        return jsonify(message="No input data provided"), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify(message="Username and password are required"), 400

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        # <-- START MODIFIED SECTION: Create and return JWT access token -->
        access_token = create_access_token(identity=str(user.id)) # Use user.id as the identity, cast to string
        return jsonify(message="Login successful", access_token=access_token, user_id=user.id, username=user.username), 200
        # <-- END MODIFIED SECTION -->
    else:
        return jsonify(message="Invalid username or password"), 401

# <-- START NEW PROTECTED ROUTE EXAMPLE -->
@app.route('/api/protected', methods=['GET'])
@jwt_required() # This decorator protects the route
def protected_route():
    current_user_id = get_jwt_identity() # Get the identity of the user from the token
    # You can now use current_user_id to fetch user details or perform actions specific to this user
    user = User.query.get(current_user_id) # Example: Fetching the user from DB
    if user:
        return jsonify(logged_in_as=user.username, user_id=user.id, message="Access granted to protected route!"), 200
    else:
        # This case should ideally not happen if the token identity is valid and refers to an existing user
        return jsonify(message="User not found (though token was valid)"), 404
# <-- END NEW PROTECTED ROUTE EXAMPLE -->


# --- Helper function to create database tables ---
def create_db_tables():
    instance_folder_path = os.path.join(basedir, 'instance')
    if not os.path.exists(instance_folder_path):
        os.makedirs(instance_folder_path)
        print(f"Created instance folder at {instance_folder_path}")

    with app.app_context():
        db.create_all()
    print("Database tables created (if they didn't exist).")

# --- Main execution block ---
if __name__ == '__main__':
    create_db_tables()
    app.run(debug=True, port=5001)
