from app.model.chat_model import ChatModel
import json
import time
from werkzeug.utils import secure_filename
from ..utils import remove_bracketed_content, validate_file
from flask import session
from app.db import Database

db = Database()

class ChatController:
    def __init__(self):
        self.chat_model = ChatModel()

    def handle_message(self, files, message, thread_id=None):
        response = {"messages": [], "thread_id": thread_id, "user_message": "", "bot_response": ""}
        try:
            if not thread_id:
                thread = self.chat_model.create_thread()
                response['thread_id'] = thread.id

                # Store the new thread ID in the user's record
                user_id = session.get('user_id')
                db.update_user_threads(user_id, thread.id)
            else:
                response['thread_id'] = thread_id

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
                response['messages'].extend(file_statuses)

            if message:
                self.chat_model.send_message(response['thread_id'], message)

                run = self.chat_model.create_run(response['thread_id'])

                run_ret = self.chat_model.retrieve_run(response['thread_id'], run.id)
                run_ret = json.loads(run_ret.model_dump_json())

                while run_ret['status'] != 'completed':
                    time.sleep(3)
                    run_ret = self.chat_model.retrieve_run(response['thread_id'], run.id)
                    run_ret = json.loads(run_ret.model_dump_json())

                if run_ret['status'] == 'completed':
                    bot_resp = self.chat_model.get_messages(response['thread_id'])

                    response['bot_response'] = bot_resp
                else:
                    response['messages'].append("Error: Timeout or failed run.")

        except Exception as e:
            response['messages'].append(f"An error occurred: {str(e)}")
            print("Error handling message:", e)

        return response