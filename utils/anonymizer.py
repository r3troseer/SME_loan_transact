"""
Anonymization utilities for the GFA Loan Sandbox.

This module provides functions to anonymize sensitive data while maintaining
analytical value. Key principle: Current lender visible, alternatives anonymized.
"""

from typing import Dict, List, Optional, Tuple


# Geographic groupings
REGION_GROUPS = {
    'London': 'Southern England',
    'South East': 'Southern England',
    'South West': 'Southern England',
    'East of England': 'Midlands & East',
    'West Midlands': 'Midlands & East',
    'East Midlands': 'Midlands & East',
    'North West': 'Northern England',
    'North East': 'Northern England',
    'Yorkshire': 'Northern England',
    'Yorkshire and the Humber': 'Northern England',
    'Scotland': 'Scotland',
    'Wales': 'Wales',
    'Northern Ireland': 'Northern Ireland',
}

# Loan amount bands
LOAN_BANDS = [
    (1_000_000, '<£1m'),
    (5_000_000, '£1-5m'),
    (10_000_000, '£5-10m'),
    (50_000_000, '£10-50m'),
    (float('inf'), '>£50m'),
]

# Turnover bands
TURNOVER_BANDS = [
    (5_000_000, '<£5m'),
    (25_000_000, '£5-25m'),
    (100_000_000, '£25-100m'),
    (float('inf'), '>£100m'),
]

# Portfolio total bands
PORTFOLIO_BANDS = [
    (50_000_000, '<£50m'),
    (100_000_000, '£50-100m'),
    (250_000_000, '£100-250m'),
    (float('inf'), '>£250m'),
]

# Lender anonymization mapping (maintained per session)
_lender_mapping: Dict[str, str] = {}
_lender_counter = 0


def reset_lender_mapping():
    """Reset the lender anonymization mapping (call at start of new context)."""
    global _lender_mapping, _lender_counter
    _lender_mapping = {}
    _lender_counter = 0


def anonymize_lender(
    name: str,
    is_current: bool = False,
    context: str = "default"
) -> str:
    """
    Anonymize a lender name.

    Args:
        name: The actual lender name
        is_current: If True, return the actual name (current lender is visible)
        context: Context identifier for different anonymization scopes

    Returns:
        The actual name if is_current, otherwise an anonymized identifier
    """
    global _lender_mapping, _lender_counter

    if is_current:
        return name

    # Check if we already have a mapping for this lender
    key = f"{context}:{name}"
    if key not in _lender_mapping:
        _lender_counter += 1
        # Use letters A, B, C, etc.
        letter = chr(ord('A') + (_lender_counter - 1) % 26)
        if _lender_counter > 26:
            letter = f"{letter}{(_lender_counter - 1) // 26}"
        _lender_mapping[key] = f"Lender {letter}"

    return _lender_mapping[key]


def anonymize_lender_for_lender_view(name: str, selected_lender: str) -> str:
    """
    Anonymize lender names for the Lender View page.

    Args:
        name: The lender name to anonymize
        selected_lender: The currently selected lender

    Returns:
        "Your Portfolio" if name matches selected_lender, otherwise anonymized
    """
    if name == selected_lender:
        return "Your Portfolio"
    return anonymize_lender(name, is_current=False, context="lender_view")


def band_loan_amount(amount: float) -> str:
    """
    Convert a loan amount to a banded range.

    Args:
        amount: The loan amount in GBP

    Returns:
        A banded string like '<£1m', '£1-5m', etc.
    """
    for threshold, band in LOAN_BANDS:
        if amount < threshold:
            return band
    return LOAN_BANDS[-1][1]


def band_turnover(amount: float) -> str:
    """
    Convert turnover to a banded range.

    Args:
        amount: The turnover in GBP

    Returns:
        A banded string like '<£5m', '£5-25m', etc.
    """
    for threshold, band in TURNOVER_BANDS:
        if amount < threshold:
            return band
    return TURNOVER_BANDS[-1][1]


def band_portfolio_total(amount: float) -> str:
    """
    Convert portfolio total to a banded range.

    Args:
        amount: The portfolio total in GBP

    Returns:
        A banded string like '<£50m', '£50-100m', etc.
    """
    for threshold, band in PORTFOLIO_BANDS:
        if amount < threshold:
            return band
    return PORTFOLIO_BANDS[-1][1]


