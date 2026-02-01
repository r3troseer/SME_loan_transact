from pydantic import BaseModel
from typing import Optional


class PortfolioOverview(BaseModel):
    total_companies: int
    total_loan_value: float
    total_loan_value_banded: str
    unaligned_loans: int
    unalign_percentage: float
    avg_risk_score: float


class SectorDistribution(BaseModel):
    sector: str
    count: int


class RegionDistribution(BaseModel):
    region: str
    count: int


class LenderDistribution(BaseModel):
    lender: str
    count: int
    percentage: float


class CompanyListItem(BaseModel):
    id: int
    sme_id: str
    sector: str
    region: str
    turnover: Optional[float]
    risk_score: Optional[float]
    risk_category: Optional[str]
    inclusion_score: Optional[float]
    inclusion_category: Optional[str]
