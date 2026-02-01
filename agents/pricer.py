"""
Agent 4: Pricer
Calculates loan valuations, suggested transaction prices, and ROI metrics
for potential loan sales/swaps.
"""

import pandas as pd
import numpy as np
from typing import Dict
from utils.anonymizer import (
    anonymize_lender, round_score, band_percentage,
    band_loan_amount, format_amount_range, band_portfolio_total
)


class Pricer:
    """
    Calculates fair prices for loan transactions and ROI for potential buyers.
    """

    # Industry standard assumptions
    RECOVERY_RATE = 0.40  # Average recovery rate on defaulted SME loans
    BASE_DISCOUNT_RATE = 0.05  # 5% annual discount rate

    def __init__(self):
        # Default probability mapping based on risk score
        self.default_prob_map = {
            (80, 100): 0.01,   # 1% default probability
            (70, 80): 0.02,    # 2%
            (60, 70): 0.03,    # 3%
            (50, 60): 0.05,    # 5%
            (40, 50): 0.08,    # 8%
            (30, 40): 0.12,    # 12%
            (0, 30): 0.18      # 18%
        }

    def analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate pricing metrics for all companies.

        Args:
            df: DataFrame with company data, risk scores, and fit scores

        Returns:
            DataFrame with added pricing columns
        """
        # Estimate default probability
        df['Default_Probability'] = df['Risk_Score'].apply(self._estimate_default_probability)

        # Calculate remaining payments
        df['Remaining_Payments'] = df.apply(self._calculate_remaining_payments, axis=1)

        # Calculate gross loan value
        df['Gross_Loan_Value'] = df['Remaining_Payments']

        # Calculate risk-adjusted value
        df['Expected_Loss'] = df.apply(
            lambda row: row['Default_Probability'] * (1 - self.RECOVERY_RATE) * row['Outstanding_Balance'],
            axis=1
        )
        df['Risk_Adjusted_Value'] = df['Gross_Loan_Value'] - df['Expected_Loss']

        # Calculate misfit discount (seller motivation to exit)
        df['Misfit_Discount'] = df['Current_Lender_Fit'].apply(self._calculate_misfit_discount)

        # Calculate suggested price
        df['Suggested_Price'] = df['Risk_Adjusted_Value'] * (1 - df['Misfit_Discount'])

        # Calculate discount from face value
        df['Discount_Percent'] = (1 - df['Suggested_Price'] / df['Outstanding_Balance']) * 100

        # Calculate buyer ROI metrics
        roi_metrics = df.apply(self._calculate_buyer_roi, axis=1)
        df['Gross_ROI'] = roi_metrics.apply(lambda x: x['gross_roi'])
        df['Risk_Adjusted_ROI'] = roi_metrics.apply(lambda x: x['risk_adjusted_roi'])
        df['Annualized_ROI'] = roi_metrics.apply(lambda x: x['annualized_roi'])

        return df

    def _estimate_default_probability(self, risk_score: float) -> float:
        """Estimate probability of default based on risk score."""
        if pd.isna(risk_score):
            return 0.05  # Default assumption

        for (low, high), prob in self.default_prob_map.items():
            if low <= risk_score < high:
                return prob

        return 0.05  # Fallback

    def _calculate_remaining_payments(self, row: pd.Series) -> float:
        """Calculate total remaining payments on the loan."""
        monthly_payment = row.get('Monthly_Payment', 0)
        years_remaining = row.get('Years_Remaining', 0)
        months_remaining = years_remaining * 12

        return monthly_payment * months_remaining

    def _calculate_misfit_discount(self, current_fit: float) -> float:
        """
        Calculate discount based on how poorly the loan fits current lender.
        Lower fit = higher motivation to sell = larger discount accepted.
        """
        if pd.isna(current_fit):
            return 0.10  # Default 10% discount

        if current_fit >= 70:
            return 0.0  # Good fit, no discount needed
        elif current_fit >= 60:
            return 0.03  # 3% discount
        elif current_fit >= 50:
            return 0.07  # 7% discount
        elif current_fit >= 40:
            return 0.12  # 12% discount
        elif current_fit >= 30:
            return 0.18  # 18% discount
        else:
            return 0.25  # Max 25% discount for very poor fit

    def _calculate_buyer_roi(self, row: pd.Series) -> Dict:
        """Calculate ROI metrics for a potential buyer."""
        purchase_price = row.get('Suggested_Price', 0)
        remaining_payments = row.get('Remaining_Payments', 0)
        expected_loss = row.get('Expected_Loss', 0)
        years_remaining = row.get('Years_Remaining', 1)

        if purchase_price <= 0:
            return {'gross_roi': 0, 'risk_adjusted_roi': 0, 'annualized_roi': 0}

        # Gross ROI (before risk adjustment)
        gross_profit = remaining_payments - purchase_price
        gross_roi = gross_profit / purchase_price

        # Risk-adjusted ROI
        risk_adjusted_profit = gross_profit - expected_loss
        risk_adjusted_roi = risk_adjusted_profit / purchase_price

        # Annualized ROI
        if years_remaining > 0:
            annualized_roi = risk_adjusted_roi / years_remaining
        else:
            annualized_roi = risk_adjusted_roi

        return {
            'gross_roi': round(gross_roi * 100, 2),
            'risk_adjusted_roi': round(risk_adjusted_roi * 100, 2),
            'annualized_roi': round(annualized_roi * 100, 2)
        }

    def get_pricing_details(self, company: pd.Series, anonymize: bool = False, for_table: bool = False) -> Dict:
        """
        Get detailed pricing breakdown for a single company.

        Args:
            company: Company data row
            anonymize: If True, band financial values and round percentages
            for_table: If True, use bands; if False use ranges (only when anonymize=True)
        """
        outstanding = company.get('Outstanding_Balance', 0)
        suggested_price = company.get('Suggested_Price', 0)
        discount_pct = company.get('Discount_Percent', 0)
        roi = company.get('Annualized_ROI', 0)

        if anonymize:
            if for_table:
                outstanding_display = band_loan_amount(outstanding)
                price_display = band_loan_amount(suggested_price)
            else:
                outstanding_display = format_amount_range(outstanding)
                price_display = format_amount_range(suggested_price)

            discount_display = band_percentage(discount_pct)
            roi_display = band_percentage(roi)
            risk_display = round_score(company.get('Risk_Score', 0))
            current_fit_display = round_score(company.get('Current_Lender_Fit', 0))
            best_fit_display = round_score(company.get('Best_Match_Fit', 0))
        else:
            outstanding_display = outstanding
            price_display = suggested_price
            discount_display = discount_pct
            roi_display = roi
            risk_display = company.get('Risk_Score', 0)
            current_fit_display = company.get('Current_Lender_Fit', 0)
            best_fit_display = company.get('Best_Match_Fit', 0)

        return {
            'company_id': company.get('SME_ID', 'Unknown'),
            'loan_details': {
                'original_amount': company.get('Loan_Amount', 0) if not anonymize else None,
                'outstanding_balance': outstanding_display,
                'years_remaining': company.get('Years_Remaining', 0),
                'monthly_payment': company.get('Monthly_Payment', 0) if not anonymize else None,
                'interest_rate': company.get('Interest_Rate', 0) if not anonymize else None
            },
            'valuation': {
                'remaining_payments': company.get('Remaining_Payments', 0) if not anonymize else None,
                'gross_value': company.get('Gross_Loan_Value', 0) if not anonymize else None,
                'expected_loss': company.get('Expected_Loss', 0) if not anonymize else None,
                'risk_adjusted_value': company.get('Risk_Adjusted_Value', 0) if not anonymize else None
            },
            'pricing': {
                'misfit_discount': company.get('Misfit_Discount', 0) if not anonymize else None,
                'suggested_price': price_display,
                'discount_from_face': discount_display
            },
            'buyer_metrics': {
                'gross_roi': company.get('Gross_ROI', 0) if not anonymize else None,
                'risk_adjusted_roi': company.get('Risk_Adjusted_ROI', 0) if not anonymize else None,
                'annualized_roi': roi_display,
                'default_probability': company.get('Default_Probability', 0) if not anonymize else None
            },
            'risk_context': {
                'risk_score': risk_display,
                'current_fit': current_fit_display,
                'best_fit': best_fit_display
            }
        }

    def format_price(self, value: float) -> str:
        """Format a price value for display."""
        if value >= 1_000_000:
            return f"£{value/1_000_000:.2f}M"
        elif value >= 1_000:
            return f"£{value/1_000:.1f}K"
        else:
            return f"£{value:.2f}"

    def get_transaction_summary(self, company: pd.Series, transaction_type: str = 'sale', anonymize: bool = False) -> Dict:
        """
        Get a summary suitable for transaction display.

        Args:
            company: Series with company and pricing data
            transaction_type: 'sale', 'swap', or 'swap_cash'
            anonymize: If True, anonymize buyer lender and band values
        """
        pricing = self.get_pricing_details(company, anonymize=anonymize, for_table=False)

        current_lender = company.get('Current_Lender', 'Unknown')
        best_lender = company.get('Best_Match_Lender', 'Unknown')

        # Anonymize buyer (recommended lender) but not seller (current lender)
        if anonymize:
            display_buyer = anonymize_lender(best_lender, is_current=False)
            outstanding_display = pricing['loan_details']['outstanding_balance']  # Already formatted
            price_display = pricing['pricing']['suggested_price']  # Already formatted
            discount_display = f"{pricing['pricing']['discount_from_face']}%"
            roi_display = f"{pricing['buyer_metrics']['annualized_roi']}%"
            risk_display = f"Risk Score {pricing['risk_context']['risk_score']}/100"
            fit_improvement = round_score(pricing['risk_context']['best_fit']) - round_score(pricing['risk_context']['current_fit'])
        else:
            display_buyer = best_lender
            outstanding_display = self.format_price(company.get('Outstanding_Balance', 0))
            price_display = self.format_price(company.get('Suggested_Price', 0))
            discount_display = f"{company.get('Discount_Percent', 0):.1f}%"
            roi_display = f"{company.get('Annualized_ROI', 0):.1f}%"
            risk_display = f"Risk Score {company.get('Risk_Score', 0):.0f}/100"
            fit_improvement = company.get('Best_Match_Fit', 0) - company.get('Current_Lender_Fit', 0)

        summary = {
            'transaction_type': transaction_type,
            'seller': current_lender,  # Current lender always visible
            'buyer': display_buyer,  # Anonymized if requested
            'loan_outstanding': outstanding_display,
            'suggested_price': price_display,
            'discount': discount_display,
            'buyer_roi': roi_display,
            'risk_profile': risk_display,
            'fit_improvement': f"+{fit_improvement:.0f} points"
        }

        if transaction_type == 'swap':
            summary['note'] = "Swap transaction - look for matching loan from buyer's portfolio"
        elif transaction_type == 'swap_cash':
            summary['note'] = "Swap with cash adjustment for value difference"

        return summary

    def get_market_pricing_stats(self, df: pd.DataFrame, anonymize: bool = False) -> Dict:
        """
        Get market-level pricing statistics.

        Args:
            df: DataFrame with pricing data
            anonymize: If True, band aggregate values
        """
        # Only look at reallocation candidates
        candidates = df[df['Is_Mismatch'] == True]

        if len(candidates) == 0:
            return {'message': 'No reallocation candidates found'}

        total_outstanding = candidates['Outstanding_Balance'].sum()
        total_suggested = candidates['Suggested_Price'].sum()
        avg_discount = candidates['Discount_Percent'].mean()
        avg_roi = candidates['Annualized_ROI'].mean()

        if anonymize:
            outstanding_display = band_portfolio_total(total_outstanding)
            suggested_display = band_portfolio_total(total_suggested)
            discount_display = f"{band_percentage(avg_discount)}%"
            roi_display = f"{band_percentage(avg_roi)}%"
        else:
            outstanding_display = self.format_price(total_outstanding)
            suggested_display = self.format_price(total_suggested)
            discount_display = f"{avg_discount:.1f}%"
            roi_display = f"{avg_roi:.1f}%"

        return {
            'candidates_count': len(candidates),
            'total_value': {
                'outstanding': outstanding_display,
                'suggested_prices': suggested_display
            },
            'average_discount': discount_display,
            'average_buyer_roi': roi_display,
            'discount_distribution': {
                '<5%': len(candidates[candidates['Discount_Percent'] < 5]),
                '5-10%': len(candidates[(candidates['Discount_Percent'] >= 5) & (candidates['Discount_Percent'] < 10)]),
                '10-15%': len(candidates[(candidates['Discount_Percent'] >= 10) & (candidates['Discount_Percent'] < 15)]),
                '15-20%': len(candidates[(candidates['Discount_Percent'] >= 15) & (candidates['Discount_Percent'] < 20)]),
                '>20%': len(candidates[candidates['Discount_Percent'] >= 20])
            },
            'roi_distribution': {
                '<5%': len(candidates[candidates['Annualized_ROI'] < 5]),
                '5-10%': len(candidates[(candidates['Annualized_ROI'] >= 5) & (candidates['Annualized_ROI'] < 10)]),
                '10-15%': len(candidates[(candidates['Annualized_ROI'] >= 10) & (candidates['Annualized_ROI'] < 15)]),
                '>15%': len(candidates[candidates['Annualized_ROI'] >= 15])
            }
        }


if __name__ == "__main__":
    # Test the pricer
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from utils.data_loader import load_data
    from agents.risk_analyst import RiskAnalyst
    from agents.inclusion_scanner import InclusionScanner
    from agents.matcher import Matcher

    excel_path = r"C:\Users\user\Downloads\UKFIN Hackathon_sample_file_data_GFA Exchange.xlsx"
    df = load_data(excel_path)

    # Run all previous agents
    df = RiskAnalyst().analyze(df)
    df = InclusionScanner().analyze(df)
    df = Matcher().analyze(df)

    # Run pricer
    pricer = Pricer()
    df = pricer.analyze(df)

    print("=== Market Pricing Stats ===")
    stats = pricer.get_market_pricing_stats(df)
    for key, value in stats.items():
        print(f"{key}: {value}")

    print("\n=== Sample Transaction ===")
    # Get a reallocation candidate
    candidate = df[df['Is_Mismatch'] == True].iloc[0]
    summary = pricer.get_transaction_summary(candidate, 'sale')
    for key, value in summary.items():
        print(f"{key}: {value}")

    print("\n=== Detailed Pricing ===")
    details = pricer.get_pricing_details(candidate)
    print(f"Company: {details['company_id']}")
    print(f"Outstanding: {pricer.format_price(details['loan_details']['outstanding_balance'])}")
    print(f"Suggested Price: {pricer.format_price(details['pricing']['suggested_price'])}")
    print(f"Discount: {details['pricing']['discount_from_face']:.1f}%")
    print(f"Buyer ROI: {details['buyer_metrics']['annualized_roi']:.1f}% annualized")
