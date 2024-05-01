from app.model.chat_model import ChatModel
import json
import time

class ChatController:
    def __init__(self):
        self.chat_model = ChatModel()

    def handle_message(self, file, message, thread_id=None):
        response = {"messages": [], "thread_id": thread_id}
        try:
            if not thread_id:
                # Create a new thread if no thread_id is provided
                thread = self.chat_model.create_thread()
                response['thread_id'] = thread.id
            else:
                # Use existing thread ID
                response['thread_id'] = thread_id

            if file:
                # Handle file upload and add status to response
                file_status = self.chat_model.upload_file(file)  
                response['messages'].append(f"File upload status: {file_status}")
            else:
                response['messages'].append("No file provided.")

            # Send the user message to the existing or new thread
            self.chat_model.send_message(response['thread_id'], message)
            
            # Start processing the message
            run = self.chat_model.create_run(response['thread_id'])
            
            # Retrieve run results, ensuring the run is completed
            run_ret = self.chat_model.retrieve_run(response['thread_id'], run.id)
            run_ret = json.loads(run_ret.model_dump_json())

            while run_ret['status'] != 'completed':
                time.sleep(5)
                run_ret = self.chat_model.retrieve_run(response['thread_id'], run.id)
                run_ret = json.loads(run_ret.model_dump_json())

            if run_ret['status'] == 'completed':
                # Fetch all messages from the thread once the run is complete
                responses = self.chat_model.get_messages(response['thread_id'])
                response['messages'].extend(responses)
            else:
                response['messages'].append("Error: Timeout or failed run.")
        
        except Exception as e:
            response['messages'].append(f"An error occurred: {str(e)}")
            print("Error handling message:", e)

        return response

    def format_message_data(self, messages):
        # Optional: format the chat data into a more readable format if needed
        conversation = []
        for message in messages:
            conversation.append(message['content']['text']['value'])
        return conversation[::-1]  # Return messages in the order they were sent

