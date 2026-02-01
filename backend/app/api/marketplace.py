from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional
from datetime import datetime

from ..core.database import get_db
from ..models import Loan, Company, Lender, ListedLoan, Bid, Interest, Reveal
from ..schemas.marketplace import (
    LoanOpportunity,
    MyLoan,
    ListLoanRequest,
    BidRequest,
    BidResponse,
    InterestRequest,
    RevealRequest,
    MarketStats,
)
from ..services.anonymizer import anonymize_lender, band_amount

router = APIRouter()


@router.get("/opportunities", response_model=list[LoanOpportunity])
async def get_opportunities(
    lender_id: int = Query(..., description="Current lender ID"),
    sector: Optional[str] = None,
    min_roi: Optional[float] = None,
    db: Session = Depends(get_db),
):
    """Get loans available to buy where current lender is best match"""
    # Find loans where this lender is the best match and loan is listed
    query = (
        db.query(Loan, Company, ListedLoan)
        .join(Company, Loan.company_id == Company.id)
        .join(ListedLoan, ListedLoan.loan_id == Loan.id)
        .filter(
            Loan.best_match_lender_id == lender_id,
            Loan.current_lender_id != lender_id,
            ListedLoan.is_active == True,
        )
    )

    if sector:
        query = query.filter(Company.sector == sector)
    if min_roi:
        query = query.filter(Loan.annualized_roi >= min_roi)

    results = query.all()

    opportunities = []
    for loan, company, listing in results:
        # Check interest/bids
        interest_count = db.query(Interest).filter(Interest.loan_id == loan.id).count()
        bid_count = db.query(Bid).filter(Bid.loan_id == loan.id).count()

        opportunities.append(
            LoanOpportunity(
                loan_id=loan.id,
                company_id=company.sme_id,
                sector=company.sector,
                region=company.region,
                seller_lender=anonymize_lender(
                    db.query(Lender)
                    .filter(Lender.id == loan.current_lender_id)
                    .first()
                    .name
                ),
                outstanding_balance=loan.outstanding_balance,
                outstanding_balance_banded=band_amount(loan.outstanding_balance),
                years_remaining=loan.years_remaining,
                risk_score=company.risk_score,
                risk_category=company.risk_category,
                inclusion_score=company.inclusion_score,
                current_fit=loan.current_lender_fit,
                your_fit=loan.best_match_fit,
                fit_improvement=loan.fit_gap,
                suggested_price=loan.suggested_price,
                discount_percent=loan.discount_percent,
                gross_roi=loan.gross_roi,
                risk_adjusted_roi=loan.risk_adjusted_roi,
                annualized_roi=loan.annualized_roi,
                interest_count=interest_count,
                bid_count=bid_count,
                listed_at=listing.listed_at,
            )
        )

    return sorted(opportunities, key=lambda x: x.fit_improvement or 0, reverse=True)


@router.get("/my-loans", response_model=list[MyLoan])
async def get_my_loans(
    lender_id: int = Query(..., description="Current lender ID"),
    unaligned_only: bool = Query(True, description="Only show unaligned loans"),
    db: Session = Depends(get_db),
):
    """Get current lender's loans, optionally filtered to unalignes"""
    query = (
        db.query(Loan, Company)
        .join(Company, Loan.company_id == Company.id)
        .filter(Loan.current_lender_id == lender_id)
    )

    if unaligned_only:
        query = query.filter(Loan.is_unalign == True)

    results = query.all()

    my_loans = []
    for loan, company in results:
        # Check if listed
        listing = (
            db.query(ListedLoan)
            .filter(ListedLoan.loan_id == loan.id, ListedLoan.is_active == True)
            .first()
        )

        # Get bid stats if listed
        bids = []
        if listing:
            bids = (
                db.query(Bid)
                .filter(Bid.loan_id == loan.id, Bid.status == "pending")
                .all()
            )

        # Get best match lender name
        best_match_name = None
        if loan.best_match_lender_id:
            best_match = (
                db.query(Lender).filter(Lender.id == loan.best_match_lender_id).first()
            )
            best_match_name = anonymize_lender(best_match.name) if best_match else None

        my_loans.append(
            MyLoan(
                loan_id=loan.id,
                company_id=company.sme_id,
                sector=company.sector,
                region=company.region,
                outstanding_balance=loan.outstanding_balance,
                outstanding_balance_banded=band_amount(loan.outstanding_balance),
                years_remaining=loan.years_remaining,
                risk_score=company.risk_score,
                current_fit=loan.current_lender_fit,
                best_match_lender=best_match_name,
                best_match_fit=loan.best_match_fit,
                fit_gap=loan.fit_gap,
                reallocation_status=loan.reallocation_status,
                suggested_price=loan.suggested_price,
                is_listed=listing is not None,
                bid_count=len(bids),
                best_bid_discount=min([b.discount_percent for b in bids])
                if bids
                else None,
            )
        )

    return sorted(my_loans, key=lambda x: x.fit_gap or 0, reverse=True)


