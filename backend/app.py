from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import logging

# Get the path to the directory this file is in
BASEDIR = os.path.abspath(os.path.dirname(__file__))

# Load environment variables from .env file in parent directory
load_dotenv(os.path.join(BASEDIR, '..', '.env'))

app = Flask(__name__, static_folder='../frontend/build', static_url_path='')
CORS(app)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')  # Make sure to add this to your .env file
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)  # Set the token to expire after 1 day

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    scores = db.relationship('Score', backref='user', lazy=True)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='user_date_uc'),)

@app.route('/api/login', methods=['POST'])
def login():
    logger.info('Received login request')
    data = request.json
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        access_token = create_access_token(identity=username)
        logger.info(f'User {username} logged in successfully')
        return jsonify(message='Logged in successfully', token=access_token), 200
    logger.info(f'Login failed for username: {username}')
    return jsonify(error='Invalid username or password'), 401

@app.route('/api/signup', methods=['POST'])
def signup():
    logger.info('Received signup request')
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if User.query.filter_by(username=username).first():
        logger.info(f'Signup failed: Username {username} already exists')
        return jsonify(error='Username already exists'), 400
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    logger.info(f'User {username} created successfully')
    return jsonify(message='User created successfully'), 201

@app.route('/api/submit_score', methods=['POST'])
@jwt_required()
def submit_score():
    logger.info('Received score submission request')
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    if not user:
        logger.error(f'User not found: {current_user}')
        return jsonify(error='User not found'), 404
    
    data = request.json
    date = data.get('date')
    score = data.get('score')
    
    if not date or not score:
        logger.error('Invalid score submission: Missing date or score')
        return jsonify(error='Date and score are required'), 400
    
    try:
        date = datetime.strptime(date, '%Y-%m-%d').date()
        score = int(score)
        if score < 1 or score > 10:
            raise ValueError('Score must be between 1 and 10')
    except ValueError as e:
        logger.error(f'Invalid score submission: {str(e)}')
        return jsonify(error=str(e)), 400

    existing_score = Score.query.filter_by(user_id=user.id, date=date).first()
    if existing_score:
        existing_score.score = score
    else:
        new_score = Score(user_id=user.id, date=date, score=score)
        db.session.add(new_score)
    
    db.session.commit()
    logger.info(f'Score submitted successfully for user {current_user} on {date}')
    return jsonify(message='Score submitted successfully'), 200

@app.route('/api/get_scores')
@jwt_required()
def get_scores():
    logger.info('Received request to get scores')
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    if not user:
        logger.error(f'User not found: {current_user}')
        return jsonify(error='User not found'), 404
    
    days = int(request.args.get('days', 365))
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)
    
    scores = Score.query.filter(Score.user_id == user.id, 
                                Score.date >= start_date,
                                Score.date <= end_date).all()
    
    score_data = [{'date': score.date.strftime('%Y-%m-%d'), 'score': score.score} for score in scores]
    logger.info(f'Retrieved {len(score_data)} scores for user {current_user}')
    return jsonify(score_data)

@app.route('/')
def serve():
    return send_from_directory(app.static_folder, 'index.html')

@app.errorhandler(404)
def not_found(e):
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/validate_token', methods=['GET'])
@jwt_required()
def validate_token():
    current_user = get_jwt_identity()
    return jsonify(username=current_user), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        users = User.query.all()
        logger.info(f"Existing users: {[user.username for user in users]}")
    app.run(debug=True)