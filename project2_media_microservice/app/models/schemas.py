from pydantic import BaseModel
from typing import Optional
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobCreate(BaseModel):
    operation: str = "resize"


class JobResponse(BaseModel):
    job_id: str
    status: str
    message: Optional[str] = None
    output_files: Optional[str] = None
    error_message: Optional[str] = None
