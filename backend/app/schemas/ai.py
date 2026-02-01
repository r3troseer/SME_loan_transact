from pydantic import BaseModel
from typing import Optional


class ExplanationRequest(BaseModel):
    loan_id: int


class ExplanationResponse(BaseModel):
    loan_id: int
    explanation: str
    generated_by: str  # "gemini" or "template"


class MarketInsightRequest(BaseModel):
    focus_area: Optional[str] = None


class MarketInsightResponse(BaseModel):
    insight: str
    generated_by: str


class SwapStoryRequest(BaseModel):
    loan1_id: int
    loan2_id: int


class SwapStoryResponse(BaseModel):
    story: str
    generated_by: str


class CompanyInsightRequest(BaseModel):
    company_id: int


class CompanyInsightResponse(BaseModel):
    company_id: int
    insight: str
    generated_by: str
