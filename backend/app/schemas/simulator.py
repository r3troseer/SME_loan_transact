from pydantic import BaseModel
from typing import Optional, Dict, Any


class SimulatorCandidate(BaseModel):
    loan_id: int
    company_id: str
    sector: Optional[str]
    region: Optional[str]
    current_lender: Optional[str]
    best_match_lender: Optional[str]  # Anonymized
    outstanding_balance: float
    outstanding_balance_banded: str
    fit_gap: Optional[float]
    reallocation_status: Optional[str]
    risk_score: Optional[float]
    inclusion_score: Optional[float]


class LoanFullDetails(BaseModel):
    # Loan info
    loan_id: int
    loan_amount: Optional[float]
    outstanding_balance: Optional[float]
    loan_term_years: Optional[int]
    years_remaining: Optional[float]
    interest_rate: Optional[float]
    monthly_payment: Optional[float]

    # Company info
    company_id: str
    sector: Optional[str]
    region: Optional[str]
    turnover: Optional[float]
    risk_score: Optional[float]
    risk_category: Optional[str]
    inclusion_score: Optional[float]
    inclusion_category: Optional[str]

    # Current lender
    current_lender_id: Optional[int]
    current_lender_name: Optional[str]
    current_lender_fit: Optional[float]
    current_fit_reasons: Optional[Dict[str, Any]]

    # Best match lender
    best_match_lender_id: Optional[int]
    best_match_lender_name: Optional[str]  # Anonymized
    best_match_fit: Optional[float]
    best_match_reasons: Optional[Dict[str, Any]]
    fit_gap: Optional[float]
    reallocation_status: Optional[str]

    # Pricing
    default_probability: Optional[float]
    remaining_payments: Optional[float]
    gross_loan_value: Optional[float]
    expected_loss: Optional[float]
    risk_adjusted_value: Optional[float]
    misfit_discount: Optional[float]
    suggested_price: Optional[float]
    discount_percent: Optional[float]
    gross_roi: Optional[float]
    risk_adjusted_roi: Optional[float]
    annualized_roi: Optional[float]


class SimulationRequest(BaseModel):
    transaction_type: str  # "sale", "swap", "swap_cash"
    outgoing_loan_id: int
    incoming_loan_id: Optional[int] = None  # Required for swap


class SimulationResult(BaseModel):
    transaction_type: str
    outgoing_loan_id: int
    outgoing_company_id: str
    outgoing_value: float
    outgoing_risk_score: Optional[float]
    outgoing_fit: Optional[float]

    incoming_loan_id: Optional[int]
    incoming_company_id: Optional[str]
    incoming_value: Optional[float]
    incoming_risk_score: Optional[float]
    incoming_fit: Optional[float]

    valuation_delta: float
    net_settlement: float
    total_fit_improvement: float
    is_zero_cash: bool
