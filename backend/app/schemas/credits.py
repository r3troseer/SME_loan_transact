from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime


class CreditBalance(BaseModel):
    balance: int
    total_spent: int
    action_count: int


class SpendRequest(BaseModel):
    lender_id: int
    action_type: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    description: Optional[str] = None


class SpendResponse(BaseModel):
    success: bool
    cost: int
    new_balance: int
    message: str


class CreditHistory(BaseModel):
    id: int
    action_type: str
    cost: int
    balance_after: int
    target_type: Optional[str]
    target_id: Optional[str]
    description: Optional[str]
    timestamp: datetime


class CreditCosts(BaseModel):
    costs: Dict[str, int]
