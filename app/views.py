# app/views.py
from flask import render_template, request, jsonify
from .controller.chat_controller import ChatController

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
                formatted_response += '<div class="message user-message">' + response['user_message'] + '</div>'
                formatted_response += '<div class="message bot-response">' + response['bot_response'] + '</div>'
            return jsonify({
                'message': formatted_response,
                'thread_id': response['thread_id']
            })
        return render_template('index.html')



# eturn render_template('chat_response.html', response=response)

# from flask import render_template, request, jsonify
# from .controller.chat_controller import ChatController

# chat_controller = ChatController()

# def init_app(app):
#     @app.route('/', methods=['GET', 'POST'])
#     def index():
#         if request.method == 'POST':
#             message = request.form.get('message')
#             file = request.files.get('file', None)
#             thread_id = request.form.get('thread_id', None)
#             response = chat_controller.handle_message(file, message, thread_id)
#             return jsonify({
#                 'message': '<br>'.join(response['messages']),
#                 'thread_id': response['thread_id']
#             })
#         return render_template('index.html')
