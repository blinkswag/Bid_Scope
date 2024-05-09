from flask import render_template, request, jsonify
from .controller.chat_controller import ChatController
import markdown
import re  # Import the regular expressions library

chat_controller = ChatController()

def remove_bracketed_content(text):
    pattern = r"【[^】]*】"
    cleaned_text = re.sub(pattern, '', text)
    return cleaned_text

def init_app(app):
    @app.route('/', methods=['GET', 'POST'])
    def index():
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

                # if response['bot_response']:
                #     formatted_response += f'<div class="message bot-response">{format_message_markdown(response["bot_response"])}</div>'

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
