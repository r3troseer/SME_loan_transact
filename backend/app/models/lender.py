from sqlalchemy import Column, Integer, String, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from ..core.database import Base


class Lender(Base):
    __tablename__ = "lenders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    # Profile
    description = Column(String)
    risk_tolerance = Column(String)  # low, medium, high
    risk_score_min = Column(Integer)

    # Preferences
    preferred_sectors = Column(JSON)  # List or None for all
    min_turnover = Column(Float)
    max_turnover = Column(Float, nullable=True)
    preferred_regions = Column(JSON)  # List or None for all
    inclusion_mandate = Column(Boolean, default=False)

    # Relationships - specify foreign_keys to avoid ambiguity with best_match_lender_id
    loans = relationship("Loan", foreign_keys="[Loan.current_lender_id]", back_populates="current_lender")
