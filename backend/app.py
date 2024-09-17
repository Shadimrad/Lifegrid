from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
# from models import db, User, Score
from datetime import datetime, timedelta


# Get the path to the directory this file is in
BASEDIR = os.path.abspath(os.path.dirname(__file__))

# Load environment variables from .env file in parent directory
load_dotenv(os.path.join(BASEDIR, '..', '.env'))


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@app.route('/')
def home():
    return "Welcome to the Flask Auth App! <a href='/login'>Login</a> | <a href='/signup'>Sign Up</a>"


class User(UserMixin, db.Model):
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


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/submit_score', methods=['POST'])
@login_required
def submit_score():
    date = request.form.get('date')
    score = request.form.get('score')
    
    if not date or not score:
        return jsonify({'error': 'Date and score are required'}), 400
    
    try:
        date = datetime.strptime(date, '%Y-%m-%d').date()
        score = int(score)
        if score < 1 or score > 10:
            raise ValueError('Score must be between 1 and 10')
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    existing_score = Score.query.filter_by(user_id=current_user.id, date=date).first()
    if existing_score:
        existing_score.score = score
    else:
        new_score = Score(user_id=current_user.id, date=date, score=score)
        db.session.add(new_score)
    
    db.session.commit()
    return jsonify({'message': 'Score submitted successfully'}), 200

@app.route('/dashboard')
@login_required
def dashboard():
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=365)  # Get scores for the last year
    scores = Score.query.filter(Score.user_id == current_user.id, 
                                Score.date >= start_date).all()
    
    score_data = {score.date.strftime('%Y-%m-%d'): score.score for score in scores}
    
    return render_template('dashboard.html', score_data=score_data)

@app.route('/get_scores')
@login_required
def get_scores():
    days = int(request.args.get('days', 30))
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)
    
    scores = Score.query.filter(Score.user_id == current_user.id, 
                                Score.date >= start_date,
                                Score.date <= end_date).all()
    
    score_data = [{'date': score.date.strftime('%Y-%m-%d'), 'score': score.score} for score in scores]
    return jsonify(score_data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)