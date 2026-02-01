"""
Agent 5: Explainer
Uses LLM (Gemini) to generate natural language explanations for
reallocation recommendations.
"""

import os
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Explainer:
    """
    Generates human-readable explanations for loan reallocation recommendations
    using Gemini API.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the explainer with API key.

        Args:
            api_key: Gemini API key. If None, tries to load from environment.
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.client = None

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                self.model = 'gemini-2.5-flash'
            except ImportError:
                print("Warning: google-genai package not installed. Using template-based explanations.")
            except Exception as e:
                print(f"Warning: Could not initialize Gemini client: {e}")

    def generate_explanation(
        self,
        company_data: Dict,
        current_lender: Dict,
        recommended_lender: Dict,
        scores: Dict,
        pricing: Dict
    ) -> str:
        """
        Generate a natural language explanation for a reallocation recommendation.

        Args:
            company_data: Company profile information
            current_lender: Current lender profile
            recommended_lender: Recommended lender profile
            scores: Risk and inclusion scores
            pricing: Pricing and ROI information

        Returns:
            Human-readable explanation string
        """
        if self.client:
            return self._generate_with_llm(
                company_data, current_lender, recommended_lender, scores, pricing
            )
        else:
            return self._generate_template(
                company_data, current_lender, recommended_lender, scores, pricing
            )

    def _generate_with_llm(
        self,
        company_data: Dict,
        current_lender: Dict,
        recommended_lender: Dict,
        scores: Dict,
        pricing: Dict
    ) -> str:
        """Generate explanation using Gemini API."""

        # Format values - handle both numeric and pre-formatted string inputs
        def format_score(val):
            if isinstance(val, str):
                return val
            return f"{val:.0f}" if val else "0"

        def format_price(val):
            if isinstance(val, str):
                return val
            return f"£{val:,.0f}" if val else "£0"

        def format_pct(val):
            if isinstance(val, str):
                return f"{val}%"
            return f"{val:.1f}%" if val else "0%"

        risk_score = format_score(scores.get('risk_score', 0))
        inclusion_score = format_score(scores.get('inclusion_score', 0))
        current_fit = format_score(scores.get('current_fit', 0))
        recommended_fit = format_score(scores.get('recommended_fit', 0))
        outstanding = format_price(pricing.get('outstanding', 0))
        suggested_price = format_price(pricing.get('suggested_price', 0))
        discount = format_pct(pricing.get('discount', 0))
        buyer_roi = format_pct(pricing.get('buyer_roi', 0))

        prompt = f"""
        You are a senior credit analyst explaining a portfolio reallocation insight
        using anonymised data. Write in a confident, professional tone appropriate
        for a credit committee or portfolio review.

        Do NOT use absolute or directive language such as "wrong", "ideal", "must",
        "should", or "offload". Frame all observations as comparative insights
        based on the available data and stated lender strategies.

        Keep the explanation concise (3–4 sentences).

        ANONYMISED COMPANY PROFILE:
        - Sector: {company_data.get('sector', 'Unknown')}
        - Size Band: {company_data.get('revenue_band', 'Unknown')}
        - Region: {company_data.get('region', 'Unknown')}
        - Risk Score: {risk_score}/100
        - Inclusion Score: {inclusion_score}/100

        LOAN SUMMARY:
        - Outstanding Balance: {outstanding}
        - Remaining Term: {pricing.get('years_remaining', 0)} years
        - Indicative Price: {suggested_price}
        ({discount} discount)

        CURRENT LENDER CONTEXT:
        - Lender Profile: {current_lender.get('description', '')}
        - Relative Fit Score: {current_fit}/100
        - Key Alignment Factors: {', '.join(scores.get('current_mismatch_reasons', ['No specific factors']))}

        ALTERNATIVE LENDER CONTEXT:
        - Lender Profile: {recommended_lender.get('description', '')}
        - Relative Fit Score: {recommended_fit}/100
        - Key Alignment Factors: {', '.join(scores.get('recommended_fit_reasons', ['No specific factors']))}

        ESTIMATED BUYER METRIC:
        - Annualised, Risk-Adjusted ROI: {buyer_roi}

        TASK:
        Explain how differences in lender strategy and portfolio focus result in
        different levels of alignment for this loan, and outline the potential
        portfolio and return implications for each party under this scenario.
        """
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"LLM API error: {e}")
            return self._generate_template(
                company_data, current_lender, recommended_lender, scores, pricing
            )

    def _generate_template(
        self,
        company_data: Dict,
        current_lender: Dict,
        recommended_lender: Dict,
        scores: Dict,
        pricing: Dict
    ) -> str:
        """Generate explanation using templates (fallback when no API key)."""

        sector = company_data.get('sector', 'Unknown')
        region = company_data.get('region', 'Unknown')

        # Handle both numeric and string values (from anonymization)
        def to_num(val, default=0):
            if isinstance(val, (int, float)):
                return val
            try:
                return float(val)
            except (ValueError, TypeError):
                return default

        def format_val(val):
            if isinstance(val, str):
                return val
            return f"{val:.0f}" if val else "0"

        def format_pct(val):
            if isinstance(val, str):
                return val
            return f"{val:.1f}" if val else "0"

        current_fit_num = to_num(scores.get('current_fit', 0))
        recommended_fit_num = to_num(scores.get('recommended_fit', 0))
        fit_improvement = recommended_fit_num - current_fit_num

        current_fit_display = format_val(scores.get('current_fit', 0))
        discount_display = format_pct(pricing.get('discount', 0))
        buyer_roi_display = format_pct(pricing.get('buyer_roi', 0))

        current_name = current_lender.get('name', 'current lender')
        recommended_name = recommended_lender.get('name', 'recommended lender')

        # Build explanation based on key factors
        explanation_parts = []

        # Current mismatch reason
        if current_fit_num < 40:
            explanation_parts.append(
                f"This {sector} company in {region} has a poor fit score of {current_fit_display}/100 "
                f"with {current_name}, indicating significant misalignment with the lender's strategy."
            )
        elif current_fit_num < 60:
            explanation_parts.append(
                f"The company's fit with {current_name} is only {current_fit_display}/100, "
                f"suggesting the lender's risk appetite and sector focus don't align well with this business."
            )
        else:
            explanation_parts.append(
                f"While the current fit with {current_name} is adequate ({current_fit_display}/100), "
                f"there is potential for improvement."
            )

        # Why recommended is better
        inclusion_score_num = to_num(scores.get('inclusion_score', 0))
        if recommended_lender.get('inclusion_mandate') and inclusion_score_num > 60:
            explanation_parts.append(
                f"{recommended_name} has an explicit inclusion mandate that aligns with this company's "
                f"profile in an underserved region/sector."
            )
        elif sector in (recommended_lender.get('preferred_sectors') or []):
            explanation_parts.append(
                f"{recommended_name} specializes in {sector}, bringing deep sector expertise "
                f"that would benefit this company."
            )
        elif region in (recommended_lender.get('preferred_regions') or []):
            explanation_parts.append(
                f"{recommended_name} has a regional focus that includes {region}, "
                f"making them better positioned to serve this company."
            )
        else:
            explanation_parts.append(
                f"{recommended_name}'s risk profile and strategy align better, "
                f"resulting in a {fit_improvement:.0f} point improvement in fit score."
            )

        # Financial benefit
        explanation_parts.append(
            f"At a {discount_display}% discount, the buyer achieves {buyer_roi_display}% annualized ROI "
            f"while the seller exits a mismatched position to optimize their portfolio."
        )

        return " ".join(explanation_parts)

    def generate_market_insight(self, market_stats: Dict) -> str:
        """Generate a market-level insight summary."""

        mismatched_pct = market_stats.get('mismatched_companies', {}).get('percentage', 0)
        strong_candidates = market_stats.get('reallocation_candidates', {}).get('strong', 0)
        avg_improvement = market_stats.get('fit_scores', {}).get('average_improvement', 0)
        total_value = market_stats.get('reallocation_value', {}).get('formatted', '£0')

        if self.client:
            prompt = f"""Generate a 2-3 sentence market insight summary based on this data:
