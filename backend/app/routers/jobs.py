# backend/app/routers/jobs.py
from fastapi import APIRouter, Form, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime, timezone
from ..database import jobs_col
from ..git import push_to_git
import uuid
from uuid import UUID
import os
import logging

router = APIRouter()

TEMP_JOB_DIR = "./temp_jobs"
os.makedirs(TEMP_JOB_DIR, exist_ok=True)

class CheckerRun(BaseModel):
    checker_run_id: UUID
    model_id: UUID
    revision_id: int
    status: Literal["QUEUED", "RUNNING", "PASSED", "FAILED"]
    result_s3_uri: str | None = None


# ── Request schema ─────────────────────────────────────────────────
class JobRequest(BaseModel):
    project:        str
    model_id:       UUID
    revision_id:    int
    loadcase:       str
    job_name:       str
    solver:         str   = "LS-DYNA MPP R12"
    instance:       str   = "c5n.18xlarge"
    nodes:          int   = 4
    commit_msg:     Optional[str] = None
    commit_at:      datetime | None = None
    commit_by:      Optional[str] = None            
    git_pushed:     bool | None = None
    git_commit_id:  str | None = None
    git_error:      str | None = None


class Job(BaseModel):
    job_id: UUID
    job_request: JobRequest
    status: Literal[
        "PROVISIONING", "QUEUED", "RUNNING",
        "COMPLETED", "FAILED", "FINALIZING", "ARCHIVED"
    ]
    started_by:     str
    started_at:     datetime | None = None
    stopped_at:     datetime | None = None
    results_s3_uri:    str | None = None
    result_on_s3: Literal["SUCCESS", "FAILURE"] | None = None
    cost_est:       float | None = None
    cost_actual:    float | None = None

# ── Helper ─────────────────────────────────────────────────────────
def _clean(doc):
    doc["id"] = str(doc.pop("_id"))
    return doc


async def save_job_to_mongo(job: Job):
    col = jobs_col()
    doc = {
    "_id": str(job.job_id),
    "job_request": {
        "project":        job.job_request.project,
        "model_id":       str(job.job_request.model_id),
        "revision_id":    job.job_request.revision_id,
        "loadcase":       job.job_request.loadcase,
        "job_name":       job.job_request.job_name,
        "solver":         job.job_request.solver,
        "instance":       job.job_request.instance,
        "nodes":          job.job_request.nodes,
        "commit_msg":     job.job_request.commit_msg,
        "commit_at":      job.job_request.commit_at,
        "commit_by":      job.job_request.commit_by,
        "git_pushed":     job.job_request.git_pushed,
        "git_commit_id":  job.job_request.git_commit_id,
        "git_error":      job.job_request.git_error
    },
    "status": job.status,
    "started_by": job.started_by,
    "started_at": job.started_at,
    "stopped_at": job.stopped_at,
    "results_s3_uri": job.results_s3_uri,
    "result_on_s3": job.result_on_s3,
    "cost_est": job.cost_est,
    "cost_actual": job.cost_actual
    }
    await col.insert_one(doc)


def create_job_manifest(Job):
    """Create start manifest file for the job, to start provisioning the infrastructure."""
    job_manifest = {
        "job_id": str(Job.job_id),
        "project": Job.job_request.project,
        "model_id": str(Job.job_request.model_id),
        "revision_id": int(Job.job_request.revision_id),
        "loadcase": Job.job_request.loadcase,
        "job_name": Job.job_request.job_name,
        "solver": Job.job_request.solver,
        "instance": Job.job_request.instance,
        "commit_msg": Job.job_request.commit_msg,
        "commit_at": Job.job_request.commit_at,
        "commit_by": Job.job_request.commit_by,
    }
    # write YAML manifest file to temp directory
    manifest_name = f"{Job.job_id}.yaml"
    manifest_path = os.path.join(TEMP_JOB_DIR, manifest_name)
    with open(manifest_path, "w") as f:
        import yaml
        yaml.dump(job_manifest, f)   
    return (manifest_name, manifest_path)

# ── Endpoints ──────────────────────────────────────────────────────

@router.get("")
async def get_jobs():
    """Return all jobs, newest first."""
    col  = jobs_col()
    docs = await col.find().sort("started_at", -1).to_list(200)
    return [_clean(d) for d in docs]


@router.post("")
async def create_job(
        project_name: str= Form(...),
        model_id:     str= Form(...),
        revision_id:  str= Form(...),
        loadcase:     str= Form(...),
        job_name:     str= Form(...),
        solver:       str= Form(...),
        instance:     str= Form(...),        
        nodes:        int= Form(...),
        started_by:   str= Form(...),   
    ):
    """
    Save a new simulation job to MongoDB.
    Job manifest is pushed to Gitlab and infrastructure provisioing is triggered by Jenkins.
    """
    job_id  = uuid.uuid4()

    # Create JobRequest object
    job_request = JobRequest(
            project=project_name,
            model_id=model_id,
            revision_id=revision_id,
            loadcase=loadcase,
            job_name=job_name,
            solver=solver,
            instance=instance,
            nodes=nodes,
            commit_msg=None,
            commit_at=None,
            commit_by=started_by,
            git_pushed = None,
            git_commit_id = None,
            git_error = None
        )
    job = Job(
        job_id=job_id,
        job_request=job_request,
        started_by=started_by,
        status="QUEUED",
        started_at=datetime.now(timezone.utc),
        stopped_at=None,
        cost_est=None,
        cost_actual=None,
    )


    manifest_file_path = None
    try:
        manifest_filename, manifest_file_path = create_job_manifest(job)
        git_result = await push_to_git(
            file_path  = manifest_file_path,
            file_name  = manifest_filename,
            model_id   = model_id,
            revision_id = revision_id,
            commit_msg = job_request.commit_msg,
            author     = job_request.commit_by,
            git_repo_key = "job",
            job_id = job.job_id,
        )
        if not git_result.get("success"):
            logging.error("GitLab manifest push failed: %s", git_result.get("error"))
            raise HTTPException(
                status_code=502,
                detail=f"GitLab manifest push failed: {git_result.get('error')}",
            )

        # Update Git Push Status  
        job_request.git_pushed = git_result.get("success")
        job_request.git_commit_id = git_result.get("commit_id")
        job_request.git_error  = None
        # Save Model to MongoDB 
        await save_job_to_mongo(job)
    finally:
        if manifest_file_path and os.path.exists(manifest_file_path):
            os.remove(manifest_file_path)
    # Create response for frontend.
    response = job.model_dump(mode="json")
    response["id"] = response.pop("job_id")
    return response



@router.get("/{job_id}")
async def get_job(job_id: str):
    col = jobs_col()
    doc = await col.find_one({"_id": job_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Job not found")
    return _clean(doc)
