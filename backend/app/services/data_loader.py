"""Data loading and migration service - loads Excel data into SQLite"""

import pandas as pd
import numpy as np
import sys
import os

# Add parent directories to path to import existing agents
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from sqlalchemy.orm import Session
from ..models import Company, Loan, Lender
from ..core.database import engine, SessionLocal

# Import existing agents
try:
    from agents.risk_analyst import RiskAnalyst
    from agents.inclusion_scanner import InclusionScanner
    from agents.matcher import Matcher
    from agents.pricer import Pricer
    from lenders.profiles import LENDERS

    AGENTS_AVAILABLE = True
except ImportError:
    print("Warning: Could not import agents, using simplified data loading")
    AGENTS_AVAILABLE = False


def load_excel_data(file_path: str) -> pd.DataFrame:
    """Load and process Excel data"""
    print(f"Loading data from {file_path}...")

    # Read all sheets
    xlsx = pd.ExcelFile(file_path)
    dfs = []

    for sheet_name in xlsx.sheet_names:
        df = pd.read_excel(xlsx, sheet_name=sheet_name)
        df["Sector"] = sheet_name
        dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)
    print(f"Loaded {len(combined)} companies from {len(xlsx.sheet_names)} sectors")

    return combined


def simulate_loans(df: pd.DataFrame, lender_names: list) -> pd.DataFrame:
    """Simulate loan details for each company"""
    np.random.seed(42)

    # Loan simulation
    df["Loan_Amount"] = df["Turnover"].apply(
        lambda x: x * np.random.uniform(0.05, 0.15) if pd.notna(x) else 0
    )
    df["Loan_Term_Years"] = np.random.choice([5, 6, 7], size=len(df))
    df["Years_Remaining"] = df["Loan_Term_Years"].apply(
        lambda x: np.random.randint(1, x)
    )
    df["Interest_Rate"] = np.random.uniform(0.045, 0.075, size=len(df))

    # Calculate outstanding balance (linear amortization)
    df["Outstanding_Balance"] = df.apply(
        lambda row: row["Loan_Amount"]
        * (row["Years_Remaining"] / row["Loan_Term_Years"])
        if row["Loan_Term_Years"] > 0
        else 0,
        axis=1,
    )

    # Monthly payment (simplified)
    df["Monthly_Payment"] = df.apply(
        lambda row: (
            row["Loan_Amount"] * (1 + row["Interest_Rate"] * row["Loan_Term_Years"])
        )
        / (row["Loan_Term_Years"] * 12)
        if row["Loan_Term_Years"] > 0
        else 0,
        axis=1,
    )

    # Assign random current lender
    df["Current_Lender"] = np.random.choice(lender_names, size=len(df))

    # Generate SME IDs
    df["SME_ID"] = [f"SME_{i:04d}" for i in range(len(df))]

    return df


def run_analysis_pipeline(df: pd.DataFrame, lenders: list) -> pd.DataFrame:
    """Run all analysis agents on the data"""
    if not AGENTS_AVAILABLE:
        print("Agents not available, using placeholder scores")
        df["Risk_Score"] = np.random.uniform(30, 80, size=len(df))
        df["Risk_Category"] = df["Risk_Score"].apply(
            lambda x: "Low Risk"
            if x >= 60
            else ("Moderate Risk" if x >= 40 else "High Risk")
        )
        df["Inclusion_Score"] = np.random.uniform(20, 90, size=len(df))
        df["Inclusion_Category"] = df["Inclusion_Score"].apply(
            lambda x: "High Priority" if x >= 60 else "Standard"
        )
        return df

    print("Running Risk Analysis...")
    risk_analyst = RiskAnalyst()
    df = risk_analyst.analyze(df)

    print("Running Inclusion Scanning...")
    inclusion_scanner = InclusionScanner()
    df = inclusion_scanner.analyze(df)

    print("Running Lender Matching...")
    matcher = Matcher(lenders)
    df = matcher.analyze(df)

    print("Running Pricing Analysis...")
    pricer = Pricer()
    df = pricer.analyze(df)

    return df