- {mismatched_pct}% of loans are mismatched with current lenders
- {strong_candidates} are strong reallocation candidates
- Average fit improvement from reallocation: {avg_improvement} points
- Total value available for reallocation: {total_value}

Focus on the opportunity and benefit for the SME lending market."""

            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                return response.text
            except Exception:
                pass

        # Fallback template
        return (
            f"Analysis reveals {mismatched_pct}% of the portfolio could benefit from reallocation, "
            f"with {strong_candidates} strong candidates identified. "
            f"If recommended reallocations were executed, average portfolio fit would improve by "
            f"{avg_improvement} points, potentially improving outcomes for {total_value} in lending exposure."
        )

    def generate_inclusion_insight(self, inclusion_stats: Dict) -> str:
        """Generate an inclusion-focused insight."""

        high_potential = inclusion_stats.get('high_potential_underserved', {})
        count = high_potential.get('count', 0)
        pct = high_potential.get('percentage', 0)

        regional_stats = inclusion_stats.get('underserved_regions', {})
        regional_pct = regional_stats.get('percentage', 0)

        if self.client:
            prompt = f"""Generate a 2-sentence insight about financial inclusion opportunities:
- {count} companies ({pct}%) have strong financials but are in underserved positions
- {regional_pct}% of companies are in underserved regions
- These companies could benefit from being matched to lenders with inclusion mandates

