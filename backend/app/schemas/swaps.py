from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AutoSwapMatch(BaseModel):
    # Your loan (giving away)
    give_loan_id: int
    give_company_id: str
    give_sector: str
    give_region: str
    give_value: float
    give_value_banded: str
    give_your_fit: Optional[float]
    give_their_fit: Optional[float]
    give_fit_improvement: Optional[float]

    # Their loan (receiving)
    receive_loan_id: int
    receive_company_id: str
    receive_sector: str
    receive_region: str
    receive_value: float
    receive_value_banded: str
    receive_their_fit: Optional[float]
    receive_your_fit: Optional[float]
    receive_fit_improvement: Optional[float]

    # Swap metrics
    counterparty_lender: str  # Anonymized
    total_fit_improvement: float
    value_difference: float
    cash_adjustment: float  # Positive = you receive cash
    inclusion_bonus: float
    is_inclusion_swap: bool
    swap_score: float


class SwapProposalCreate(BaseModel):
    proposer_lender_id: int
    proposer_loan_id: int
    counterparty_lender_id: int
    counterparty_loan_id: Optional[int] = None  # None for open swap
    reasoning: Optional[str] = None


class SwapProposalResponse(BaseModel):
    proposal_id: int
    status: str
    message: str


class SwapProposalDetail(BaseModel):
    id: int
    is_proposer: bool
    status: str
    is_open_swap: bool

    # Proposer side
    proposer_lender: str
    proposer_loan_id: int
    proposer_company_id: Optional[str]
    proposer_sector: Optional[str]
    proposer_value: Optional[float]

    # Counterparty side
    counterparty_lender: str
    counterparty_loan_id: Optional[int]
    counterparty_company_id: Optional[str]
    counterparty_sector: Optional[str]
    counterparty_value: Optional[float]

    # Metrics
    cash_adjustment: float
    total_fit_improvement: float
    is_inclusion_swap: bool
    swap_reasoning: Optional[str]
    created_at: datetime


class SwapAcceptRequest(BaseModel):
    proposal_id: int
    lender_id: int
    selected_loan_id: Optional[int] = None  # For open swaps
