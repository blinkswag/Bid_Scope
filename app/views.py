# app/views.py
from flask import render_template, request, jsonify
from .controller.chat_controller import ChatController
import markdown

chat_controller = ChatController()

def init_app(app):
    @app.route('/', methods=['GET', 'POST'])
    def index():
        if request.method == 'POST':
            message = request.form.get('message')
            file = request.files.get('file', None)
            thread_id = request.form.get('thread_id', None)
            response = chat_controller.handle_message(file, message, thread_id)
            formatted_response = ''
            if message:
                formatted_response = ''
                for message in response['messages']:
                    formatted_response += f'<div class="message bot-response">{format_message_markdown(message)}</div>'

                if response['user_message']:
                    formatted_response += f'<div class="message user-message">{format_message_markdown(response["user_message"])}</div>'

                if response['bot_response']:
                    formatted_response += f'<div class="message bot-response">{format_message_markdown(response["bot_response"])}</div>'
            return jsonify({
                'message': formatted_response,
                'thread_id': response['thread_id']
            })
        return render_template('index.html')
    def format_message_markdown(message):
        html = markdown.markdown(message, extensions=['fenced_code', 'tables'])
        return html
