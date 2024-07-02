# app/__init__.py

from flask import Flask, request, render_template, session
from flask_session import Session
import os
from datetime import timedelta
from dotenv import load_dotenv
from .db import Database
from .token_manager import ZohoDeskTokenManager
import logging

load_dotenv()

def get_remote_address():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    else:
        return request.remote_addr

def create_app():
    app = Flask(__name__)
    db = Database()
    token_manager = ZohoDeskTokenManager(db.db)

    @app.before_request
    def limit_remote_addr():
        allowed_ips = db.get_allowed_ips()
        client_ip = get_remote_address()
        logging.info(f"Client IP: {client_ip}")
        if client_ip not in allowed_ips:
            return render_template('403.html'), 403

    app.jinja_env.globals.update(enumerate=enumerate)

    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'supersecretkey')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    Session(app)

    from .views import init_app
    init_app(app, token_manager)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
