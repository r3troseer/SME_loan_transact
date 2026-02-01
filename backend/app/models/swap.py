from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from datetime import datetime
from ..core.database import Base


class SwapProposal(Base):
    """Loan swap proposals between lenders"""
    __tablename__ = "swap_proposals"

    id = Column(Integer, primary_key=True, index=True)

    # Proposer side
    proposer_lender_id = Column(Integer, index=True)
    proposer_loan_id = Column(Integer, ForeignKey("loans.id"))

    # Counterparty side
    counterparty_lender_id = Column(Integer, index=True)
    counterparty_loan_id = Column(Integer, ForeignKey("loans.id"), nullable=True)  # Null for "open" swaps

    # Swap details
    is_open_swap = Column(Boolean, default=False)  # Counterparty chooses which loan
    cash_adjustment = Column(Float, default=0.0)  # Positive = proposer pays, negative = counterparty pays

    # Fit metrics
    proposer_fit_improvement = Column(Float)
    counterparty_fit_improvement = Column(Float)
    total_fit_improvement = Column(Float)

    # Inclusion bonus
    inclusion_bonus = Column(Float, default=0.0)
    is_inclusion_swap = Column(Boolean, default=False)

    # Status
    status = Column(String, default="pending")  # pending, accepted, declined, expired
    created_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime, nullable=True)

    # Reasoning
    swap_reasoning = Column(String, nullable=True)
    ai_story = Column(String, nullable=True)  # AI-generated inclusion story
