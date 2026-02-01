from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from datetime import datetime
from ..core.database import Base


class MarketplaceAction(Base):
    """Generic marketplace action tracking"""
    __tablename__ = "marketplace_actions"

    id = Column(Integer, primary_key=True, index=True)
    action_type = Column(String, index=True)  # list, bid, interest, reveal
    loan_id = Column(Integer, ForeignKey("loans.id"), index=True)
    lender_id = Column(Integer, index=True)
    data = Column(String, nullable=True)  # JSON string for additional data
    timestamp = Column(DateTime, default=datetime.utcnow)


class ListedLoan(Base):
    """Loans listed for sale in the marketplace"""
    __tablename__ = "listed_loans"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id"), unique=True, index=True)
    seller_lender_id = Column(Integer, index=True)
    listed_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class Bid(Base):
    """Bids on listed loans"""
    __tablename__ = "bids"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id"), index=True)
    buyer_lender_id = Column(Integer, index=True)
    discount_percent = Column(Float)  # Discount from suggested price
    submitted_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")  # pending, accepted, rejected


class Interest(Base):
    """Expressions of interest in loans"""
    __tablename__ = "interests"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id"), index=True)
    buyer_lender_id = Column(Integer, index=True)
    expressed_at = Column(DateTime, default=datetime.utcnow)


class Reveal(Base):
    """Identity reveals between buyer and seller"""
    __tablename__ = "reveals"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id"), index=True)
    seller_revealed = Column(Boolean, default=False)
    buyer_revealed = Column(Boolean, default=False)
    seller_lender_id = Column(Integer)
    buyer_lender_id = Column(Integer)
    revealed_at = Column(DateTime, nullable=True)
