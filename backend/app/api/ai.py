from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import os

from ..core.database import get_db
from ..core.config import settings
from ..models import Loan, Company, Lender
from ..schemas.ai import (
    ExplanationRequest,
    ExplanationResponse,
    MarketInsightRequest,
    MarketInsightResponse,
    SwapStoryRequest,
    SwapStoryResponse,
    CompanyInsightRequest,
    CompanyInsightResponse,
)

router = APIRouter()

# Try to import Gemini
try:
    import google.generativeai as genai

    if settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
    else:
        GEMINI_AVAILABLE = False
except ImportError:
    GEMINI_AVAILABLE = False


def generate_with_gemini(prompt: str) -> str:
    """Generate text using Gemini API"""
    if not GEMINI_AVAILABLE:
        return None

    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini error: {e}")
        return None


def generate_loan_explanation_template(
    loan, company, current_lender, best_lender
) -> str:
    """Generate explanation using template (fallback)"""
    reasons = []

    if loan.fit_gap and loan.fit_gap > 20:
        reasons.append(
            f"This loan shows a significant fit improvement of {loan.fit_gap:.0f}% with the recommended lender."
        )

    if company.inclusion_score and company.inclusion_score >= 60:
        reasons.append(
            f"The company has a high inclusion priority score of {company.inclusion_score:.0f}, indicating it serves an underserved market."
        )

    if company.risk_score and company.risk_score >= 60:
        reasons.append(
            f"With a risk score of {company.risk_score:.0f}, this company demonstrates solid financial health."
        )

    if best_lender and best_lender.inclusion_mandate:
        reasons.append(
            f"The recommended lender has an inclusion mandate, making this a mission-aligned opportunity."
        )

    if not reasons:
        reasons.append(
            "This reallocation would optimize portfolio fit for both parties."
        )

    return " ".join(reasons)


