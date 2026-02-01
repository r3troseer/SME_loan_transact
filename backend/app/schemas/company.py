from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class CompanyDetail(BaseModel):
    id: int
    sme_id: str
    sector: Optional[str]
    region: Optional[str]
    turnover: Optional[float]
    turnover_banded: Optional[str]
    employees: Optional[int]

    # Risk scores
    risk_score: Optional[float]
    risk_category: Optional[str]
    liquidity_score: Optional[float]
    profitability_score: Optional[float]
    leverage_score: Optional[float]
    cash_score: Optional[float]
    efficiency_score: Optional[float]
    size_score: Optional[float]

    # Inclusion scores
    inclusion_score: Optional[float]
    inclusion_category: Optional[str]
    regional_inclusion_score: Optional[float]
    sector_inclusion_score: Optional[float]
    size_inclusion_score: Optional[float]
    overlooked_score: Optional[float]
    inclusion_flags: List[str]

    # Lender info
    current_lender: Optional[str]
    current_lender_fit: Optional[float]
    best_match_lender: Optional[str]
    best_match_fit: Optional[float]
    fit_gap: Optional[float]
    reallocation_status: Optional[str]


class LoanSummary(BaseModel):
    id: int
    loan_amount: Optional[float]
    outstanding_balance: Optional[float]
    loan_term_years: Optional[int]
    years_remaining: Optional[float]
    interest_rate: Optional[float]
    monthly_payment: Optional[float]

    # Fit
    current_lender_fit: Optional[float]
    current_fit_reasons: Dict[str, Any]
    best_match_fit: Optional[float]
    best_match_reasons: Dict[str, Any]
    fit_gap: Optional[float]
    reallocation_status: Optional[str]

    # Pricing
    suggested_price: Optional[float]
    discount_percent: Optional[float]
    gross_roi: Optional[float]
    risk_adjusted_roi: Optional[float]
    annualized_roi: Optional[float]


class LenderProfile(BaseModel):
    name: str
    description: Optional[str]
    risk_tolerance: Optional[str]
    inclusion_mandate: Optional[bool]


class CompanyAnalysis(BaseModel):
    company: CompanyDetail
    loan: Optional[LoanSummary]
    current_lender_profile: Optional[Dict[str, Any]]
    best_match_lender_profile: Optional[Dict[str, Any]]
