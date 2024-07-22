import certifi
import pymongo
from bson import ObjectId
import bcrypt
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

class Database:
    def __init__(self):
        connection_string = os.getenv('mongo_srv')
        client = pymongo.MongoClient(connection_string, tlsCAFile=certifi.where())
        try:
            client.server_info()
            self.db = client.Bid
            self.users_collection = self.db.Users
            self.threads_collection = self.db.Threads
            self.ips_collection = self.db.IP
            self.bid_records_collection = self.db.Bid_records
            self.counter_collection = self.db.counter
        except Exception as e:
            print(f"Failed to connect to the database: {e}")
            raise e

    def check_user_credentials(self, email, password):
        email = email.lower()
        user = self.users_collection.find_one({"Email": email})
        if user:
            stored_password = user['Password']
            if isinstance(stored_password, str):
                stored_password = stored_password.encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                return True
        return False

    def update_user_threads(self, user_id, thread_id):
        from app.services.user_service import UserService  # Import here to avoid circular dependency
        user = UserService.get_user_by_id(user_id)
        if not user:
            return False

        thread_ids = user.get('threads', [])
        thread_ids = [t for t in thread_ids if t['id'] != thread_id]
        thread_ids.insert(0, {'id': thread_id, 'created_at': datetime.utcnow()})

        result = self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"threads": thread_ids}}
        )
        return result.modified_count > 0
    
    def get_user_threads(self, user_id):
        user = self.users_collection.find_one({"_id": ObjectId(user_id)})
        thread_ids = [thread['id'] for thread in user.get('threads', [])]

        threads = self.threads_collection.find({"thread_id": {"$in": thread_ids}})
        return list(threads)