@router.post("/explanation", response_model=ExplanationResponse)
async def generate_explanation(
    request: ExplanationRequest, db: Session = Depends(get_db)
):
    """Generate AI explanation for why a loan is a good match"""
    loan = db.query(Loan).filter(Loan.id == request.loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    company = db.query(Company).filter(Company.id == loan.company_id).first()
    current_lender = (
        db.query(Lender).filter(Lender.id == loan.current_lender_id).first()
    )
    best_lender = (
        db.query(Lender).filter(Lender.id == loan.best_match_lender_id).first()
        if loan.best_match_lender_id
        else None
    )

    # Try Gemini first
    if GEMINI_AVAILABLE:
        prompt = f"""Generate a concise 2-3 sentence explanation for why this SME loan reallocation makes sense:

Company: {company.sme_id}
Sector: {company.sector}
Region: {company.region}
Risk Score: {company.risk_score:.0f}/100 ({company.risk_category})
Inclusion Score: {company.inclusion_score:.0f}/100 ({company.inclusion_category})

Current Lender Fit: {loan.current_lender_fit:.0f}%
Best Match Fit: {loan.best_match_fit:.0f}%
Fit Improvement: {loan.fit_gap:.0f}%

Current Lender Focus: {current_lender.description if current_lender else "N/A"}
Recommended Lender Focus: {best_lender.description if best_lender else "N/A"}

Explain why this reallocation benefits both parties and the SME. Focus on risk alignment, sector expertise, and inclusion impact."""

        explanation = generate_with_gemini(prompt)
        if explanation:
            return ExplanationResponse(
                loan_id=request.loan_id, explanation=explanation, generated_by="gemini"
            )

    # Fallback to template
    explanation = generate_loan_explanation_template(
        loan, company, current_lender, best_lender
    )
    return ExplanationResponse(
        loan_id=request.loan_id, explanation=explanation, generated_by="template"
    )


@router.post("/market-insight", response_model=MarketInsightResponse)
async def generate_market_insight(
    request: MarketInsightRequest, db: Session = Depends(get_db)
):
    """Generate AI market insight"""
    # Gather market stats
    from sqlalchemy import func

    total_companies = db.query(Company).count()
    unaligned_loans = db.query(Loan).filter(Loan.is_unalign == True).count()
    high_inclusion = db.query(Company).filter(Company.inclusion_score >= 60).count()
    avg_fit_gap = (
        db.query(func.avg(Loan.fit_gap)).filter(Loan.is_unalign == True).scalar() or 0
    )

    if GEMINI_AVAILABLE:
        prompt = f"""Generate a brief market insight (2-3 sentences) about SME loan reallocation opportunities:

Total SMEs: {total_companies}
Unaligned Loans: {unaligned_loans} ({unaligned_loans / total_companies * 100:.1f}%)
High Inclusion Priority: {high_inclusion}
Average Fit Improvement Potential: {avg_fit_gap:.1f}%

Focus area: {request.focus_area or "general market opportunity"}

Be specific about opportunities and actionable insights."""

        insight = generate_with_gemini(prompt)
        if insight:
            return MarketInsightResponse(insight=insight, generated_by="gemini")

    # Fallback
    insight = f"The market shows {unaligned_loans} loans with reallocation potential, representing a {avg_fit_gap:.1f}% average fit improvement opportunity. {high_inclusion} companies qualify as high inclusion priority."
    return MarketInsightResponse(insight=insight, generated_by="template")


@router.post("/swap-story", response_model=SwapStoryResponse)
async def generate_swap_story(request: SwapStoryRequest, db: Session = Depends(get_db)):
    """Generate AI inclusion story for a swap"""
    loan1 = db.query(Loan).filter(Loan.id == request.loan1_id).first()
    loan2 = db.query(Loan).filter(Loan.id == request.loan2_id).first()

    if not loan1 or not loan2:
        raise HTTPException(status_code=404, detail="One or both loans not found")

    company1 = db.query(Company).filter(Company.id == loan1.company_id).first()
    company2 = db.query(Company).filter(Company.id == loan2.company_id).first()

    if GEMINI_AVAILABLE:
        prompt = f"""Generate an inspiring 2-3 sentence story about how this loan swap promotes financial inclusion:

Swap Details:
- Company A: {company1.sector} in {company1.region}, Inclusion Score: {company1.inclusion_score:.0f}
- Company B: {company2.sector} in {company2.region}, Inclusion Score: {company2.inclusion_score:.0f}

Inclusion flags for A: {", ".join(company1.inclusion_flags or ["None"])}
Inclusion flags for B: {", ".join(company2.inclusion_flags or ["None"])}

Focus on the human impact and how better-matched lenders can support underserved businesses."""

        story = generate_with_gemini(prompt)
        if story:
            return SwapStoryResponse(story=story, generated_by="gemini")

    # Fallback
    story = f"This swap connects {company1.sector} and {company2.sector} businesses with lenders better suited to their needs, advancing financial inclusion in {company1.region} and {company2.region}."
    return SwapStoryResponse(story=story, generated_by="template")


@router.post("/company-insight", response_model=CompanyInsightResponse)
async def generate_company_insight(
    request: CompanyInsightRequest, db: Session = Depends(get_db)
):
    """Generate AI insight for a specific company"""
    company = db.query(Company).filter(Company.id == request.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    loan = db.query(Loan).filter(Loan.company_id == company.id).first()

    if GEMINI_AVAILABLE:
        risk_str = f"{company.risk_score:.0f}" if company.risk_score else "N/A"
        inclusion_str = (
            f"{company.inclusion_score:.0f}" if company.inclusion_score else "N/A"
        )
        fit_str = f"{loan.current_lender_fit:.0f}" if loan.current_lender_fit else "N/A"
        gap_str = f"{loan.fit_gap:.0f}" if loan.fit_gap else "N/A"
        prompt = f"""Generate a brief insight (2-3 sentences) about this SME's lending situation:

Company: {company.sme_id}
Sector: {company.sector}
Region: {company.region}
Risk Score: {risk_str}/100
Inclusion Score: {inclusion_str}/100
Inclusion Flags: {", ".join(company.inclusion_flags or ["None"])}
Current Lender Fit: {fit_str}% (Fit Gap: {gap_str}%)

Provide actionable insight about this company's financial health and lending alignment."""

        insight = generate_with_gemini(prompt)
        if insight:
            return CompanyInsightResponse(
                company_id=request.company_id, insight=insight, generated_by="gemini"
            )

    # Fallback
    fit_gap_str = f"{loan.fit_gap:.0f}%" if loan.fit_gap else "N/A"
    risk_level = (
        "strong" if (company.risk_score and company.risk_score >= 60) else "moderate"
    )
    insight = f"This {company.sector} company in {company.region} shows {risk_level} financial health with a {fit_gap_str} potential fit improvement through reallocation."
    return CompanyInsightResponse(
        company_id=request.company_id, insight=insight, generated_by="template"
    )
