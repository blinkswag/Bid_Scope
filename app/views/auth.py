# app/views/auth.py

from flask import render_template, request, jsonify, redirect, url_for, session, g
from app.services.auth_service import AuthService
from app.db import Database
import requests
import logging

logger = logging.getLogger(__name__)

db = Database()

def init_auth_views(app):

    def verify_recaptcha(response):
        secret_key = '6LdhOwAqAAAAAEl9dCDlm3J8Xy4mEN-2m0djQaRh'
        payload = {'secret': secret_key, 'response': response}
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=payload)
        return r.json()

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['username'].lower()
            password = request.form['password']
            recaptcha_response = request.form['g-recaptcha-response']

            recaptcha_result = verify_recaptcha(recaptcha_response)
            if not recaptcha_result.get('success'):
                return jsonify({'success': False, 'error': 'Invalid reCAPTCHA. Please try again.'}), 400

            if not email or not password:
                return jsonify({'success': False, 'error': 'Email and password are required'}), 400
            if AuthService.check_user_credentials(email, password):
                user = db.users_collection.find_one({"Email": email})
                session['email'] = email
                session['logged_in'] = True
                session['role'] = user['role']
                session['username'] = user['Username']
                session['user_id'] = str(user['_id'])
                print("User session data:", session)  # Debug statement
                return jsonify({'success': True, 'email': email})
            else:
                return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

