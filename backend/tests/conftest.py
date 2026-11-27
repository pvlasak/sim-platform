# backend/tests/conftest.py
# Shared fixtures. Tests run without real MongoDB, S3 or Git: MongoDB is
# replaced by an in-memory mongomock-motor client, S3 and Git are patched.
import os

import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

# boto3 client is created at import time of the models router
if not os.environ.get("AWS_REGION"):
    os.environ["AWS_REGION"] = "eu-central-1"

from app import database
from app.main import app
from app.routers import models as models_router

FAKE_COMMIT_ID = "abc1234"


@pytest.fixture
def mongo_db(monkeypatch):
    """In-memory MongoDB wired into app.database."""
    client = AsyncMongoMockClient()
    monkeypatch.setattr(database, "_client", client)
    monkeypatch.setenv("MONGODB_DB", "simflow_test")
    return client["simflow_test"]


@pytest.fixture
def api_client(mongo_db, monkeypatch, tmp_path):
    """TestClient with S3 upload and git push mocked as successful.

    The client is not used as a context manager, so the app lifespan
    (connect_db to a real server) is not triggered.
    """
    monkeypatch.setattr(models_router, "TEMP_DIR", str(tmp_path))

    async def fake_upload_to_s3(file_obj, bucket, s3_key):
        return True

    async def fake_push_to_git(**kwargs):
        return {"success": True, "commit_id": FAKE_COMMIT_ID, "error": None}

    monkeypatch.setattr(models_router, "upload_to_s3", fake_upload_to_s3)
    monkeypatch.setattr(models_router, "push_to_git", fake_push_to_git)
    return TestClient(app)
