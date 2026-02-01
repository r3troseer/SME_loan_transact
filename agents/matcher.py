"""
Agent 3: Matcher
Calculates fit scores between companies and lenders, identifies unalignes,
and generates reallocation recommendations.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from lenders.profiles import LENDERS, get_lender
from utils.anonymizer import (
    anonymize_lender,
    round_score,
    band_turnover,
    group_region,
    anonymize_fit_reason,
    reset_lender_mapping,
)


class Matcher:
    """
    Matches companies to lenders based on fit scoring.
    Identifies unalignes and recommends reallocations.
    """

    def __init__(self):
        self.fit_threshold_strong = 30  # Gap for strong reallocation candidate
        self.fit_threshold_moderate = 15  # Gap for moderate candidate

    def analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze all companies and calculate fit scores with all lenders.

        Args:
            df: DataFrame with company data, risk scores, and inclusion scores

        Returns:
            DataFrame with fit scores and reallocation recommendations
        """
        # Calculate fit with current lender
        df["Current_Lender_Fit"], df["Current_Fit_Reasons"] = zip(
            *df.apply(
                lambda row: self._calculate_fit(row, get_lender(row["Current_Lender"])),
                axis=1,
            )
        )

        # Calculate fit with all lenders and find best match
        fit_results = df.apply(self._find_best_match, axis=1)
        df["Best_Match_Lender"] = fit_results.apply(lambda x: x["best_lender"])
        df["Best_Match_Fit"] = fit_results.apply(lambda x: x["best_fit"])
        df["Best_Match_Reasons"] = fit_results.apply(lambda x: x["best_reasons"])
        df["All_Lender_Fits"] = fit_results.apply(lambda x: x["all_fits"])

        # Calculate fit gap
        df["Fit_Gap"] = df["Best_Match_Fit"] - df["Current_Lender_Fit"]

        # Determine reallocation recommendation
        df["Reallocation_Status"] = df["Fit_Gap"].apply(self._categorize_reallocation)

        # Is it a unalign?
        df["Is_Unalign"] = df["Fit_Gap"] > self.fit_threshold_moderate

        return df

    def _calculate_fit(
        self, company: pd.Series, lender: dict
    ) -> Tuple[float, List[str]]:
        """
        Calculate fit score between a company and a lender.

        Returns:
            Tuple of (score, list of reasons)
        """
        if lender is None:
            return 0, ["Unknown lender"]

        score = 0
        reasons = []
        unalign_reasons = []

        # 1. Risk alignment (30 points max)
        risk_score = company.get("Risk_Score", 50)
        risk_min = lender.get("risk_score_min", 50)

        if risk_score >= risk_min:
            risk_points = 30
            reasons.append(f"Risk score {risk_score:.0f} meets threshold {risk_min}")
        else:
            # Partial points if close
            gap = risk_min - risk_score
            if gap <= 10:
                risk_points = 20
                unalign_reasons.append(
                    f"Risk score {risk_score:.0f} slightly below {risk_min}"
                )
            elif gap <= 20:
                risk_points = 10
                unalign_reasons.append(
                    f"Risk score {risk_score:.0f} below threshold {risk_min}"
                )
            else:
                risk_points = 0
                unalign_reasons.append(
                    f"Risk score {risk_score:.0f} significantly below {risk_min}"
                )

        score += risk_points

        # 2. Sector match (25 points max)
        company_sector = company.get("Sector", "")
        preferred_sectors = lender.get("preferred_sectors")

        if preferred_sectors is None:
            # Sector agnostic
            score += 20
            reasons.append("Lender is sector-agnostic")
        elif company_sector in preferred_sectors:
            score += 25
            reasons.append(f"Sector '{company_sector}' matches lender preference")
        else:
            unalign_reasons.append(
                f"Sector '{company_sector}' not in lender's focus: {preferred_sectors}"
            )

        # 3. Region match (20 points max)
        company_region = company.get("Region", "")
        preferred_regions = lender.get("preferred_regions")

        if preferred_regions is None:
            # National coverage
            score += 15
            reasons.append("Lender has national coverage")
        elif company_region in preferred_regions:
            score += 20
            reasons.append(f"Region '{company_region}' matches lender focus")
        else:
            unalign_reasons.append(f"Region '{company_region}' outside lender's focus")

        # 4. Size match (15 points max)
        turnover = company.get("Turnover", 0)
        min_turnover = lender.get("min_turnover", 0)
        max_turnover = lender.get("max_turnover")

        size_match = turnover >= min_turnover
        if max_turnover:
            size_match = size_match and turnover <= max_turnover

        if size_match:
            score += 15
            reasons.append(f"Company size £{turnover / 1e6:.1f}m in lender's range")
        else:
            if turnover < min_turnover:
                unalign_reasons.append(
                    f"Company too small (£{turnover / 1e6:.1f}m < £{min_turnover / 1e6:.1f}m min)"
                )
            elif max_turnover and turnover > max_turnover:
                unalign_reasons.append(
                    f"Company too large (£{turnover / 1e6:.1f}m > £{max_turnover / 1e6:.1f}m max)"
                )

        # 5. Inclusion alignment (10 points max)
        inclusion_score = company.get("Inclusion_Score", 50)
        has_inclusion_mandate = lender.get("inclusion_mandate", False)

        if has_inclusion_mandate:
            if inclusion_score >= 60:
                score += 10
                reasons.append("Strong inclusion alignment with lender's mandate")
            elif inclusion_score >= 45:
                score += 5
                reasons.append("Moderate inclusion alignment")
        else:
            # Non-inclusion lenders still get partial points for well-served companies
            if inclusion_score < 45:
                score += 5

        # Compile final reasons
        all_reasons = {"positive": reasons, "negative": unalign_reasons}

        return score, all_reasons

    def _find_best_match(self, company: pd.Series) -> Dict:
        """
        Find the best matching lender for a company.
        """
        all_fits = {}
        best_lender = None
        best_fit = 0
        best_reasons = None

        for lender_name, lender in LENDERS.items():
            fit_score, reasons = self._calculate_fit(company, lender)
            all_fits[lender_name] = fit_score

            if fit_score > best_fit:
                best_fit = fit_score
                best_lender = lender_name
                best_reasons = reasons

        return {
            "best_lender": best_lender,
            "best_fit": best_fit,
            "best_reasons": best_reasons,
            "all_fits": all_fits,
        }

    def _categorize_reallocation(self, fit_gap: float) -> str:
        """Categorize the reallocation recommendation."""
        if fit_gap >= self.fit_threshold_strong:
            return "STRONG REALLOCATION CANDIDATE"
        elif fit_gap >= self.fit_threshold_moderate:
            return "MODERATE REALLOCATION CANDIDATE"
        elif fit_gap > 0:
            return "MINOR IMPROVEMENT POSSIBLE"
        else:
            return "ADEQUATE FIT - NO ACTION"

    def get_reallocation_recommendation(
        self, company: pd.Series, anonymize: bool = False
    ) -> Dict:
        """
        Get detailed reallocation recommendation for a company.

        Args:
            company: Company data row
            anonymize: If True, anonymize alternative lenders and band financial values
        """
        current_lender = company.get("Current_Lender", "Unknown")
        current_fit = company.get("Current_Lender_Fit", 0)
        best_lender = company.get("Best_Match_Lender", "Unknown")
        best_fit = company.get("Best_Match_Fit", 0)
        fit_gap = company.get("Fit_Gap", 0)
        status = company.get("Reallocation_Status", "Unknown")

        if anonymize:
            # Current lender stays visible, recommended lender is anonymized
            display_best_lender = anonymize_lender(best_lender, is_current=False)
            display_region = group_region(company.get("Region", "Unknown"))
            display_turnover = band_turnover(company.get("Turnover", 0))
            display_risk = round_score(company.get("Risk_Score", 0))
            display_inclusion = round_score(company.get("Inclusion_Score", 0))
            display_current_fit = round_score(current_fit)
            display_best_fit = round_score(best_fit)
            display_gap = round_score(fit_gap)

            # Anonymize lender names in fit reasons
            current_reasons = company.get("Current_Fit_Reasons", {})
            best_reasons = company.get("Best_Match_Reasons", {})

            # Anonymize all lender fits (except current)
            all_fits = company.get("All_Lender_Fits", {})
            anon_all_fits = {}
            for lender_name, fit in all_fits.items():
                if lender_name == current_lender:
                    anon_all_fits[lender_name] = round_score(fit)
                else:
                    anon_name = anonymize_lender(lender_name, is_current=False)
                    anon_all_fits[anon_name] = round_score(fit)
        else:
            display_best_lender = best_lender
            display_region = company.get("Region", "Unknown")
            display_turnover = company.get("Turnover", 0)
            display_risk = company.get("Risk_Score", 0)
            display_inclusion = company.get("Inclusion_Score", 0)
            display_current_fit = current_fit
            display_best_fit = best_fit
            display_gap = fit_gap
            current_reasons = company.get("Current_Fit_Reasons", {})
            best_reasons = company.get("Best_Match_Reasons", {})
            anon_all_fits = company.get("All_Lender_Fits", {})

        return {
            "company_id": company.get("SME_ID", "Unknown"),
            "sector": company.get("Sector", "Unknown"),
            "region": display_region,
            "turnover": display_turnover,
            "risk_score": display_risk,
            "inclusion_score": display_inclusion,
            "current_situation": {
                "lender": current_lender,  # Always visible
                "fit_score": display_current_fit,
                "reasons": current_reasons,
            },
            "recommendation": {
                "lender": display_best_lender,  # Anonymized if not current
                "fit_score": display_best_fit,
                "reasons": best_reasons,
                "fit_improvement": display_gap,
            },
            "status": status,
            "is_unalign": company.get("Is_Unalign", False),
            "all_lender_fits": anon_all_fits,
        }

    def get_reallocation_candidates(
        self, df: pd.DataFrame, status_filter: str = None
    ) -> pd.DataFrame:
        """
        Get all companies that are reallocation candidates.

        Args:
            df: DataFrame with fit scores
            status_filter: Optional filter ('STRONG', 'MODERATE', or None for all)

        Returns:
            DataFrame of reallocation candidates
        """
        candidates = df[df["Is_Unalign"] == True].copy()

        if status_filter == "STRONG":
            candidates = candidates[
                candidates["Reallocation_Status"] == "STRONG REALLOCATION CANDIDATE"
            ]
        elif status_filter == "MODERATE":
            candidates = candidates[
                candidates["Reallocation_Status"].str.contains("CANDIDATE")
            ]

        return candidates.sort_values("Fit_Gap", ascending=False)

    def get_market_summary(self, df: pd.DataFrame, anonymize: bool = False) -> Dict:
        """
        Get market-level summary of fit and reallocation opportunities.

        Args:
            df: DataFrame with company and fit data
            anonymize: If True, anonymize lender names and band values
        """
        total = len(df)
        unalignes = len(df[df["Is_Unalign"] == True])
        strong_candidates = len(
            df[df["Reallocation_Status"] == "STRONG REALLOCATION CANDIDATE"]
        )
        moderate_candidates = len(
            df[df["Reallocation_Status"] == "MODERATE REALLOCATION CANDIDATE"]
        )

        # Average fit scores
        avg_current_fit = df["Current_Lender_Fit"].mean()
        avg_best_fit = df["Best_Match_Fit"].mean()

        # Lender analysis
        lender_stats = {}
        for lender_name in LENDERS.keys():
            current_count = len(df[df["Current_Lender"] == lender_name])
            best_match_count = len(df[df["Best_Match_Lender"] == lender_name])

            # Anonymize lender name if requested
            display_name = (
                anonymize_lender(lender_name, is_current=False)
                if anonymize
                else lender_name
            )

            lender_stats[display_name] = {
                "current_portfolio": current_count,
                "optimal_portfolio": best_match_count,
                "net_flow": best_match_count - current_count,
            }

        # Potential value if reallocated
        candidates = df[df["Is_Unalign"] == True]
        total_reallocation_value = candidates["Outstanding_Balance"].sum()

        # Anonymize values if requested
        if anonymize:
            from utils.anonymizer import band_portfolio_total, band_percentage

            value_display = band_portfolio_total(total_reallocation_value)
            pct_display = band_percentage(unalignes / total * 100)
            avg_imp_display = round_score(avg_best_fit - avg_current_fit)
        else:
            value_display = f"£{total_reallocation_value / 1e6:.1f}M"
            pct_display = round(unalignes / total * 100, 1)
            avg_imp_display = round(avg_best_fit - avg_current_fit, 1)

        return {
            "total_companies": total,
            "unaligned_companies": {"count": unalignes, "percentage": pct_display},
            "reallocation_candidates": {
                "strong": strong_candidates,
                "moderate": moderate_candidates,
                "total": strong_candidates + moderate_candidates,
            },
            "fit_scores": {
                "average_current_fit": round_score(avg_current_fit)
                if anonymize
                else round(avg_current_fit, 1),
                "average_optimal_fit": round_score(avg_best_fit)
                if anonymize
                else round(avg_best_fit, 1),
                "average_improvement": avg_imp_display,
            },
            "lender_flows": lender_stats,
            "reallocation_value": {
                "total_outstanding": round(total_reallocation_value, 2)
                if not anonymize
                else None,
                "formatted": value_display,
            },
        }


