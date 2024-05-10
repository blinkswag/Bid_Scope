from flask import render_template, request, jsonify, redirect, url_for, session
from .controller.chat_controller import ChatController
import markdown
import re  # Import the regular expressions library
import os
import json
from dotenv import load_dotenv



chat_controller = ChatController()

users={"0": {"Email": "shahrukh@blinkswag.com", "Password": "basecamp@123", "role": "Admin"},
       "1": {"Email": "shahrukh.aleem@basecampdata.com", "Password": "Test@123", "role": "User"},
       "2": {"Email": "Alee@blinkswag.com", "Password": "blink@123", "role": "Admin"}}

def check_user_credentials(email, password):
    for user_id, details in users.items():
        if details['Email'] == email and details['Password'] == password:
            return True
    return False

def remove_bracketed_content(text):
    pattern = r"【[^】]*】"
    cleaned_text = re.sub(pattern, '', text)
    return cleaned_text


def init_app(app):
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['username']
            password = request.form['password']
            if check_user_credentials(email, password):
                # Send successful login state and email as JSON
                return jsonify({'success': True, 'email': email})
            else:
                return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        return render_template('login.html')

    @app.route('/', methods=['GET', 'POST'])
    def index():
        # if not session.get('logged_in'):
        #     return redirect(url_for('login'))

        if request.method == 'POST':
            message = request.form.get('message')
            files = request.files.getlist('file')  # Change here to get multiple files
            thread_id = request.form.get('thread_id', None)
            response = chat_controller.handle_message(files, message, thread_id)  # Pass the list of files
            formatted_response = ''
            if message:
                formatted_response = ''
                for msg in response['messages']:  # Avoid using 'message' as variable name here, it's used above
                    formatted_response += f'<div class="message bot-response">{format_message_markdown(msg)}</div>'

                if response['user_message']:
                    formatted_response += f'<div class="message user-message">{format_message_markdown(response["user_message"])}</div>'

                if response['bot_response']:
                    cleaned_bot_response = remove_bracketed_content(response['bot_response'])
                    formatted_response += f'<div class="message bot-response">{format_message_markdown(cleaned_bot_response)}</div>'

            return jsonify({
                'message': formatted_response,
                'thread_id': response['thread_id']
            })
        return render_template('index.html')
    
    def format_message_markdown(message):
        html = markdown.markdown(message, extensions=['fenced_code', 'tables'])
        return html
