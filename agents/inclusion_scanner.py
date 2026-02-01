"""
Agent 2: Inclusion Scanner
Detects financial inclusion gaps - identifies companies that may be underserved
based on region, sector, or size characteristics.
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from utils.anonymizer import group_region, round_score, band_turnover, band_percentage


class InclusionScanner:
    """
    Analyzes companies for financial inclusion signals.
    Identifies underserved regions, sectors, and company profiles.
    """

    # Define underserved regions (outside major financial centers)
    UNDERSERVED_REGIONS = [
        'North East',
        'North West',
        'Scotland',
        'Wales',
        'Northern Ireland',
        'Yorkshire And The Humber',
        'East Midlands',
        'West Midlands'
    ]

    # Major financial centers (typically well-served)
    WELL_SERVED_REGIONS = [
        'London',
        'South East'
    ]

    # Sectors that may face lending bias
    UNDERSERVED_SECTORS = [
        'Creative_Industries',
        'Clean_Energy',  # Newer sector, less understood
        'Life_Science',  # High uncertainty
    ]

    def __init__(self):
        self.weights = {
            'regional': 0.35,
            'sector': 0.25,
            'size': 0.20,
            'strong_but_overlooked': 0.20
        }

    def analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze all companies for inclusion signals.

        Args:
            df: DataFrame with company data (must include Risk_Score from RiskAnalyst)

        Returns:
            DataFrame with added inclusion score columns
        """
        # Calculate regional benchmarks
        self.regional_stats = self._calculate_regional_stats(df)
        self.sector_stats = self._calculate_sector_stats(df)

        # Calculate component scores
        df = self._calculate_regional_score(df)
        df = self._calculate_sector_score(df)
        df = self._calculate_size_score(df)
        df = self._calculate_overlooked_score(df)

        # Calculate overall inclusion score
        df['Inclusion_Score'] = (
            df['Regional_Inclusion_Score'] * self.weights['regional'] +
            df['Sector_Inclusion_Score'] * self.weights['sector'] +
            df['Size_Inclusion_Score'] * self.weights['size'] +
            df['Overlooked_Score'] * self.weights['strong_but_overlooked']
        ).round(1)

        # Add inclusion flags
        df['Inclusion_Flags'] = df.apply(self._generate_flags, axis=1)

        # Add inclusion category
        df['Inclusion_Category'] = df['Inclusion_Score'].apply(self._categorize_inclusion)

        return df

    def _calculate_regional_stats(self, df: pd.DataFrame) -> Dict:
        """Calculate statistics by region."""
        return df.groupby('Region').agg({
            'Turnover': 'mean',
            'Risk_Score': 'mean',
            'SME_ID': 'count'
        }).rename(columns={'SME_ID': 'count'}).to_dict('index')

    def _calculate_sector_stats(self, df: pd.DataFrame) -> Dict:
        """Calculate statistics by sector."""
        return df.groupby('Sector').agg({
            'Turnover': 'mean',
            'Risk_Score': 'mean',
            'SME_ID': 'count'
        }).rename(columns={'SME_ID': 'count'}).to_dict('index')

    def _calculate_regional_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate regional inclusion score.
        Higher score = more likely to be underserved due to location.
        """
        def score_region(region):
            if pd.isna(region) or region == 'Unknown':
                return 50  # Neutral

            if region in self.UNDERSERVED_REGIONS:
                # Check how underserved this specific region is
                if region in ['North East', 'Northern Ireland', 'Wales']:
                    return 85  # Most underserved
                elif region in ['Scotland', 'North West']:
                    return 75
                else:
                    return 65
            elif region in self.WELL_SERVED_REGIONS:
                return 25  # Well-served, low inclusion priority
            else:
                return 45  # Neutral

        df['Regional_Inclusion_Score'] = df['Region'].apply(score_region)
        return df

    def _calculate_sector_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate sector-based inclusion score.
        Some sectors face systemic lending bias.
        """
        def score_sector(sector):
            if pd.isna(sector):
                return 50

            if sector in self.UNDERSERVED_SECTORS:
                return 75  # Higher inclusion priority
            elif sector in ['Financial', 'Professional_Business']:
                return 30  # Well-understood sectors, low inclusion priority
            else:
                return 50  # Neutral

        df['Sector_Inclusion_Score'] = df['Sector'].apply(score_sector)
        return df

    def _calculate_size_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate size-based inclusion score.
        Smaller companies often face more barriers.
        """
        # Get turnover percentiles
        p25 = df['Turnover'].quantile(0.25)
        p50 = df['Turnover'].quantile(0.50)
        p75 = df['Turnover'].quantile(0.75)

        def score_size(turnover):
            if pd.isna(turnover):
                return 50

            if turnover <= p25:
                return 80  # Smallest quartile - highest inclusion priority
            elif turnover <= p50:
                return 65
            elif turnover <= p75:
                return 45
            else:
                return 30  # Largest - well-served

        df['Size_Inclusion_Score'] = df['Turnover'].apply(score_size)
        return df

    def _calculate_overlooked_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Identify 'strong but overlooked' companies.
        High financial health but in underserved region/sector.
        """
        def score_overlooked(row):
            risk_score = row.get('Risk_Score', 50)
            regional_score = row.get('Regional_Inclusion_Score', 50)
            sector_score = row.get('Sector_Inclusion_Score', 50)

            # Strong financials (risk score > 65) but in underserved position
            if risk_score >= 65:
                avg_inclusion = (regional_score + sector_score) / 2
                if avg_inclusion >= 60:
                    # Strong company in underserved position - high priority
                    return 90
                elif avg_inclusion >= 50:
                    return 70
                else:
                    return 40
            elif risk_score >= 50:
                # Moderate financials
                return 55
            else:
                # Weaker financials - lower inclusion priority
                return 35

        df['Overlooked_Score'] = df.apply(score_overlooked, axis=1)
        return df

    def _generate_flags(self, row: pd.Series) -> List[str]:
        """Generate inclusion flag labels for a company."""
        flags = []

        if row.get('Regional_Inclusion_Score', 0) >= 70:
            flags.append('Underserved Region')

        if row.get('Sector_Inclusion_Score', 0) >= 70:
            flags.append('Underserved Sector')

        if row.get('Size_Inclusion_Score', 0) >= 70:
            flags.append('Smaller Company')

        if row.get('Overlooked_Score', 0) >= 80:
            flags.append('Strong but Overlooked')

        if row.get('Risk_Score', 0) >= 70 and row.get('Inclusion_Score', 0) >= 60:
            flags.append('High Potential - Inclusion Candidate')

        return flags

    def _categorize_inclusion(self, score: float) -> str:
        """Categorize inclusion score."""
        if score >= 75:
            return "High Inclusion Priority"
        elif score >= 60:
            return "Moderate Inclusion Priority"
        elif score >= 45:
            return "Standard"
        else:
            return "Well-Served"

    def get_inclusion_breakdown(self, company: pd.Series, anonymize: bool = False) -> Dict:
        """
        Get detailed inclusion breakdown for a single company.

        Args:
            company: Company data row
            anonymize: If True, group regions and band values
        """
        if anonymize:
            region_display = group_region(company.get('Region', 'Unknown'))
            overall_score = round_score(company.get('Inclusion_Score', 0))
            regional_score = round_score(company.get('Regional_Inclusion_Score', 0))
            sector_score = round_score(company.get('Sector_Inclusion_Score', 0))
            size_score = round_score(company.get('Size_Inclusion_Score', 0))
            overlooked_score = round_score(company.get('Overlooked_Score', 0))
            turnover_display = band_turnover(company.get('Turnover', 0))
        else:
            region_display = company.get('Region', 'Unknown')
            overall_score = company.get('Inclusion_Score', 0)
            regional_score = company.get('Regional_Inclusion_Score', 0)
            sector_score = company.get('Sector_Inclusion_Score', 0)
            size_score = company.get('Size_Inclusion_Score', 0)
            overlooked_score = company.get('Overlooked_Score', 0)
            turnover_display = company.get('Turnover', 0)

        return {
            'overall_score': overall_score,
            'category': company.get('Inclusion_Category', 'Unknown'),
            'flags': company.get('Inclusion_Flags', []),
            'components': {
                'regional': {
                    'score': regional_score,
                    'weight': self.weights['regional'],
                    'region': region_display,
                    'is_underserved': company.get('Region') in self.UNDERSERVED_REGIONS
                },
                'sector': {
                    'score': sector_score,
                    'weight': self.weights['sector'],
                    'sector': company.get('Sector', 'Unknown'),
                    'is_underserved': company.get('Sector') in self.UNDERSERVED_SECTORS
                },
                'size': {
                    'score': size_score,
                    'weight': self.weights['size'],
                    'turnover': turnover_display
                },
                'overlooked': {
                    'score': overlooked_score,
                    'weight': self.weights['strong_but_overlooked'],
                    'interpretation': self._interpret_overlooked(
                        company.get('Risk_Score', 0),
                        company.get('Overlooked_Score', 0)
                    )
                }
            }
        }

    def _interpret_overlooked(self, risk_score: float, overlooked_score: float) -> str:
        if risk_score >= 70 and overlooked_score >= 80:
            return "Strong financials in underserved position - high potential"
        elif risk_score >= 60 and overlooked_score >= 60:
            return "Good fundamentals, may be overlooked"
        elif risk_score >= 50:
            return "Moderate profile"
        else:
            return "Financial improvement needed before inclusion focus"

    def get_market_insights(self, df: pd.DataFrame, anonymize: bool = False) -> Dict:
        """
        Generate market-level inclusion insights.

        Args:
            df: DataFrame with inclusion data
            anonymize: If True, group regions and round percentages
        """
        total = len(df)

        # Regional analysis
        underserved_region_count = len(df[df['Region'].isin(self.UNDERSERVED_REGIONS)])
        underserved_region_pct = underserved_region_count / total * 100

        # High potential in underserved
        high_potential_underserved = len(df[
            (df['Risk_Score'] >= 65) &
            (df['Inclusion_Score'] >= 60)
        ])

        # Sector analysis
        sector_distribution = df['Sector'].value_counts().to_dict()

        # Inclusion priority distribution
        priority_distribution = df['Inclusion_Category'].value_counts().to_dict()

        if anonymize:
            # Group regions for display
            grouped_regions = ['Northern England', 'Midlands & East', 'Scotland', 'Wales', 'Northern Ireland']
            underserved_pct_display = band_percentage(underserved_region_pct)
            high_potential_pct_display = band_percentage(high_potential_underserved / total * 100)
        else:
            grouped_regions = self.UNDERSERVED_REGIONS
            underserved_pct_display = round(underserved_region_pct, 1)
            high_potential_pct_display = round(high_potential_underserved / total * 100, 1)

        return {
            'total_companies': total,
            'underserved_regions': {
                'count': underserved_region_count,
                'percentage': underserved_pct_display,
                'regions': grouped_regions
            },
            'high_potential_underserved': {
                'count': high_potential_underserved,
                'percentage': high_potential_pct_display,
                'description': 'Companies with strong financials in underserved positions'
            },
            'sector_distribution': sector_distribution,
            'priority_distribution': priority_distribution,
            'key_insight': self._generate_key_insight(df)
        }

    def _generate_key_insight(self, df: pd.DataFrame) -> str:
        """Generate a key insight statement."""
        high_priority = len(df[df['Inclusion_Category'] == 'High Inclusion Priority'])
        strong_overlooked = len(df[df['Inclusion_Flags'].apply(lambda x: 'Strong but Overlooked' in x)])

        return (
            f"{high_priority} companies ({high_priority/len(df)*100:.0f}%) are high inclusion priority. "
            f"{strong_overlooked} have strong financials but may be overlooked due to region or sector."
        )


