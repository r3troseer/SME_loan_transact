"""
GFA Exchange - Inclusive AI Loan Reallocation Sandbox
Main Streamlit Application
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Import our modules
from utils.data_loader import load_data, get_data_summary
from agents.risk_analyst import RiskAnalyst
from agents.inclusion_scanner import InclusionScanner
from agents.matcher import Matcher
from agents.pricer import Pricer
from agents.explainer import Explainer, prepare_explanation_data
from agents.swap_matcher import SwapMatcher, get_swap_statistics
from lenders.profiles import LENDERS, get_lender_for_display
from utils.anonymizer import (
    anonymize_lender,
    group_region,
    round_score,
    band_turnover,
    band_loan_amount,
    band_percentage,
    band_portfolio_total,
    format_amount_range,
    reset_lender_mapping,
    anonymize_lender_for_lender_view,
)
from utils.credit_system import CreditManager, CREDIT_PACKAGES

# Enable anonymization (set to True for demo/production)
ANONYMIZE = True

# Page config
st.set_page_config(
    page_title="GFA Exchange - Loan Reallocation Sandbox",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-top: 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .fit-score-good { color: #2ca02c; font-weight: bold; }
    .fit-score-moderate { color: #ff7f0e; font-weight: bold; }
    .fit-score-poor { color: #d62728; font-weight: bold; }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def load_and_process_data(excel_path: str):
    """Load and process all data through the agent pipeline."""
    # Load raw data
    df = load_data(excel_path)

    # Run all agents
    df = RiskAnalyst().analyze(df)
    df = InclusionScanner().analyze(df)
    df = Matcher().analyze(df)
    df = Pricer().analyze(df)

    return df


def get_credit_manager():
    """Get or create credit manager in session state."""
    if "credit_manager" not in st.session_state:
        st.session_state.credit_manager = CreditManager(initial_credits=100)
    return st.session_state.credit_manager


def init_matching_state():
    """Initialize session state for double-blind matching system."""
    if "bids" not in st.session_state:
        # {loan_id: [{buyer_id, discount_range, timestamp}]}
        st.session_state.bids = {}
    if "interests" not in st.session_state:
        # {loan_id: [buyer_ids]}
        st.session_state.interests = {}
    if "reveals" not in st.session_state:
        # {loan_id: {seller_revealed: bool, buyer_revealed: bool, buyer_id: str}}
        st.session_state.reveals = {}
    if "listed_for_sale" not in st.session_state:
        # Set of loan_ids that sellers have listed
        st.session_state.listed_for_sale = set()


def init_swap_state():
    """Initialize session state for loan swap system."""
    # Auto-generated swap suggestions (cached)
    if "auto_swap_suggestions" not in st.session_state:
        st.session_state.auto_swap_suggestions = []

    # Manual swap proposals
    # {proposal_id: {proposer_lender, proposer_loan_id, target_lender,
    #                target_loan_id, status, message, created_at}}
    if "swap_proposals" not in st.session_state:
        st.session_state.swap_proposals = {}

    # Proposal counter for unique IDs
    if "swap_proposal_counter" not in st.session_state:
        st.session_state.swap_proposal_counter = 0

    # Manual proposal wizard state
    if "manual_proposal_draft" not in st.session_state:
        st.session_state.manual_proposal_draft = {
            "step": 1,
            "my_loan_id": None,
            "target_lender": None,
            "their_loan_id": None,
            "message": "",
        }

    # Accepted swaps (for demo tracking)
    if "accepted_swaps" not in st.session_state:
        st.session_state.accepted_swaps = set()  # Set of swap identifiers

    # Generated inclusion stories (cached for display)
    if "generated_stories" not in st.session_state:
        st.session_state.generated_stories = {}


def render_sidebar():
    """Render the sidebar with navigation and credit balance."""
    st.sidebar.markdown("## 🏦 GFA Exchange")
    st.sidebar.markdown("### AI Loan Reallocation Sandbox")

    # Credit Balance Display
    cm = get_credit_manager()
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💳 Credits")

    # Show credit balance with color coding
    balance = cm.check_balance()
    if balance > 50:
        st.sidebar.markdown(f"**Balance: {balance} credits** ✅")
    elif balance > 20:
        st.sidebar.markdown(f"**Balance: {balance} credits** ⚠️")
    else:
        st.sidebar.markdown(f"**Balance: {balance} credits** 🔴")

    # Show quick stats
    summary = cm.get_summary()
    st.sidebar.caption(
        f"Spent: {summary['total_spent']} | Actions: {summary['total_transactions']}"
    )

    # Add credits button (for demo)
    if st.sidebar.button("➕ Add 50 Credits (Demo)"):
        cm.add_credits(50, "demo_bonus")
        st.rerun()

    # Reset button
    if st.sidebar.button("🔄 Reset Credits"):
        cm.reset()
        st.rerun()

    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "Navigate to:",
        [
            "📊 Portfolio Overview",
            "🏢 Company Analysis",
            "💵 Loan Sales",
            "🔄 Loan Swaps",
            "🏛️ Lender View",
            "📈 Market Insights",
            "💰 Transaction Simulator",
        ],
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.markdown(
        "This sandbox demonstrates how AI can enable "
        "**fair, responsible, and insight-led** SME loan allocation "
        "through shared intelligence."
    )

    # Credit pricing info
    with st.sidebar.expander("💰 Credit Costs"):
        st.markdown("""
        **Loan Sales:**
        | Action | Cost |
        |--------|------|
        | View Details | 1 credit |
        | AI Explanation | 2 credits |
        | Submit Bid | 3 credits |
        | View Bids | 3 credits |
        | Express Interest | 5 credits |
        | Reveal Identity | 5 credits |

        **Loan Swaps:**
        | Action | Cost |
        |--------|------|
        | View Swap Details | 1 credit |
        | Accept Swap | 3 credits |
        | Browse Unlisted | 2 credits |
        | Propose Swap | 5 credits |
        | Swap Inclusion Story | 2 credits |
        """)

    return page


def render_portfolio_overview(df):
    """Render the Portfolio Overview page."""
    st.markdown('<p class="main-header">Portfolio Overview</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Aggregated view of all SME companies in the dataset</p>',
        unsafe_allow_html=True,
    )

    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)

    total_value = df["Outstanding_Balance"].sum()
    unaligned = len(df[df["Is_Unalign"] == True])
    avg_risk = df["Risk_Score"].mean()

    with col1:
        st.metric("Total Companies", len(df))
    with col2:
        # Band the total loan value if anonymizing
        if ANONYMIZE:
            st.metric("Total Loan Value", band_portfolio_total(total_value))
        else:
            st.metric("Total Loan Value", f"£{total_value / 1e6:.1f}M")
    with col3:
        unalign_pct = (
            band_percentage(unaligned / len(df) * 100)
            if ANONYMIZE
            else round(unaligned / len(df) * 100)
        )
        st.metric("Unaligned Loans", f"{unaligned} ({unalign_pct}%)")
    with col4:
        risk_display = round_score(avg_risk) if ANONYMIZE else round(avg_risk)
        st.metric("Avg Risk Score", f"{risk_display}/100")

    st.markdown("---")

    # Charts row
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Companies by Sector")
        sector_counts = df["Sector"].value_counts().reset_index()
        sector_counts.columns = ["Sector", "Count"]
        fig = px.bar(
            sector_counts,
            x="Sector",
            y="Count",
            color="Count",
            color_continuous_scale="Blues",
        )
        fig.update_layout(showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Companies by Region")
        # Group regions if anonymizing
        if ANONYMIZE:
            df_regions = df.copy()
            df_regions["Region_Grouped"] = df_regions["Region"].apply(group_region)
            region_counts = df_regions["Region_Grouped"].value_counts().reset_index()
            region_counts.columns = ["Region", "Count"]
        else:
            region_counts = df["Region"].value_counts().reset_index()
            region_counts.columns = ["Region", "Count"]
        fig = px.bar(
            region_counts,
            x="Region",
            y="Count",
            color="Count",
            color_continuous_scale="Oranges",
        )
        fig.update_layout(showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    # Score distributions
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Risk Score Distribution")
        fig = px.histogram(
            df, x="Risk_Score", nbins=20, color_discrete_sequence=["#1f77b4"]
        )
        fig.update_layout(xaxis_title="Risk Score", yaxis_title="Count")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Inclusion Score Distribution")
        fig = px.histogram(
            df, x="Inclusion_Score", nbins=20, color_discrete_sequence=["#ff7f0e"]
        )
        fig.update_layout(xaxis_title="Inclusion Score", yaxis_title="Count")
        st.plotly_chart(fig, use_container_width=True)

    # Lender distribution - anonymize lender names in overview
    st.subheader("Current Lender Distribution")
    lender_counts = df["Current_Lender"].value_counts().reset_index()
    lender_counts.columns = ["Lender", "Count"]
    if ANONYMIZE:
        reset_lender_mapping()  # Reset for consistent mapping
        lender_counts["Lender"] = lender_counts["Lender"].apply(
            lambda x: anonymize_lender(x, is_current=False)
        )
    fig = px.pie(
        lender_counts,
        values="Count",
        names="Lender",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_company_analysis(df):
    """Render the Company Analysis page."""
    st.markdown('<p class="main-header">Company Analysis</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Deep dive into individual company profiles</p>',
        unsafe_allow_html=True,
    )

    # Company selector
    company_options = df["SME_ID"].tolist()
    selected_company = st.selectbox("Select Company", company_options)

    company = df[df["SME_ID"] == selected_company].iloc[0]

    # Apply anonymization
    if ANONYMIZE:
        reset_lender_mapping()
        region_display = group_region(company["Region"])
        turnover_display = band_turnover(company["Turnover"])
        risk_display = round_score(company["Risk_Score"])
        inclusion_display = round_score(company["Inclusion_Score"])
        current_fit_display = round_score(company["Current_Lender_Fit"])
        best_fit_display = round_score(company["Best_Match_Fit"])
        fit_gap_display = round_score(company["Fit_Gap"])
        best_lender_display = anonymize_lender(
            company["Best_Match_Lender"], is_current=False
        )
    else:
        region_display = company["Region"]
        turnover_display = f"£{company['Turnover'] / 1e6:.1f}M"
        risk_display = company["Risk_Score"]
        inclusion_display = company["Inclusion_Score"]
        current_fit_display = company["Current_Lender_Fit"]
        best_fit_display = company["Best_Match_Fit"]
        fit_gap_display = company["Fit_Gap"]
        best_lender_display = company["Best_Match_Lender"]

    # Overview cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### Company Profile")
        st.markdown(f"**Sector:** {company['Sector']}")
        st.markdown(f"**Region:** {region_display}")
        st.markdown(f"**Turnover:** {turnover_display}")
        st.markdown(f"**Employees:** {int(company['Number of Employees'])}")

    with col2:
        st.markdown("### Risk Assessment")
        risk_color = (
            "fit-score-good"
            if risk_display >= 65
            else "fit-score-moderate"
            if risk_display >= 45
            else "fit-score-poor"
        )
        st.markdown(
            f"**Risk Score:** <span class='{risk_color}'>{risk_display}/100</span>",
            unsafe_allow_html=True,
        )
        st.markdown(f"**Category:** {company['Risk_Category']}")

    with col3:
        st.markdown("### Inclusion Profile")
        inc_color = (
            "fit-score-good" if inclusion_display >= 60 else "fit-score-moderate"
        )
        st.markdown(
            f"**Inclusion Score:** <span class='{inc_color}'>{inclusion_display}/100</span>",
            unsafe_allow_html=True,
        )
        st.markdown(f"**Category:** {company['Inclusion_Category']}")

    st.markdown("---")

    # Fit analysis
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Current Lender Fit")
        # Current lender is always visible
        st.markdown(f"**Lender:** {company['Current_Lender']}")
        fit_color = (
            "fit-score-good"
            if current_fit_display >= 65
            else "fit-score-moderate"
            if current_fit_display >= 45
            else "fit-score-poor"
        )
        st.markdown(
            f"**Fit Score:** <span class='{fit_color}'>{current_fit_display}/100</span>",
            unsafe_allow_html=True,
        )

        # Reasons
        if company["Current_Fit_Reasons"]:
            if company["Current_Fit_Reasons"].get("positive"):
                st.markdown("**Positive factors:**")
                for r in company["Current_Fit_Reasons"]["positive"]:
                    st.markdown(f"✓ {r}")
            if company["Current_Fit_Reasons"].get("negative"):
                st.markdown("**Unalign factors:**")
                for r in company["Current_Fit_Reasons"]["negative"]:
                    st.markdown(f"✗ {r}")

    with col2:
        st.markdown("### Best Match Lender")
        # Best match lender is anonymized
        st.markdown(f"**Lender:** {best_lender_display}")
        st.markdown(
            f"**Fit Score:** <span class='fit-score-good'>{best_fit_display}/100</span>",
            unsafe_allow_html=True,
        )
        st.markdown(f"**Improvement:** +{fit_gap_display} points")
        st.markdown(f"**Status:** {company['Reallocation_Status']}")

    # Financial metrics radar chart
    st.markdown("---")
    st.subheader("Financial Health Breakdown")

    categories = [
        "Liquidity",
        "Profitability",
        "Leverage",
        "Cash Position",
        "Efficiency",
        "Stability",
    ]
    values = [
        company.get("Liquidity_Score", 50),
        company.get("Profitability_Score", 50),
        company.get("Leverage_Score", 50),
        company.get("Cash_Score", 50),
        company.get("Efficiency_Score", 50),
        company.get("Size_Score", 50),
    ]

    fig = go.Figure(
        data=go.Scatterpolar(
            r=values, theta=categories, fill="toself", line_color="#1f77b4"
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)


def render_loan_sales(df):
    """Render the Loan Sales page with double-blind matching."""
    st.markdown('<p class="main-header">Loan Sales</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Buy and sell loans in a double-blind marketplace</p>',
        unsafe_allow_html=True,
    )

    # Initialize matching state
    init_matching_state()
    init_swap_state()

    # Store DataFrame in session state for swap proposals
    st.session_state.current_df = df

    # Reset lender mapping for consistent anonymization
    if ANONYMIZE:
        reset_lender_mapping()

    # Get credit manager
    cm = get_credit_manager()

    # Lender selector (simulates login)
    st.markdown("### 🏦 Select Your Lender")
    lender_list = list(df["Current_Lender"].unique())
    selected_lender = st.selectbox(
        "This simulates being logged in as a lender",
        lender_list,
        help="In production, this would be determined by your login credentials",
    )

    st.markdown("---")

    # Two tabs: Seller and Buyer perspectives
    seller_tab, buyer_tab = st.tabs(["📤 Loans to Sell", "📥 Opportunities to Buy"])

    with seller_tab:
        render_seller_view(df, selected_lender, cm)

    with buyer_tab:
        render_buyer_view(df, selected_lender, cm)


def render_seller_view(df, my_lender, cm):
    """Show loans I hold that are unaligned - seller's perspective."""
    st.markdown("### Your Unaligned Loans")
    st.markdown(
        "These loans in your portfolio don't fit your strategy. Consider selling or swapping them."
    )

    # Get my unaligned loans
    my_unaligned = df[
        (df["Current_Lender"] == my_lender) & (df["Is_Unalign"] == True)
    ].sort_values("Fit_Gap", ascending=False)

    if len(my_unaligned) == 0:
        st.success("All your loans are well-matched to your portfolio strategy.")
        return

    st.info(f"📤 Found **{len(my_unaligned)}** loans that may not fit your strategy")

    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "Strong Candidates", "Moderate Candidates"],
            key="seller_status",
        )
    with col2:
        sector_filter = st.selectbox(
            "Filter by Sector",
            ["All"] + list(my_unaligned["Sector"].unique()),
            key="seller_sector",
        )

    # Apply filters
    filtered = my_unaligned.copy()
    if status_filter == "Strong Candidates":
        filtered = filtered[
            filtered["Reallocation_Status"] == "STRONG REALLOCATION CANDIDATE"
        ]
    elif status_filter == "Moderate Candidates":
        filtered = filtered[
            filtered["Reallocation_Status"] == "MODERATE REALLOCATION CANDIDATE"
        ]
    if sector_filter != "All":
        filtered = filtered[filtered["Sector"] == sector_filter]

    # Display seller cards
    for idx, row in filtered.head(10).iterrows():
        render_seller_card(row, my_lender, cm)


