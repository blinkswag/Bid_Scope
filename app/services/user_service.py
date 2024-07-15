from bson import ObjectId
import bcrypt
from app.utils.validation import validate_password
from app.db import Database

db = Database()
class UserService:
    @staticmethod
    def get_all_users():
        db = Database()
        return db.users_collection.find({}, {"Password": 0})

    @staticmethod
    def add_user(username, email, password, role):
        db = Database()
        email = email.lower()
        if db.users_collection.find_one({"Username": username}):
            return "username_exists"
        if db.users_collection.find_one({"Email": email}):
            return "email_exists"
        valid, message = validate_password(password)
        if not valid:
            return message
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        db.users_collection.insert_one({"Username": username, "Email": email, "Password": hashed_password, "role": role})
        return "user_added"

    @staticmethod
    def get_user_by_id(user_id):
        db = Database()
        return db.users_collection.find_one({"_id": ObjectId(user_id)}, {"Password": 0})

    @staticmethod
    def update_user(user_id, username, email, role, password=None):
        db = Database()
        email = email.lower()
        user = db.users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return False
        updates = {"Username": username, "Email": email, "role": role}
        if password:
            valid, message = validate_password(password)
            if not valid:
                return message
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            updates["Password"] = hashed_password
        result = db.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": updates}
        )
        return result.modified_count > 0

    @staticmethod
    def delete_user(user_id):
        db = Database()
        result = db.users_collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0

    @staticmethod
    def get_user_threads(user_id):
        user = db.users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            print("User not found")
            return []
        
        thread_ids = user.get('threads', [])
        # print("User thread IDs:", thread_ids)  # Debug statement
        threads = []

        for i, thread in enumerate(thread_ids):
            thread_data = db.threads_collection.find_one({"thread_id": thread['id']})
            if thread_data:
                threads.append({
                    'id': thread['id'],
                    'name': thread_data.get('name', f'{i + 1}')
                })
            else:
                # Use default name if thread data is not found
                threads.append({
                    'id': thread['id'],
                    'name': f'{i + 1}'
                })
                # print(f"No thread found with thread_id: {thread['id']}, using default name 'Thread {i + 1}'")  # Debug statement

        # print("Fetched threads:", threads)  # Debug statement
        return threads
    
    @staticmethod
    def remove_user_thread(user_id, thread_id):
        db = Database()
        user = db.users_collection.find_one({"_id": ObjectId(user_id)})
        if user:
            threads = user.get('threads', [])
            updated_threads = [thread for thread in threads if thread['id'] != thread_id]
            result = db.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"threads": updated_threads}}
            )
            return result.modified_count > 0
        return False