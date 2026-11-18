import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from pymongo import MongoClient

# Load environment variables from .env
load_dotenv()

mongo_uri = os.getenv("MONGODB_URI")
db_name = os.getenv("MONGODB_DB_NAME", "creatorpilot_db")

client = MongoClient(mongo_uri)
db = client[db_name]
users_collection = db["users"]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Clear existing test user
users_collection.delete_many({"email": "test@creatorpilot.ai"})

# Hash the password
hashed_password = pwd_context.hash("mypassword123")

# Insert test user
users_collection.insert_one({
    "email": "test@creatorpilot.ai",
    "password": hashed_password
})

print("Test user created successfully with hashed password!")