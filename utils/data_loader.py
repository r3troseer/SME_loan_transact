"""
Data Loader Module
Loads SME company data from Excel and adds simulated loan details.
"""

import pandas as pd
import random
from pathlib import Path

# Lender names for random assignment
LENDER_NAMES = [
    "Alpha Bank",
    "Growth Capital Partners",
    "Regional Development Fund",
    "Sector Specialist Credit"
]

# Seed for reproducibility
random.seed(41)


def load_data(excel_path: str) -> pd.DataFrame:
    """
    Load all sheets from the Excel file and combine into single DataFrame.

    Args:
        excel_path: Path to the Excel file

    Returns:
        DataFrame with all companies and their sector labels
    """
    xl = pd.ExcelFile(excel_path)

    all_data = []
    for sheet_name in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=sheet_name)
        df['Sector'] = sheet_name
        all_data.append(df)

    combined = pd.concat(all_data, ignore_index=True)

    # Clean data
    combined = clean_data(combined)

    # Add revenue bands
    combined['Revenue_Band'] = pd.cut(
        combined['Turnover'],
        bins=[0, 5_000_000, 25_000_000, 100_000_000, float('inf')],
        labels=['<£5m', '£5m-£25m', '£25m-£100m', '>£100m']
    )

    # Add simulated loan details
    combined = add_loan_simulation(combined)

    # Generate anonymized IDs
    combined['SME_ID'] = [f"SME_{str(i).zfill(4)}" for i in range(len(combined))]

    return combined


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the DataFrame - handle missing values, ensure numeric types.
    """
    # Key numeric columns
    numeric_cols = [
        'Turnover', 'Gross Profit', 'Operating Profit', 'EBITDA',
        'Profit Before Tax', 'Profit After Tax', 'Total Assets',
        'Total Liabilities', 'Net Assets', 'Cash', 'Working Capital',
        'Total Current Assets', 'Total Current Liabilities',
        'Number of Employees', 'Trade Debtors', 'Trade Creditors'
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Fill missing Region with 'Unknown'
    if 'Region' in df.columns:
        df['Region'] = df['Region'].fillna('Unknown')

    # Fill missing employees with median
    if 'Number of Employees' in df.columns:
        df['Number of Employees'] = df['Number of Employees'].fillna(
            df['Number of Employees'].median()
        )

    return df


def simulate_loan_details(company: pd.Series) -> dict:
    """
    Generate realistic loan terms based on company financials.

    Args:
        company: Series with company data

    Returns:
        Dictionary with simulated loan details
    """
    turnover = company.get('Turnover', 10_000_000)

    # Loan amount: 5-15% of turnover (realistic for SME lending)
    loan_amount = turnover * random.uniform(0.05, 0.15)

    # Term: 5-7 years
    term_years = random.choice([5, 6, 7])

    # Base interest rate (will be adjusted by risk score later)
    base_rate = random.uniform(4.5, 7.5)

    # Repayment progress: 1 to term-1 years paid
    years_paid = random.randint(1, term_years - 1)
    years_remaining = term_years - years_paid

    # Calculate outstanding balance (simplified linear amortization)
    outstanding = loan_amount * (years_remaining / term_years)

    # Monthly payment (simplified)
    monthly_rate = base_rate / 100 / 12
    total_months = term_years * 12
    if monthly_rate > 0:
        monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**total_months) / ((1 + monthly_rate)**total_months - 1)
    else:
        monthly_payment = loan_amount / total_months

    # Randomly assign to a synthetic lender
    current_lender = random.choice(LENDER_NAMES)

    return {
        'Loan_Amount': round(loan_amount, 2),
        'Loan_Term_Years': term_years,
        'Interest_Rate': round(base_rate, 2),
        'Years_Paid': years_paid,
        'Years_Remaining': years_remaining,
        'Outstanding_Balance': round(outstanding, 2),
        'Monthly_Payment': round(monthly_payment, 2),
        'Current_Lender': current_lender
    }


def add_loan_simulation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add simulated loan columns to the DataFrame.
    """
    loan_details = df.apply(simulate_loan_details, axis=1)
    loan_df = pd.DataFrame(loan_details.tolist())

    return pd.concat([df, loan_df], axis=1)


def get_data_summary(df: pd.DataFrame) -> dict:
    """
    Get summary statistics for the dataset.
    """
    return {
        'total_companies': len(df),
        'sectors': df['Sector'].nunique(),
        'regions': df['Region'].nunique(),
        'turnover_range': {
            'min': df['Turnover'].min(),
            'max': df['Turnover'].max(),
            'median': df['Turnover'].median()
        },
        'revenue_bands': df['Revenue_Band'].value_counts().to_dict(),
        'lender_distribution': df['Current_Lender'].value_counts().to_dict(),
        'total_loan_value': df['Outstanding_Balance'].sum()
    }


if __name__ == "__main__":
    # Test the data loader
    excel_path = r"C:\Users\user\Downloads\UKFIN Hackathon_sample_file_data_GFA Exchange.xlsx"

    print("Loading data...")
    df = load_data(excel_path)

    print(f"\nLoaded {len(df)} companies")
    print(f"\nColumns: {df.columns.tolist()}")

    print("\n=== Data Summary ===")
    summary = get_data_summary(df)
    for key, value in summary.items():
        print(f"{key}: {value}")

    print("\n=== Sample Company ===")
    sample = df.iloc[0]
    print(f"SME_ID: {sample['SME_ID']}")
    print(f"Sector: {sample['Sector']}")
    print(f"Region: {sample['Region']}")
    print(f"Turnover: £{sample['Turnover']:,.0f}")
    print(f"Current Lender: {sample['Current_Lender']}")
    print(f"Loan Outstanding: £{sample['Outstanding_Balance']:,.0f}")
    print(f"Years Remaining: {sample['Years_Remaining']}")
