from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from ..core.database import Base


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(Integer, primary_key=True, index=True)

    # Who performed the action
    lender_id = Column(Integer, index=True)

    # Transaction details
    action_type = Column(String)  # view_details, submit_bid, express_interest, etc.
    cost = Column(Integer)
    balance_after = Column(Integer)

    # What the action was on
    target_type = Column(String, nullable=True)  # loan, swap, company, etc.
    target_id = Column(String, nullable=True)

    # Metadata
    description = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
