# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .database import connect_db, disconnect_db
from .routers import models, jobs

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await disconnect_db()

app = FastAPI(
    title="SimFlow API",
    version="0.3.0",
    lifespan=lifespan
)

# Allow the Vue dev server to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:80"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(models.router, prefix="/models", tags=["models"])
app.include_router(jobs.router,   prefix="/jobs",   tags=["jobs"])

@app.get("/health")
async def health():
    return {"status": "ok"}
