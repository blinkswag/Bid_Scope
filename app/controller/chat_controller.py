from app.model.chat_model import ChatModel
import json
import time

class ChatController:
    def __init__(self):
        self.chat_model = ChatModel()

    def handle_message(self, file, message):
        response = {"messages": []}
        try:
            if file:
                file_status = self.chat_model.upload_file(file)  
                response['messages'].append(f"File upload status: {file_status}")
            else:
                response['messages'].append("No file provided.")

            thread = self.chat_model.create_thread()

            self.chat_model.send_message(thread.id, message)
            run = self.chat_model.create_run(thread.id)
            run_ret = self.chat_model.retrieve_run(thread.id,run.id)
            run_ret = json.loads(run_ret.model_dump_json())

            while run_ret['status'] != 'completed':
                time.sleep(5)
                run_ret = self.chat_model.retrieve_run(thread.id,run.id)
                run_ret = json.loads(run_ret.json())
                print("Status",run_ret['status'])

            if run_ret['status'] == 'completed':
                print("its in")
                responses = self.chat_model.get_messages(thread.id)
                response['messages'].extend(responses)
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