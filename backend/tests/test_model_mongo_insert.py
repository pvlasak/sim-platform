# backend/tests/test_model_mongo_insert.py
import asyncio

from .conftest import FAKE_COMMIT_ID


def test_model_is_inserted_into_mongo_after_successful_git_commit(api_client, mongo_db):
    response = api_client.post(
        "/models",
        files={"file": ("model.zip", b"dummy-content", "application/zip")},
        data={
            "project": "demo-project",
            "description": "demo description",
            "commit_msg": "initial commit",
            "committed_by": "tester",
        },
    )
    assert response.status_code == 200
    model_id = response.json()["id"]

    doc = asyncio.run(mongo_db["models"].find_one({"_id": model_id}))
    assert doc is not None, "model was not inserted into MongoDB"
    assert doc["project"] == "demo-project"
    assert doc["description"] == "demo description"
    assert len(doc["revisions"]) == 1

    rev = doc["revisions"][0]
    assert rev["revision_id"] == 1
    assert rev["file_name"] == "model.zip"
    assert rev["commit_msg"] == "initial commit"
    assert rev["committed_by"] == "tester"
    assert rev["check_status"] == "PENDING"
    assert rev["git_pushed"] is True
    assert rev["git_commit_id"] == FAKE_COMMIT_ID
    assert rev["package_s3_uri"] == f"s3://simflow-models/{model_id}/revisions/1/model.zip"


def test_nothing_inserted_when_git_commit_fails(api_client, mongo_db, monkeypatch):
    from app.routers import models as models_router

    async def failing_push(**kwargs):
        return {"success": False, "commit_id": None, "error": "boom"}

    monkeypatch.setattr(models_router, "push_to_git", failing_push)
    response = api_client.post(
        "/models",
        files={"file": ("model.zip", b"x", "application/zip")},
        data={"project": "p", "commit_msg": "m", "committed_by": "t"},
    )
    assert response.status_code == 502
    assert asyncio.run(mongo_db["models"].count_documents({})) == 0