Emphasize the virtuous cycle: more appropriate loans -> more business success -> more lending demand."""

            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                return response.text
            except Exception:
                pass

        # Fallback
        return (
            f"{count} companies with strong fundamentals may be overlooked due to their location "
            f"or sector, representing a significant inclusion opportunity. "
            f"Matching these businesses to lenders with appropriate mandates could create a virtuous cycle "
            f"of successful lending, business growth, and increased capital availability."
        )

    def generate_swap_inclusion_story(self, swap_data: Dict) -> str:
        """
        Generate an inclusion-focused story for a loan swap.

        Args:
            swap_data: Dictionary containing swap details including:
                - loan_a_sector, loan_a_region, loan_a_inclusion_score
                - loan_b_sector, loan_b_region, loan_b_inclusion_score
                - total_fit_improvement
                - is_inclusion_swap

        Returns:
            Inclusion-focused narrative about the swap's impact
        """
        loan_a_sector = swap_data.get('loan_a_sector', 'Unknown')
        loan_a_region = swap_data.get('loan_a_region', 'Unknown')
        loan_a_inclusion = swap_data.get('loan_a_inclusion_score', 0)
        loan_b_sector = swap_data.get('loan_b_sector', 'Unknown')
        loan_b_region = swap_data.get('loan_b_region', 'Unknown')
        loan_b_inclusion = swap_data.get('loan_b_inclusion_score', 0)
        fit_improvement = swap_data.get('total_fit_improvement', 0)

        if self.client:
            prompt = f"""Generate a 2-3 sentence inclusion-focused story about this loan swap.
Focus on how the swap benefits underserved companies and improves financial inclusion.

SWAP DETAILS:
- Loan A: {loan_a_sector} sector in {loan_a_region}, Inclusion Score: {loan_a_inclusion}/100
- Loan B: {loan_b_sector} sector in {loan_b_region}, Inclusion Score: {loan_b_inclusion}/100
- Combined Fit Improvement: +{fit_improvement} points

The story should emphasize:
1. How mismatched loans can disadvantage SMEs in underserved regions/sectors
2. How this swap helps both companies access lenders who understand their needs
3. The virtuous cycle: appropriate lending → business success → more capital → more lending

