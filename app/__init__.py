# app/__init__.py
from flask import Flask, session
from flask_session import Session  # You might need to install this: pip install Flask-Session

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '00727903382703'  # Change to your actual secret key
    app.config['SESSION_TYPE'] = 'filesystem'
    Session(app)
    from .views import init_app
    init_app(app)
    return app
