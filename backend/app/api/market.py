from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..core.database import get_db
from ..models import Company, Loan, Lender
from ..schemas.market import (
    InclusionAnalysis,
    RegionalInclusion,
    LenderFlow,
    ReallocationStats,
)
from ..services.anonymizer import group_region

router = APIRouter()


@router.get("/inclusion-analysis", response_model=InclusionAnalysis)
async def get_inclusion_analysis(db: Session = Depends(get_db)):
    """Get financial inclusion analysis by region"""
    # Get companies grouped by region with inclusion scores
    results = (
        db.query(
            Company.region,
            func.count(Company.id).label("count"),
            func.avg(Company.inclusion_score).label("avg_inclusion"),
            func.sum(func.cast(Company.inclusion_score >= 60, Integer)).label(
                "high_priority_count"
            ),
        )
        .group_by(Company.region)
        .all()
    )

    # Group by macro regions
    regional_data = {}
    for region, count, avg_inclusion, high_priority in results:
        group = group_region(region)
        if group not in regional_data:
            regional_data[group] = {
                "count": 0,
                "total_inclusion": 0,
                "high_priority": 0,
            }
        regional_data[group]["count"] += count
        regional_data[group]["total_inclusion"] += (avg_inclusion or 0) * count
        regional_data[group]["high_priority"] += high_priority or 0

    regions = []
    for region, data in regional_data.items():
        avg = data["total_inclusion"] / data["count"] if data["count"] > 0 else 0
        regions.append(
            RegionalInclusion(
                region=region,
                company_count=data["count"],
                avg_inclusion_score=round(avg, 1),
                high_priority_count=data["high_priority"],
                inclusion_percentage=round(
                    data["high_priority"] / data["count"] * 100, 1
                )
                if data["count"] > 0
                else 0,
            )
        )

    # Sort by inclusion percentage descending
    regions.sort(key=lambda x: x.inclusion_percentage, reverse=True)

    # Calculate totals
    total_companies = sum(r.company_count for r in regions)
    total_high_priority = sum(r.high_priority_count for r in regions)

    return InclusionAnalysis(
        regions=regions,
        total_companies=total_companies,
        total_high_priority=total_high_priority,
        overall_inclusion_rate=round(total_high_priority / total_companies * 100, 1)
        if total_companies > 0
        else 0,
    )


# Need to import Integer for cast
from sqlalchemy import Integer


@router.get("/lender-flows", response_model=list[LenderFlow])
async def get_lender_flows(db: Session = Depends(get_db)):
    """Get current vs optimal portfolio distribution by lender"""
    lenders = db.query(Lender).all()

    flows = []
    for lender in lenders:
        # Current portfolio
        current_count = (
            db.query(Loan).filter(Loan.current_lender_id == lender.id).count()
        )
        current_value = (
            db.query(func.sum(Loan.outstanding_balance))
            .filter(Loan.current_lender_id == lender.id)
            .scalar()
            or 0
        )

        # Optimal portfolio (where this lender is best match)
        optimal_count = (
            db.query(Loan).filter(Loan.best_match_lender_id == lender.id).count()
        )
        optimal_value = (
            db.query(func.sum(Loan.outstanding_balance))
            .filter(Loan.best_match_lender_id == lender.id)
            .scalar()
            or 0
        )

        # Inbound (loans from others that fit better here)
        inbound_count = (
            db.query(Loan)
            .filter(
                Loan.best_match_lender_id == lender.id,
                Loan.current_lender_id != lender.id,
            )
            .count()
        )

        # Outbound (loans here that fit better elsewhere)
        outbound_count = (
            db.query(Loan)
            .filter(
                Loan.current_lender_id == lender.id,
                Loan.best_match_lender_id != lender.id,
                Loan.is_unalign == True,
            )
            .count()
        )

        flows.append(
            LenderFlow(
                lender_id=lender.id,
                lender_name=lender.name,
                current_count=current_count,
                current_value=current_value,
                optimal_count=optimal_count,
                optimal_value=optimal_value,
                inbound_count=inbound_count,
                outbound_count=outbound_count,
                net_flow=inbound_count - outbound_count,
            )
        )

    return flows


@router.get("/reallocation-stats", response_model=ReallocationStats)
async def get_reallocation_stats(db: Session = Depends(get_db)):
    """Get overall reallocation statistics"""
    # Total loans
    total_loans = db.query(Loan).count()

    # Unaligned loans
    unaligned = db.query(Loan).filter(Loan.is_unalign == True).all()
    unaligned_count = len(unaligned)

    # Total value at risk (sum of unaligned loan values)
    total_value = sum(l.outstanding_balance for l in unaligned)

    # Average fit improvement
    avg_improvement = (
        db.query(func.avg(Loan.fit_gap)).filter(Loan.is_unalign == True).scalar() or 0
    )

    # By reallocation status
    strong = len([l for l in unaligned if l.reallocation_status == "STRONG"])
    moderate = len([l for l in unaligned if l.reallocation_status == "MODERATE"])
    minor = len([l for l in unaligned if l.reallocation_status == "MINOR"])

    # High inclusion priority among unaligned
    high_inclusion_unaligned = (
        db.query(Loan)
        .join(Company, Loan.company_id == Company.id)
        .filter(
            Loan.is_unalign == True,
            Company.inclusion_score >= 60,
        )
        .count()
    )

    return ReallocationStats(
        total_loans=total_loans,
        unaligned_count=unaligned_count,
        unaligned_percentage=round(unaligned_count / total_loans * 100, 1)
        if total_loans > 0
        else 0,
        total_value_at_risk=total_value,
        avg_fit_improvement=round(avg_improvement, 1),
        strong_reallocation_count=strong,
        moderate_reallocation_count=moderate,
        minor_reallocation_count=minor,
        high_inclusion_priority_count=high_inclusion_unaligned,
    )