@router.post("/list")
async def list_loan(request: ListLoanRequest, db: Session = Depends(get_db)):
    """List a loan for sale in the marketplace"""
    # Verify loan exists and belongs to lender
    loan = db.query(Loan).filter(Loan.id == request.loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    if loan.current_lender_id != request.lender_id:
        raise HTTPException(
            status_code=403, detail="Loan does not belong to this lender"
        )

    # Check if already listed
    existing = (
        db.query(ListedLoan)
        .filter(ListedLoan.loan_id == request.loan_id, ListedLoan.is_active == True)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Loan is already listed")

    # Create listing
    listing = ListedLoan(
        loan_id=request.loan_id,
        seller_lender_id=request.lender_id,
    )
    db.add(listing)
    db.commit()

    return {"status": "success", "message": "Loan listed for sale"}


@router.post("/bid", response_model=BidResponse)
async def submit_bid(request: BidRequest, db: Session = Depends(get_db)):
    """Submit a bid on a listed loan"""
    # Verify loan is listed
    listing = (
        db.query(ListedLoan)
        .filter(ListedLoan.loan_id == request.loan_id, ListedLoan.is_active == True)
        .first()
    )
    if not listing:
        raise HTTPException(status_code=404, detail="Loan is not listed for sale")

    # Can't bid on own loan
    if listing.seller_lender_id == request.lender_id:
        raise HTTPException(status_code=400, detail="Cannot bid on your own loan")

    # Create bid
    bid = Bid(
        loan_id=request.loan_id,
        buyer_lender_id=request.lender_id,
        discount_percent=request.discount_percent,
    )
    db.add(bid)
    db.commit()

    return BidResponse(
        bid_id=bid.id, status="pending", message="Bid submitted successfully"
    )


@router.post("/interest")
async def express_interest(request: InterestRequest, db: Session = Depends(get_db)):
    """Express interest in a loan"""
    # Verify loan exists
    loan = db.query(Loan).filter(Loan.id == request.loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    # Check for existing interest
    existing = (
        db.query(Interest)
        .filter(
            Interest.loan_id == request.loan_id,
            Interest.buyer_lender_id == request.lender_id,
        )
        .first()
    )
    if existing:
        return {"status": "exists", "message": "Interest already expressed"}

    interest = Interest(
        loan_id=request.loan_id,
        buyer_lender_id=request.lender_id,
    )
    db.add(interest)
    db.commit()

    return {"status": "success", "message": "Interest expressed"}


@router.post("/reveal")
async def reveal_identity(request: RevealRequest, db: Session = Depends(get_db)):
    """Reveal identity to counterparty"""
    loan = db.query(Loan).filter(Loan.id == request.loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    # Find or create reveal record
    reveal = db.query(Reveal).filter(Reveal.loan_id == request.loan_id).first()

    if not reveal:
        reveal = Reveal(
            loan_id=request.loan_id,
            seller_lender_id=loan.current_lender_id,
            buyer_lender_id=request.lender_id if request.is_buyer else None,
        )
        db.add(reveal)

    if request.is_buyer:
        reveal.buyer_revealed = True
        reveal.buyer_lender_id = request.lender_id
    else:
        reveal.seller_revealed = True

    if reveal.buyer_revealed and reveal.seller_revealed:
        reveal.revealed_at = datetime.utcnow()

    db.commit()

    return {
        "status": "success",
        "both_revealed": reveal.buyer_revealed and reveal.seller_revealed,
        "seller_name": db.query(Lender)
        .filter(Lender.id == reveal.seller_lender_id)
        .first()
        .name
        if reveal.both_revealed
        else None,
        "buyer_name": db.query(Lender)
        .filter(Lender.id == reveal.buyer_lender_id)
        .first()
        .name
        if reveal.both_revealed
        else None,
    }


@router.get("/stats", response_model=MarketStats)
async def get_market_stats(db: Session = Depends(get_db)):
    """Get marketplace statistics"""
    listed_count = db.query(ListedLoan).filter(ListedLoan.is_active == True).count()
    total_bids = db.query(Bid).filter(Bid.status == "pending").count()
    total_interests = db.query(Interest).count()

    return MarketStats(
        listed_loans=listed_count,
        pending_bids=total_bids,
        total_interests=total_interests,
    )
