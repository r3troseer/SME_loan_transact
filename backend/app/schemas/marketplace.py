from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LoanOpportunity(BaseModel):
    loan_id: int
    company_id: str
    sector: Optional[str]
    region: Optional[str]
    seller_lender: str  # Anonymized

    outstanding_balance: Optional[float]
    outstanding_balance_banded: Optional[str]
    years_remaining: Optional[float]

    risk_score: Optional[float]
    risk_category: Optional[str]
    inclusion_score: Optional[float]

    current_fit: Optional[float]
    your_fit: Optional[float]
    fit_improvement: Optional[float]

    suggested_price: Optional[float]
    discount_percent: Optional[float]
    gross_roi: Optional[float]
    risk_adjusted_roi: Optional[float]
    annualized_roi: Optional[float]

    interest_count: int
    bid_count: int
    listed_at: datetime


class MyLoan(BaseModel):
    loan_id: int
    company_id: str
    sector: Optional[str]
    region: Optional[str]

    outstanding_balance: Optional[float]
    outstanding_balance_banded: Optional[str]
    years_remaining: Optional[float]

    risk_score: Optional[float]
    current_fit: Optional[float]
    best_match_lender: Optional[str]
    best_match_fit: Optional[float]
    fit_gap: Optional[float]
    reallocation_status: Optional[str]
    suggested_price: Optional[float]

    is_listed: bool
    bid_count: int
    best_bid_discount: Optional[float]


class ListLoanRequest(BaseModel):
    loan_id: int
    lender_id: int


class BidRequest(BaseModel):
    loan_id: int
    lender_id: int
    discount_percent: float


class BidResponse(BaseModel):
    bid_id: int
    status: str
    message: str


class InterestRequest(BaseModel):
    loan_id: int
    lender_id: int


class RevealRequest(BaseModel):
    loan_id: int
    lender_id: int
    is_buyer: bool


class MarketStats(BaseModel):
    listed_loans: int
    pending_bids: int
    total_interests: int
