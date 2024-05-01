# app/views.py
from flask import render_template, request
from .controller.chat_controller import ChatController

chat_controller = ChatController()

def init_app(app):
    @app.route('/', methods=['GET', 'POST'])
    def index():
        if request.method == 'POST':
            message = request.form.get('message')
            file = request.files.get('file', None)
            print("Views 1 File")
            response = chat_controller.handle_message(file, message)
            return render_template('chat_response.html', response=response)
        return render_template('index.html')

    @app.route('/chat', methods=['POST'])
    def chat():
        message = request.form['message']
        file = request.files.get('file', None)
        print("Views 2 Chat")
        response = chat_controller.handle_message(file, message)
        return render_template('chat_response.html', response=response)
    @app.route('/continue_chat', methods=['POST'])
    def continue_chat():
        thread_id = request.form.get('thread_id')
        message = request.form.get('message')
        file = request.files.get('file', None)
        response = chat_controller.handle_message(file, message, thread_id)
        
        return render_template('chat_response.html', response=response)