if __name__ == "__main__":
    # Test the matcher
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent))

    from utils.data_loader import load_data
    from agents.risk_analyst import RiskAnalyst
    from agents.inclusion_scanner import InclusionScanner

    excel_path = (
        r"C:\Users\user\Downloads\UKFIN Hackathon_sample_file_data_GFA Exchange.xlsx"
    )
    df = load_data(excel_path)

    # Run risk analyst
    risk_analyst = RiskAnalyst()
    df = risk_analyst.analyze(df)

    # Run inclusion scanner
    scanner = InclusionScanner()
    df = scanner.analyze(df)

    # Run matcher
    matcher = Matcher()
    df = matcher.analyze(df)

    print("=== Market Summary ===")
    summary = matcher.get_market_summary(df)
    for key, value in summary.items():
        print(f"{key}: {value}")

    print("\n=== Top 5 Reallocation Candidates ===")
    candidates = matcher.get_reallocation_candidates(df, "STRONG")
    for idx, row in candidates.head(5).iterrows():
        rec = matcher.get_reallocation_recommendation(row)
        print(f"\n{rec['company_id']} ({rec['sector']}, {rec['region']})")
        print(
            f"  Current: {rec['current_situation']['lender']} (Fit: {rec['current_situation']['fit_score']})"
        )
        print(
            f"  Recommended: {rec['recommendation']['lender']} (Fit: {rec['recommendation']['fit_score']})"
        )
        print(f"  Improvement: +{rec['recommendation']['fit_improvement']} points")
