import certifi
import pymongo
from bson import ObjectId
import bcrypt
from dotenv import load_dotenv
import os
from .validation import validate_password
load_dotenv()

class Database:
    def __init__(self):
        connection_string= os.getenv('mongo_srv')
        client = pymongo.MongoClient(connection_string, tlsCAFile=certifi.where())

        try:
            client.server_info()  
            self.db = client.Bid
            self.users_collection = self.db.Users
            self.threads_collection = self.db.Threads
        except Exception as e:
            print(f"Failed to connect to the database: {e}")
            raise e

    def check_user_credentials(self, email, password):
        user = self.users_collection.find_one({"Email": email})
        if user:
            stored_password = user['Password']
            if isinstance(stored_password, str):
                stored_password = stored_password.encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                return True
        return False

    def get_all_users(self):
        return self.users_collection.find({}, {"Password": 0})

    def add_user(self, username, email, password, role):
        if self.users_collection.find_one({"Username": username}):
            return "username_exists"
        if self.users_collection.find_one({"Email": email}):
            return "email_exists"
        valid, message = validate_password(password)
        if not valid:
            return message
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        self.users_collection.insert_one({"Username": username, "Email": email, "Password": hashed_password, "role": role})
        return "user_added"

    def get_user_by_id(self, user_id):
        return self.users_collection.find_one({"_id": ObjectId(user_id)}, {"Password": 0})

    def update_user(self, user_id, username, email, role, password=None):
        user = self.users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return False
        updates = {"Username": username, "Email": email, "role": role}
        if password:
            valid, message = validate_password(password)
            if not valid:
                return message
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            updates["Password"] = hashed_password
        result = self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": updates}
        )
        return result.modified_count > 0

    def delete_user(self, user_id):
        result = self.users_collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0

    def update_user_threads(self, user_id, new_thread_id):
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        thread_ids = user.get('threads', [])
        if len(thread_ids) >= 10:
            thread_ids = thread_ids[1:]
        thread_ids.append(new_thread_id)
        
        result = self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"threads": thread_ids}}
        )
        return result.modified_count > 0
    
    def get_user_threads(self, user_id):
        user = self.get_user_by_id(user_id)
        if not user:
            return []
        return user.get('threads', [])
