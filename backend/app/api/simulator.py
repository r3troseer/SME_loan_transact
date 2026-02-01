from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..core.database import get_db
from ..models import Loan, Company, Lender
from ..schemas.simulator import (
    SimulatorCandidate,
    SimulationRequest,
    SimulationResult,
    LoanFullDetails,
)
from ..services.anonymizer import anonymize_lender, band_amount

router = APIRouter()


@router.get("/candidates", response_model=list[SimulatorCandidate])
async def get_candidates(
    lender_id: Optional[int] = Query(None, description="Filter by lender"),
    db: Session = Depends(get_db)
):
    """Get loans that are candidates for reallocation simulation"""
    query = (
        db.query(Loan, Company)
        .join(Company, Loan.company_id == Company.id)
        .filter(Loan.is_mismatch == True)
    )

    if lender_id:
        query = query.filter(Loan.current_lender_id == lender_id)

    results = query.all()

    candidates = []
    for loan, company in results:
        current_lender = db.query(Lender).filter(Lender.id == loan.current_lender_id).first()
        best_lender = db.query(Lender).filter(Lender.id == loan.best_match_lender_id).first() if loan.best_match_lender_id else None

        candidates.append(SimulatorCandidate(
            loan_id=loan.id,
            company_id=company.sme_id,
            sector=company.sector,
            region=company.region,
            current_lender=current_lender.name if current_lender else "Unknown",
            best_match_lender=anonymize_lender(best_lender.name) if best_lender else "Unknown",
            outstanding_balance=loan.outstanding_balance,
            outstanding_balance_banded=band_amount(loan.outstanding_balance),
            fit_gap=loan.fit_gap,
            reallocation_status=loan.reallocation_status,
            risk_score=company.risk_score,
            inclusion_score=company.inclusion_score,
        ))

    return sorted(candidates, key=lambda x: x.fit_gap or 0, reverse=True)


@router.get("/details/{loan_id}", response_model=LoanFullDetails)
async def get_loan_details(loan_id: int, db: Session = Depends(get_db)):
    """Get full details for a loan for simulation"""
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    company = db.query(Company).filter(Company.id == loan.company_id).first()
    current_lender = db.query(Lender).filter(Lender.id == loan.current_lender_id).first()
    best_lender = db.query(Lender).filter(Lender.id == loan.best_match_lender_id).first() if loan.best_match_lender_id else None

    return LoanFullDetails(
        # Loan info
        loan_id=loan.id,
        loan_amount=loan.loan_amount,
        outstanding_balance=loan.outstanding_balance,
        loan_term_years=loan.loan_term_years,
        years_remaining=loan.years_remaining,
        interest_rate=loan.interest_rate,
        monthly_payment=loan.monthly_payment,
        # Company info
        company_id=company.sme_id,
        sector=company.sector,
        region=company.region,
        turnover=company.turnover,
        risk_score=company.risk_score,
        risk_category=company.risk_category,
        inclusion_score=company.inclusion_score,
        inclusion_category=company.inclusion_category,
        # Current lender
        current_lender_id=current_lender.id if current_lender else None,
        current_lender_name=current_lender.name if current_lender else None,
        current_lender_fit=loan.current_lender_fit,
        current_fit_reasons=loan.current_fit_reasons,
        # Best match lender
        best_match_lender_id=best_lender.id if best_lender else None,
        best_match_lender_name=anonymize_lender(best_lender.name) if best_lender else None,
        best_match_fit=loan.best_match_fit,
        best_match_reasons=loan.best_match_reasons,
        fit_gap=loan.fit_gap,
        reallocation_status=loan.reallocation_status,
        # Pricing
        default_probability=loan.default_probability,
        remaining_payments=loan.remaining_payments,
        gross_loan_value=loan.gross_loan_value,
        expected_loss=loan.expected_loss,
        risk_adjusted_value=loan.risk_adjusted_value,
        misfit_discount=loan.misfit_discount,
        suggested_price=loan.suggested_price,
        discount_percent=loan.discount_percent,
        gross_roi=loan.gross_roi,
        risk_adjusted_roi=loan.risk_adjusted_roi,
        annualized_roi=loan.annualized_roi,
    )


@router.post("/calculate", response_model=SimulationResult)
async def calculate_simulation(
    request: SimulationRequest,
    db: Session = Depends(get_db)
):
    """Calculate simulation for a swap or sale transaction"""
    # Get outgoing loan
    outgoing_loan = db.query(Loan).filter(Loan.id == request.outgoing_loan_id).first()
    if not outgoing_loan:
        raise HTTPException(status_code=404, detail="Outgoing loan not found")

    outgoing_company = db.query(Company).filter(Company.id == outgoing_loan.company_id).first()
    outgoing_lender = db.query(Lender).filter(Lender.id == outgoing_loan.current_lender_id).first()

    # Initialize result
    result = {
        "transaction_type": request.transaction_type,
        "outgoing_loan_id": outgoing_loan.id,
        "outgoing_company_id": outgoing_company.sme_id,
        "outgoing_value": outgoing_loan.suggested_price or outgoing_loan.outstanding_balance,
        "outgoing_risk_score": outgoing_company.risk_score,
        "outgoing_fit": outgoing_loan.current_lender_fit,
        "incoming_loan_id": None,
        "incoming_company_id": None,
        "incoming_value": None,
        "incoming_risk_score": None,
        "incoming_fit": None,
        "valuation_delta": 0,
        "net_settlement": 0,
        "total_fit_improvement": outgoing_loan.fit_gap or 0,
        "is_zero_cash": True,
    }

    if request.transaction_type == "sale":
        # Simple sale - buyer pays suggested price
        result["net_settlement"] = -(outgoing_loan.suggested_price or outgoing_loan.outstanding_balance)
        result["is_zero_cash"] = False

    elif request.transaction_type in ["swap", "swap_cash"]:
        # Get incoming loan
        if not request.incoming_loan_id:
            raise HTTPException(status_code=400, detail="Incoming loan required for swap")

        incoming_loan = db.query(Loan).filter(Loan.id == request.incoming_loan_id).first()
        if not incoming_loan:
            raise HTTPException(status_code=404, detail="Incoming loan not found")

        incoming_company = db.query(Company).filter(Company.id == incoming_loan.company_id).first()

        incoming_value = incoming_loan.suggested_price or incoming_loan.outstanding_balance
        outgoing_value = outgoing_loan.suggested_price or outgoing_loan.outstanding_balance

        result["incoming_loan_id"] = incoming_loan.id
        result["incoming_company_id"] = incoming_company.sme_id
        result["incoming_value"] = incoming_value
        result["incoming_risk_score"] = incoming_company.risk_score
        result["incoming_fit"] = incoming_loan.best_match_fit  # Your fit for incoming loan

        result["valuation_delta"] = outgoing_value - incoming_value
        result["total_fit_improvement"] = (outgoing_loan.fit_gap or 0) + (incoming_loan.fit_gap or 0)

        if request.transaction_type == "swap":
            # Pure swap - try for zero cash
            if abs(result["valuation_delta"]) < outgoing_value * 0.05:  # Within 5%
                result["net_settlement"] = 0
                result["is_zero_cash"] = True
            else:
                result["net_settlement"] = result["valuation_delta"]
                result["is_zero_cash"] = False
        else:
            # Swap + cash - always settle difference
            result["net_settlement"] = result["valuation_delta"]
            result["is_zero_cash"] = result["net_settlement"] == 0

    return SimulationResult(**result)
