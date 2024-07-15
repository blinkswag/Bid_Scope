import bcrypt
from app.db import Database

class AuthService:
    @staticmethod
    def check_user_credentials(email, password):
        db = Database()
        email = email.lower()
        user = db.users_collection.find_one({"Email": email})
        if user:
            stored_password = user['Password']
            if isinstance(stored_password, str):
                stored_password = stored_password.encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                return True
        return False
