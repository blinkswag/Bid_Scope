# app/views/chat.py
from flask import render_template, request, jsonify, redirect, url_for, session
from app.controller.chat_controller import ChatController
import markdown
from app.db import Database
from app.utils.helpers import validate_file, remove_bracketed_content
import logging
from app.services.user_service import UserService
from app.model.chat_model import ChatModel  # Ensure ChatModel is imported
import re
from bson import ObjectId

logger = logging.getLogger(__name__)

db = Database()
chat_controller = ChatController()

def init_chat_views(app):
    @app.route('/', methods=['GET', 'POST'])
    def index():
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        
        user_id = session.get('user_id')
        threads = UserService.get_user_threads(user_id)
        # print("Threads to be passed to template:", threads)  # Debug statement

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
        return render_template('index.html', role=session.get('role'), username=session.get('username'), threads=threads)

    @app.route('/new-chat', methods=['POST'])
    def new_chat():
        try:
            user_id = session.get('user_id')
            chat_model = ChatModel(db=db)
            thread = chat_model.create_thread()
            db.update_user_threads(user_id, thread.id)
            session.pop('uploaded_file_name', None)
            logger.info(f"Created new thread {thread.id} for user {user_id}")
            return jsonify({'thread_id': thread.id})
        except Exception as e:
            logger.error(f"Failed to create new chat thread: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/rename-thread', methods=['POST'])
    def rename_thread():
        try:
            thread_id = request.form.get('thread_id')
            new_name = request.form.get('new_name')
            if not thread_id or not new_name:
                return jsonify({"success": False, "error": "Invalid input."}), 400
            
            result = db.threads_collection.update_one(
                {"thread_id": thread_id},
                {"$set": {"name": new_name}}
            )
            if result.modified_count == 0:
                raise Exception("Thread rename failed.")
            
            logger.info(f"Successfully renamed thread {thread_id} to {new_name}")
            return jsonify({"success": True})
        except Exception as e:
            logger.error(f"Failed to rename thread {thread_id}: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/delete-thread', methods=['POST'])
    def delete_thread():
        try:
            thread_id = request.form.get('thread_id')
            if not thread_id:
                return jsonify({"success": False, "error": "Invalid input."}), 400
            
            result = db.threads_collection.delete_one({"thread_id": thread_id})
            if result.deleted_count == 0:
                raise Exception("Thread delete failed.")
            
            # Also remove the thread ID from the user's threads
            user_id = session.get('user_id')
            UserService.remove_user_thread(user_id, thread_id)
            
            logger.info(f"Successfully deleted thread {thread_id}")
            return jsonify({"success": True})
        except Exception as e:
            logger.error(f"Failed to delete thread {thread_id}: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500

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