def render_seller_card(loan, my_lender, cm):
    """Render a card for seller view - my loan to potentially sell."""
    sme_id = loan["SME_ID"]

    # Get market interest for this loan from session state
    interest_count = len(st.session_state.interests.get(sme_id, []))
    bids = st.session_state.bids.get(sme_id, [])
    is_listed = sme_id in st.session_state.listed_for_sale

    # Display values
    if ANONYMIZE:
        my_fit = round_score(loan["Current_Lender_Fit"])
        best_fit = round_score(loan["Best_Match_Fit"])
        outstanding = band_loan_amount(loan["Outstanding_Balance"])
        region = group_region(loan["Region"])
    else:
        my_fit = f"{loan['Current_Lender_Fit']:.0f}"
        best_fit = f"{loan['Best_Match_Fit']:.0f}"
        outstanding = f"£{loan['Outstanding_Balance']:,.0f}"
        region = loan["Region"]

    # Card header with fit score indicator
    fit_indicator = (
        "🔴"
        if loan["Current_Lender_Fit"] < 40
        else "🟡"
        if loan["Current_Lender_Fit"] < 60
        else "🟢"
    )
    expander_title = (
        f"{fit_indicator} {sme_id} | {loan['Sector']} | Your Fit: {my_fit}/100"
    )

    with st.expander(expander_title, expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**YOUR POSITION**")
            st.markdown(f"**Lender:** {my_lender} (You)")
            st.markdown(f"**Fit Score:** {my_fit}/100")
            st.markdown(f"**Sector:** {loan['Sector']}")
            st.markdown(f"**Region:** {region}")
            st.markdown(f"**Outstanding:** {outstanding}")
            st.markdown(f"**Remaining Term:** {loan['Years_Remaining']} years")

        with col2:
            st.markdown("**MARKET INTEREST**")
            if is_listed:
                st.markdown(f"**Status:** 🟢 Listed for Sale")
                st.markdown(f"**Buyers interested:** {interest_count}")
                if bids:
                    avg_discount = sum(b["discount"] for b in bids) / len(bids)
                    discount_display = (
                        f"{band_percentage(avg_discount)}%"
                        if ANONYMIZE
                        else f"{avg_discount:.1f}%"
                    )
                    st.markdown(f"**Bid range:** ~{discount_display} discount")
                else:
                    st.markdown("**Bids:** No bids yet")
                st.markdown(f"**Best buyer fit:** {best_fit}/100")
            else:
                st.markdown("**Status:** ⚪ Not listed")
                st.markdown("*List for sale to see market interest*")

        st.markdown("---")

        # Actions
        col1, col2, col3 = st.columns(3)

        with col1:
            if not is_listed:
                if st.button("📋 List for Sale", key=f"list_{sme_id}"):
                    st.session_state.listed_for_sale.add(sme_id)
                    st.success("Listed! Potential buyers will be notified.")
                    st.rerun()
            else:
                st.markdown("✅ **Listed**")

        with col2:
            # View bids - costs credits
            if is_listed and bids:
                has_viewed_bids = cm.has_viewed_item("view_bids", sme_id)
                if has_viewed_bids:
                    st.markdown("**Bid Details:**")
                    for i, bid in enumerate(bids):
                        discount_display = (
                            f"{band_percentage(bid['discount'])}%"
                            if ANONYMIZE
                            else f"{bid['discount']:.1f}%"
                        )
                        st.markdown(f"- Buyer {i + 1}: {discount_display} discount")
                else:
                    cost = cm.get_cost("view_bids")
                    if cm.can_afford("view_bids"):
                        if st.button(
                            f"👁 View Bids ({cost} credits)", key=f"viewbids_{sme_id}"
                        ):
                            cm.spend("view_bids", sme_id)
                            st.rerun()
                    else:
                        st.caption(f"Need {cost} credits to view bids")

        with col3:
            # Reveal counterparty (if mutual interest)
            if is_listed and interest_count > 0:
                reveal_info = st.session_state.reveals.get(sme_id, {})
                if reveal_info.get("seller_revealed") and reveal_info.get(
                    "buyer_revealed"
                ):
                    buyer_id = reveal_info.get("buyer_id", "Unknown")
                    st.success(f"🔓 Matched with: {buyer_id}")
                else:
                    cost = cm.get_cost("reveal_counterparty")
                    if cm.can_afford("reveal_counterparty"):
                        if st.button(
                            f"🔓 Accept Reveal ({cost} credits)",
                            key=f"reveal_seller_{sme_id}",
                        ):
                            cm.spend("reveal_counterparty", sme_id)
                            if sme_id not in st.session_state.reveals:
                                st.session_state.reveals[sme_id] = {}
                            st.session_state.reveals[sme_id]["seller_revealed"] = True
                            st.info("Waiting for buyer to also accept reveal...")
                            st.rerun()
                    else:
                        st.caption(f"Need {cost} credits to reveal")


def render_buyer_view(df, my_lender, cm):
    """Show loans from others that fit me - buyer's perspective."""
    st.markdown("### Acquisition Opportunities")
    st.markdown("Loans from other lenders that would be a good fit for your portfolio.")

    # Get opportunities: loans where I'm the best match but not the current holder
    opportunities = df[
        (df["Best_Match_Lender"] == my_lender)
        & (df["Current_Lender"] != my_lender)
        & (df["Is_Unalign"] == True)
    ].sort_values("Fit_Gap", ascending=False)

    if len(opportunities) == 0:
        st.info(
            "No acquisition opportunities match your portfolio strategy at this time."
        )
        return

    st.info(f"📥 Found **{len(opportunities)}** loans that would fit your portfolio")

    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "Strong Candidates", "Moderate Candidates"],
            key="buyer_status",
        )
    with col2:
        sector_filter = st.selectbox(
            "Filter by Sector",
            ["All"] + list(opportunities["Sector"].unique()),
            key="buyer_sector",
        )

    # Apply filters
    filtered = opportunities.copy()
    if status_filter == "Strong Candidates":
        filtered = filtered[
            filtered["Reallocation_Status"] == "STRONG REALLOCATION CANDIDATE"
        ]
    elif status_filter == "Moderate Candidates":
        filtered = filtered[
            filtered["Reallocation_Status"] == "MODERATE REALLOCATION CANDIDATE"
        ]
    if sector_filter != "All":
        filtered = filtered[filtered["Sector"] == sector_filter]

    # Display buyer cards
    for idx, row in filtered.head(10).iterrows():
        render_buyer_card(row, my_lender, cm)


