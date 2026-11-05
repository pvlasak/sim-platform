# backend/app/routers/models.py
from asyncio import sleep

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from datetime import datetime, timezone
from pydantic import BaseModel
from ..database import models_col
from ..git import push_model_to_git
import uuid
from uuid import UUID
from typing import Literal
import os
import hashlib
import boto3
import logging
from botocore.exceptions import ClientError


router = APIRouter()

# Temporary folder — file is written here first, then copied to the git repo
# and deleted after the push completes
TEMP_DIR = "./temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

# S3_ENDPOINT_URL = "http://localhost:9000"
S3_BUCKET_NAME = "simflow-models"



s3_client = boto3.client(
    "s3",
    endpoint_url=os.getenv("S3_ENDPOINT_URL") or None,
    region_name=os.getenv("AWS_REGION", "eu-central-1"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

class ModelRevision(BaseModel):
    revision_id: int          
    file_name: str
    commit_msg: str
    committed_by: str
    committed_at: datetime | None = None
    package_s3_key: str | None = None
    package_s3_uri: str
    check_status: Literal["PENDING", "CHECKING", "READY", "NEEDS_FIX"]
    git_pushed: bool | None = None
    git_commit_id: str | None = None
    git_error: str | None = None

class Model(BaseModel):
    model_id: UUID
    project: str
    description: str | None
    revisions: list[ModelRevision] = []


def _clean(doc):
    """MongoDB returns _id — rename to id for the frontend."""
    doc["id"] = str(doc.pop("_id"))
    return doc


def create_commit_manifest(ModelRevision):
    """Create a manifest file for the model revision, to be stored in S3."""
    commit_manifest = {
        "revision_id": ModelRevision.revision_id,
        "file_name": ModelRevision.file_name,
        "commit_msg": ModelRevision.commit_msg,
        "committed_by": ModelRevision.committed_by,
        "committed_at": ModelRevision.committed_at.isoformat(),
        "package_s3_key": ModelRevision.package_s3_key,
        "package_s3_uri": ModelRevision.package_s3_uri,
        "check_status": ModelRevision.check_status,
    }
    # write YAML manifest file to temp directory
    manifest_name = f"{ModelRevision.file_name}_rev-{ModelRevision.revision_id}_commit.yaml"
    manifest_path = os.path.join(TEMP_DIR, manifest_name)
    with open(manifest_path, "w") as f:
        import yaml
        yaml.dump(commit_manifest, f)   
    return (manifest_name, manifest_path)


async def upload_to_s3(file_obj, bucket: str, s3_key: str) -> bool:
    """ Upload the file to S3 storage. """
    try:
        s3_client.upload_fileobj(file_obj, bucket, s3_key)
    except ClientError as e:
        logging.error(e)
        return False
    return True


async def save_model_to_mongo(model: Model):
    """Save model metadata to MongoDB."""
    col = models_col()
    doc = {
        "_id": str(model.model_id),
        "project": model.project,
        "description": model.description,
        "revisions": [rev.dict() for rev in model.revisions],
    }
    await col.insert_one(doc)

async def update_model_in_mongo(model: Model):
    """Update model metadata in MongoDB."""
    col = models_col()
    doc = {
        "project": model.project,
        "description": model.description,
        "revisions": [rev.dict() for rev in model.revisions],
    }
    await col.update_one({"_id": str(model.model_id)}, {"$set": doc})

async def update_check_status(model_id: str, revision_id: int, new_status: str):
    """Update the check_status of a specific model revision in MongoDB."""
    col = models_col()
    result = await col.update_one(
    {
        "_id": model_id,
        "revisions.revision_id": revision_id,
    },
    {"$set": {"revisions.$.check_status": new_status}},
    )
    if result.matched_count != 1:
        raise HTTPException(
            status_code=409,
            detail="Revision not found.",
    )

async def run_check(model_id: str, revision_id: int) -> None:
    await sleep(60)
    result = "READY" if uuid.uuid4().int % 2 == 0 else "NEEDS_FIX"
    await update_check_status(model_id, revision_id, result)
    
    
@router.get("")
async def get_models():
    """Return all committed models, newest first."""
    col  = models_col()
    docs = await col.find().sort("committed_at", -1).to_list(200)
    return [_clean(d) for d in docs]


@router.post("")
async def create_new_model(
    file:         UploadFile = File(...),
    project:      str        = Form(...),
    description:  str | None = Form(None),
    commit_msg:   str        = Form(...),
    committed_by: str        = Form(...),
):
# Create Model and Revision Pydantic Objects
    model_id  = uuid.uuid4()
    revision_id = 1   
    model = Model(
        model_id = model_id,
        project = project,
        description = description,
        revisions = [],
    )
    revision = ModelRevision(
            revision_id = revision_id,
            file_name = file.filename,
            commit_msg = commit_msg,
            committed_by = committed_by,
            committed_at = datetime.now(timezone.utc).isoformat(),
            package_s3_key = f"{model_id}/revisions/{revision_id}/{file.filename}",
            package_s3_uri = f"s3://{S3_BUCKET_NAME}/{model_id}/revisions/{revision_id}/{file.filename}",
            check_status = "PENDING",
            git_pushed = None,
            git_commit_id = None,
            git_error = None
            )
    # Upload the package first; do not save the model unless GitLab confirms
    # the manifest commit.
    if not await upload_to_s3(
        file.file, S3_BUCKET_NAME, revision.package_s3_key
    ):
        logging.error("Model upload to S3 failed: %s", file.filename)
        raise HTTPException(status_code=500, detail="Model upload failed")

    manifest_file_path = None
    try:
        manifest_filename, manifest_file_path = create_commit_manifest(revision)
        git_result = await push_model_to_git(
            file_path  = manifest_file_path,
            file_name  = manifest_filename,
            revision_id = revision_id,
            model_id   = model_id,
            project    = project,
            commit_msg = commit_msg,
            author     = committed_by,
        )
        if not git_result.get("success"):
            logging.error("GitLab manifest push failed: %s", git_result.get("error"))
            raise HTTPException(
                status_code=502,
                detail=f"GitLab manifest push failed: {git_result.get('error')}",
            )

        # Update Git Push Status  
        revision.git_pushed = git_result.get("success")
        revision.git_commit_id = git_result.get("commit_id")
        revision.git_error  = None
        # Add revision to model
        model.revisions.append(revision)
        # Save Model to MongoDB 
        await save_model_to_mongo(model)
    finally:
        if manifest_file_path and os.path.exists(manifest_file_path):
            os.remove(manifest_file_path)
    # Create response for frontend.
    response = model.model_dump(mode="json")
    response["id"] = response.pop("model_id")
    return response

@router.post("/{model_id}/revisions")
async def create_new_model_revision(
    model_id: UUID,
    file:         UploadFile = File(...),
    commit_msg:   str        = Form(...),
    committed_by: str        = Form(...),
):
    # Get the model from MongoDB to determine the next revision number
    col = models_col()
    doc = await col.find_one({"_id": str(model_id)})
    if doc is None:
        raise HTTPException(status_code=404, detail="Model not found")  
    doc["model_id"] = UUID(doc.pop("_id"))
    existing_model = Model(**doc)
    if (
        not existing_model.revisions
        or existing_model.revisions[-1].check_status != "NEEDS_FIX"
    ):
        raise HTTPException(
            status_code=409,
            detail="A correction can only be uploaded when the latest revision needs fixes.",
        )
    current_revision_id = existing_model.revisions[-1].revision_id if existing_model.revisions else 0
    new_revision_id = max(
        revision.revision_id for revision in existing_model.revisions
    ) + 1
    new_revision = ModelRevision(
            revision_id = new_revision_id,
            file_name = file.filename or "model",
            commit_msg = commit_msg,
            committed_by = committed_by,
            committed_at = datetime.now(timezone.utc).isoformat(),
            package_s3_key = f"{model_id}/revisions/{new_revision_id}/{file.filename}",
            package_s3_uri = f"s3://{S3_BUCKET_NAME}/{model_id}/revisions/{new_revision_id}/{file.filename}",
            check_status = "PENDING",   
            git_pushed = None,
            git_commit_id = None,
            git_error = None
            )
    
    # Upload Model Package to S3 Storage
    if not await upload_to_s3(
        file.file, S3_BUCKET_NAME, new_revision.package_s3_key
    ):
        raise HTTPException(status_code=500, detail="Model upload failed")
    manifest_file_path = None
    try:
        manifest_filename, manifest_file_path = create_commit_manifest(new_revision)
        git_result = await push_model_to_git(
            file_path  = manifest_file_path,
            file_name  = manifest_filename,
            model_id   = model_id,
            revision_id = new_revision_id,
            project    = existing_model.project,
            commit_msg = commit_msg,
            author     = committed_by,
        )
        if not git_result.get("success"):
            raise HTTPException(
                status_code=502,
                detail=f"GitLab push failed: {git_result.get('error')}",
            )
        # Update Git status
        new_revision.git_pushed = git_result.get("success")
        new_revision.git_commit_id = git_result.get("commit_id")
        # Add model revision to a list of revisions 
        existing_model.revisions.append(new_revision)
        # Save Model Revision in MongoDB
        await update_model_in_mongo(existing_model)
    finally:
        if manifest_file_path and os.path.exists(manifest_file_path):
            os.remove(manifest_file_path)
    # Create response for frontend.
    response = existing_model.model_dump(mode="json")
    response["id"] = response.pop("model_id")
    return response


@router.get("/{model_id}")
async def get_model(model_id: str):
    col = models_col()
    doc = await col.find_one({"_id": model_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Model not found")
    return _clean(doc)

@router.post("/{model_id}/revisions/{revision_id}/check")
async def start_check(
    model_id: str,
    revision_id: int,
    background_tasks: BackgroundTasks,
):
    await update_check_status(model_id, revision_id, "CHECKING")
    background_tasks.add_task(run_check, model_id, revision_id)

    return {
        "model_id": model_id,
        "revision_id": revision_id,
        "check_status": "CHECKING",
    }

  