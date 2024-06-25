# from flask import Flask
# from flask_session import Session
# import os
# from datetime import timedelta
# from dotenv import load_dotenv

# load_dotenv()

# def create_app():
#     app = Flask(__name__)
#     app.config['SESSION_TYPE'] = 'filesystem'
#     app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'supersecretkey')  # Ensure a secure key
#     app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Set session to expire after 7 days
#     Session(app)

#     # Add enumerate to Jinja environment globals
#     app.jinja_env.globals.update(enumerate=enumerate)

#     from .views import init_app
#     init_app(app)

#     return app
from flask import Flask, request, render_template, jsonify
from flask_session import Session
import os
from datetime import timedelta
from dotenv import load_dotenv
from .db import Database

load_dotenv()

def create_app():
    app = Flask(__name__)
    db = Database()

    @app.before_request
    def limit_remote_addr():
        allowed_ips = db.get_allowed_ips()
        if request.remote_addr not in allowed_ips:
            return render_template('403.html'), 403

    # Add enumerate to Jinja environment globals
    app.jinja_env.globals.update(enumerate=enumerate)

    # Your existing session and app configuration
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'supersecretkey')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    Session(app)

    # Initialize app views
    from .views import init_app
    init_app(app)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
