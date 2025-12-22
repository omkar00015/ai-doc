
import os
from flask import Flask
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
import dotenv
from bson.objectid import ObjectId

# Load env variables
dotenv.load_dotenv()

app = Flask(__name__)
app.config['MONGO_URI'] = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/document_reader')

print(f"Connecting to: {app.config['MONGO_URI']}")

mongo = PyMongo(app)
bcrypt = Bcrypt(app)

with app.app_context():
    try:
        # Test connection
        db_names = mongo.cx.list_database_names()
        print(f"Databases: {db_names}")
        
        # Check users collection
        user_count = mongo.db.users.count_documents({})
        print(f"User count: {user_count}")
        
        users = mongo.db.users.find()
        print("\n--- Registered Users ---")
        for user in users:
            print(f"Email: {user.get('email')}, Name: {user.get('name')}, ID: {user.get('_id')}")
        print("------------------------\n")
            
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
