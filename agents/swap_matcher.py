"""
Agent: SwapMatcher
Identifies complementary mismatches between lenders for potential swaps.

A swap is complementary when:
- Lender A holds Loan X that fits Lender B better
- Lender B holds Loan Y that fits Lender A better
- Both loans are mismatches for current holders
"""

import pandas as pd
from typing import List, Dict, Optional, Tuple
from utils.anonymizer import round_score, band_loan_amount


class SwapMatcher:
    """
    Identifies complementary loan swap opportunities between lenders.

    Swaps are ranked by:
    1. Combined fit improvement (how much both parties benefit)
    2. Inclusion bonus (extra points for swaps involving underserved companies)
    """

    def __init__(self, min_fit_improvement: int = 15, value_tolerance: float = 0.20):
        """
        Initialize the swap matcher.

        Args:
            min_fit_improvement: Minimum fit gap required for a loan to be considered mismatched
            value_tolerance: Maximum value difference ratio for swap compatibility (e.g., 0.20 = 20%)
        """
        self.min_fit_improvement = min_fit_improvement
        self.value_tolerance = value_tolerance

    def find_complementary_swaps(self, df: pd.DataFrame) -> List[Dict]:
        """
        Find all complementary swap pairs ranked by score.

        Args:
            df: DataFrame with company/loan data including:
                - Current_Lender
                - Best_Match_Lender
                - Fit_Gap (Best_Match_Fit - Current_Lender_Fit)
                - Outstanding_Balance
                - Inclusion_Score
                - Inclusion_Flags

        Returns:
            List of swap records sorted by swap_score (descending)
        """
        swaps = []
        seen_pairs = set()  # Track (loan_a, loan_b) pairs to avoid duplicates

        # Get list of unique lenders
        lenders = df['Current_Lender'].unique()

        for lender_A in lenders:
            # Find loans that lender A holds that are mismatched
            a_mismatched = df[
                (df['Current_Lender'] == lender_A) &
                (df['Fit_Gap'] >= self.min_fit_improvement)
            ]

            for _, loan_X in a_mismatched.iterrows():
                lender_B = loan_X['Best_Match_Lender']

                # Skip if lender_B is the same as lender_A
                if lender_B == lender_A:
                    continue

                # Find complementary: loans B holds that fit A better
                b_to_a = df[
                    (df['Current_Lender'] == lender_B) &
                    (df['Best_Match_Lender'] == lender_A) &
                    (df['Fit_Gap'] >= self.min_fit_improvement)
                ]

                for _, loan_Y in b_to_a.iterrows():
                    # Create a canonical pair ID to avoid duplicates
                    pair_id = tuple(sorted([loan_X['SME_ID'], loan_Y['SME_ID']]))
                    if pair_id in seen_pairs:
                        continue
                    seen_pairs.add(pair_id)

                    # Check value compatibility
                    if self._check_value_compatibility(loan_X, loan_Y):
                        swap = self._create_swap_record(loan_X, loan_Y, lender_A, lender_B)
                        swaps.append(swap)

        # Sort by swap_score descending
        return sorted(swaps, key=lambda x: x['swap_score'], reverse=True)

    def find_swaps_for_lender(self, df: pd.DataFrame, lender: str) -> List[Dict]:
        """
        Find swap opportunities relevant to a specific lender.

        Args:
            df: DataFrame with company/loan data
            lender: The lender to find swaps for

        Returns:
            List of swap records where this lender is involved
        """
        all_swaps = self.find_complementary_swaps(df)
        return [s for s in all_swaps if s['lender_a'] == lender or s['lender_b'] == lender]

    def _check_value_compatibility(self, loan_a: pd.Series, loan_b: pd.Series) -> bool:
        """
        Check if two loans have compatible values for a swap.

        Args:
            loan_a: First loan
            loan_b: Second loan

        Returns:
            True if loans are within value tolerance of each other
        """
        val_a = loan_a.get('Outstanding_Balance', 0)
        val_b = loan_b.get('Outstanding_Balance', 0)

        if val_a <= 0 or val_b <= 0:
            return False

        value_ratio = val_a / val_b

        # Check if within tolerance (e.g., 0.83 to 1.20 for 20% tolerance)
        min_ratio = 1 / (1 + self.value_tolerance)
        max_ratio = 1 + self.value_tolerance

        return min_ratio <= value_ratio <= max_ratio

    def _create_swap_record(
        self,
        loan_a: pd.Series,
        loan_b: pd.Series,
        lender_a: str,
        lender_b: str
    ) -> Dict:
        """
        Create a swap record from two complementary loans.

        Args:
            loan_a: Loan held by lender_a that fits lender_b
            loan_b: Loan held by lender_b that fits lender_a
            lender_a: First lender
            lender_b: Second lender

        Returns:
            Dict with swap details
        """
        # Calculate fit improvements
        fit_improvement_a = loan_a.get('Fit_Gap', 0)
        fit_improvement_b = loan_b.get('Fit_Gap', 0)
        total_fit_improvement = fit_improvement_a + fit_improvement_b

        # Calculate inclusion bonus
        inclusion_bonus = self._calculate_inclusion_bonus(loan_a, loan_b)

        # Calculate value difference for potential cash adjustment
        val_a = loan_a.get('Outstanding_Balance', 0)
        val_b = loan_b.get('Outstanding_Balance', 0)
        value_diff = abs(val_a - val_b)
        value_diff_pct = (value_diff / max(val_a, val_b)) * 100 if max(val_a, val_b) > 0 else 0

        return {
            # Lender info
            'lender_a': lender_a,
            'lender_b': lender_b,

            # Loan A details (held by lender_a, fits lender_b)
            'loan_a_id': loan_a['SME_ID'],
            'loan_a_sector': loan_a.get('Sector', 'Unknown'),
            'loan_a_region': loan_a.get('Region', 'Unknown'),
            'loan_a_outstanding': val_a,
            'loan_a_outstanding_band': band_loan_amount(val_a),
            'loan_a_current_fit': loan_a.get('Current_Lender_Fit', 0),
            'loan_a_new_fit': loan_a.get('Best_Match_Fit', 0),
            'loan_a_fit_gap': fit_improvement_a,
            'loan_a_inclusion_score': loan_a.get('Inclusion_Score', 0),
            'loan_a_years_remaining': loan_a.get('Years_Remaining', 0),

            # Loan B details (held by lender_b, fits lender_a)
            'loan_b_id': loan_b['SME_ID'],
            'loan_b_sector': loan_b.get('Sector', 'Unknown'),
            'loan_b_region': loan_b.get('Region', 'Unknown'),
            'loan_b_outstanding': val_b,
            'loan_b_outstanding_band': band_loan_amount(val_b),
            'loan_b_current_fit': loan_b.get('Current_Lender_Fit', 0),
            'loan_b_new_fit': loan_b.get('Best_Match_Fit', 0),
            'loan_b_fit_gap': fit_improvement_b,
            'loan_b_inclusion_score': loan_b.get('Inclusion_Score', 0),
            'loan_b_years_remaining': loan_b.get('Years_Remaining', 0),

            # Swap metrics
            'total_fit_improvement': total_fit_improvement,
            'inclusion_bonus': inclusion_bonus,
            'swap_score': total_fit_improvement + inclusion_bonus,
            'is_inclusion_swap': inclusion_bonus > 0,

            # Value adjustment
            'value_difference': value_diff,
            'value_difference_pct': value_diff_pct,
            'needs_cash_adjustment': value_diff_pct > 5,  # Flag if >5% difference
        }

    def _calculate_inclusion_bonus(self, loan_a: pd.Series, loan_b: pd.Series) -> float:
        """
        Calculate inclusion bonus for the swap.

        Bonuses:
        - +10 points for each loan with Inclusion_Score >= 60
        - +5 points for each loan flagged as "Strong but Overlooked"

        Args:
            loan_a: First loan
            loan_b: Second loan

        Returns:
            Total inclusion bonus
        """
        bonus = 0

        for loan in [loan_a, loan_b]:
            # High inclusion score bonus
            inclusion_score = loan.get('Inclusion_Score', 0)
            if inclusion_score >= 60:
                bonus += 10

            # Strong but overlooked bonus
            flags = loan.get('Inclusion_Flags', [])
            if isinstance(flags, list) and 'Strong but Overlooked' in flags:
                bonus += 5
            elif isinstance(flags, str) and 'Strong but Overlooked' in flags:
                bonus += 5

        return bonus

    def get_swap_summary(self, swap: Dict, for_lender: str) -> Dict:
        """
        Get a summary of a swap from a specific lender's perspective.

        Args:
            swap: Swap record
            for_lender: The lender viewing this swap

        Returns:
            Dict with swap summary from that lender's perspective
        """
        if for_lender == swap['lender_a']:
            # Lender A gives loan_a, receives loan_b
            return {
                'you_give': {
                    'loan_id': swap['loan_a_id'],
                    'sector': swap['loan_a_sector'],
                    'outstanding_band': swap['loan_a_outstanding_band'],
                    'your_fit': round_score(swap['loan_a_current_fit']),
                    'their_fit': round_score(swap['loan_a_new_fit']),
                },
                'you_receive': {
                    'loan_id': swap['loan_b_id'],
                    'sector': swap['loan_b_sector'],
                    'outstanding_band': swap['loan_b_outstanding_band'],
                    'your_fit': round_score(swap['loan_b_new_fit']),
                    'their_fit': round_score(swap['loan_b_current_fit']),
                },
                'counterparty': swap['lender_b'],
                'total_fit_improvement': swap['total_fit_improvement'],
                'is_inclusion_swap': swap['is_inclusion_swap'],
                'needs_cash_adjustment': swap['needs_cash_adjustment'],
            }
        else:
            # Lender B gives loan_b, receives loan_a
            return {
                'you_give': {
                    'loan_id': swap['loan_b_id'],
                    'sector': swap['loan_b_sector'],
                    'outstanding_band': swap['loan_b_outstanding_band'],
                    'your_fit': round_score(swap['loan_b_current_fit']),
                    'their_fit': round_score(swap['loan_b_new_fit']),
                },
                'you_receive': {
                    'loan_id': swap['loan_a_id'],
                    'sector': swap['loan_a_sector'],
                    'outstanding_band': swap['loan_a_outstanding_band'],
                    'your_fit': round_score(swap['loan_a_new_fit']),
                    'their_fit': round_score(swap['loan_a_current_fit']),
                },
                'counterparty': swap['lender_a'],
                'total_fit_improvement': swap['total_fit_improvement'],
                'is_inclusion_swap': swap['is_inclusion_swap'],
                'needs_cash_adjustment': swap['needs_cash_adjustment'],
            }


