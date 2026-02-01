from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..core.database import get_db
from ..core.config import settings
from ..models import CreditTransaction
from ..schemas.credits import (
    CreditBalance,
    SpendRequest,
    SpendResponse,
    CreditHistory,
    CreditCosts,
)

router = APIRouter()

# Credit costs for different actions
CREDIT_COSTS = {
    "view_details": 1,
    "view_swap_details": 1,
    "generate_explanation": 2,
    "generate_swap_story": 2,
    "browse_unlisted_loans": 2,
    "submit_bid": 3,
    "view_bids": 3,
    "accept_swap": 3,
    "express_interest": 5,
    "reveal_counterparty": 5,
    "propose_swap": 5,
}


def get_current_balance(db: Session, lender_id: int) -> int:
    """Get current credit balance for a lender"""
    last_transaction = (
        db.query(CreditTransaction)
        .filter(CreditTransaction.lender_id == lender_id)
        .order_by(CreditTransaction.timestamp.desc())
        .first()
    )
    if last_transaction:
        return last_transaction.balance_after
    return settings.INITIAL_CREDITS


@router.get("/balance", response_model=CreditBalance)
async def get_balance(
    lender_id: int = Query(..., description="Lender ID"),
    db: Session = Depends(get_db)
):
    """Get current credit balance"""
    balance = get_current_balance(db, lender_id)

    # Get spending stats
    total_spent = (
        db.query(func.sum(CreditTransaction.cost))
        .filter(CreditTransaction.lender_id == lender_id)
        .scalar() or 0
    )
    action_count = (
        db.query(CreditTransaction)
        .filter(CreditTransaction.lender_id == lender_id)
        .count()
    )

    return CreditBalance(
        balance=balance,
        total_spent=total_spent,
        action_count=action_count,
    )


@router.post("/spend", response_model=SpendResponse)
async def spend_credits(
    request: SpendRequest,
    db: Session = Depends(get_db)
):
    """Spend credits on an action"""
    # Get cost for action
    cost = CREDIT_COSTS.get(request.action_type)
    if cost is None:
        raise HTTPException(status_code=400, detail=f"Unknown action type: {request.action_type}")

    # Check balance
    current_balance = get_current_balance(db, request.lender_id)
    if current_balance < cost:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. Need {cost}, have {current_balance}"
        )

    # Check if already viewed (prevent double charging)
    if request.target_id:
        existing = (
            db.query(CreditTransaction)
            .filter(
                CreditTransaction.lender_id == request.lender_id,
                CreditTransaction.action_type == request.action_type,
                CreditTransaction.target_id == request.target_id,
            )
            .first()
        )
        if existing:
            return SpendResponse(
                success=True,
                cost=0,
                new_balance=current_balance,
                message="Already performed this action (no charge)"
            )

    # Record transaction
    new_balance = current_balance - cost
    transaction = CreditTransaction(
        lender_id=request.lender_id,
        action_type=request.action_type,
        cost=cost,
        balance_after=new_balance,
        target_type=request.target_type,
        target_id=request.target_id,
        description=request.description,
    )
    db.add(transaction)
    db.commit()

    return SpendResponse(
        success=True,
        cost=cost,
        new_balance=new_balance,
        message=f"Spent {cost} credits on {request.action_type}"
    )


@router.get("/history", response_model=list[CreditHistory])
async def get_history(
    lender_id: int = Query(..., description="Lender ID"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get credit transaction history"""
    transactions = (
        db.query(CreditTransaction)
        .filter(CreditTransaction.lender_id == lender_id)
        .order_by(CreditTransaction.timestamp.desc())
        .limit(limit)
        .all()
    )

    return [
        CreditHistory(
            id=t.id,
            action_type=t.action_type,
            cost=t.cost,
            balance_after=t.balance_after,
            target_type=t.target_type,
            target_id=t.target_id,
            description=t.description,
            timestamp=t.timestamp,
        )
        for t in transactions
    ]


@router.get("/costs", response_model=CreditCosts)
async def get_costs():
    """Get credit costs for all actions"""
    return CreditCosts(costs=CREDIT_COSTS)
