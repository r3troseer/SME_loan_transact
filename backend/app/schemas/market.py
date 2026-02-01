from pydantic import BaseModel
from typing import List


class RegionalInclusion(BaseModel):
    region: str
    company_count: int
    avg_inclusion_score: float
    high_priority_count: int
    inclusion_percentage: float


class InclusionAnalysis(BaseModel):
    regions: List[RegionalInclusion]
    total_companies: int
    total_high_priority: int
    overall_inclusion_rate: float


class LenderFlow(BaseModel):
    lender_id: int
    lender_name: str
    current_count: int
    current_value: float
    optimal_count: int
    optimal_value: float
    inbound_count: int
    outbound_count: int
    net_flow: int


class ReallocationStats(BaseModel):
    total_loans: int
    unaligned_count: int
    unaligned_percentage: float
    total_value_at_risk: float
    avg_fit_improvement: float
    strong_reallocation_count: int
    moderate_reallocation_count: int
    minor_reallocation_count: int
    high_inclusion_priority_count: int
