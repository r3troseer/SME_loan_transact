from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models import Company, Loan, Lender
from ..schemas.company import CompanyDetail, CompanyAnalysis, LoanSummary
from ..services.anonymizer import anonymize_lender, band_turnover

router = APIRouter()


@router.get("/{company_id}", response_model=CompanyDetail)
async def get_company(company_id: int, db: Session = Depends(get_db)):
    """Get company details by ID"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get associated loan
    loan = db.query(Loan).filter(Loan.company_id == company_id).first()
    current_lender = None
    best_match_lender = None

    if loan:
        current_lender = db.query(Lender).filter(Lender.id == loan.current_lender_id).first()
        if loan.best_match_lender_id:
            best_match_lender = db.query(Lender).filter(Lender.id == loan.best_match_lender_id).first()

    return CompanyDetail(
        id=company.id,
        sme_id=company.sme_id,
        sector=company.sector,
        region=company.region,
        turnover=company.turnover,
        turnover_banded=band_turnover(company.turnover),
        employees=company.employees,
        # Risk
        risk_score=company.risk_score,
        risk_category=company.risk_category,
        liquidity_score=company.liquidity_score,
        profitability_score=company.profitability_score,
        leverage_score=company.leverage_score,
        cash_score=company.cash_score,
        efficiency_score=company.efficiency_score,
        size_score=company.size_score,
        # Inclusion
        inclusion_score=company.inclusion_score,
        inclusion_category=company.inclusion_category,
        regional_inclusion_score=company.regional_inclusion_score,
        sector_inclusion_score=company.sector_inclusion_score,
        size_inclusion_score=company.size_inclusion_score,
        overlooked_score=company.overlooked_score,
        inclusion_flags=company.inclusion_flags or [],
        # Lender info
        current_lender=current_lender.name if current_lender else None,
        current_lender_fit=loan.current_lender_fit if loan else None,
        best_match_lender=anonymize_lender(best_match_lender.name) if best_match_lender else None,
        best_match_fit=loan.best_match_fit if loan else None,
        fit_gap=loan.fit_gap if loan else None,
        reallocation_status=loan.reallocation_status if loan else None,
    )


@router.get("/{company_id}/analysis", response_model=CompanyAnalysis)
async def get_company_analysis(company_id: int, db: Session = Depends(get_db)):
    """Get full analysis for a company including loan details"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    loan = db.query(Loan).filter(Loan.company_id == company_id).first()
    current_lender = None
    best_match_lender = None

    loan_summary = None
    if loan:
        current_lender = db.query(Lender).filter(Lender.id == loan.current_lender_id).first()
        if loan.best_match_lender_id:
            best_match_lender = db.query(Lender).filter(Lender.id == loan.best_match_lender_id).first()

        loan_summary = LoanSummary(
            id=loan.id,
            loan_amount=loan.loan_amount,
            outstanding_balance=loan.outstanding_balance,
            loan_term_years=loan.loan_term_years,
            years_remaining=loan.years_remaining,
            interest_rate=loan.interest_rate,
            monthly_payment=loan.monthly_payment,
            # Fit
            current_lender_fit=loan.current_lender_fit,
            current_fit_reasons=loan.current_fit_reasons or {},
            best_match_fit=loan.best_match_fit,
            best_match_reasons=loan.best_match_reasons or {},
            fit_gap=loan.fit_gap,
            reallocation_status=loan.reallocation_status,
            # Pricing
            suggested_price=loan.suggested_price,
            discount_percent=loan.discount_percent,
            gross_roi=loan.gross_roi,
            risk_adjusted_roi=loan.risk_adjusted_roi,
            annualized_roi=loan.annualized_roi,
        )

    return CompanyAnalysis(
        company=CompanyDetail(
            id=company.id,
            sme_id=company.sme_id,
            sector=company.sector,
            region=company.region,
            turnover=company.turnover,
            turnover_banded=band_turnover(company.turnover),
            employees=company.employees,
            risk_score=company.risk_score,
            risk_category=company.risk_category,
            liquidity_score=company.liquidity_score,
            profitability_score=company.profitability_score,
            leverage_score=company.leverage_score,
            cash_score=company.cash_score,
            efficiency_score=company.efficiency_score,
            size_score=company.size_score,
            inclusion_score=company.inclusion_score,
            inclusion_category=company.inclusion_category,
            regional_inclusion_score=company.regional_inclusion_score,
            sector_inclusion_score=company.sector_inclusion_score,
            size_inclusion_score=company.size_inclusion_score,
            overlooked_score=company.overlooked_score,
            inclusion_flags=company.inclusion_flags or [],
            current_lender=current_lender.name if current_lender else None,
            current_lender_fit=loan.current_lender_fit if loan else None,
            best_match_lender=anonymize_lender(best_match_lender.name) if best_match_lender else None,
            best_match_fit=loan.best_match_fit if loan else None,
            fit_gap=loan.fit_gap if loan else None,
            reallocation_status=loan.reallocation_status if loan else None,
        ),
        loan=loan_summary,
        current_lender_profile={
            "name": current_lender.name,
            "description": current_lender.description,
            "risk_tolerance": current_lender.risk_tolerance,
            "inclusion_mandate": current_lender.inclusion_mandate,
        } if current_lender else None,
        best_match_lender_profile={
            "name": anonymize_lender(best_match_lender.name),
            "description": best_match_lender.description,
            "risk_tolerance": best_match_lender.risk_tolerance,
            "inclusion_mandate": best_match_lender.inclusion_mandate,
        } if best_match_lender else None,
    )
