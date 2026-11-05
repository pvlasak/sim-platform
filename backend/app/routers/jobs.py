# backend/app/routers/jobs.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime, timezone
from ..database import jobs_col
import uuid
from uuid import UUID


router = APIRouter()

class CheckerRun(BaseModel):
    checker_run_id: UUID
    model_id: UUID
    revision_id: int
    status: Literal["QUEUED", "RUNNING", "PASSED", "FAILED"]
    result_s3_uri: str | None = None


# ── Request schema ─────────────────────────────────────────────────
class JobRequest(BaseModel):
    name:        str
    model_id:    str
    model_name:  str
    solver:      str   = "LS-DYNA MPP R14"
    licence:     str   = "MPP"
    preset:      str   = "Frontal Impact 56 km/h"
    instance:    str   = "c5n.18xlarge"
    nodes:       int   = 4
    started_by:  str   = "unknown"


class Job(BaseModel):
    job_id: UUID
    model_id: UUID
    job_request: JobRequest
    revision_id: str
    status: Literal[
        "PROVISIONING", "QUEUED", "RUNNING",
        "COMPLETED", "FAILED", "FINALIZING", "ARCHIVED"
    ]

# ── Helper ─────────────────────────────────────────────────────────
def _clean(doc):
    doc["id"] = str(doc.pop("_id"))
    return doc

# ── Endpoints ──────────────────────────────────────────────────────

@router.get("")
async def get_jobs():
    """Return all jobs, newest first."""
    col  = jobs_col()
    docs = await col.find().sort("started_at", -1).to_list(200)
    return [_clean(d) for d in docs]


@router.post("")
async def create_job(payload: JobRequest):
    """
    Save a new simulation job to MongoDB.
    In production this also triggers the Jenkins
    provisioning + LS-DYNA pipeline.
    """
    col = jobs_col()
    job = {
        "_id":         uuid.uuid4().hex[:7],
        "name":        payload.name,
        "model_id":    payload.model_id,
        "model_name":  payload.model_name,
        "status":      "queued",
        "progress":    0,
        "solver":      payload.solver,
        "licence":     payload.licence,
        "preset":      payload.preset,
        "instance":    payload.instance,
        "nodes":       payload.nodes,
        "started_by":  payload.started_by,
        "started_at":  datetime.now(timezone.utc).isoformat(),
        "stopped_at":  None,
        # Rough cost estimate: nodes × price/h × 2.5h + storage
        "cost_est":    round(payload.nodes * 3.888 * 2.5 + payload.nodes * 30 * 0.023, 2),
        "cost_actual": None,
    }
    await col.insert_one(job)
    return _clean(job)


@router.get("/{job_id}")
async def get_job(job_id: str):
    col = jobs_col()
    doc = await col.find_one({"_id": job_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Job not found")
    return _clean(doc)
