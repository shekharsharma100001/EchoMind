from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from bson.objectid import ObjectId

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data.get('username')
        self.email = user_data.get('email')
        self.password_hash = user_data.get('password_hash')
        self.role = user_data.get('role', 'user')
        self.profile_picture = user_data.get('profile_picture')
        self.created_at = user_data.get('created_at', datetime.utcnow())
        
        # New for OAuth
        self.google_id = user_data.get('google_id')
        self.is_oauth = user_data.get('is_oauth', False)

    def get_id(self):
        return self.id

    def check_password(self, password):
        if self.is_oauth and not self.password_hash:
            return False
        import bcrypt
        try:
            return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
        except ValueError:
            # Fallback for old werkzeug hashes during transition if needed
            from werkzeug.security import check_password_hash
            return check_password_hash(self.password_hash, password)
        except Exception:
            return False

    @property
    def is_admin(self):
        return self.role == 'admin'

    @staticmethod
    def get(user_id):
        import database.db as db_module
        if db_module.db is not None:
            try:
                user_data = db_module.db.users.find_one({'_id': ObjectId(user_id)})
                if user_data:
                    return User(user_data)
            except Exception:
                return None
        return None

    @staticmethod
    def find_by_email(email):
        import database.db as db_module
        if db_module.db is not None:
            user_data = db_module.db.users.find_one({'email': email})
            if user_data:
                return User(user_data)
        return None

    @staticmethod
    def create(username, email, password=None, role='user', google_id=None, profile_picture=None):
        import database.db as db_module
        import bcrypt
        
        user_doc = {
            'username': username,
            'email': email,
            'role': role,
            'created_at': datetime.utcnow(),
            'profile_picture': profile_picture
        }
        
        if google_id:
            user_doc['google_id'] = google_id
            user_doc['is_oauth'] = True
        else:
            user_doc['is_oauth'] = False
            
        if password:
            salt = bcrypt.gensalt()
            user_doc['password_hash'] = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
            
        result = db_module.db.users.insert_one(user_doc)
        user_doc['_id'] = result.inserted_id
        return User(user_doc)
