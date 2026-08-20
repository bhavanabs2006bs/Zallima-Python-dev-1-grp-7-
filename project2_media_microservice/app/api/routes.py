from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from typing import Optional
import uuid
import os
from datetime import datetime
from ..models.schemas import JobCreate, JobResponse, JobStatus
from ..workers.tasks import process_media_task
from ..core.config import settings
from sqlalchemy import create_engine, text

router = APIRouter()
engine = create_engine(settings.DATABASE_URL)


@router.post("/jobs", response_model=JobResponse)
async def create_job(background_tasks: BackgroundTasks, file: UploadFile = File(...), operation: str = "resize"):
    job_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".bin"
    input_path = os.path.join(settings.UPLOAD_DIR, f"{job_id}{file_ext}")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    content = await file.read()
    with open(input_path, "wb") as f:
        f.write(content)

    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO media_jobs (job_id, status, input_file, created_at) VALUES (:jid, :st, :inf, :ca)"),
            {"jid": job_id, "st": "pending", "inf": input_path, "ca": datetime.now()}
        )
        conn.commit()

    background_tasks.add_task(process_media_task.delay, job_id, input_path, operation)

    return JobResponse(job_id=job_id, status="pending", message="Job created successfully")


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT job_id, status, output_files, error_message FROM media_jobs WHERE job_id=:jid"),
            {"jid": job_id}
        )
        row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobResponse(
        job_id=row[0], status=row[1],
        output_files=row[2], error_message=row[3]
    )


@router.get("/jobs")
async def list_jobs(limit: int = 20):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT job_id, status, created_at FROM media_jobs ORDER BY id DESC LIMIT :limit"),
            {"limit": limit}
        )
        rows = result.fetchall()

    return [{"job_id": r[0], "status": r[1], "created_at": str(r[2])} for r in rows]
