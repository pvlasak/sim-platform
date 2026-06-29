# backend/app/database.py
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()   # reads backend/.env when running locally

_client = None

async def connect_db():
    global _client
    url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
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
