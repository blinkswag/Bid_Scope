from flask import render_template, request, jsonify, redirect, url_for, session, g
from .controller.chat_controller import ChatController
import markdown
from .db import Database
from .utils import validate_file, remove_bracketed_content, check_user_role
from .validation import validate_password
import bcrypt
from openai import OpenAI
import os
import re
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

db = Database()
chat_controller = ChatController()
client = OpenAI(api_key=os.getenv('API_KEY'))
ASSISTANT_ID = os.getenv('ASSISTANT_ID')

def init_app(app, token_manager):
    @app.before_request
    def load_logged_in_user():
        user_email = session.get('email')
        if user_email is None:
            g.user = None
        else:
            g.user = db.users_collection.find_one({"Email": user_email.lower()})

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
            if db.check_user_credentials(email, password):
                user = db.users_collection.find_one({"Email": email})
                session['email'] = email
                session['logged_in'] = True
                session['role'] = user['role']
                session['username'] = user['Username']
                session['user_id'] = str(user['_id'])
                return jsonify({'success': True, 'email': email})
            else:
                return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

    @app.route('/', methods=['GET', 'POST'])
    def index():
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        
        user_id = session.get('user_id')
        thread_ids = db.get_user_threads(user_id)

        if request.method == 'POST':
            message = request.form.get('message')
            files = request.files.getlist('file')
            thread_id = request.form.get('thread_id', None)
            if not message and not files:
                return jsonify({'error': 'No message or file provided'}), 400
            if files:
                for file in files:
                    valid, error = validate_file(file)
                    if not valid:
                        return jsonify({'error': error}), 400
            response = chat_controller.handle_message(files, message, thread_id)
            if "error" in response['messages']:
                return jsonify({'error': response['messages']}), 400
            
            formatted_response = ''
            if message:
                formatted_response = ''
                for msg in response['messages']:
                    formatted_response += f'<div class="message bot-response">{format_message_markdown(msg)}</div>'
                if response['user_message']:
                    formatted_response += f'<div class="message user-message">{format_message_markdown(response["user_message"])}</div>'
                if response['bot_response']:
                    cleaned_bot_response = remove_bracketed_content(response['bot_response'])
                    formatted_response += f'<div class="message bot-response">{format_message_markdown(cleaned_bot_response)}</div>'
            return jsonify({'message': formatted_response, 'thread_id': response['thread_id']})
        return render_template('index.html', role=session.get('role'), username=session.get('username'), thread_ids=thread_ids)

    @app.route('/edit-profile', methods=['GET', 'POST'])
    def edit_profile():
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        current_user_email = session.get('email')
        user = db.users_collection.find_one({"Email": current_user_email})
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            updates = {"Username": username, "Email": email}
            if password:
                valid, message = validate_password(password)
                if not valid:
                    error_messages = [message]
                    return render_template('edit_profile.html', user=user, error_messages=error_messages)
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                updates["Password"] = hashed_password
            result = db.users_collection.update_one({"Email": current_user_email}, {"$set": updates})
            if result.modified_count > 0:
                session['email'] = email
                session['username'] = username
                return redirect('/')
            else:
                error_messages = ["Error updating profile"]
                return render_template('edit_profile.html', user=user, error_messages=error_messages)
        return render_template('edit_profile.html', user=user)

    @app.route('/manage-users')
    @check_user_role(['Super Admin', 'Admin'])
    def manage_users():
        current_user_email = session.get('email')
        users = list(db.get_all_users())
        filtered_users = [user for user in users if user['Email'] != current_user_email]
        ips = list(db.get_all_ips())
        return render_template('manage_users.html', users=filtered_users, role=session.get('role'), ips=ips)

    @app.route('/add-user', methods=['POST'])
    @check_user_role(['Super Admin', 'Admin'])
    def add_user():
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        result = db.add_user(username, email, password, role)
        error_messages = []
        if result == "username_exists":
            error_messages.append("Username already exists")
        if result == "email_exists":
            error_messages.append("Email already exists")
        if result == "user_added":
            return redirect('/manage-users')
        else:
            current_user_email = session.get('email')
            users = list(db.get_all_users())
            filtered_users = [user for user in users if user['Email'] != current_user_email]
            ips = list(db.get_all_ips())
            return render_template('manage_users.html', users=filtered_users, ips=ips, error_messages=error_messages, role=session.get('role'))

    @app.route('/edit-user/<user_id>', methods=['POST'])
    @check_user_role(['Super Admin', 'Admin'])
    def edit_user(user_id):
        user_to_edit = db.get_user_by_id(user_id)
        if not user_to_edit:
            return redirect(url_for('page_not_found'))
        target_user_role = user_to_edit.get('role')
        current_user_role = session.get('role')
        if current_user_role == 'Admin' and target_user_role in ['Super Admin', 'Admin']:
            return redirect(url_for('unauthorized'))
        username = request.form['username']
        email = request.form['email']
        role = request.form['role']
        password = request.form.get('password', None)
        result = db.update_user(user_id, username, email, role, password)
        if result == True or result == False:
            return redirect('/manage-users')
        else:
            error_messages = [result]
            current_user_email = session.get('email')
            users = list(db.get_all_users())
            filtered_users = [user for user in users if user['Email'] != current_user_email]
            ips = list(db.get_all_ips())
            return render_template('manage_users.html', users=filtered_users, ips=ips, error_messages=error_messages, role=session.get('role'))

    @app.route('/delete-user/<user_id>', methods=['POST'])
    @check_user_role(['Super Admin', 'Admin'])
    def delete_user(user_id):
        user_to_delete = db.get_user_by_id(user_id)
        if not user_to_delete:
            return redirect(url_for('page_not_found'))
        target_user_role = user_to_delete.get('role')
        current_user_role = session.get('role')
        
        if current_user_role == 'Admin' and target_user_role == 'Super Admin':
            return redirect(url_for('unauthorized'))
            
        if db.delete_user(user_id):
            return redirect('/manage-users')
        else:
            return "Error deleting user", 400

    @app.route('/add-ip', methods=['POST'])
    @check_user_role(['Super Admin', 'Admin'])
    def add_ip():
        ip_address = request.form['ip_address']
        tag = request.form['tag']
        result = db.add_ip(ip_address, tag)
        if result == "ip_exists":
            return redirect(url_for('manage_users', error_messages=["IP address already exists"]))
        return redirect(url_for('manage_users'))

    @app.route('/delete-ip/<ip_id>', methods=['POST'])
    @check_user_role(['Super Admin', 'Admin'])
    def delete_ip(ip_id):
        db.delete_ip(ip_id)
        return redirect(url_for('manage_users'))

    @app.route('/bot-settings', methods=['GET', 'POST'])
    @check_user_role(['Super Admin'])
    def bot_settings():
        if request.method == 'POST':
            update_data = {}
            if 'name' in request.form:
                update_data['name'] = request.form['name']
            if 'description' in request.form:
                update_data['description'] = request.form['description']
            if 'instructions' in request.form:
                update_data['instructions'] = request.form['instructions']
            if 'model' in request.form:
                update_data['model'] = request.form['model']
            if 'temperature' in request.form:
                update_data['temperature'] = float(request.form['temperature'])
            
            try:
                client.beta.assistants.update(ASSISTANT_ID, **update_data)
                return redirect(url_for('bot_settings'))
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        my_assistant = client.beta.assistants.retrieve(ASSISTANT_ID)
        return render_template('bot_settings.html', assistant=my_assistant)

    @app.errorhandler(401)
    def unauthorized(error):
        return render_template('401.html'), 401

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('403.html'), 403

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template('500.html'), 500

    @app.route('/unauthorized')
    def unauthorized():
        return render_template('401.html'), 401

    @app.route('/get-thread-messages', methods=['GET'])
    def get_thread_messages():
        thread_id = request.args.get('thread_id')
        if not thread_id:
            return jsonify({'error': 'Thread ID is required'}), 400
        
        try:
            messages = chat_controller.chat_model.get_threads_messages(thread_id)
            messages.reverse()
            response_messages = []
            file_prefix_pattern = re.compile(r"From the file .*?:\s*")
            for message in messages:
                formatted_content = remove_bracketed_content(message['content'][0]['text']['value'])
                formatted_content = file_prefix_pattern.sub("", formatted_content)
                response_messages.append({
                    'role': message['role'],
                    'content': format_message_markdown(formatted_content)
                })
            return jsonify({'messages': response_messages})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    def format_message_markdown(message):
        html = markdown.markdown(message, extensions=['fenced_code', 'tables'])
        return html

    @app.route('/new-chat', methods=['POST'])
    def new_chat():
        thread = chat_controller.chat_model.create_thread()
        user_id = session.get('user_id')
        db.update_user_threads(user_id, thread.id)
        session.pop('uploaded_file_name', None)
        return jsonify({'thread_id': thread.id})
    
    # Zoho Desk
    @app.route('/get_ticket_details', methods=['POST'])
    def get_ticket_details():
        data = request.get_json()
        ticket_id = data.get('ticket_id')

        if not ticket_id:
            return jsonify({'error': 'Ticket ID is required'}), 400

        try:
            access_token = token_manager.get_access_token()
            logger.debug(f"Using access token: {access_token}")

            # Fetch ticket details
            ticket_response = requests.get(
                f'https://desk.zoho.com/api/v1/tickets/{ticket_id}',
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                }
            )

            if ticket_response.ok:
                ticket_details = ticket_response.json()
                logger.debug(f"Ticket details fetched: {ticket_details}")
                return jsonify(ticket_details)
            else:
                logger.error(f"Failed to fetch ticket details: {ticket_response.text}")
                return jsonify({'error': 'Failed to fetch ticket details'}), 500

        except Exception as e:
            logger.error(f"Exception occurred while fetching ticket details: {str(e)}")
            return jsonify({'error': str(e)}), 500
        
    @app.route('/add_comment_to_ticket', methods=['POST'])
    def add_comment_to_ticket():
        data = request.get_json()
        ticket_id = data.get('ticket_id')
        comment = data.get('comment')

        try:
            access_token = token_manager.get_access_token()

            url = f"https://desk.zoho.com/api/v1/tickets/{ticket_id}/comments"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            comment_data = {
                'content': comment
            }
            response = requests.post(url, headers=headers, json=comment_data)
            return jsonify(response.json())
        except Exception as e:
            return jsonify({'error': str(e)}), 500