def get_swap_statistics(swaps: List[Dict]) -> Dict:
    """
    Calculate statistics about available swaps.

    Args:
        swaps: List of swap records

    Returns:
        Dict with swap statistics
    """
    if not swaps:
        return {
            'total_swaps': 0,
            'inclusion_swaps': 0,
            'avg_fit_improvement': 0,
            'swaps_needing_cash': 0,
        }

    return {
        'total_swaps': len(swaps),
        'inclusion_swaps': sum(1 for s in swaps if s['is_inclusion_swap']),
        'avg_fit_improvement': sum(s['total_fit_improvement'] for s in swaps) / len(swaps),
        'swaps_needing_cash': sum(1 for s in swaps if s['needs_cash_adjustment']),
    }


if __name__ == "__main__":
    # Test the swap matcher
    print("Testing SwapMatcher...")

    # Create sample data
    import numpy as np

    sample_data = {
        'SME_ID': ['SME_0001', 'SME_0002', 'SME_0003', 'SME_0004'],
        'Current_Lender': ['Alpha Bank', 'Growth Capital Partners', 'Alpha Bank', 'Growth Capital Partners'],
        'Best_Match_Lender': ['Growth Capital Partners', 'Alpha Bank', 'Regional Development Fund', 'Alpha Bank'],
        'Current_Lender_Fit': [35, 40, 45, 38],
        'Best_Match_Fit': [75, 72, 80, 70],
        'Fit_Gap': [40, 32, 35, 32],
        'Outstanding_Balance': [1_500_000, 1_400_000, 2_000_000, 1_200_000],
        'Sector': ['Clean_Energy', 'Financial', 'Advanced_Manufacturing', 'Digital&Technologies'],
        'Region': ['Scotland', 'London', 'North West', 'South East'],
        'Inclusion_Score': [65, 45, 70, 42],
        'Inclusion_Flags': [['Strong but Overlooked'], [], ['Underserved Region'], []],
        'Years_Remaining': [3, 2, 4, 3],
    }

    df = pd.DataFrame(sample_data)

    matcher = SwapMatcher()
    swaps = matcher.find_complementary_swaps(df)

    print(f"\nFound {len(swaps)} complementary swaps:")
    for i, swap in enumerate(swaps, 1):
        print(f"\n--- Swap {i} ---")
        print(f"  {swap['lender_a']} <-> {swap['lender_b']}")
        print(f"  Loan A: {swap['loan_a_id']} ({swap['loan_a_sector']})")
        print(f"  Loan B: {swap['loan_b_id']} ({swap['loan_b_sector']})")
        print(f"  Total Fit Improvement: +{swap['total_fit_improvement']}")
        print(f"  Inclusion Bonus: +{swap['inclusion_bonus']}")
        print(f"  Swap Score: {swap['swap_score']}")
        print(f"  Is Inclusion Swap: {swap['is_inclusion_swap']}")

    print("\n--- Statistics ---")
    stats = get_swap_statistics(swaps)
    for key, value in stats.items():
        print(f"  {key}: {value}")
