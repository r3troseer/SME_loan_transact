from sqlalchemy import Column, Integer, String, Float, JSON
from sqlalchemy.orm import relationship
from ..core.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    sme_id = Column(String, unique=True, index=True)

    # Basic info
    sector = Column(String, index=True)
    region = Column(String, index=True)

    # Financial data
    turnover = Column(Float)
    ebitda = Column(Float)
    profit_after_tax = Column(Float)
    total_assets = Column(Float)
    total_liabilities = Column(Float)
    current_assets = Column(Float)
    current_liabilities = Column(Float)
    cash = Column(Float)
    inventory = Column(Float)
    receivables = Column(Float)
    fixed_assets = Column(Float)
    equity = Column(Float)
    employees = Column(Integer)

    # Risk analysis scores (from RiskAnalyst agent)
    risk_score = Column(Float)
    risk_category = Column(String)
    liquidity_score = Column(Float)
    profitability_score = Column(Float)
    leverage_score = Column(Float)
    cash_score = Column(Float)
    efficiency_score = Column(Float)
    size_score = Column(Float)

    # Inclusion analysis scores (from InclusionScanner agent)
    inclusion_score = Column(Float)
    inclusion_category = Column(String)
    regional_inclusion_score = Column(Float)
    sector_inclusion_score = Column(Float)
    size_inclusion_score = Column(Float)
    overlooked_score = Column(Float)
    inclusion_flags = Column(JSON)  # List of flags

    # Relationships
    loans = relationship("Loan", back_populates="company")
