from app.model.chat_model import ChatModel
import json
import time
from werkzeug.utils import secure_filename
from ..utils.file_utils import validate_file
from ..utils.helpers import remove_bracketed_content
from flask import session
from app.db import Database

db = Database()

# chat_controller.py
class ChatController:
    def __init__(self):
        self.chat_model = ChatModel()

    def handle_message(self, files, message, thread_id=None, thread_name=None):
        response = {"messages": [], "thread_id": thread_id, "user_message": "", "bot_response": ""}
        try:
            if not thread_id:
                if thread_name:
                    thread = self.chat_model.create_thread(name=thread_name)
                else:
                    thread = self.chat_model.create_thread()
                thread_id = thread.id
                response['thread_id'] = thread_id
            else:
                user_id = session.get('user_id')
                db.update_user_threads(user_id, thread_id)

            if files:
                file_statuses = []
                for file in files:
                    valid, error = validate_file(file)
                    if not valid:
                        response['messages'].append(error)
                        return response
                    filename = secure_filename(file.filename)
                    file_status = self.chat_model.upload_file(file)
                    file_statuses.append(f"{filename}: {file_status}")
                    session['uploaded_file_name'] = filename  # Store the uploaded file name in the session
                response['messages'].extend(file_statuses)

            if message:
                if 'uploaded_file_name' in session:
                    message = f'From the file {session["uploaded_file_name"]}: {message}'
                self.chat_model.send_message(thread_id, message)
                run = self.chat_model.create_run(thread_id)
                run_ret = self.chat_model.retrieve_run(thread_id, run.id)
                run_ret = json.loads(run_ret.model_dump_json())

                while run_ret['status'] != 'completed':
                    time.sleep(3)
                    run_ret = self.chat_model.retrieve_run(thread_id, run.id)
                    run_ret = json.loads(run_ret.model_dump_json())

                if run_ret['status'] == 'completed':
                    bot_resp = self.chat_model.get_messages(thread_id)
                    cleaned_bot_response = remove_bracketed_content(bot_resp)
                    response['bot_response'] = cleaned_bot_response
                else:
                    response['messages'].append("Error: Timeout or failed run.")

        except Exception as e:
            response['messages'].append(f"An error occurred: {str(e)}")
            print("Error handling message:", e)

        return response