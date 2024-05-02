import os
from openai import OpenAI
from dotenv import load_dotenv
import json
from io import BytesIO

load_dotenv()

class ChatModel:
    def __init__(self):
        self.api_key = os.getenv('API_KEY')
        self.vector_store_id = os.getenv('VS_ID')
        self.assistant_id = os.getenv('ASSISTANT_ID')
        self.client = OpenAI(api_key=self.api_key)

    def upload_file(self, file_storage):
        try:
            file_bytes = file_storage.read()
            file_storage.seek(0)  
            file_like_object = BytesIO(file_bytes)
            file_like_object.name = file_storage.filename
            pdf = self.client.files.create(file=file_like_object, purpose="assistants")
            print(pdf.id)
            file_status = self.client.beta.vector_stores.files.create_and_poll(vector_store_id=self.vector_store_id, file_id=pdf.id).status
            self.client.beta.assistants.update(
                assistant_id=self.assistant_id,
                tool_resources={"file_search": {"vector_store_ids": [self.vector_store_id]}}
            )
            return f"File upload and indexing status: {file_status}"
        except Exception as e:
            print(f"Failed to upload file: {e}")
            return str(e)
            

    def create_thread(self):
        thread = self.client.beta.threads.create(
            tool_resources={
                "file_search": {
                    "vector_store_ids": [self.vector_store_id]
                }
            }
        )
        return thread

    def send_message(self, thread_id, message):
        self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )
    

    def create_run(self, thread_id):
      run = self.client.beta.threads.runs.create(
          thread_id=thread_id,
          assistant_id=self.assistant_id,
      )
      return run
    
    def retrieve_run(self, thread_id,run_id):
        run = self.client.beta.threads.runs.retrieve(
          thread_id=thread_id,
          run_id=run_id
        )
        return run

    def get_messages(self, thread_id):
      response = self.client.beta.threads.messages.list(
          thread_id=thread_id
      )
      parsed_data = json.loads(response.model_dump_json())
      content_values = [message['content'][0]['text']['value'] for message in parsed_data['data']]
      content_values.reverse()
    #   content_values = parsed_data['data'][0]['content'][0]['text']['value']
      return content_values[-2:]

