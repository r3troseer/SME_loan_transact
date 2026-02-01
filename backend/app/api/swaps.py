from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import datetime
from typing import Optional

from ..core.database import get_db
from ..models import Loan, Company, Lender, SwapProposal
from ..schemas.swaps import (
    AutoSwapMatch,
    SwapProposalCreate,
    SwapProposalResponse,
    SwapProposalDetail,
    SwapAcceptRequest,
)
from ..services.anonymizer import anonymize_lender, band_amount

router = APIRouter()


@router.get("/auto-matches", response_model=list[AutoSwapMatch])
async def get_auto_matches(
    lender_id: int = Query(..., description="Current lender ID"),
    inclusion_only: bool = Query(False, description="Only show inclusion swaps"),
    db: Session = Depends(get_db)
):
    """Get system-suggested complementary swaps"""
    # Find loans where:
    # 1. Lender A has a loan that fits better with Lender B
    # 2. Lender B has a loan that fits better with Lender A
    # 3. Both fit gaps are significant (>= 15)

    # Get all mismatched loans from current lender
    my_mismatched = (
        db.query(Loan)
        .filter(
            Loan.current_lender_id == lender_id,
            Loan.is_mismatch == True,
            Loan.fit_gap >= 15,
        )
        .all()
    )

    matches = []
    for my_loan in my_mismatched:
        # Find complementary loans from the best match lender
        if not my_loan.best_match_lender_id:
            continue

        # Find their mismatched loans that would fit better with us
        their_loans = (
            db.query(Loan)
            .filter(
                Loan.current_lender_id == my_loan.best_match_lender_id,
                Loan.best_match_lender_id == lender_id,
                Loan.is_mismatch == True,
                Loan.fit_gap >= 15,
            )
            .all()
        )

        for their_loan in their_loans:
            # Calculate value difference
            my_value = my_loan.suggested_price or my_loan.outstanding_balance
            their_value = their_loan.suggested_price or their_loan.outstanding_balance
            value_diff = abs(my_value - their_value)
            value_tolerance = 0.2 * max(my_value, their_value)

            # Skip if values too different
            if value_diff > value_tolerance:
                continue

            # Get companies
            my_company = db.query(Company).filter(Company.id == my_loan.company_id).first()
            their_company = db.query(Company).filter(Company.id == their_loan.company_id).first()

            # Calculate inclusion bonus
            inclusion_bonus = 0
            is_inclusion_swap = False
            if my_company.inclusion_score and my_company.inclusion_score >= 60:
                inclusion_bonus += 10
                is_inclusion_swap = True
            if their_company.inclusion_score and their_company.inclusion_score >= 60:
                inclusion_bonus += 10
                is_inclusion_swap = True

            # Filter by inclusion if requested
            if inclusion_only and not is_inclusion_swap:
                continue

            # Calculate total improvement
            total_improvement = (my_loan.fit_gap or 0) + (their_loan.fit_gap or 0)
            swap_score = total_improvement + inclusion_bonus

            # Get lender names
            their_lender = db.query(Lender).filter(Lender.id == my_loan.best_match_lender_id).first()

            matches.append(AutoSwapMatch(
                # Your loan (giving away)
                give_loan_id=my_loan.id,
                give_company_id=my_company.sme_id,
                give_sector=my_company.sector,
                give_region=my_company.region,
                give_value=my_value,
                give_value_banded=band_amount(my_value),
                give_your_fit=my_loan.current_lender_fit,
                give_their_fit=my_loan.best_match_fit,
                give_fit_improvement=my_loan.fit_gap,
                # Their loan (receiving)
                receive_loan_id=their_loan.id,
                receive_company_id=their_company.sme_id,
                receive_sector=their_company.sector,
                receive_region=their_company.region,
                receive_value=their_value,
                receive_value_banded=band_amount(their_value),
                receive_their_fit=their_loan.current_lender_fit,
                receive_your_fit=their_loan.best_match_fit,
                receive_fit_improvement=their_loan.fit_gap,
                # Swap metrics
                counterparty_lender=anonymize_lender(their_lender.name) if their_lender else "Unknown",
                total_fit_improvement=total_improvement,
                value_difference=value_diff,
                cash_adjustment=my_value - their_value,  # Positive = you receive cash
                inclusion_bonus=inclusion_bonus,
                is_inclusion_swap=is_inclusion_swap,
                swap_score=swap_score,
            ))

    # Sort by swap score
    return sorted(matches, key=lambda x: x.swap_score, reverse=True)