if __name__ == "__main__":
    # Test the inclusion scanner
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from utils.data_loader import load_data
    from agents.risk_analyst import RiskAnalyst
    from pathlib import Path

    excel_path = r"C:\Users\user\Downloads\UKFIN Hackathon_sample_file_data_GFA Exchange.xlsx"
    df = load_data(excel_path)

    # First run risk analyst
    risk_analyst = RiskAnalyst()
    df = risk_analyst.analyze(df)

    # Then run inclusion scanner
    scanner = InclusionScanner()
    df = scanner.analyze(df)

    print("=== Inclusion Score Distribution ===")
    print(df['Inclusion_Score'].describe())

    print("\n=== Inclusion Categories ===")
    print(df['Inclusion_Category'].value_counts())

    print("\n=== Market Insights ===")
    insights = scanner.get_market_insights(df)
    for key, value in insights.items():
        print(f"{key}: {value}")

    print("\n=== Sample with High Inclusion Priority ===")
    high_priority = df[df['Inclusion_Category'] == 'High Inclusion Priority'].head(1)
    if len(high_priority) > 0:
        sample = high_priority.iloc[0]
        breakdown = scanner.get_inclusion_breakdown(sample)
        print(f"Company: {sample['SME_ID']}")
        print(f"Region: {sample['Region']}")
        print(f"Sector: {sample['Sector']}")
        print(f"Inclusion Score: {breakdown['overall_score']}")
        print(f"Flags: {breakdown['flags']}")
