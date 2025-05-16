from flask import Flask, request, render_template, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from twilio.rest import Client
import bcrypt
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Twilio configuration
twilio_client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')

# Email configuration
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(200), nullable=False)
    sent_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    responded = db.Column(db.Boolean, default=False)
    response_deadline = db.Column(db.DateTime, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def send_sms(phone_number, message):
    try:
        twilio_client.messages.create(
            body=message,
            from_=twilio_phone,
            to=phone_number
        )
        return True
    except Exception as e:
        print(f"SMS Error: {e}")
        return False

def send_email(to_email, subject, body):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_USERNAME
        msg['To'] = to_email

        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False

def check_response_deadline():
    with app.app_context():
        alerts = Alert.query.filter_by(responded=False).all()
        for alert in alerts:
            if datetime.utcnow() >= alert.response_deadline:
                user = User.query.get(alert.user_id)
                send_email(
                    user.email,
                    "Alert Response Overdue",
                    f"You have not responded to the alert sent at {alert.sent_at}"
                )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and bcrypt.checkpw(request.form['password'].encode('utf-8'), user.password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_password = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
        user = User(
            username=request.form['username'],
            password=hashed_password,
            phone_number=request.form['phone_number'],
            email=request.form['email']
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    alerts = Alert.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', alerts=alerts)

@app.route('/create_alert', methods=['GET', 'POST'])
@login_required
def create_alert():
    if request.method == 'POST':
        message = request.form['message']
        response_time = int(request.form['response_time'])  # in minutes
        
        alert = Alert(
            user_id=current_user.id,
            message=message,
            response_deadline=datetime.utcnow() + timedelta(minutes=response_time)
        )
        
        if send_sms(current_user.phone_number, message):
            db.session.add(alert)
            db.session.commit()
            flash('Alert created successfully')
        else:
            flash('Failed to send SMS')
            
    return render_template('create_alert.html')

@app.route('/respond/<int:alert_id>', methods=['POST'])
@login_required
def respond_to_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    if alert.user_id == current_user.id:
        alert.responded = True
        db.session.commit()
        flash('Response recorded')
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Schedule the response checker to run every minute
    scheduler.add_job(check_response_deadline, 'interval', minutes=1)
    
    app.run(host='0.0.0.0', port=5000) 