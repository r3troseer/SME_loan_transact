from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from ..core.database import get_db
from ..models import Company, Loan, Lender
from ..schemas.portfolio import (
    PortfolioOverview,
    SectorDistribution,
    RegionDistribution,
    LenderDistribution,
    CompanyListItem,
)
from ..services.anonymizer import band_amount, group_region

router = APIRouter()


@router.get("/overview", response_model=PortfolioOverview)
async def get_portfolio_overview(db: Session = Depends(get_db)):
    """Get portfolio-wide summary metrics"""
    # Total companies
    total_companies = db.query(Company).count()

    # Total loan value
    total_loan_value = db.query(func.sum(Loan.outstanding_balance)).scalar() or 0

    # Unaligned loans
    total_loans = db.query(Loan).count()
    unaligned_loans = db.query(Loan).filter(Loan.is_unalign == True).count()
    unalign_percentage = (unaligned_loans / total_loans * 100) if total_loans > 0 else 0

    # Average risk score
    avg_risk_score = db.query(func.avg(Company.risk_score)).scalar() or 0

    return PortfolioOverview(
        total_companies=total_companies,
        total_loan_value=total_loan_value,
        total_loan_value_banded=band_amount(total_loan_value),
        unaligned_loans=unaligned_loans,
        unalign_percentage=round(unalign_percentage, 1),
        avg_risk_score=round(avg_risk_score, 1),
    )


@router.get("/by-sector", response_model=list[SectorDistribution])
async def get_by_sector(db: Session = Depends(get_db)):
    """Get company distribution by sector"""
    results = (
        db.query(Company.sector, func.count(Company.id).label("count"))
        .group_by(Company.sector)
        .order_by(func.count(Company.id).desc())
        .all()
    )

    return [SectorDistribution(sector=sector, count=count) for sector, count in results]


@router.get("/by-region", response_model=list[RegionDistribution])
async def get_by_region(
    grouped: bool = Query(True, description="Group regions into larger categories"),
    db: Session = Depends(get_db),
):
    """Get company distribution by region"""
    results = (
        db.query(Company.region, func.count(Company.id).label("count"))
        .group_by(Company.region)
        .all()
    )

    if grouped:
        # Group regions
        grouped_counts = {}
        for region, count in results:
            group = group_region(region)
            grouped_counts[group] = grouped_counts.get(group, 0) + count

        return sorted(
            [
                RegionDistribution(region=region, count=count)
                for region, count in grouped_counts.items()
            ],
            key=lambda x: x.count,
            reverse=True,
        )

    return sorted(
        [RegionDistribution(region=region, count=count) for region, count in results],
        key=lambda x: x.count,
        reverse=True,
    )


@router.get("/lender-distribution", response_model=list[LenderDistribution])
async def get_lender_distribution(db: Session = Depends(get_db)):
    """Get loan distribution by current lender"""
    results = (
        db.query(Lender.name, func.count(Loan.id).label("count"))
        .join(Loan, Loan.current_lender_id == Lender.id)
        .group_by(Lender.name)
        .order_by(func.count(Loan.id).desc())
        .all()
    )

    total = sum(count for _, count in results)

    return [
        LenderDistribution(
            lender=name,
            count=count,
            percentage=round(count / total * 100, 1) if total > 0 else 0,
        )
        for name, count in results
    ]


@router.get("/companies", response_model=list[CompanyListItem])
async def get_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    sector: Optional[str] = None,
    region: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get paginated list of companies"""
    query = db.query(Company)

    if sector:
        query = query.filter(Company.sector == sector)
    if region:
        query = query.filter(Company.region == region)

    companies = query.offset(skip).limit(limit).all()

    return [
        CompanyListItem(
            id=c.id,
            sme_id=c.sme_id,
            sector=c.sector,
            region=c.region,
            turnover=c.turnover,
            risk_score=c.risk_score,
            risk_category=c.risk_category,
            inclusion_score=c.inclusion_score,
            inclusion_category=c.inclusion_category,
        )
        for c in companies
    ]
