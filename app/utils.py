# app/utils.py
import re
from flask import redirect, url_for, session
from functools import wraps
from .db import Database

db = Database()
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
MAX_CONTENT_LENGTH = 32 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file(file):
    if not allowed_file(file.filename):
        return False, f'File type not allowed: {file.filename}'
    if file.content_length > MAX_CONTENT_LENGTH:
        return False, f'File too large: {file.filename} (max allowed is {MAX_CONTENT_LENGTH / (1024 * 1024)} MB)'
    return True, ''

def remove_bracketed_content(text):
    pattern = r"【.*?】"
    cleaned_text = re.sub(pattern, '', text)
    return cleaned_text

def check_user_role(required_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'email' not in session:
                return redirect(url_for('login'))
            user = db.users_collection.find_one({"Email": session['email']})
            if not user or user.get('role') not in required_roles:
                return redirect(url_for('unauthorized'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def user_can_edit(target_user_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_email = session.get('email')
            if not user_email:
                return redirect(url_for('login'))
            current_user = db.users_collection.find_one({"Email": user_email})
            if not current_user:
                return redirect(url_for('unauthorized'))
            current_role = current_user.get('role')
            if current_role == 'Admin' and target_user_role in ['Super Admin', 'Admin']:
                return redirect(url_for('unauthorized'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