def format_amount_range(amount: float) -> str:
    """
    Format an amount as a range for detailed views.

    Args:
        amount: The amount in GBP

    Returns:
        A range string like '£1.2-1.5m'
    """
    if amount < 1_000_000:
        # Round to nearest 100k range
        lower = (amount // 100_000) * 100_000
        upper = lower + 100_000
        return f"£{lower/1000:.0f}-{upper/1000:.0f}k"
    elif amount < 10_000_000:
        # Round to nearest 500k range
        lower = (amount // 500_000) * 500_000
        upper = lower + 500_000
        return f"£{lower/1_000_000:.1f}-{upper/1_000_000:.1f}m"
    else:
        # Round to nearest 5m range
        lower = (amount // 5_000_000) * 5_000_000
        upper = lower + 5_000_000
        return f"£{lower/1_000_000:.0f}-{upper/1_000_000:.0f}m"


def band_percentage(pct: float, interval: int = 5) -> int:
    """
    Round a percentage to the nearest interval.

    Args:
        pct: The percentage value
        interval: The rounding interval (default 5)

    Returns:
        The rounded percentage
    """
    return round(pct / interval) * interval


def round_score(score: float, interval: int = 5) -> int:
    """
    Round a score to the nearest interval.

    Args:
        score: The score value (typically 0-100)
        interval: The rounding interval (default 5)

    Returns:
        The rounded score
    """
    rounded = round(score / interval) * interval
    return max(0, min(100, rounded))  # Clamp to 0-100


def group_region(region: str) -> str:
    """
    Group a specific region into a broader geographic area.

    Args:
        region: The specific region name

    Returns:
        The grouped region name
    """
    return REGION_GROUPS.get(region, region)


def anonymize_fit_reason(reason: str, current_lender: str) -> str:
    """
    Anonymize lender names that appear in fit reason text.

    Args:
        reason: The fit reason text
        current_lender: The current lender name (should remain visible)

    Returns:
        The reason with alternative lenders anonymized
    """
    # Get list of all lender names that might appear
    from lenders.profiles import LENDERS

    result = reason
    for lender_name in LENDERS.keys():
        if lender_name != current_lender and lender_name in result:
            anon_name = anonymize_lender(lender_name, is_current=False)
            result = result.replace(lender_name, anon_name)

    return result


def anonymize_company_data(company: Dict, for_display: bool = True) -> Dict:
    """
    Anonymize company data for display.

    Args:
        company: The company data dictionary
        for_display: If True, apply display-level anonymization

    Returns:
        Anonymized company data
    """
    anon = company.copy()

    if for_display:
        # Group region
        if 'Region' in anon:
            anon['Region_Grouped'] = group_region(anon['Region'])

        # Band turnover
        if 'Turnover' in anon:
            anon['Turnover_Band'] = band_turnover(anon['Turnover'])

        # Round scores
        if 'Risk_Score' in anon:
            anon['Risk_Score_Rounded'] = round_score(anon['Risk_Score'])
        if 'Inclusion_Score' in anon:
            anon['Inclusion_Score_Rounded'] = round_score(anon['Inclusion_Score'])
        if 'Current_Lender_Fit' in anon:
            anon['Current_Lender_Fit_Rounded'] = round_score(anon['Current_Lender_Fit'])
        if 'Best_Match_Fit' in anon:
            anon['Best_Match_Fit_Rounded'] = round_score(anon['Best_Match_Fit'])

    return anon


def anonymize_pricing_data(pricing: Dict, for_table: bool = True) -> Dict:
    """
    Anonymize pricing data for display.

    Args:
        pricing: The pricing data dictionary
        for_table: If True, use bands; if False, use ranges

    Returns:
        Anonymized pricing data
    """
    anon = pricing.copy()

    loan_details = pricing.get('loan_details', {})
    pricing_info = pricing.get('pricing', {})
    buyer_metrics = pricing.get('buyer_metrics', {})

    if for_table:
        # Use bands for table display
        if 'outstanding_balance' in loan_details:
            anon['outstanding_band'] = band_loan_amount(loan_details['outstanding_balance'])
        if 'suggested_price' in pricing_info:
            anon['price_band'] = band_loan_amount(pricing_info['suggested_price'])
    else:
        # Use ranges for detailed display
        if 'outstanding_balance' in loan_details:
            anon['outstanding_range'] = format_amount_range(loan_details['outstanding_balance'])
        if 'suggested_price' in pricing_info:
            anon['price_range'] = format_amount_range(pricing_info['suggested_price'])

    # Round percentages
    if 'discount_from_face' in pricing_info:
        anon['discount_rounded'] = band_percentage(pricing_info['discount_from_face'])
    if 'annualized_roi' in buyer_metrics:
        anon['roi_rounded'] = band_percentage(buyer_metrics['annualized_roi'])

    return anon


def get_anonymized_market_stats(stats: Dict) -> Dict:
    """
    Anonymize market-level statistics.

    Args:
        stats: Market statistics dictionary

    Returns:
        Anonymized statistics
    """
    anon = stats.copy()

    # Band total values
    if 'reallocation_value' in anon:
        value = anon['reallocation_value'].get('total', 0)
        anon['reallocation_value']['banded'] = band_portfolio_total(value)

    # Round percentages
    if 'mismatched_companies' in anon:
        pct = anon['mismatched_companies'].get('percentage', 0)
        anon['mismatched_companies']['percentage_rounded'] = band_percentage(pct)

    if 'fit_scores' in anon:
        avg_imp = anon['fit_scores'].get('average_improvement', 0)
        anon['fit_scores']['average_improvement_rounded'] = round_score(avg_imp)

    return anon
