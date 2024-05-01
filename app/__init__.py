# app/__init__.py
from flask import Flask

def create_app():
    app = Flask(__name__)
    from .views import init_app
    init_app(app)
    return app
