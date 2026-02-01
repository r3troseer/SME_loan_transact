"""Anonymization utilities for privacy-preserving data display"""

from typing import Dict

# Lender anonymization mapping (session-based in real app)
_lender_mapping: Dict[str, str] = {}
_lender_counter = 0


def anonymize_lender(lender_name: str) -> str:
    """Anonymize lender name to 'Lender A', 'Lender B', etc."""
    global _lender_counter

    if lender_name not in _lender_mapping:
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        _lender_mapping[lender_name] = f"Lender {letters[_lender_counter % 26]}"
        _lender_counter += 1

    return _lender_mapping[lender_name]


def reset_anonymization():
    """Reset anonymization mapping (for testing)"""
    global _lender_mapping, _lender_counter
    _lender_mapping = {}
    _lender_counter = 0


def group_region(region: str) -> str:
    """Group UK regions into larger categories"""
    if region is None:
        return "Unknown"

    region_groups = {
        # Northern England
        "North East": "Northern England",
        "North West": "Northern England",
        "Yorkshire and The Humber": "Northern England",
        "Yorkshire": "Northern England",
        # Midlands
        "East Midlands": "Midlands",
        "West Midlands": "Midlands",
        # Southern England
        "South East": "Southern England",
        "South West": "Southern England",
        "East of England": "Southern England",
        "East Of England": "Southern England",
        "East": "Southern England",
        # London
        "London": "Greater London",
        "Greater London": "Greater London",
        # Devolved nations
        "Scotland": "Scotland",
        "Wales": "Wales",
        "Northern Ireland": "Northern Ireland",
    }
    return region_groups.get(region, region)


def band_amount(amount: float) -> str:
    """Band financial amounts into ranges"""
    if amount is None:
        return "N/A"

    if amount < 100_000:
        return "<£100k"
    elif amount < 500_000:
        return "£100k-£500k"
    elif amount < 1_000_000:
        return "£500k-£1M"
    elif amount < 2_000_000:
        return "£1M-£2M"
    elif amount < 5_000_000:
        return "£2M-£5M"
    elif amount < 10_000_000:
        return "£5M-£10M"
    elif amount < 25_000_000:
        return "£10M-£25M"
    elif amount < 50_000_000:
        return "£25M-£50M"
    elif amount < 100_000_000:
        return "£50M-£100M"
    else:
        return ">£100M"


def band_turnover(turnover: float) -> str:
    """Band company turnover into ranges"""
    if turnover is None:
        return "N/A"

    if turnover < 1_000_000:
        return "<£1M"
    elif turnover < 5_000_000:
        return "£1M-£5M"
    elif turnover < 10_000_000:
        return "£5M-£10M"
    elif turnover < 25_000_000:
        return "£10M-£25M"
    elif turnover < 50_000_000:
        return "£25M-£50M"
    elif turnover < 100_000_000:
        return "£50M-£100M"
    else:
        return ">£100M"


def round_score(score: float, nearest: int = 5) -> float:
    """Round score to nearest value"""
    if score is None:
        return None
    return round(score / nearest) * nearest


def band_percentage(pct: float) -> float:
    """Round percentage to nearest 5%"""
    if pct is None:
        return None
    return round(pct / 5) * 5
