from app.model.chat_model import ChatModel
import json
import time

class ChatController:
    def __init__(self):
        self.chat_model = ChatModel()

    def handle_message(self, file, message, thread_id=None):
        response = {"messages": [], "thread_id": thread_id,"user_message": "", "bot_response": ""}
        try:
            file_uploaded = False
            if not thread_id:
                thread = self.chat_model.create_thread()
                response['thread_id'] = thread.id
            else:
                response['thread_id'] = thread_id

            if file:
                file_status = self.chat_model.upload_file(file)  
                response['messages'].append(f"File Uploaded: {file_status}")
                file_uploaded = True

            if message:
                self.chat_model.send_message(response['thread_id'], message)
            
                run = self.chat_model.create_run(response['thread_id'])

                run_ret = self.chat_model.retrieve_run(response['thread_id'], run.id)
                run_ret = json.loads(run_ret.model_dump_json())

                while run_ret['status'] != 'completed':
                    time.sleep(5)
                    run_ret = self.chat_model.retrieve_run(response['thread_id'], run.id)
                    run_ret = json.loads(run_ret.model_dump_json())

                if run_ret['status'] == 'completed':
                    bot_resp = self.chat_model.get_messages(response['thread_id'])
                    # if not file_uploaded:
                    #     response['user_message'] = user_msg
                    response['bot_response'] = bot_resp
                else:
                    response['messages'].append("Error: Timeout or failed run.")
            
        except Exception as e:
            response['messages'].append(f"An error occurred: {str(e)}")
            print("Error handling message:", e)

        return response

    def format_message_data(self, messages):

        conversation = []
        for message in messages:
            conversation.append(message['content']['text']['value'])
        return conversation[::-1]  