Keep the tone professional but impactful. Avoid hyperbole."""

            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                return response.text
            except Exception:
                pass

        # Fallback template - use the loan with higher inclusion score
        if loan_a_inclusion > loan_b_inclusion:
            higher_region = loan_a_region
            higher_sector = loan_a_sector
        else:
            higher_region = loan_b_region
            higher_sector = loan_b_sector

        return (
            f"This swap enables a {higher_sector} company in {higher_region} to access "
            f"a lender better suited to support businesses in their region and sector. "
            f"With a combined fit improvement of +{fit_improvement} points, both companies "
            f"gain access to lenders who understand their specific needs. "
            f"This creates a virtuous cycle: appropriate financing leads to business success, "
            f"which increases demand for lending in underserved areas."
        )


def prepare_explanation_data(company, current_lender_profile, recommended_lender_profile, pricing_details, anonymize: bool = True) -> tuple:
    """
    Helper function to prepare data for the explainer from DataFrame row and profiles.

    Args:
        company: Company data (DataFrame row or dict)
        current_lender_profile: Current lender profile dict
        recommended_lender_profile: Recommended lender profile dict
        pricing_details: Pricing details dict
        anonymize: If True, anonymize recommended lender and band values (default True)

    Returns:
        Tuple of (company_data, current_lender, recommended_lender, scores, pricing)
    """
    from utils.anonymizer import (
        anonymize_lender, round_score, band_percentage,
        format_amount_range, group_region, band_turnover
    )

    if anonymize:
        # Anonymize region and band turnover
        region_display = group_region(company.get('Region', 'Unknown'))
        revenue_band = band_turnover(company.get('Turnover', 0))

        # Round scores
        risk_display = round_score(company.get('Risk_Score', 0))
        inclusion_display = round_score(company.get('Inclusion_Score', 0))
        current_fit_display = round_score(company.get('Current_Lender_Fit', 0))
        recommended_fit_display = round_score(company.get('Best_Match_Fit', 0))

        # Get pricing values and band them
        outstanding = pricing_details.get('loan_details', {}).get('outstanding_balance', 0)
        suggested_price = pricing_details.get('pricing', {}).get('suggested_price', 0)
        discount = pricing_details.get('pricing', {}).get('discount_from_face', 0)
        buyer_roi = pricing_details.get('buyer_metrics', {}).get('annualized_roi', 0)

        outstanding_display = format_amount_range(outstanding)
        price_display = format_amount_range(suggested_price)
        discount_display = band_percentage(discount)
        roi_display = band_percentage(buyer_roi)

        # Anonymize recommended lender
        recommended_name = recommended_lender_profile.get('name', 'Unknown')
        anon_recommended = recommended_lender_profile.copy()
        anon_recommended['name'] = anonymize_lender(recommended_name, is_current=False)
        anon_recommended['description'] = f"Alternative lender with {recommended_lender_profile.get('risk_tolerance', 'medium')} risk tolerance"
    else:
        region_display = company.get('Region', 'Unknown')
        revenue_band = company.get('Revenue_Band', 'Unknown')
        risk_display = company.get('Risk_Score', 0)
        inclusion_display = company.get('Inclusion_Score', 0)
        current_fit_display = company.get('Current_Lender_Fit', 0)
        recommended_fit_display = company.get('Best_Match_Fit', 0)

        outstanding_display = pricing_details.get('loan_details', {}).get('outstanding_balance', 0)
        price_display = pricing_details.get('pricing', {}).get('suggested_price', 0)
        discount_display = pricing_details.get('pricing', {}).get('discount_from_face', 0)
        roi_display = pricing_details.get('buyer_metrics', {}).get('annualized_roi', 0)
        anon_recommended = recommended_lender_profile

    company_data = {
        'sector': company.get('Sector', 'Unknown'),
        'region': region_display,
        'revenue_band': revenue_band,
        'turnover': company.get('Turnover', 0)
    }

    scores = {
        'risk_score': risk_display,
        'inclusion_score': inclusion_display,
        'current_fit': current_fit_display,
        'recommended_fit': recommended_fit_display,
        'current_mismatch_reasons': company.get('Current_Fit_Reasons', {}).get('negative', []),
        'recommended_fit_reasons': company.get('Best_Match_Reasons', {}).get('positive', [])
    }

    pricing = {
        'outstanding': outstanding_display,
        'years_remaining': pricing_details.get('loan_details', {}).get('years_remaining', 0),
        'suggested_price': price_display,
        'discount': discount_display,
        'buyer_roi': roi_display
    }

    # Current lender stays visible
    return company_data, current_lender_profile, anon_recommended, scores, pricing


if __name__ == "__main__":
    # Test the explainer
    print("Testing Explainer (template mode - no API key)...")

    explainer = Explainer()

    # Mock data for testing
    company_data = {
        'sector': 'Advanced_Manufacturing',
        'region': 'North West',
        'revenue_band': '£10m-£25m'
    }

    current_lender = {
        'name': 'Alpha Bank',
        'description': 'Conservative traditional bank',
        'preferred_sectors': ['Financial', 'Professional_Business'],
        'preferred_regions': ['London', 'South East'],
        'inclusion_mandate': False
    }

    recommended_lender = {
        'name': 'Regional Development Fund',
        'description': 'Regional inclusion mandate',
        'preferred_sectors': None,
        'preferred_regions': ['North West', 'Scotland'],
        'inclusion_mandate': True
    }

    scores = {
        'risk_score': 72,
        'inclusion_score': 68,
        'current_fit': 38,
        'recommended_fit': 82,
        'current_mismatch_reasons': ['Wrong sector', 'Wrong region'],
        'recommended_fit_reasons': ['Regional match', 'Inclusion alignment']
    }

    pricing = {
        'outstanding': 1_500_000,
        'years_remaining': 3,
        'suggested_price': 1_320_000,
        'discount': 12.0,
        'buyer_roi': 14.2
    }

    explanation = explainer.generate_explanation(
        company_data, current_lender, recommended_lender, scores, pricing
    )

    print("\n=== Generated Explanation ===")
    print(explanation)
