from flask import Flask, render_template, redirect, url_for, request, flash, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import requests
import joblib
import urllib.parse
import os
import re  # Added for Hybrid Sanity Check

app = Flask(__name__)
app.config['SECRET_KEY'] = 'waf-admin-secure-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['INVITE_CODE'] = 'SHIELD-2026' 

db = SQLAlchemy(app)
model = joblib.load('model.pkl')
vectorizer = joblib.load('vectorizer.pkl')

TARGET_APP_URL = "http://127.0.0.1:5001"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class RequestLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(50), nullable=False)
    payload = db.Column(db.Text, nullable=False)
    result = db.Column(db.String(20), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class BlacklistIP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(50), unique=True, nullable=False)
    ban_time = db.Column(db.DateTime, default=datetime.utcnow)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id): 
    # Updated for SQLAlchemy 2.0 compatibility
    return db.session.get(User, int(user_id))

# --- THE ACTIVE SHIELD ---
@app.route('/proxy', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/proxy/<path:path>', methods=['GET', 'POST'])
def reverse_proxy(path):
    client_ip = request.remote_addr

    if BlacklistIP.query.filter_by(ip_address=client_ip).first():
        return "<h1 style='color:red; text-align:center; margin-top:50px;'>⛔ 403 FORBIDDEN</h1><p style='text-align:center;'>Your IP Address has been permanently banned by ShieldAI.</p>", 403

    # Extract the Payload (Supports both URL params and Form Submissions)
    payload = ""
    if request.method == 'GET':
        payload = urllib.parse.unquote(request.query_string.decode('utf-8'))
    elif request.method == 'POST':
        # Get the raw body of the POST request
        payload = urllib.parse.unquote(request.get_data(as_text=True))

    if payload and len(payload) > 2:
        # HYBRID SANITY CHECK: Pure alphanumeric/spaces bypass the heavy AI
        if re.match(r'^[a-zA-Z0-9\s]+$', payload):
            prediction = 0 # Force Benign
            confidence = 99.9
        else:
            vect = vectorizer.transform([payload])
            prediction = model.predict(vect)[0]
            prob = model.predict_proba(vect)[0]
            confidence = round(max(prob) * 100, 2)
        
        result_text = "MALICIOUS" if prediction == 1 else "BENIGN"
        new_log = RequestLog(ip_address=client_ip, payload=payload, result=result_text, confidence=confidence)
        db.session.add(new_log)
        db.session.commit()

        if prediction == 1:
            malicious_count = RequestLog.query.filter_by(ip_address=client_ip, result="MALICIOUS").count()
            if malicious_count >= 3:
                new_ban = BlacklistIP(ip_address=client_ip)
                db.session.add(new_ban)
                db.session.commit()
                return "<h1 style='color:red; text-align:center; margin-top:50px;'>⛔ CRITICAL THREAT DETECTED</h1><p style='text-align:center;'>ShieldAI has permanently banned your IP.</p>", 403
            return f"<h1 style='color:orange; text-align:center; margin-top:50px;'>⚠️ 406 NOT ACCEPTABLE</h1><p style='text-align:center;'>ShieldAI blocked this request. Malicious intent detected. Warning {malicious_count}/3.</p>", 406

    target_url = f"{TARGET_APP_URL}/{path}"
    resp = requests.request(
        method=request.method,
        url=target_url,
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(), # Pass the form data to the dummy app
        allow_redirects=False
    )
    headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in ['content-encoding', 'transfer-encoding']]
    return Response(resp.content, resp.status_code, headers)

# --- UNBAN ROUTE ---
@app.route('/unblock/<ip>', methods=['POST'])
@login_required
def unblock(ip):
    ban_record = BlacklistIP.query.filter_by(ip_address=ip).first()
    if ban_record:
        db.session.delete(ban_record)
        # Wipe their malicious history so they start at 0 strikes
        RequestLog.query.filter_by(ip_address=ip, result="MALICIOUS").delete()
        db.session.commit()
        flash(f'IP {ip} has been unblocked.', 'success')
    return redirect(url_for('dashboard'))

# --- DASHBOARD & AUTH ---
@app.route('/')
def index(): 
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        if request.form.get('invite_code') != app.config['INVITE_CODE']:
            flash('Registration Denied: Invalid Admin Invite Code.', 'error')
            return redirect(url_for('signup'))
        hashed_pw = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        new_user = User(username=request.form['username'], password=hashed_pw)
        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        except:
            flash('Username already exists.', 'error')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid Access Credentials', 'error')
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    result = None
    confidence = None
    payload = ""
    
    # Restored manual form inspection logic
    if request.method == 'POST':
        payload = request.form.get('payload', '')
        if payload and len(payload) > 2:
            # HYBRID SANITY CHECK
            if re.match(r'^[a-zA-Z0-9\s]+$', payload):
                result = "BENIGN"
                confidence = 99.9
            else:
                vect = vectorizer.transform([payload])
                prediction = model.predict(vect)[0]
                prob = model.predict_proba(vect)[0]
                result = "MALICIOUS" if prediction == 1 else "BENIGN"
                confidence = round(max(prob) * 100, 2)

    recent_logs = RequestLog.query.order_by(RequestLog.timestamp.desc()).limit(10).all()
    banned_ips = BlacklistIP.query.all()
    
    return render_template('dashboard.html', logs=recent_logs, banned=banned_ips, 
                           result=result, confidence=confidence, payload=payload)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- STARTUP BLOCK ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(port=5000, debug=True)