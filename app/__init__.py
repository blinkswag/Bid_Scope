from flask import Flask, request, render_template, jsonify
from flask_session import Session
import os
from datetime import timedelta
from dotenv import load_dotenv
from .db import Database
import logging

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

def get_remote_address():
    # Check for the 'X-Forwarded-For' header
    if request.headers.get('X-Forwarded-For'):
        # Use the first IP in the 'X-Forwarded-For' header
        return request.headers.get('X-Forwarded-For').split(',')[0]
    else:
        # Fallback to the default remote address
        return request.remote_addr

def limit_remote_addr():
    db = Database()  # Create a new instance of Database here
    allowed_ips = db.get_allowed_ips()
    client_ip = get_remote_address()
    logging.info(f"Client IP: {client_ip}")
    if client_ip not in allowed_ips:
        return render_template('403.html'), 403

def create_app():
    app = Flask(__name__)
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'supersecretkey')
    Session(app)

    # Add enumerate to Jinja environment globals
    app.jinja_env.globals.update(enumerate=enumerate)

    from .views import init_app
    init_app(app)

    # Logging configuration
    logging.basicConfig(level=logging.INFO)

    @app.before_request
    def limit_remote_addr():
        from flask import request, render_template
        from .db import Database

        db = Database()
        allowed_ips = [ip['ip_address'] for ip in db.get_all_ips()]
        client_ip = request.remote_addr
        logging.info(f"Client IP: {client_ip}")
        if client_ip not in allowed_ips:
            return render_template('403.html'), 403

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
