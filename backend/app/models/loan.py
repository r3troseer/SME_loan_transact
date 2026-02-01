from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from ..core.database import Base


class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    company_id = Column(Integer, ForeignKey("companies.id"), index=True)
    current_lender_id = Column(Integer, ForeignKey("lenders.id"), index=True)

    # Loan details
    loan_amount = Column(Float)
    outstanding_balance = Column(Float)
    loan_term_years = Column(Integer)
    years_remaining = Column(Float)
    interest_rate = Column(Float)
    monthly_payment = Column(Float)

    # Matcher analysis (from Matcher agent)
    current_lender_fit = Column(Float)
    current_fit_reasons = Column(JSON)  # Positive/negative factors
    best_match_lender_id = Column(Integer, ForeignKey("lenders.id"), nullable=True)
    best_match_fit = Column(Float)
    best_match_reasons = Column(JSON)
    fit_gap = Column(Float)
    reallocation_status = Column(String)  # STRONG, MODERATE, MINOR, ADEQUATE
    is_mismatch = Column(Boolean, default=False)

    # Pricer analysis (from Pricer agent)
    default_probability = Column(Float)
    remaining_payments = Column(Float)
    gross_loan_value = Column(Float)
    expected_loss = Column(Float)
    risk_adjusted_value = Column(Float)
    misfit_discount = Column(Float)
    suggested_price = Column(Float)
    discount_percent = Column(Float)
    gross_roi = Column(Float)
    risk_adjusted_roi = Column(Float)
    annualized_roi = Column(Float)

    # Relationships
    company = relationship("Company", back_populates="loans")
    current_lender = relationship("Lender", foreign_keys=[current_lender_id], back_populates="loans")
    best_match_lender = relationship("Lender", foreign_keys=[best_match_lender_id])
