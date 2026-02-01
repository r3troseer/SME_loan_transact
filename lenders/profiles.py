"""
Synthetic Lender Profiles
Defines 4 lender archetypes with different risk appetites, sector focuses, and inclusion mandates.
"""

LENDERS = {
    "Alpha Bank": {
        "name": "Alpha Bank",
        "risk_tolerance": "low",
        "risk_score_min": 70,
        "preferred_sectors": ["Financial", "Professional_Business"],
        "sector_strategy": "Conservative, established sectors",
        "min_turnover": 20_000_000,
        "max_turnover": None,
        "preferred_regions": ["London", "South East"],
        "inclusion_mandate": False,
        "volatility_tolerance": "low",
        "description": "Conservative traditional bank focused on established businesses in financial and professional services sectors.",
        "color": "#1f77b4"  # Blue for UI
    },
    "Growth Capital Partners": {
        "name": "Growth Capital Partners",
        "risk_tolerance": "high",
        "risk_score_min": 40,
        "preferred_sectors": ["Digital&Technologies", "Clean_Energy", "Life_Science"],
        "sector_strategy": "High-growth, innovation-led sectors",
        "min_turnover": 5_000_000,
        "max_turnover": 50_000_000,
        "preferred_regions": None,  # National coverage
        "inclusion_mandate": False,
        "volatility_tolerance": "high",
        "description": "Growth-focused investor comfortable with volatility, specializing in tech, clean energy, and life sciences.",
        "color": "#2ca02c"  # Green for UI
    },
    "Regional Development Fund": {
        "name": "Regional Development Fund",
        "risk_tolerance": "medium",
        "risk_score_min": 55,
        "preferred_sectors": None,  # Sector agnostic
        "sector_strategy": "Open to all sectors - focus on regional impact",
        "min_turnover": 5_000_000,
        "max_turnover": 30_000_000,
        "preferred_regions": ["North West", "Scotland", "Wales", "North East", "Yorkshire And The Humber", "Northern Ireland"],
        "inclusion_mandate": True,
        "volatility_tolerance": "medium",
        "description": "Development fund with explicit inclusion mandate for underserved regions. Prioritizes regional economic impact.",
        "color": "#ff7f0e"  # Orange for UI
    },
    "Sector Specialist Credit": {
        "name": "Sector Specialist Credit",
        "risk_tolerance": "medium",
        "risk_score_min": 50,
        "preferred_sectors": ["Advanced_Manufacturing", "Defence"],
        "sector_strategy": "Deep expertise in manufacturing and defence sectors",
        "min_turnover": 10_000_000,
        "max_turnover": 100_000_000,
        "preferred_regions": None,  # National coverage
        "inclusion_mandate": False,
        "volatility_tolerance": "medium",
        "description": "Specialist lender with deep sector knowledge in advanced manufacturing and defence industries.",
        "color": "#9467bd"  # Purple for UI
    }
}


def get_lender(name: str) -> dict:
    """Get a lender profile by name."""
    return LENDERS.get(name, None)


def get_all_lenders() -> dict:
    """Get all lender profiles."""
    return LENDERS


def get_lender_names() -> list:
    """Get list of all lender names."""
    return list(LENDERS.keys())


def get_lender_for_display(name: str, anonymize: bool = False, is_current: bool = False) -> dict:
    """
    Get lender info formatted for UI display.

    Args:
        name: The lender name
        anonymize: If True, anonymize the lender identity
        is_current: If True, show actual name even when anonymizing (current lender)
    """
    lender = LENDERS.get(name)
    if not lender:
        return None

    sectors = lender['preferred_sectors'] if lender['preferred_sectors'] else ['All sectors']
    regions = lender['preferred_regions'] if lender['preferred_regions'] else ['National']

    # Determine display name
    if anonymize and not is_current:
        from utils.anonymizer import anonymize_lender
        display_name = anonymize_lender(name, is_current=False)
        # Also anonymize description for non-current lenders
        display_desc = f"Alternative lender with {lender['risk_tolerance']} risk tolerance"
    else:
        display_name = lender['name']
        display_desc = lender['description']

    return {
        'name': display_name,
        'description': display_desc,
        'risk_appetite': f"{lender['risk_tolerance'].title()} (min score: {lender['risk_score_min']})",
        'sectors': ', '.join(sectors),
        'regions': ', '.join(regions),
        'size_range': f"£{lender['min_turnover']/1_000_000:.0f}m - " + ('No limit' if not lender['max_turnover'] else f"£{lender['max_turnover']/1_000_000:.0f}m"),
        'inclusion_focus': 'Yes' if lender['inclusion_mandate'] else 'No',
        'color': lender['color']
    }


def get_anonymized_lender_name(name: str, current_lender: str = None) -> str:
    """
    Get anonymized lender name.

    Args:
        name: The actual lender name
        current_lender: The current lender (shown as actual name)

    Returns:
        Actual name if current lender, otherwise anonymized
    """
    from utils.anonymizer import anonymize_lender
    is_current = (name == current_lender) if current_lender else False
    return anonymize_lender(name, is_current=is_current)


if __name__ == "__main__":
    print("=== Lender Profiles ===\n")
    for name, lender in LENDERS.items():
        print(f"--- {name} ---")
        display = get_lender_for_display(name)
        for key, value in display.items():
            print(f"  {key}: {value}")
        print()
