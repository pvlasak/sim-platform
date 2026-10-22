# backend/app/database.py
import os
from motor.motor_asyncio import AsyncIOMotorClient

# dotenv is used when running locally, without docker
#from dotenv import load_dotenv
#load_dotenv()

_client = None

async def connect_db():
    global _client
    username=os.getenv("MONGODB_USER")
    password=os.getenv("MONGODB_PASSWORD")
    # deployment on localhost withoud docker images
    #url = os.getenv("MONGODB_URL")
    # deployment using docker image
    url = os.getenv("MONGODB_URL", f"mongodb://{username}:{password}@mongodb:27017")
    _client = AsyncIOMotorClient(url)
    print(f"MongoDB connected: {url}")

async def disconnect_db():
    if _client:
        _client.close()

def get_db():
    db_name = os.getenv("MONGODB_DB", "simflow")
    return _client[db_name]

def models_col():
    return get_db()["models"]

def jobs_col():
    return get_db()["jobs"]
