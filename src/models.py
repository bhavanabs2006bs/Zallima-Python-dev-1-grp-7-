from pydantic import BaseModel
from typing import Optional


class Customer(BaseModel):
    id: str
    name: Optional[str] = None
    email: Optional[str] = None


class Payment(BaseModel):
    id: str
    customer_id: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    status: Optional[str] = None