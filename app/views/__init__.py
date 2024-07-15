# app/views.py

from flask import Flask
from app.views.auth import init_auth_views
from app.views.user import init_user_views
from app.views.chat import init_chat_views
from app.views.error import init_error_views
from app.views.bot_settings import init_bot_settings_views
from app.views.zoho import init_zoho_views

def init_app(app, token_manager):
    init_auth_views(app)
    init_user_views(app)
    init_chat_views(app)
    init_error_views(app)
    init_bot_settings_views(app)
    init_zoho_views(app, token_manager)
