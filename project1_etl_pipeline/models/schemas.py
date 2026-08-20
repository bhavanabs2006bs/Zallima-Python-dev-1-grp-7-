from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class DataSource(str, Enum):
    SALESFORCE = "salesforce"
    STRIPE = "stripe"
    ZENDESK = "zendesk"


class SalesforceContact(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    company: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class StripeTransaction(BaseModel):
    id: str
    customer_id: str
    amount: int = Field(ge=0, description="Amount in cents")
    currency: str = Field(min_length=3, max_length=3)
    status: str
    description: Optional[str] = None
    created_at: datetime


class ZendeskTicket(BaseModel):
    id: str
    subject: str
    description: Optional[str] = None
    status: str
    priority: Optional[str] = None
    requester_id: str
    created_at: datetime
    updated_at: datetime


class ETLJob(BaseModel):
    id: Optional[int] = None
    source: DataSource
    status: JobStatus = JobStatus.PENDING
    records_extracted: int = 0
    records_loaded: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class TransformResult(BaseModel):
    success: bool
    records_processed: int
    records_failed: int
    errors: List[str] = []
    data: List[Any] = []


class UnifiedRecord(BaseModel):
    source: DataSource
    source_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    company: Optional[str] = None
    amount: Optional[int] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    metadata: dict = {}
