# backend/app/routers/models.py

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from datetime import datetime, timezone
from ..database import models_col
from ..git import push_model_to_git
import uuid, os, aiofiles

router = APIRouter()

# Temporary folder — file is written here first, then copied to the git repo
# and deleted after the push completes
TEMP_DIR = "./temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)


def _clean(doc):
    """MongoDB returns _id — rename to id for the frontend."""
    doc["id"] = str(doc.pop("_id"))
    return doc


@router.get("")
async def get_models():
    """Return all committed models, newest first."""
    col  = models_col()
    docs = await col.find().sort("committed_at", -1).to_list(200)
    return [_clean(d) for d in docs]


@router.post("")
async def create_model(
    file:         UploadFile = File(...),
    project:      str        = Form(...),
    commit_msg:   str        = Form(...),
    committed_by: str        = Form(...),
):
    """
    1. Write uploaded file to temp folder
    2. git.py copies it to the local git repo and pushes to remote
    3. Save model metadata to MongoDB
    4. Delete the temp file
    """
    model_id  = uuid.uuid4().hex[:7]

    # Step 1 — write to temp location
    temp_path = os.path.join(TEMP_DIR, f"{model_id}_{file.filename}")
    async with aiofiles.open(temp_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # Step 2 — copy to git repo and push
    git_result = await push_model_to_git(
        file_path  = temp_path,
        file_name  = file.filename,
        commit_msg = commit_msg,
        author     = committed_by,
    )

    # Step 3 — save metadata to MongoDB
    col   = models_col()
    model = {
        "_id":          model_id,
        "name":         file.filename,
        "project":      project,
        "commit_id":    git_result.get("commit_id") or model_id,
        "commit_msg":   commit_msg,
        "committed_by": committed_by,
        "committed_at": datetime.now(timezone.utc).isoformat(),
        "check_status": "pending",
        "git_pushed":   git_result.get("success", False),
        "git_error":    git_result.get("error"),
    }
    await col.insert_one(model)

    # Step 4 — clean up temp file
    os.remove(temp_path)

    return _clean(model)


@router.patch("/{model_id}/check")
async def update_check_status(model_id: str, body: dict):
    """Called by Jenkins after model check pipeline finishes."""
    col = models_col()
    await col.update_one(
        {"_id": model_id},
        {"$set": {"check_status": body.get("check_status", "failed")}}
    )
    return {"ok": True}


@router.get("/{model_id}")
async def get_model(model_id: str):
    col = models_col()
    doc = await col.find_one({"_id": model_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Model not found")
    return _clean(doc)
