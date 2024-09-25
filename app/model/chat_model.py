import os
from openai import OpenAI
from dotenv import load_dotenv
import json
from io import BytesIO
from app.db import Database  # Import Database class
import logging
logger = logging.getLogger(__name__)

load_dotenv()

class ChatModel:
    def __init__(self, db=None):
        self.api_key = os.getenv('API_KEY')
        self.vector_store_id = os.getenv('VS_ID')
        self.assistant_id = os.getenv('ASSISTANT_ID')
        self.client = OpenAI(api_key=self.api_key)
        self.db = db or Database()  # Initialize db if not provided

    def upload_file(self, file_storage):
        try:
            file_bytes = file_storage.read()
            file_storage.seek(0)
            file_like_object = BytesIO(file_bytes)
            file_like_object.name = file_storage.filename
            
            # Step 1: Upload the file
            pdf = self.client.files.create(file=file_like_object, purpose="assistants")
            file_id = pdf.id
            
            # Step 2: Poll the vector database for file upload status
            file_status = self.client.beta.vector_stores.files.create_and_poll(
                vector_store_id=self.vector_store_id, file_id=file_id
            ).status
            
            if file_status != "completed":
                return f"Failed to upload file '{file_like_object.name}' to vector database. Status: {file_status}"

            # Step 3: Check the file status using the list method
            vs_files = self.client.beta.vector_stores.files.list(vector_store_id=self.vector_store_id)
            result = self.check_file_status(vs_files.data, file_id)
            return result  # This will return a message indicating the status of the file.

        except Exception as e:
            print(f"Failed to upload file: {e}")
            return str(e)

    # Utility function to check the file status and log any errors
    def check_file_status(self, vs_files, file_id):
        for file in vs_files:
            if file.id == file_id:
                if file.status == 'completed':
                    return f"File {file_id} uploaded successfully to vector database and processing is complete."
                elif file.status == 'failed':
                    # Check for errors if the status is failed
                    error_message = file.last_error.message if file.last_error else "Unknown error."
                    return f"File {file_id} failed to upload. Error: {error_message}."
                else:
                    return f"File {file_id} status is: {file.status} (processing)."
        return f"File {file_id} not found."

    def create_thread(self, name=None):
        try:
            thread = self.client.beta.threads.create(
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [self.vector_store_id]
                    }
                }
            )
            thread_name = name if name else f'Thread {thread.id}'
            # Log thread creation
            logger.info(f"Created thread with ID: {thread.id} and name: {thread_name}")
            # Store the thread details in the database with a separate field for thread_id
            result = self.db.threads_collection.update_one(
                {"thread_id": thread.id},
                {"$set": {"name": thread_name, "thread_id": thread.id}},
                upsert=True
            )
            # Log database insertion
            logger.info(f"Thread stored in database: {result.upserted_id if result.upserted_id else 'Existing thread updated'}")
            return thread
        except Exception as e:
            logger.error(f"Failed to create thread: {e}")
            raise e

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

    def retrieve_run(self, thread_id, run_id):
        run = self.client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        )
        return run

    def get_messages(self, thread_id):
        response = self.client.beta.threads.messages.list(thread_id=thread_id)
        parsed_data = json.loads(response.model_dump_json())
        content_values = [message['content'][0]['text']['value'] for message in parsed_data['data']]
        content_values.reverse()
        return content_values[-2:][1]

    def get_threads_messages(self, thread_id):
        response = self.client.beta.threads.messages.list(thread_id=thread_id)
        parsed_data = json.loads(response.model_dump_json())
        return parsed_data['data']