def render_buyer_card(loan, my_lender, cm):
    """Render a card for buyer view - opportunity to acquire."""
    sme_id = loan["SME_ID"]

    # Check states
    is_listed = sme_id in st.session_state.listed_for_sale
    my_interests = st.session_state.interests.get(sme_id, [])
    has_expressed_interest = my_lender in my_interests
    my_bids = [
        b
        for b in st.session_state.bids.get(sme_id, [])
        if b.get("buyer_id") == my_lender
    ]
    has_bid = len(my_bids) > 0

    # Display values (seller identity COMPLETELY hidden)
    if ANONYMIZE:
        my_fit = round_score(loan["Best_Match_Fit"])
        outstanding = band_loan_amount(loan["Outstanding_Balance"])
        suggested_price = band_loan_amount(loan["Suggested_Price"])
        discount = f"{band_percentage(loan['Discount_Percent'])}%"
        roi = f"{band_percentage(loan['Annualized_ROI'])}%"
        region = group_region(loan["Region"])
    else:
        my_fit = f"{loan['Best_Match_Fit']:.0f}"
        outstanding = f"£{loan['Outstanding_Balance']:,.0f}"
        suggested_price = f"£{loan['Suggested_Price']:,.0f}"
        discount = f"{loan['Discount_Percent']:.1f}%"
        roi = f"{loan['Annualized_ROI']:.1f}%"
        region = loan["Region"]

    # Card header with your fit score
    fit_indicator = (
        "🟢"
        if loan["Best_Match_Fit"] >= 70
        else "🟡"
        if loan["Best_Match_Fit"] >= 50
        else "🔴"
    )
    expander_title = (
        f"{fit_indicator} {sme_id} | {loan['Sector']} | Your Fit: {my_fit}/100"
    )

    with st.expander(expander_title, expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**CURRENT HOLDER**")
            # Check if identity has been revealed
            reveal_info = st.session_state.reveals.get(sme_id, {})
            if reveal_info.get("seller_revealed") and reveal_info.get("buyer_revealed"):
                st.markdown(f"**Lender:** {loan['Current_Lender']}")
                st.success("🔓 Identity revealed!")
            else:
                st.markdown("🔒 *[Hidden until mutual consent]*")
                st.caption("Express interest to initiate matching")

            st.markdown(f"**Outstanding:** {outstanding}")
            st.markdown(f"**Remaining Term:** {loan['Years_Remaining']} years")

        with col2:
            st.markdown("**YOUR FIT**")
            st.markdown(f"**Fit Score:** {my_fit}/100")
            st.markdown(f"**Sector:** {loan['Sector']}")
            st.markdown(f"**Region:** {region}")

            # Show why it fits (from Best_Match_Reasons)
            reasons = loan.get("Best_Match_Reasons", {})
            if reasons and reasons.get("positive"):
                st.markdown("**Why it fits you:**")
                for r in reasons["positive"][:2]:
                    st.markdown(f"✓ {r}")

        # Pricing info (if details viewed)
        has_viewed_details = cm.has_viewed_item("view_details", sme_id)

        if has_viewed_details:
            st.markdown("---")
            st.markdown("**INDICATIVE PRICING**")
            pcol1, pcol2, pcol3 = st.columns(3)
            with pcol1:
                st.markdown(f"**Suggested Price:** {suggested_price}")
            with pcol2:
                st.markdown(f"**Discount:** {discount}")
            with pcol3:
                st.markdown(f"**Your ROI:** {roi}")
        else:
            st.markdown("---")
            cost = cm.get_cost("view_details")
            if cm.can_afford("view_details"):
                if st.button(
                    f"🔓 View Pricing Details ({cost} credit)",
                    key=f"viewdetails_{sme_id}",
                ):
                    cm.spend("view_details", sme_id)
                    st.rerun()
            else:
                st.caption(f"Need {cost} credit to view pricing details")

        st.markdown("---")

        # Actions
        col1, col2, col3 = st.columns(3)

        with col1:
            # Express interest
            if has_expressed_interest:
                st.markdown("✅ **Interest Expressed**")
            else:
                cost = cm.get_cost("express_interest")
                if cm.can_afford("express_interest"):
                    if st.button(
                        f"🤝 Express Interest ({cost} credits)",
                        key=f"interest_{sme_id}",
                    ):
                        cm.spend("express_interest", sme_id)
                        if sme_id not in st.session_state.interests:
                            st.session_state.interests[sme_id] = []
                        st.session_state.interests[sme_id].append(my_lender)
                        st.success("Interest expressed! Seller will be notified.")
                        st.rerun()
                else:
                    st.caption(f"Need {cost} credits")

        with col2:
            # Submit bid
            if has_expressed_interest:
                if has_bid:
                    bid_discount = my_bids[0]["discount"]
                    discount_display = (
                        f"{band_percentage(bid_discount)}%"
                        if ANONYMIZE
                        else f"{bid_discount:.1f}%"
                    )
                    st.markdown(f"💰 **Bid: {discount_display}**")
                else:
                    cost = cm.get_cost("submit_bid")
                    if cm.can_afford("submit_bid"):
                        # Simple bid input
                        bid_discount = st.slider(
                            "Discount %",
                            min_value=5,
                            max_value=30,
                            value=15,
                            step=5,
                            key=f"bid_slider_{sme_id}",
                        )
                        if st.button(
                            f"💰 Submit Bid ({cost} credits)", key=f"submitbid_{sme_id}"
                        ):
                            cm.spend("submit_bid", sme_id)
                            if sme_id not in st.session_state.bids:
                                st.session_state.bids[sme_id] = []
                            st.session_state.bids[sme_id].append(
                                {
                                    "buyer_id": my_lender,
                                    "discount": bid_discount,
                                    "timestamp": pd.Timestamp.now(),
                                }
                            )
                            st.success(f"Bid submitted at {bid_discount}% discount!")
                            st.rerun()
                    else:
                        st.caption(f"Need {cost} credits to bid")

        with col3:
            # Reveal counterparty
            if has_expressed_interest:
                reveal_info = st.session_state.reveals.get(sme_id, {})
                if reveal_info.get("seller_revealed") and reveal_info.get(
                    "buyer_revealed"
                ):
                    st.success("🔓 Matched!")
                elif reveal_info.get("seller_revealed"):
                    # Seller has revealed, buyer can now reveal
                    cost = cm.get_cost("reveal_counterparty")
                    if cm.can_afford("reveal_counterparty"):
                        if st.button(
                            f"🔓 Accept Match ({cost} credits)",
                            key=f"reveal_buyer_{sme_id}",
                        ):
                            cm.spend("reveal_counterparty", sme_id)
                            st.session_state.reveals[sme_id]["buyer_revealed"] = True
                            st.session_state.reveals[sme_id]["buyer_id"] = my_lender
                            st.success(
                                f"Match confirmed! Seller: {loan['Current_Lender']}"
                            )
                            st.rerun()
                    else:
                        st.caption(f"Need {cost} credits")
                else:
                    st.caption("Waiting for seller response...")

        # AI Explanation (if details viewed)
        if has_viewed_details:
            st.markdown("---")
            has_explanation = cm.has_viewed_item("generate_explanation", sme_id)

            if has_explanation:
                explainer = Explainer()
                current_lender = LENDERS.get(loan["Current_Lender"], {})
                recommended_lender = LENDERS.get(loan["Best_Match_Lender"], {})

                pricing_details = {
                    "loan_details": {
                        "outstanding_balance": loan["Outstanding_Balance"],
                        "years_remaining": loan["Years_Remaining"],
                    },
                    "pricing": {
                        "suggested_price": loan["Suggested_Price"],
                        "discount_from_face": loan["Discount_Percent"],
                    },
                    "buyer_metrics": {"annualized_roi": loan["Annualized_ROI"]},
                }

                company_data, curr_lender, rec_lender, scores, pricing = (
                    prepare_explanation_data(
                        loan,
                        current_lender,
                        recommended_lender,
                        pricing_details,
                        anonymize=ANONYMIZE,
                    )
                )

                explanation = explainer.generate_explanation(
                    company_data, curr_lender, rec_lender, scores, pricing
                )
                st.markdown("**🤖 AI Explanation:**")
                st.info(explanation)
            else:
                cost = cm.get_cost("generate_explanation")
                if cm.can_afford("generate_explanation"):
                    if st.button(
                        f"🤖 Generate AI Explanation ({cost} credits)",
                        key=f"explain_{sme_id}",
                    ):
                        cm.spend("generate_explanation", sme_id)
                        st.rerun()
                else:
                    st.caption(f"Need {cost} credits for AI explanation")

        # Propose Swap Instead section
        st.markdown("---")
        st.markdown("**🔄 OR: Propose a Swap Instead**")
        st.caption("Offer one of your loans in exchange instead of paying cash")

        # Get the current lender (buyer's) unaligned loans they could offer
        if "df_for_swap" not in st.session_state:
            st.session_state.df_for_swap = None

        with st.expander("🔄 Propose Swap Instead", expanded=False):
            # Show the buyer's unaligned loans they could offer
            st.markdown("**Select a loan from your portfolio to offer in exchange:**")

            # We need access to the full DataFrame - pass it through session state
            if hasattr(st.session_state, "current_df"):
                my_loans = st.session_state.current_df[
                    (st.session_state.current_df["Current_Lender"] == my_lender)
                    & (st.session_state.current_df["Is_Unalign"] == True)
                ]

                if len(my_loans) == 0:
                    st.info("You don't have any unaligned loans to offer in exchange.")
                else:
                    # Create options for loan selection
                    loan_options = {}
                    for _, my_loan in my_loans.iterrows():
                        my_loan_id = my_loan["SME_ID"]
                        my_loan_fit = (
                            round_score(my_loan["Current_Lender_Fit"])
                            if ANONYMIZE
                            else f"{my_loan['Current_Lender_Fit']:.0f}"
                        )
                        my_loan_band = (
                            band_loan_amount(my_loan["Outstanding_Balance"])
                            if ANONYMIZE
                            else f"£{my_loan['Outstanding_Balance']:,.0f}"
                        )
                        option_text = f"{my_loan_id} | {my_loan['Sector']} | {my_loan_band} | Fit: {my_loan_fit}"
                        loan_options[option_text] = my_loan_id

                    selected_option = st.selectbox(
                        "Your loan to offer:",
                        list(loan_options.keys()),
                        key=f"swap_offer_{sme_id}",
                    )

                    # Optional message
                    swap_message = st.text_area(
                        "Optional message (e.g., inclusion story):",
                        placeholder="This swap would help an underserved company in Scotland access appropriate financing...",
                        key=f"swap_message_{sme_id}",
                        max_chars=200,
                    )

                    # Submit swap proposal
                    cost = cm.get_cost("propose_swap")
                    if cm.can_afford("propose_swap"):
                        if st.button(
                            f"🔄 Send Swap Proposal ({cost} credits)",
                            key=f"send_swap_{sme_id}",
                        ):
                            cm.spend("propose_swap", sme_id)
                            # Create the swap proposal
                            proposal_id = st.session_state.swap_proposal_counter
                            st.session_state.swap_proposal_counter += 1
                            st.session_state.swap_proposals[proposal_id] = {
                                "proposer_lender": my_lender,
                                "proposer_loan_id": loan_options[selected_option],
                                "target_lender": loan["Current_Lender"],
                                "target_loan_id": sme_id,
                                "status": "pending",
                                "message": swap_message,
                                "created_at": pd.Timestamp.now(),
                            }
                            st.success(
                                f"Swap proposal sent! The seller will be notified."
                            )
                            st.rerun()
                    else:
                        st.caption(f"Need {cost} credits to propose swap")
            else:
                st.info("Loading loan data...")


def render_loan_swaps(df):
    """Render the Loan Swaps page with auto-swaps and manual proposals."""
    st.markdown('<p class="main-header">Loan Swaps</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Exchange loans directly with other lenders - no cash required</p>',
        unsafe_allow_html=True,
    )

    # Initialize states
    init_matching_state()
    init_swap_state()

    # Store DataFrame in session state
    st.session_state.current_df = df

    # Reset lender mapping for consistent anonymization
    if ANONYMIZE:
        reset_lender_mapping()

    # Get credit manager
    cm = get_credit_manager()

    # Lender selector (simulates login)
    st.markdown("### 🏦 Select Your Lender")
    lender_list = list(df["Current_Lender"].unique())
    selected_lender = st.selectbox(
        "This simulates being logged in as a lender",
        lender_list,
        key="swap_lender_select",
        help="In production, this would be determined by your login credentials",
    )

    st.markdown("---")

    # Two tabs: Auto Swaps and Manual Proposals
    auto_tab, manual_tab = st.tabs(["🤖 Auto Swaps", "💡 Manual Proposals"])

    with auto_tab:
        render_auto_swaps(df, selected_lender, cm)

    with manual_tab:
        render_manual_proposals(df, selected_lender, cm)


def render_auto_swaps(df, my_lender, cm):
    """Show system-generated complementary swap opportunities."""
    st.markdown("### System-Suggested Swaps")
    st.markdown(
        "These are complementary unalignes where both parties benefit from exchanging loans."
    )

    # Find complementary swaps
    matcher = SwapMatcher()
    all_swaps = matcher.find_complementary_swaps(df)

    # Filter to swaps involving this lender
    my_swaps = [
        s for s in all_swaps if s["lender_a"] == my_lender or s["lender_b"] == my_lender
    ]

    if len(my_swaps) == 0:
        st.info(
            "No complementary swap opportunities found for your portfolio at this time."
        )
        st.markdown("Try the Manual Proposals tab to initiate your own swap requests.")
        return

    # Show statistics
    stats = get_swap_statistics(my_swaps)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Available Swaps", stats["total_swaps"])
    with col2:
        st.metric("Inclusion Swaps", stats["inclusion_swaps"])
    with col3:
        st.metric("Avg Fit Improvement", f"+{stats['avg_fit_improvement']:.0f}")

    st.markdown("---")

    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        show_inclusion = st.checkbox(
            "Show only inclusion swaps", value=False, key="filter_inclusion"
        )
    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Swap Score", "Fit Improvement", "Inclusion Bonus"],
            key="sort_swaps",
        )

    # Apply filters and sorting
    filtered_swaps = my_swaps
    if show_inclusion:
        filtered_swaps = [s for s in filtered_swaps if s["is_inclusion_swap"]]

    if sort_by == "Swap Score":
        filtered_swaps = sorted(
            filtered_swaps, key=lambda x: x["swap_score"], reverse=True
        )
    elif sort_by == "Fit Improvement":
        filtered_swaps = sorted(
            filtered_swaps, key=lambda x: x["total_fit_improvement"], reverse=True
        )
    else:
        filtered_swaps = sorted(
            filtered_swaps, key=lambda x: x["inclusion_bonus"], reverse=True
        )

    # Display swap cards
    for swap in filtered_swaps[:10]:
        render_auto_swap_card(swap, my_lender, cm)