def migrate_to_database(df: pd.DataFrame, lenders_data: list):
    """Migrate processed data to SQLite database"""
    db = SessionLocal()

    try:
        # Clear existing data
        db.query(Loan).delete()
        db.query(Company).delete()
        db.query(Lender).delete()
        db.commit()

        # Insert lenders
        lender_map = {}
        for lender_data in lenders_data:
            lender = Lender(
                name=lender_data["name"],
                description=lender_data.get("description", ""),
                risk_tolerance=lender_data.get("risk_tolerance", "medium"),
                risk_score_min=lender_data.get("risk_score_min", 0),
                preferred_sectors=lender_data.get("preferred_sectors"),
                min_turnover=lender_data.get("min_turnover", 0),
                max_turnover=lender_data.get("max_turnover"),
                preferred_regions=lender_data.get("preferred_regions"),
                inclusion_mandate=lender_data.get("inclusion_mandate", False),
            )
            db.add(lender)
            db.flush()
            lender_map[lender_data["name"]] = lender.id

        db.commit()
        print(f"Inserted {len(lenders_data)} lenders")

        # Insert companies and loans
        for _, row in df.iterrows():
            # Create company
            company = Company(
                sme_id=row.get("SME_ID", f"SME_{_}"),
                sector=row.get("Sector", "Unknown"),
                region=row.get("Region", "Unknown"),
                turnover=row.get("Turnover"),
                ebitda=row.get("EBITDA"),
                profit_after_tax=row.get("Profit After Tax"),
                total_assets=row.get("Total Assets"),
                total_liabilities=row.get("Total Liabilities"),
                current_assets=row.get("Current Assets"),
                current_liabilities=row.get("Current Liabilities"),
                cash=row.get("Cash"),
                inventory=row.get("Inventory"),
                receivables=row.get("Receivables"),
                fixed_assets=row.get("Fixed Assets"),
                equity=row.get("Equity"),
                employees=int(row.get("Employees", 0))
                if pd.notna(row.get("Employees"))
                else None,
                # Risk scores
                risk_score=row.get("Risk_Score"),
                risk_category=row.get("Risk_Category"),
                liquidity_score=row.get("Liquidity_Score"),
                profitability_score=row.get("Profitability_Score"),
                leverage_score=row.get("Leverage_Score"),
                cash_score=row.get("Cash_Score"),
                efficiency_score=row.get("Efficiency_Score"),
                size_score=row.get("Size_Score"),
                # Inclusion scores
                inclusion_score=row.get("Inclusion_Score"),
                inclusion_category=row.get("Inclusion_Category"),
                regional_inclusion_score=row.get("Regional_Inclusion_Score"),
                sector_inclusion_score=row.get("Sector_Inclusion_Score"),
                size_inclusion_score=row.get("Size_Inclusion_Score"),
                overlooked_score=row.get("Overlooked_Score"),
                inclusion_flags=row.get("Inclusion_Flags")
                if isinstance(row.get("Inclusion_Flags"), list)
                else None,
            )
            db.add(company)
            db.flush()

            # Get lender IDs
            current_lender_id = lender_map.get(row.get("Current_Lender"))
            best_match_lender_id = lender_map.get(row.get("Best_Match_Lender"))

            # Create loan
            loan = Loan(
                company_id=company.id,
                current_lender_id=current_lender_id,
                loan_amount=row.get("Loan_Amount"),
                outstanding_balance=row.get("Outstanding_Balance"),
                loan_term_years=int(row.get("Loan_Term_Years", 5)),
                years_remaining=row.get("Years_Remaining"),
                interest_rate=row.get("Interest_Rate"),
                monthly_payment=row.get("Monthly_Payment"),
                # Matching
                current_lender_fit=row.get("Current_Lender_Fit"),
                current_fit_reasons=row.get("Current_Fit_Reasons")
                if isinstance(row.get("Current_Fit_Reasons"), dict)
                else None,
                best_match_lender_id=best_match_lender_id,
                best_match_fit=row.get("Best_Match_Fit"),
                best_match_reasons=row.get("Best_Match_Reasons")
                if isinstance(row.get("Best_Match_Reasons"), dict)
                else None,
                fit_gap=row.get("Fit_Gap"),
                reallocation_status=row.get("Reallocation_Status"),
                is_unalign=row.get("Is_Unalign", False),
                # Pricing
                default_probability=row.get("Default_Probability"),
                remaining_payments=row.get("Remaining_Payments"),
                gross_loan_value=row.get("Gross_Loan_Value"),
                expected_loss=row.get("Expected_Loss"),
                risk_adjusted_value=row.get("Risk_Adjusted_Value"),
                misfit_discount=row.get("Misfit_Discount"),
                suggested_price=row.get("Suggested_Price"),
                discount_percent=row.get("Discount_Percent"),
                gross_roi=row.get("Gross_ROI"),
                risk_adjusted_roi=row.get("Risk_Adjusted_ROI"),
                annualized_roi=row.get("Annualized_ROI"),
            )
            db.add(loan)

        db.commit()
        print(f"Inserted {len(df)} companies and loans")

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def run_migration(excel_path: str = None):
    """Run full data migration"""
    from ..core.database import init_db

    # Initialize database tables
    init_db()

    # Default path - try multiple locations
    if excel_path is None:
        # Try Docker path first (/app/data/), then local dev path
        possible_paths = [
            # Docker: /app/app/services -> /app/data
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "UKFIN Hackathon_sample_file_data_GFA Exchange.xlsx"),
            # Local dev: backend/app/services -> data (project root)
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "UKFIN Hackathon_sample_file_data_GFA Exchange.xlsx"),
        ]

        for path in possible_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                excel_path = abs_path
                break

        if excel_path is None:
            excel_path = possible_paths[0]  # Default to first path for error message

        print(f"Looking for Excel file at: {excel_path}")

    # Get lenders
    if AGENTS_AVAILABLE:
        lenders_data = LENDERS
    else:
        lenders_data = [
            {
                "name": "Alpha Bank",
                "description": "Conservative lender",
                "risk_tolerance": "low",
                "risk_score_min": 60,
            },
            {
                "name": "Growth Capital Partners",
                "description": "Growth-focused",
                "risk_tolerance": "high",
                "risk_score_min": 30,
            },
            {
                "name": "Regional Development Fund",
                "description": "Regional focus",
                "risk_tolerance": "medium",
                "inclusion_mandate": True,
            },
            {
                "name": "Sector Specialist Credit",
                "description": "Sector specialist",
                "risk_tolerance": "medium",
            },
        ]

    lender_names = [l["name"] for l in lenders_data]

    # Load and process data
    df = load_excel_data(excel_path)
    df = simulate_loans(df, lender_names)
    df = run_analysis_pipeline(df, lenders_data)

    # Migrate to database
    migrate_to_database(df, lenders_data)

    print("Migration complete!")


if __name__ == "__main__":
    run_migration()
