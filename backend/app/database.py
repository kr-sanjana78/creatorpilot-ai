import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB_NAME", "creatorpilot_db")

client = None
db = None

def connect_to_mongo():
    global client, db
    client = MongoClient(MONGODB_URI)
    db = client[DB_NAME]
    print("Connected to MongoDB!")

def close_mongo_connection():
    global client
    if client:
        client.close()
        print("Closed MongoDB connection.")

def get_database():
    return db