def render_auto_swap_card(swap, my_lender, cm):
    """Render a card for an auto-suggested swap opportunity."""
    # Get perspective-based summary
    summary = SwapMatcher().get_swap_summary(swap, my_lender)

    # Create swap identifier for tracking
    swap_id = f"{swap['loan_a_id']}_{swap['loan_b_id']}"
    is_accepted = swap_id in st.session_state.accepted_swaps

    # Header with score
    inclusion_badge = " 💚" if swap["is_inclusion_swap"] else ""
    header = (
        f"🔄 Combined Fit: +{swap['total_fit_improvement']} points{inclusion_badge}"
    )

    with st.expander(header, expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**YOUR LOAN OUT:**")
            you_give = summary["you_give"]
            if ANONYMIZE:
                st.markdown(f"**Loan:** {you_give['loan_id']}")
                st.markdown(f"**Sector:** {you_give['sector']}")
                st.markdown(f"**Outstanding:** {you_give['outstanding_band']}")
                st.markdown(f"**Your Fit:** {you_give['your_fit']}/100 (poor)")
                st.markdown(
                    f"**Their Fit:** {you_give['their_fit']}/100 (good for them)"
                )
            else:
                st.markdown(f"**Loan:** {you_give['loan_id']}")
                st.markdown(f"**Sector:** {you_give['sector']}")
                st.markdown(f"**Your Fit:** {you_give['your_fit']}/100")

        with col2:
            st.markdown("**THEIR LOAN IN:**")
            you_receive = summary["you_receive"]
            if ANONYMIZE:
                st.markdown(f"**Loan:** {you_receive['loan_id']}")
                st.markdown(f"**Sector:** {you_receive['sector']}")
                st.markdown(f"**Outstanding:** {you_receive['outstanding_band']}")
                st.markdown(f"**Your Fit:** {you_receive['your_fit']}/100 (excellent)")
                st.markdown(
                    f"**Their Fit:** {you_receive['their_fit']}/100 (poor for them)"
                )
            else:
                st.markdown(f"**Loan:** {you_receive['loan_id']}")
                st.markdown(f"**Sector:** {you_receive['sector']}")
                st.markdown(f"**Your Fit:** {you_receive['your_fit']}/100")

        # Why this works
        st.markdown("---")
        st.markdown("**WHY THIS WORKS:**")
        st.markdown(f"✓ Your {you_give['sector']} loan fits their portfolio better")
        st.markdown(f"✓ Their {you_receive['sector']} loan fits your portfolio better")
        if swap["is_inclusion_swap"]:
            st.markdown(
                "💚 This swap helps underserved companies access appropriate financing"
            )

        # Value adjustment notice
        if summary["needs_cash_adjustment"]:
            st.warning(
                f"📊 Value difference detected - small cash adjustment may be needed"
            )

        # Actions
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            # View details
            has_viewed = cm.has_viewed_item("view_swap_details", swap_id)
            if not has_viewed:
                cost = cm.get_cost("view_swap_details")
                if cm.can_afford("view_swap_details"):
                    if st.button(
                        f"🔍 View Details ({cost} credit)", key=f"view_swap_{swap_id}"
                    ):
                        cm.spend("view_swap_details", swap_id)
                        st.rerun()
                else:
                    st.caption(f"Need {cost} credit")
            else:
                st.markdown("✅ Details viewed")

        with col2:
            # Accept swap
            if is_accepted:
                st.success("✅ Accepted!")
            else:
                cost = cm.get_cost("accept_swap")
                if cm.can_afford("accept_swap"):
                    if st.button(
                        f"✅ Accept Swap ({cost} credits)", key=f"accept_{swap_id}"
                    ):
                        cm.spend("accept_swap", swap_id)
                        st.session_state.accepted_swaps.add(swap_id)
                        st.success("Swap accepted! Counterparty will be notified.")
                        st.rerun()
                else:
                    st.caption(f"Need {cost} credits")

        with col3:
            # Generate inclusion story
            has_story = cm.has_viewed_item("generate_swap_story", swap_id)
            if swap["is_inclusion_swap"]:
                if has_story:
                    st.markdown("💚 Story generated")
                else:
                    cost = cm.get_cost("generate_swap_story")
                    if cm.can_afford("generate_swap_story"):
                        if st.button(
                            f"💚 Inclusion Story ({cost})", key=f"story_{swap_id}"
                        ):
                            cm.spend("generate_swap_story", swap_id)
                            # Generate the story using Explainer
                            from agents.explainer import Explainer

                            explainer = Explainer()
                            story = explainer.generate_swap_inclusion_story(swap)
                            # Store in session state for display
                            st.session_state.generated_stories[swap_id] = story
                            st.rerun()

        # Display the generated story if it exists
        if swap_id in st.session_state.generated_stories:
            st.markdown("---")
            st.markdown("**💚 INCLUSION STORY:**")
            st.info(st.session_state.generated_stories[swap_id])


def render_manual_proposals(df, my_lender, cm):
    """Render manual swap proposal wizard and incoming proposals."""
    st.markdown("### Create Swap Proposal")
    st.markdown("Propose a loan swap to any lender - even for unlisted loans.")

    # Get my unaligned loans
    my_unaligned = df[
        (df["Current_Lender"] == my_lender) & (df["Is_Unalign"] == True)
    ].sort_values("Fit_Gap", ascending=False)

    if len(my_unaligned) == 0:
        st.success("All your loans are well-matched - no need to swap!")
    else:
        # Wizard interface
        draft = st.session_state.manual_proposal_draft

        # Step 1: Select your loan
        st.markdown("#### Step 1: Select Your Loan to Offer")
        loan_options = {}
        for _, loan in my_unaligned.iterrows():
            loan_id = loan["SME_ID"]
            fit = (
                round_score(loan["Current_Lender_Fit"])
                if ANONYMIZE
                else f"{loan['Current_Lender_Fit']:.0f}"
            )
            band = (
                band_loan_amount(loan["Outstanding_Balance"])
                if ANONYMIZE
                else f"£{loan['Outstanding_Balance']:,.0f}"
            )
            option_text = f"{loan_id} | {loan['Sector']} | {band} | Fit: {fit}"
            loan_options[option_text] = loan_id

        selected_my_loan = st.selectbox(
            "Your unaligned loan:", list(loan_options.keys()), key="wizard_my_loan"
        )
        my_loan_id = loan_options[selected_my_loan]
        my_loan_data = my_unaligned[my_unaligned["SME_ID"] == my_loan_id].iloc[0]

        # Step 2: Select target lender (anonymized)
        st.markdown("#### Step 2: Select Target Lender")
        # Show lenders ranked by fit for your loan
        other_lenders = [l for l in LENDERS.keys() if l != my_lender]

        # In anonymized mode, show as "Lender A", "Lender B", etc.
        if ANONYMIZE:
            lender_display = {
                f"Lender {chr(65 + i)}": l for i, l in enumerate(other_lenders)
            }
        else:
            lender_display = {l: l for l in other_lenders}

        selected_target_display = st.selectbox(
            "Target lender:", list(lender_display.keys()), key="wizard_target_lender"
        )
        target_lender = lender_display[selected_target_display]

        # Step 3: Browse their loans (costs credits)
        st.markdown("#### Step 3: Select Their Loan You Want")

        # Check if already browsed
        browse_key = f"{my_lender}_{target_lender}"
        has_browsed = cm.has_viewed_item("browse_unlisted_loans", browse_key)

        if has_browsed:
            # Show their loans that fit us
            their_loans = df[
                (df["Current_Lender"] == target_lender)
                & (df["Best_Match_Lender"] == my_lender)
            ].sort_values("Fit_Gap", ascending=False)

            if len(their_loans) == 0:
                st.info(
                    f"This lender doesn't have loans that fit your portfolio. Try another lender or choose 'Open Swap'."
                )
                their_loan_id = None
            else:
                their_options = {}
                for _, loan in their_loans.iterrows():
                    loan_id = loan["SME_ID"]
                    fit = (
                        round_score(loan["Best_Match_Fit"])
                        if ANONYMIZE
                        else f"{loan['Best_Match_Fit']:.0f}"
                    )
                    band = (
                        band_loan_amount(loan["Outstanding_Balance"])
                        if ANONYMIZE
                        else f"£{loan['Outstanding_Balance']:,.0f}"
                    )
                    option_text = (
                        f"{loan_id} | {loan['Sector']} | {band} | Your Fit: {fit}"
                    )
                    their_options[option_text] = loan_id

                # Add "Open Swap" option
                their_options["🎲 Open Swap - Let them choose"] = "OPEN"

                selected_their_loan = st.selectbox(
                    "Their loan you want:",
                    list(their_options.keys()),
                    key="wizard_their_loan",
                )
                their_loan_id = their_options[selected_their_loan]
        else:
            cost = cm.get_cost("browse_unlisted_loans")
            if cm.can_afford("browse_unlisted_loans"):
                if st.button(
                    f"🔓 Browse Their Loans ({cost} credits)", key="browse_loans"
                ):
                    cm.spend("browse_unlisted_loans", browse_key)
                    st.rerun()
            else:
                st.caption(f"Need {cost} credits to browse their loans")
            their_loan_id = None

        # Step 4: Send proposal
        if has_browsed:
            st.markdown("#### Step 4: Send Proposal")

            message = st.text_area(
                "Optional inclusion story or message:",
                placeholder="This swap helps an underserved Clean Energy company in Scotland access appropriate financing...",
                key="wizard_message",
                max_chars=300,
            )

            cost = cm.get_cost("propose_swap")
            if cm.can_afford("propose_swap"):
                if st.button(
                    f"🔄 Send Swap Proposal ({cost} credits)",
                    key="send_wizard_proposal",
                ):
                    cm.spend("propose_swap", f"{my_loan_id}_{target_lender}")
                    proposal_id = st.session_state.swap_proposal_counter
                    st.session_state.swap_proposal_counter += 1
                    st.session_state.swap_proposals[proposal_id] = {
                        "proposer_lender": my_lender,
                        "proposer_loan_id": my_loan_id,
                        "target_lender": target_lender,
                        "target_loan_id": their_loan_id,
                        "status": "pending",
                        "message": message,
                        "created_at": pd.Timestamp.now(),
                    }
                    st.success("Swap proposal sent successfully!")
                    st.rerun()
            else:
                st.caption(f"Need {cost} credits to send proposal")

    # Show incoming proposals
    st.markdown("---")
    st.markdown("### 📬 Incoming Swap Proposals")

    incoming = [
        p
        for pid, p in st.session_state.swap_proposals.items()
        if p["target_lender"] == my_lender and p["status"] == "pending"
    ]

    if len(incoming) == 0:
        st.info("No incoming swap proposals at this time.")
    else:
        st.info(f"You have **{len(incoming)}** incoming swap proposal(s)")

        for proposal in incoming:
            render_incoming_proposal(proposal, my_lender, cm, df)


def render_incoming_proposal(proposal, my_lender, cm, df):
    """Render an incoming swap proposal card."""
    proposer = proposal["proposer_lender"]
    proposer_display = (
        anonymize_lender(proposer, is_current=False) if ANONYMIZE else proposer
    )

    with st.expander(f"📩 Proposal from {proposer_display}", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**THEY OFFER:**")
            # Get proposer's loan details
            proposer_loan = df[df["SME_ID"] == proposal["proposer_loan_id"]]
            if len(proposer_loan) > 0:
                loan = proposer_loan.iloc[0]
                fit = (
                    round_score(loan["Best_Match_Fit"])
                    if ANONYMIZE
                    else f"{loan['Best_Match_Fit']:.0f}"
                )
                band = (
                    band_loan_amount(loan["Outstanding_Balance"])
                    if ANONYMIZE
                    else f"£{loan['Outstanding_Balance']:,.0f}"
                )
                st.markdown(f"**Loan:** {loan['SME_ID']}")
                st.markdown(f"**Sector:** {loan['Sector']}")
                st.markdown(f"**Outstanding:** {band}")
                st.markdown(f"**Your Fit:** {fit}/100")

        with col2:
            st.markdown("**THEY WANT:**")
            if proposal["target_loan_id"] == "OPEN":
                st.markdown("🎲 *Open Swap - You choose which loan*")
            else:
                target_loan = df[df["SME_ID"] == proposal["target_loan_id"]]
                if len(target_loan) > 0:
                    loan = target_loan.iloc[0]
                    fit = (
                        round_score(loan["Current_Lender_Fit"])
                        if ANONYMIZE
                        else f"{loan['Current_Lender_Fit']:.0f}"
                    )
                    band = (
                        band_loan_amount(loan["Outstanding_Balance"])
                        if ANONYMIZE
                        else f"£{loan['Outstanding_Balance']:,.0f}"
                    )
                    st.markdown(f"**Loan:** {loan['SME_ID']}")
                    st.markdown(f"**Sector:** {loan['Sector']}")
                    st.markdown(f"**Outstanding:** {band}")
                    st.markdown(f"**Your Fit:** {fit}/100")

        # Show message if any
        if proposal.get("message"):
            st.markdown("---")
            st.markdown("**Their message:**")
            st.info(proposal["message"])

        # Actions
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            cost = cm.get_cost("accept_swap")
            if cm.can_afford("accept_swap"):
                if st.button(
                    f"✅ Accept Swap ({cost} credits)",
                    key=f"accept_proposal_{proposal['proposer_loan_id']}",
                ):
                    cm.spend("accept_swap", proposal["proposer_loan_id"])
                    proposal["status"] = "accepted"
                    st.success("Swap accepted! Both parties will be notified.")
                    st.rerun()
            else:
                st.caption(f"Need {cost} credits")

        with col2:
            if st.button(
                "❌ Decline", key=f"decline_proposal_{proposal['proposer_loan_id']}"
            ):
                proposal["status"] = "declined"
                st.info("Proposal declined.")
                st.rerun()


def render_lender_view(df):
    """Render the Lender View page."""
    st.markdown('<p class="main-header">Lender View</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Portfolio analysis from each lender\'s perspective</p>',
        unsafe_allow_html=True,
    )

    # Reset lender mapping for this view
    if ANONYMIZE:
        reset_lender_mapping()

    # Lender selector - in anonymized mode, show "Your Portfolio" concept
    selected_lender = st.selectbox("Select Lender", list(LENDERS.keys()))

    lender_info = get_lender_for_display(selected_lender)
    lender_df = df[df["Current_Lender"] == selected_lender]

    # In Lender View, we show "Your Portfolio" for the selected lender
    if ANONYMIZE:
        display_name = "Your Portfolio"
        total_outstanding = band_portfolio_total(lender_df["Outstanding_Balance"].sum())
        avg_fit = round_score(lender_df["Current_Lender_Fit"].mean())
    else:
        display_name = selected_lender
        total_outstanding = f"£{lender_df['Outstanding_Balance'].sum() / 1e6:.1f}M"
        avg_fit = f"{lender_df['Current_Lender_Fit'].mean():.0f}"

    # Lender profile
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"### {display_name if ANONYMIZE else 'Lender Profile'}")
        st.markdown(f"**Description:** {lender_info['description']}")
        st.markdown(f"**Risk Appetite:** {lender_info['risk_appetite']}")
        st.markdown(f"**Preferred Sectors:** {lender_info['sectors']}")
        st.markdown(f"**Regional Focus:** {lender_info['regions']}")
        st.markdown(f"**Inclusion Mandate:** {lender_info['inclusion_focus']}")

    with col2:
        st.markdown("### Portfolio Summary")
        st.markdown(f"**Current Portfolio:** {len(lender_df)} companies")
        st.markdown(f"**Total Outstanding:** {total_outstanding}")
        st.markdown(f"**Avg Fit Score:** {avg_fit}/100")
        unaligned = len(lender_df[lender_df["Is_Unalign"] == True])
        unalign_pct = (
            band_percentage(unaligned / len(lender_df) * 100)
            if ANONYMIZE and len(lender_df) > 0
            else (round(unaligned / len(lender_df) * 100) if len(lender_df) > 0 else 0)
        )
        st.markdown(f"**Unaligned Loans:** {unaligned} ({unalign_pct}%)")

    st.markdown("---")

    # Inbound vs Outbound
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Outbound (Should Release)")
        outbound = lender_df[
            lender_df["Best_Match_Lender"] != selected_lender
        ].sort_values("Fit_Gap", ascending=False)
        st.markdown(f"{len(outbound)} loans don't fit this lender's profile")

        for idx, row in outbound.head(5).iterrows():
            if ANONYMIZE:
                # Anonymize the destination lender
                dest_lender = anonymize_lender_for_lender_view(
                    row["Best_Match_Lender"], selected_lender
                )
                fit_gap = round_score(row["Fit_Gap"])
            else:
                dest_lender = row["Best_Match_Lender"]
                fit_gap = f"{row['Fit_Gap']:.0f}"
            st.markdown(
                f"- {row['SME_ID']} ({row['Sector']}) → {dest_lender} (+{fit_gap} fit)"
            )

    with col2:
        st.markdown("### Inbound (Should Acquire)")
        inbound = df[
            (df["Best_Match_Lender"] == selected_lender)
            & (df["Current_Lender"] != selected_lender)
        ]
        st.markdown(f"{len(inbound)} loans from other lenders would fit better here")

        for idx, row in inbound.head(5).iterrows():
            if ANONYMIZE:
                # Anonymize the source lender
                source_lender = anonymize_lender_for_lender_view(
                    row["Current_Lender"], selected_lender
                )
            else:
                source_lender = row["Current_Lender"]
            st.markdown(f"- {row['SME_ID']} ({row['Sector']}) from {source_lender}")


def render_market_insights(df):
    """Render the Market Insights page."""
    st.markdown('<p class="main-header">Market Insights</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">System-wide intelligence and inclusion analysis</p>',
        unsafe_allow_html=True,
    )

    # Reset lender mapping
    if ANONYMIZE:
        reset_lender_mapping()

    # Get market stats with anonymization
    matcher = Matcher()
    market_summary = matcher.get_market_summary(df, anonymize=ANONYMIZE)

    scanner = InclusionScanner()
    inclusion_insights = scanner.get_market_insights(df, anonymize=ANONYMIZE)

    pricer = Pricer()
    pricing_stats = pricer.get_market_pricing_stats(df, anonymize=ANONYMIZE)

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Reallocation Candidates",
            f"{market_summary['unaligned_companies']['count']} ({market_summary['unaligned_companies']['percentage']}%)",
        )
    with col2:
        st.metric(
            "Total Reallocation Value",
            market_summary["reallocation_value"]["formatted"],
        )
    with col3:
        st.metric(
            "Avg Fit Improvement",
            f"+{market_summary['fit_scores']['average_improvement']} pts",
        )
    with col4:
        st.metric(
            "High Inclusion Priority",
            f"{inclusion_insights['high_potential_underserved']['count']} companies",
        )

    st.markdown("---")

    # Inclusion analysis
    st.subheader("Financial Inclusion Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Regional Distribution")
        st.markdown(
            f"**Underserved Regions:** {inclusion_insights['underserved_regions']['percentage']}% of companies"
        )
        # Show grouped regions if anonymizing
        regions_list = inclusion_insights["underserved_regions"]["regions"][:4]
        st.markdown(f"Regions: {', '.join(regions_list)}...")

    with col2:
        st.markdown("### Inclusion Priority")
        priority_dist = inclusion_insights["priority_distribution"]
        for category, count in priority_dist.items():
            pct = (
                band_percentage(count / len(df) * 100)
                if ANONYMIZE
                else round(count / len(df) * 100)
            )
            st.markdown(f"**{category}:** {count} ({pct}%)")

    # Key insight
    st.info(f"**Key Insight:** {inclusion_insights['key_insight']}")

    st.markdown("---")

    # Lender flow analysis
    st.subheader("Optimal Lender Flows")
    st.markdown(
        "If all recommendations were executed, this is how portfolios would change:"
    )

    flow_data = []
    for lender, stats in market_summary["lender_flows"].items():
        # Lender names are already anonymized in market_summary if ANONYMIZE=True
        flow_data.append(
            {
                "Lender": lender,
                "Current Portfolio": stats["current_portfolio"],
                "Optimal Portfolio": stats["optimal_portfolio"],
                "Net Flow": stats["net_flow"],
            }
        )

    flow_df = pd.DataFrame(flow_data)

    fig = go.Figure(
        data=[
            go.Bar(
                name="Current",
                x=flow_df["Lender"],
                y=flow_df["Current Portfolio"],
                marker_color="#1f77b4",
            ),
            go.Bar(
                name="Optimal",
                x=flow_df["Lender"],
                y=flow_df["Optimal Portfolio"],
                marker_color="#2ca02c",
            ),
        ]
    )
    fig.update_layout(barmode="group", xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    # Generate LLM insight
    explainer = Explainer()
    market_insight = explainer.generate_market_insight(market_summary)
    inclusion_insight = explainer.generate_inclusion_insight(inclusion_insights)

    st.markdown("### AI-Generated Insights")
    st.success(f"**Market Opportunity:** {market_insight}")
    st.info(f"**Inclusion Opportunity:** {inclusion_insight}")


def render_transaction_simulator(df):
    """Render the Transaction Simulator page."""
    st.markdown(
        '<p class="main-header">Transaction Simulator</p>', unsafe_allow_html=True
    )
    st.markdown(
        '<p class="sub-header">Simulate loan sales and swaps</p>',
        unsafe_allow_html=True,
    )

    # Reset lender mapping
    if ANONYMIZE:
        reset_lender_mapping()

    # Select a reallocation candidate
    candidates = df[df["Is_Unalign"] == True].sort_values("Fit_Gap", ascending=False)

    if len(candidates) == 0:
        st.warning("No reallocation candidates found.")
        return

    def format_candidate(x):
        row = candidates[candidates["SME_ID"] == x].iloc[0]
        gap = round_score(row["Fit_Gap"]) if ANONYMIZE else f"{row['Fit_Gap']:.0f}"
        return f"{x} | {row['Sector']} | Gap: +{gap}"

    selected_id = st.selectbox(
        "Select Reallocation Candidate",
        candidates["SME_ID"].tolist(),
        format_func=format_candidate,
    )

    company = candidates[candidates["SME_ID"] == selected_id].iloc[0]

    # Transaction type
    transaction_type = st.radio(
        "Transaction Type", ["Loan Sale", "Loan Swap", "Swap + Cash"], horizontal=True
    )

    st.markdown("---")

    # Apply anonymization
    if ANONYMIZE:
        current_fit_display = round_score(company["Current_Lender_Fit"])
        best_fit_display = round_score(company["Best_Match_Fit"])
        best_lender_display = anonymize_lender(
            company["Best_Match_Lender"], is_current=False
        )
        outstanding_display = format_amount_range(company["Outstanding_Balance"])
        risk_display = round_score(company["Risk_Score"])
        face_value_display = format_amount_range(company["Outstanding_Balance"])
        risk_adj_display = format_amount_range(company["Risk_Adjusted_Value"])
        price_display = format_amount_range(company["Suggested_Price"])
        discount_display = f"{band_percentage(company['Discount_Percent'])}%"
        gross_roi_display = f"{band_percentage(company['Gross_ROI'])}%"
        risk_adj_roi_display = f"{band_percentage(company['Risk_Adjusted_ROI'])}%"
        annual_roi_display = f"{band_percentage(company['Annualized_ROI'])}%"
    else:
        current_fit_display = f"{company['Current_Lender_Fit']:.0f}"
        best_fit_display = f"{company['Best_Match_Fit']:.0f}"
        best_lender_display = company["Best_Match_Lender"]
        outstanding_display = f"£{company['Outstanding_Balance']:,.0f}"
        risk_display = f"{company['Risk_Score']:.0f}"
        face_value_display = f"£{company['Outstanding_Balance']:,.0f}"
        risk_adj_display = f"£{company['Risk_Adjusted_Value']:,.0f}"
        price_display = f"£{company['Suggested_Price']:,.0f}"
        discount_display = f"{company['Discount_Percent']:.1f}%"
        gross_roi_display = f"{company['Gross_ROI']:.1f}%"
        risk_adj_roi_display = f"{company['Risk_Adjusted_ROI']:.1f}%"
        annual_roi_display = f"{company['Annualized_ROI']:.1f}%"

    # Transaction details
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### Seller")
        st.markdown(
            f"**Lender:** {company['Current_Lender']}"
        )  # Current lender visible
        st.markdown(f"**Current Fit:** {current_fit_display}/100")
        st.markdown(f"**Reason to Sell:** Portfolio unalign")

    with col2:
        st.markdown("### Buyer")
        st.markdown(f"**Lender:** {best_lender_display}")  # Anonymized
        st.markdown(f"**New Fit:** {best_fit_display}/100")
        st.markdown(f"**Reason to Buy:** Matches appetite")

    with col3:
        st.markdown("### Loan Details")
        st.markdown(f"**Outstanding:** {outstanding_display}")
        st.markdown(f"**Remaining Term:** {company['Years_Remaining']} years")
        st.markdown(f"**Risk Score:** {risk_display}/100")

    st.markdown("---")

    # Pricing
    st.subheader("Transaction Pricing")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Suggested Price")
        st.markdown(f"**Face Value:** {face_value_display}")
        st.markdown(f"**Risk-Adjusted Value:** {risk_adj_display}")
        st.markdown(f"**Suggested Price:** {price_display}")
        st.markdown(f"**Discount:** {discount_display}")

    with col2:
        st.markdown("### Buyer Returns")
        st.markdown(f"**Gross ROI:** {gross_roi_display}")
        st.markdown(f"**Risk-Adjusted ROI:** {risk_adj_roi_display}")
        st.markdown(f"**Annualized ROI:** {annual_roi_display}")

    # Explanation
    st.markdown("---")
    st.subheader("AI Explanation")

    explainer = Explainer()
    current_lender = LENDERS.get(company["Current_Lender"], {})
    recommended_lender = LENDERS.get(company["Best_Match_Lender"], {})

    # Build pricing dict for prepare_explanation_data
    pricing_details = {
        "loan_details": {
            "outstanding_balance": company["Outstanding_Balance"],
            "years_remaining": company["Years_Remaining"],
        },
        "pricing": {
            "suggested_price": company["Suggested_Price"],
            "discount_from_face": company["Discount_Percent"],
        },
        "buyer_metrics": {"annualized_roi": company["Annualized_ROI"]},
    }

    # Use prepare_explanation_data with anonymization
    company_data, curr_lender, rec_lender, scores, pricing = prepare_explanation_data(
        company,
        current_lender,
        recommended_lender,
        pricing_details,
        anonymize=ANONYMIZE,
    )

    explanation = explainer.generate_explanation(
        company_data, curr_lender, rec_lender, scores, pricing
    )

    st.info(explanation)

    # Execute button (simulated)
    if st.button("🚀 Initiate Transaction (Demo)", type="primary"):
        if ANONYMIZE:
            st.success(
                f"Transaction initiated! In a production system, this would notify both {company['Current_Lender']} and the matched lender to begin the transfer process."
            )
        else:
            st.success(
                f"Transaction initiated! In a production system, this would notify both {company['Current_Lender']} and {company['Best_Match_Lender']} to begin the transfer process."
            )
        st.balloons()


def main():
    """Main application entry point."""
    # Data path - update this to your actual path
    excel_path = r"c:\Users\user\gfa-loan-sandbox\data\UKFIN Hackathon_sample_file_data_GFA Exchange.xlsx"

    # Check if file exists
    if not Path(excel_path).exists():
        st.error(f"Data file not found at {excel_path}")
        st.info(
            "Please update the excel_path variable in app.py to point to your data file."
        )
        return

    # Load data
    with st.spinner("Loading and processing data..."):
        df = load_and_process_data(excel_path)

    # Render sidebar and get selected page
    page = render_sidebar()

    # Render selected page
    if page == "📊 Portfolio Overview":
        render_portfolio_overview(df)
    elif page == "🏢 Company Analysis":
        render_company_analysis(df)
    elif page == "💵 Loan Sales":
        render_loan_sales(df)
    elif page == "🔄 Loan Swaps":
        render_loan_swaps(df)
    elif page == "🏛️ Lender View":
        render_lender_view(df)
    elif page == "📈 Market Insights":
        render_market_insights(df)
    elif page == "💰 Transaction Simulator":
        render_transaction_simulator(df)


if __name__ == "__main__":
    main()
