from flask import Flask
from flask_session import Session
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'supersecretkey')  # Ensure a secure key
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Set session to expire after 7 days
    Session(app)

    # Add enumerate to Jinja environment globals
    app.jinja_env.globals.update(enumerate=enumerate)

    from .views import init_app
    init_app(app)

    return app
