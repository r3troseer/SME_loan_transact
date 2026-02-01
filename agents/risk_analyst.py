"""
Agent 1: Risk Analyst
Calculates financial health metrics and risk scores for each company.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from utils.anonymizer import round_score


class RiskAnalyst:
    """
    Analyzes company financial health and produces risk scores.
    Uses rule-based scoring with financial ratios.
    """

    def __init__(self):
        # Weights for different risk components
        self.weights = {
            'liquidity': 0.20,
            'profitability': 0.25,
            'leverage': 0.20,
            'cash_position': 0.15,
            'efficiency': 0.10,
            'size_stability': 0.10
        }

    def analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze all companies and add risk scores.

        Args:
            df: DataFrame with company financial data

        Returns:
            DataFrame with added risk score columns
        """
        # Calculate individual metrics
        df = self._calculate_liquidity(df)
        df = self._calculate_profitability(df)
        df = self._calculate_leverage(df)
        df = self._calculate_cash_position(df)
        df = self._calculate_efficiency(df)
        df = self._calculate_size_stability(df)

        # Calculate component scores (0-100)
        df = self._calculate_component_scores(df)

        # Calculate overall risk score
        df['Risk_Score'] = (
            df['Liquidity_Score'] * self.weights['liquidity'] +
            df['Profitability_Score'] * self.weights['profitability'] +
            df['Leverage_Score'] * self.weights['leverage'] +
            df['Cash_Score'] * self.weights['cash_position'] +
            df['Efficiency_Score'] * self.weights['efficiency'] +
            df['Size_Score'] * self.weights['size_stability']
        ).round(1)

        # Add risk category
        df['Risk_Category'] = df['Risk_Score'].apply(self._categorize_risk)

        return df

    def _calculate_liquidity(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate liquidity ratios."""
        # Current Ratio = Current Assets / Current Liabilities
        df['Current_Ratio'] = np.where(
            df['Total Current Liabilities'] > 0,
            df['Total Current Assets'] / df['Total Current Liabilities'],
            0
        )

        # Quick Ratio = (Current Assets - Stock) / Current Liabilities
        stock = df['Stock'].fillna(0)
        df['Quick_Ratio'] = np.where(
            df['Total Current Liabilities'] > 0,
            (df['Total Current Assets'] - stock) / df['Total Current Liabilities'],
            0
        )

        return df

    def _calculate_profitability(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate profitability ratios."""
        # Operating Margin = Operating Profit / Turnover
        df['Operating_Margin'] = np.where(
            df['Turnover'] > 0,
            df['Operating Profit'] / df['Turnover'],
            0
        )

        # EBITDA Margin
        df['EBITDA_Margin'] = np.where(
            df['Turnover'] > 0,
            df['EBITDA'] / df['Turnover'],
            0
        )

        # Gross Margin
        df['Gross_Margin'] = np.where(
            df['Turnover'] > 0,
            df['Gross Profit'] / df['Turnover'],
            0
        )

        # Return on Assets
        df['ROA'] = np.where(
            df['Total Assets'] > 0,
            df['Profit After Tax'] / df['Total Assets'],
            0
        )

        return df

    def _calculate_leverage(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate leverage ratios."""
        # Debt Ratio = Total Liabilities / Total Assets
        df['Debt_Ratio'] = np.where(
            df['Total Assets'] > 0,
            df['Total Liabilities'] / df['Total Assets'],
            1  # Assume high risk if no assets
        )

        # Debt to Equity = Total Liabilities / Net Assets
        df['Debt_to_Equity'] = np.where(
            df['Net Assets'] > 0,
            df['Total Liabilities'] / df['Net Assets'],
            10  # Cap at high value if negative equity
        )

        return df

    def _calculate_cash_position(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate cash position metrics."""
        # Cash Ratio = Cash / Current Liabilities
        df['Cash_Ratio'] = np.where(
            df['Total Current Liabilities'] > 0,
            df['Cash'].fillna(0) / df['Total Current Liabilities'],
            0
        )

        # Cash to Assets
        df['Cash_to_Assets'] = np.where(
            df['Total Assets'] > 0,
            df['Cash'].fillna(0) / df['Total Assets'],
            0
        )

        return df

    def _calculate_efficiency(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate efficiency metrics."""
        # Asset Turnover = Turnover / Total Assets
        df['Asset_Turnover'] = np.where(
            df['Total Assets'] > 0,
            df['Turnover'] / df['Total Assets'],
            0
        )

        # Revenue per Employee
        df['Revenue_per_Employee'] = np.where(
            df['Number of Employees'] > 0,
            df['Turnover'] / df['Number of Employees'],
            0
        )

        return df

    def _calculate_size_stability(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate size/stability indicators."""
        # Working Capital ratio
        df['Working_Capital_Ratio'] = np.where(
            df['Total Current Liabilities'] > 0,
            df['Working Capital'] / df['Total Current Liabilities'],
            0
        )

        return df

    def _normalize(self, value: float, min_val: float, max_val: float, inverse: bool = False) -> float:
        """Normalize a value to 0-100 scale."""
        if pd.isna(value):
            return 50  # Default to middle if missing

        # Clip to range
        clipped = max(min_val, min(max_val, value))

        # Normalize to 0-1
        if max_val == min_val:
            normalized = 0.5
        else:
            normalized = (clipped - min_val) / (max_val - min_val)

        # Inverse if needed (e.g., for debt ratio where lower is better)
        if inverse:
            normalized = 1 - normalized

        return normalized * 100

    def _calculate_component_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate normalized component scores (0-100)."""

        # Liquidity Score (higher is better)
        # Good current ratio: 1.5-3.0
        df['Liquidity_Score'] = df['Current_Ratio'].apply(
            lambda x: self._normalize(x, 0.5, 3.0)
        )

        # Profitability Score (higher margin is better)
        # Good operating margin: 5-25%
        df['Profitability_Score'] = df['Operating_Margin'].apply(
            lambda x: self._normalize(x, -0.1, 0.25)
        )

        # Leverage Score (lower debt is better - inverse)
        # Good debt ratio: 0.2-0.6
        df['Leverage_Score'] = df['Debt_Ratio'].apply(
            lambda x: self._normalize(x, 0.2, 0.8, inverse=True)
        )

        # Cash Score (higher is better)
        # Good cash ratio: 0.1-1.0
        df['Cash_Score'] = df['Cash_Ratio'].apply(
            lambda x: self._normalize(x, 0, 1.0)
        )

        # Efficiency Score (higher turnover is better)
        # Good asset turnover: 0.5-2.5
        df['Efficiency_Score'] = df['Asset_Turnover'].apply(
            lambda x: self._normalize(x, 0.3, 2.5)
        )

        # Size/Stability Score (positive working capital is better)
        df['Size_Score'] = df['Working_Capital_Ratio'].apply(
            lambda x: self._normalize(x, -0.5, 2.0)
        )

        return df

    def _categorize_risk(self, score: float) -> str:
        """Categorize risk score into bands."""
        if score >= 75:
            return "Low Risk"
        elif score >= 60:
            return "Moderate-Low Risk"
        elif score >= 45:
            return "Moderate Risk"
        elif score >= 30:
            return "Moderate-High Risk"
        else:
            return "High Risk"

    def get_risk_breakdown(self, company: pd.Series, anonymize: bool = False) -> Dict:
        """
        Get detailed risk breakdown for a single company.

        Args:
            company: Series with company data including risk scores
            anonymize: If True, round scores to nearest 5

        Returns:
            Dictionary with risk breakdown
        """
        if anonymize:
            overall = round_score(company.get('Risk_Score', 0))
            liquidity = round_score(company.get('Liquidity_Score', 0))
            profitability = round_score(company.get('Profitability_Score', 0))
            leverage = round_score(company.get('Leverage_Score', 0))
            cash = round_score(company.get('Cash_Score', 0))
            efficiency = round_score(company.get('Efficiency_Score', 0))
            stability = round_score(company.get('Size_Score', 0))
        else:
            overall = company.get('Risk_Score', 0)
            liquidity = company.get('Liquidity_Score', 0)
            profitability = company.get('Profitability_Score', 0)
            leverage = company.get('Leverage_Score', 0)
            cash = company.get('Cash_Score', 0)
            efficiency = company.get('Efficiency_Score', 0)
            stability = company.get('Size_Score', 0)

        return {
            'overall_score': overall,
            'category': company.get('Risk_Category', 'Unknown'),
            'components': {
                'liquidity': {
                    'score': liquidity,
                    'weight': self.weights['liquidity'],
                    'current_ratio': company.get('Current_Ratio', 0),
                    'interpretation': self._interpret_liquidity(company.get('Current_Ratio', 0))
                },
                'profitability': {
                    'score': profitability,
                    'weight': self.weights['profitability'],
                    'operating_margin': company.get('Operating_Margin', 0),
                    'interpretation': self._interpret_profitability(company.get('Operating_Margin', 0))
                },
                'leverage': {
                    'score': leverage,
                    'weight': self.weights['leverage'],
                    'debt_ratio': company.get('Debt_Ratio', 0),
                    'interpretation': self._interpret_leverage(company.get('Debt_Ratio', 0))
                },
                'cash_position': {
                    'score': cash,
                    'weight': self.weights['cash_position'],
                    'cash_ratio': company.get('Cash_Ratio', 0),
                    'interpretation': self._interpret_cash(company.get('Cash_Ratio', 0))
                },
                'efficiency': {
                    'score': efficiency,
                    'weight': self.weights['efficiency'],
                    'asset_turnover': company.get('Asset_Turnover', 0),
                    'interpretation': self._interpret_efficiency(company.get('Asset_Turnover', 0))
                },
                'stability': {
                    'score': stability,
                    'weight': self.weights['size_stability'],
                    'working_capital_ratio': company.get('Working_Capital_Ratio', 0)
                }
            }
        }

    def _interpret_liquidity(self, ratio: float) -> str:
        if ratio >= 2.0:
            return "Strong liquidity - can easily meet short-term obligations"
        elif ratio >= 1.5:
            return "Adequate liquidity"
        elif ratio >= 1.0:
            return "Tight liquidity - monitor closely"
        else:
            return "Weak liquidity - potential cash flow issues"

    def _interpret_profitability(self, margin: float) -> str:
        if margin >= 0.15:
            return "Strong profitability"
        elif margin >= 0.08:
            return "Healthy profitability"
        elif margin >= 0.03:
            return "Modest profitability"
        elif margin >= 0:
            return "Thin margins"
        else:
            return "Operating at a loss"

    def _interpret_leverage(self, ratio: float) -> str:
        if ratio <= 0.3:
            return "Conservative leverage - strong balance sheet"
        elif ratio <= 0.5:
            return "Moderate leverage"
        elif ratio <= 0.7:
            return "Elevated leverage - some risk"
        else:
            return "High leverage - significant debt burden"

    def _interpret_cash(self, ratio: float) -> str:
        if ratio >= 0.5:
            return "Strong cash reserves"
        elif ratio >= 0.2:
            return "Adequate cash position"
        elif ratio >= 0.1:
            return "Limited cash buffer"
        else:
            return "Very low cash - liquidity risk"

    def _interpret_efficiency(self, turnover: float) -> str:
        if turnover >= 2.0:
            return "Highly efficient asset utilization"
        elif turnover >= 1.0:
            return "Good asset efficiency"
        elif turnover >= 0.5:
            return "Moderate asset efficiency"
        else:
            return "Low asset turnover - may have idle assets"


if __name__ == "__main__":
    # Test the risk analyst
    from utils.data_loader import load_data

    excel_path = r"C:\Users\user\Downloads\UKFIN Hackathon_sample_file_data_GFA Exchange.xlsx"
    df = load_data(excel_path)

    analyst = RiskAnalyst()
    df = analyst.analyze(df)

    print("=== Risk Score Distribution ===")
    print(df['Risk_Score'].describe())

    print("\n=== Risk Categories ===")
    print(df['Risk_Category'].value_counts())

    print("\n=== Sample Risk Breakdown ===")
    sample = df.iloc[0]
    breakdown = analyst.get_risk_breakdown(sample)
    print(f"Company: {sample['SME_ID']}")
    print(f"Overall Score: {breakdown['overall_score']}")
    print(f"Category: {breakdown['category']}")
    print("\nComponents:")
    for name, details in breakdown['components'].items():
        print(f"  {name}: {details['score']:.1f} (weight: {details['weight']})")