@router.get("/my-proposals", response_model=list[SwapProposalDetail])
async def get_my_proposals(
    lender_id: int = Query(..., description="Current lender ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """Get swap proposals involving this lender"""
    query = db.query(SwapProposal).filter(
        or_(
            SwapProposal.proposer_lender_id == lender_id,
            SwapProposal.counterparty_lender_id == lender_id,
        )
    )

    if status:
        query = query.filter(SwapProposal.status == status)

    proposals = query.order_by(SwapProposal.created_at.desc()).all()

    results = []
    for p in proposals:
        proposer_loan = db.query(Loan).filter(Loan.id == p.proposer_loan_id).first()
        counterparty_loan = db.query(Loan).filter(Loan.id == p.counterparty_loan_id).first() if p.counterparty_loan_id else None

        proposer_company = db.query(Company).filter(Company.id == proposer_loan.company_id).first() if proposer_loan else None
        counterparty_company = db.query(Company).filter(Company.id == counterparty_loan.company_id).first() if counterparty_loan else None

        proposer_lender = db.query(Lender).filter(Lender.id == p.proposer_lender_id).first()
        counterparty_lender = db.query(Lender).filter(Lender.id == p.counterparty_lender_id).first()

        is_proposer = p.proposer_lender_id == lender_id

        results.append(SwapProposalDetail(
            id=p.id,
            is_proposer=is_proposer,
            status=p.status,
            is_open_swap=p.is_open_swap,
            # Proposer side
            proposer_lender=proposer_lender.name if is_proposer else anonymize_lender(proposer_lender.name),
            proposer_loan_id=p.proposer_loan_id,
            proposer_company_id=proposer_company.sme_id if proposer_company else None,
            proposer_sector=proposer_company.sector if proposer_company else None,
            proposer_value=proposer_loan.suggested_price if proposer_loan else None,
            # Counterparty side
            counterparty_lender=counterparty_lender.name if not is_proposer else anonymize_lender(counterparty_lender.name),
            counterparty_loan_id=p.counterparty_loan_id,
            counterparty_company_id=counterparty_company.sme_id if counterparty_company else None,
            counterparty_sector=counterparty_company.sector if counterparty_company else None,
            counterparty_value=counterparty_loan.suggested_price if counterparty_loan else None,
            # Metrics
            cash_adjustment=p.cash_adjustment,
            total_fit_improvement=p.total_fit_improvement,
            is_inclusion_swap=p.is_inclusion_swap,
            swap_reasoning=p.swap_reasoning,
            created_at=p.created_at,
        ))

    return results


@router.post("/propose", response_model=SwapProposalResponse)
async def create_proposal(
    request: SwapProposalCreate,
    db: Session = Depends(get_db)
):
    """Create a new swap proposal"""
    # Verify proposer loan
    proposer_loan = db.query(Loan).filter(Loan.id == request.proposer_loan_id).first()
    if not proposer_loan:
        raise HTTPException(status_code=404, detail="Proposer loan not found")
    if proposer_loan.current_lender_id != request.proposer_lender_id:
        raise HTTPException(status_code=403, detail="Loan does not belong to proposer")

    # Verify counterparty loan if not open swap
    counterparty_loan = None
    if request.counterparty_loan_id:
        counterparty_loan = db.query(Loan).filter(Loan.id == request.counterparty_loan_id).first()
        if not counterparty_loan:
            raise HTTPException(status_code=404, detail="Counterparty loan not found")
        if counterparty_loan.current_lender_id != request.counterparty_lender_id:
            raise HTTPException(status_code=403, detail="Counterparty loan does not belong to specified lender")

    # Calculate fit improvements
    proposer_improvement = proposer_loan.fit_gap or 0
    counterparty_improvement = counterparty_loan.fit_gap if counterparty_loan else 0

    # Check inclusion
    proposer_company = db.query(Company).filter(Company.id == proposer_loan.company_id).first()
    counterparty_company = db.query(Company).filter(Company.id == counterparty_loan.company_id).first() if counterparty_loan else None

    inclusion_bonus = 0
    is_inclusion = False
    if proposer_company and proposer_company.inclusion_score and proposer_company.inclusion_score >= 60:
        inclusion_bonus += 10
        is_inclusion = True
    if counterparty_company and counterparty_company.inclusion_score and counterparty_company.inclusion_score >= 60:
        inclusion_bonus += 10
        is_inclusion = True

    # Calculate cash adjustment
    proposer_value = proposer_loan.suggested_price or proposer_loan.outstanding_balance
    counterparty_value = (counterparty_loan.suggested_price or counterparty_loan.outstanding_balance) if counterparty_loan else 0
    cash_adjustment = proposer_value - counterparty_value

    proposal = SwapProposal(
        proposer_lender_id=request.proposer_lender_id,
        proposer_loan_id=request.proposer_loan_id,
        counterparty_lender_id=request.counterparty_lender_id,
        counterparty_loan_id=request.counterparty_loan_id,
        is_open_swap=request.counterparty_loan_id is None,
        cash_adjustment=cash_adjustment,
        proposer_fit_improvement=proposer_improvement,
        counterparty_fit_improvement=counterparty_improvement,
        total_fit_improvement=proposer_improvement + counterparty_improvement,
        inclusion_bonus=inclusion_bonus,
        is_inclusion_swap=is_inclusion,
        swap_reasoning=request.reasoning,
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)

    return SwapProposalResponse(
        proposal_id=proposal.id,
        status="pending",
        message="Swap proposal created successfully"
    )


@router.post("/accept")
async def accept_proposal(
    request: SwapAcceptRequest,
    db: Session = Depends(get_db)
):
    """Accept a swap proposal"""
    proposal = db.query(SwapProposal).filter(SwapProposal.id == request.proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if proposal.counterparty_lender_id != request.lender_id:
        raise HTTPException(status_code=403, detail="Only counterparty can accept")
    if proposal.status != "pending":
        raise HTTPException(status_code=400, detail=f"Proposal is already {proposal.status}")

    # For open swaps, need to specify which loan
    if proposal.is_open_swap and not request.selected_loan_id:
        raise HTTPException(status_code=400, detail="Must select a loan for open swap")

    if request.selected_loan_id:
        proposal.counterparty_loan_id = request.selected_loan_id

    proposal.status = "accepted"
    proposal.responded_at = datetime.utcnow()
    db.commit()

    return {"status": "success", "message": "Swap proposal accepted"}


@router.post("/decline")
async def decline_proposal(
    proposal_id: int,
    lender_id: int,
    db: Session = Depends(get_db)
):
    """Decline a swap proposal"""
    proposal = db.query(SwapProposal).filter(SwapProposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if proposal.counterparty_lender_id != lender_id:
        raise HTTPException(status_code=403, detail="Only counterparty can decline")
    if proposal.status != "pending":
        raise HTTPException(status_code=400, detail=f"Proposal is already {proposal.status}")

    proposal.status = "declined"
    proposal.responded_at = datetime.utcnow()
    db.commit()

    return {"status": "success", "message": "Swap proposal declined"}
