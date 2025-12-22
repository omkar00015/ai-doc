"""
User model for MongoDB authentication
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from bson.objectid import ObjectId


class User(UserMixin):
    """User model for authentication"""
    
    def __init__(self, user_data):
        """Initialize user from MongoDB document"""
        self.id = str(user_data.get('_id'))
        self.email = user_data.get('email')
        self.password_hash = user_data.get('password_hash') or user_data.get('password')
        self.name = user_data.get('name', '')
        self.created_at = user_data.get('created_at')
    
    def get_id(self):
        """Return user ID as string for Flask-Login"""
        return self.id
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        if self.password_hash and self.password_hash.startswith(('$2b$', '$2a$', '$2y$')):
            import bcrypt
            try:
                # bcrypt requires bytes
                return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
            except Exception:
                return False
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert user to dictionary (excluding password)"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def create_user(mongo, email, password, name=''):
        """Create a new user in MongoDB"""
        password_hash = generate_password_hash(password)
        
        user_doc = {
            'email': email.lower(),
            'password_hash': password_hash,
            'name': name,
            'created_at': datetime.utcnow()
        }
        
        result = mongo.db.users.insert_one(user_doc)
        user_doc['_id'] = result.inserted_id
        
        return User(user_doc)
    
    @staticmethod
    def find_by_email(mongo, email):
        """Find user by email"""
        user_doc = mongo.db.users.find_one({'email': email.lower()})
        if user_doc:
            return User(user_doc)
        return None
    
    @staticmethod
    def find_by_id(mongo, user_id):
        """Find user by ID"""
        try:
            user_doc = mongo.db.users.find_one({'_id': ObjectId(user_id)})
            if user_doc:
                return User(user_doc)
        except:
            pass
        return None
