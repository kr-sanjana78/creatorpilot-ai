
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB_NAME")

try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")

    print("MongoDB Connected Successfully!")
    print("Database:", DB_NAME)

    client.close()

except Exception as e:
    print("MongoDB Connection Failed!")
    print(e)
