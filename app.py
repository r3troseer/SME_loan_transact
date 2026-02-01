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
from lenders.profiles import LENDERS, get_lender_for_display
from utils.anonymizer import (
    anonymize_lender, group_region, round_score, band_turnover,
    band_loan_amount, band_percentage, band_portfolio_total,
    format_amount_range, reset_lender_mapping, anonymize_lender_for_lender_view
)
from utils.credit_system import CreditManager, CREDIT_PACKAGES

# Enable anonymization (set to True for demo/production)
ANONYMIZE = True

# Page config
st.set_page_config(
    page_title="GFA Exchange - Loan Reallocation Sandbox",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
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
""", unsafe_allow_html=True)


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
    if 'credit_manager' not in st.session_state:
        st.session_state.credit_manager = CreditManager(initial_credits=100)
    return st.session_state.credit_manager


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
    st.sidebar.caption(f"Spent: {summary['total_spent']} | Actions: {summary['total_transactions']}")

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
            "🔄 Swap Recommendations",
            "🏛️ Lender View",
            "📈 Market Insights",
            "💰 Transaction Simulator"
        ]
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
        | Action | Cost |
        |--------|------|
        | View Details | 1 credit |
        | AI Explanation | 2 credits |
        | Express Interest | 5 credits |
        | Reveal Identity | 10 credits |
        """)

    return page


def render_portfolio_overview(df):
    """Render the Portfolio Overview page."""
    st.markdown('<p class="main-header">Portfolio Overview</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Aggregated view of all SME companies in the dataset</p>', unsafe_allow_html=True)

    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)

    total_value = df['Outstanding_Balance'].sum()
    mismatched = len(df[df['Is_Mismatch'] == True])
    avg_risk = df['Risk_Score'].mean()

    with col1:
        st.metric("Total Companies", len(df))
    with col2:
        # Band the total loan value if anonymizing
        if ANONYMIZE:
            st.metric("Total Loan Value", band_portfolio_total(total_value))
        else:
            st.metric("Total Loan Value", f"£{total_value/1e6:.1f}M")
    with col3:
        mismatch_pct = band_percentage(mismatched/len(df)*100) if ANONYMIZE else round(mismatched/len(df)*100)
        st.metric("Mismatched Loans", f"{mismatched} ({mismatch_pct}%)")
    with col4:
        risk_display = round_score(avg_risk) if ANONYMIZE else round(avg_risk)
        st.metric("Avg Risk Score", f"{risk_display}/100")

    st.markdown("---")

    # Charts row
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Companies by Sector")
        sector_counts = df['Sector'].value_counts().reset_index()
        sector_counts.columns = ['Sector', 'Count']
        fig = px.bar(sector_counts, x='Sector', y='Count', color='Count',
                     color_continuous_scale='Blues')
        fig.update_layout(showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Companies by Region")
        # Group regions if anonymizing
        if ANONYMIZE:
            df_regions = df.copy()
            df_regions['Region_Grouped'] = df_regions['Region'].apply(group_region)
            region_counts = df_regions['Region_Grouped'].value_counts().reset_index()
            region_counts.columns = ['Region', 'Count']
        else:
            region_counts = df['Region'].value_counts().reset_index()
            region_counts.columns = ['Region', 'Count']
        fig = px.bar(region_counts, x='Region', y='Count', color='Count',
                     color_continuous_scale='Oranges')
        fig.update_layout(showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    # Score distributions
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Risk Score Distribution")
        fig = px.histogram(df, x='Risk_Score', nbins=20, color_discrete_sequence=['#1f77b4'])
        fig.update_layout(xaxis_title="Risk Score", yaxis_title="Count")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Inclusion Score Distribution")
        fig = px.histogram(df, x='Inclusion_Score', nbins=20, color_discrete_sequence=['#ff7f0e'])
        fig.update_layout(xaxis_title="Inclusion Score", yaxis_title="Count")
        st.plotly_chart(fig, use_container_width=True)

    # Lender distribution - anonymize lender names in overview
    st.subheader("Current Lender Distribution")
    lender_counts = df['Current_Lender'].value_counts().reset_index()
    lender_counts.columns = ['Lender', 'Count']
    if ANONYMIZE:
        reset_lender_mapping()  # Reset for consistent mapping
        lender_counts['Lender'] = lender_counts['Lender'].apply(
            lambda x: anonymize_lender(x, is_current=False)
        )
    fig = px.pie(lender_counts, values='Count', names='Lender',
                 color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig, use_container_width=True)


def render_company_analysis(df):
    """Render the Company Analysis page."""
    st.markdown('<p class="main-header">Company Analysis</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Deep dive into individual company profiles</p>', unsafe_allow_html=True)

    # Company selector
    company_options = df['SME_ID'].tolist()
    selected_company = st.selectbox("Select Company", company_options)

    company = df[df['SME_ID'] == selected_company].iloc[0]

    # Apply anonymization
    if ANONYMIZE:
        reset_lender_mapping()
        region_display = group_region(company['Region'])
        turnover_display = band_turnover(company['Turnover'])
        risk_display = round_score(company['Risk_Score'])
        inclusion_display = round_score(company['Inclusion_Score'])
        current_fit_display = round_score(company['Current_Lender_Fit'])
        best_fit_display = round_score(company['Best_Match_Fit'])
        fit_gap_display = round_score(company['Fit_Gap'])
        best_lender_display = anonymize_lender(company['Best_Match_Lender'], is_current=False)
    else:
        region_display = company['Region']
        turnover_display = f"£{company['Turnover']/1e6:.1f}M"
        risk_display = company['Risk_Score']
        inclusion_display = company['Inclusion_Score']
        current_fit_display = company['Current_Lender_Fit']
        best_fit_display = company['Best_Match_Fit']
        fit_gap_display = company['Fit_Gap']
        best_lender_display = company['Best_Match_Lender']

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
        risk_color = "fit-score-good" if risk_display >= 65 else "fit-score-moderate" if risk_display >= 45 else "fit-score-poor"
        st.markdown(f"**Risk Score:** <span class='{risk_color}'>{risk_display}/100</span>", unsafe_allow_html=True)
        st.markdown(f"**Category:** {company['Risk_Category']}")

    with col3:
        st.markdown("### Inclusion Profile")
        inc_color = "fit-score-good" if inclusion_display >= 60 else "fit-score-moderate"
        st.markdown(f"**Inclusion Score:** <span class='{inc_color}'>{inclusion_display}/100</span>", unsafe_allow_html=True)
        st.markdown(f"**Category:** {company['Inclusion_Category']}")

    st.markdown("---")

    # Fit analysis
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Current Lender Fit")
        # Current lender is always visible
        st.markdown(f"**Lender:** {company['Current_Lender']}")
        fit_color = "fit-score-good" if current_fit_display >= 65 else "fit-score-moderate" if current_fit_display >= 45 else "fit-score-poor"
        st.markdown(f"**Fit Score:** <span class='{fit_color}'>{current_fit_display}/100</span>", unsafe_allow_html=True)

        # Reasons
        if company['Current_Fit_Reasons']:
            if company['Current_Fit_Reasons'].get('positive'):
                st.markdown("**Positive factors:**")
                for r in company['Current_Fit_Reasons']['positive']:
                    st.markdown(f"✓ {r}")
            if company['Current_Fit_Reasons'].get('negative'):
                st.markdown("**Mismatch factors:**")
                for r in company['Current_Fit_Reasons']['negative']:
                    st.markdown(f"✗ {r}")

    with col2:
        st.markdown("### Best Match Lender")
        # Best match lender is anonymized
        st.markdown(f"**Lender:** {best_lender_display}")
        st.markdown(f"**Fit Score:** <span class='fit-score-good'>{best_fit_display}/100</span>", unsafe_allow_html=True)
        st.markdown(f"**Improvement:** +{fit_gap_display} points")
        st.markdown(f"**Status:** {company['Reallocation_Status']}")

    # Financial metrics radar chart
    st.markdown("---")
    st.subheader("Financial Health Breakdown")

    categories = ['Liquidity', 'Profitability', 'Leverage', 'Cash Position', 'Efficiency', 'Stability']
    values = [
        company.get('Liquidity_Score', 50),
        company.get('Profitability_Score', 50),
        company.get('Leverage_Score', 50),
        company.get('Cash_Score', 50),
        company.get('Efficiency_Score', 50),
        company.get('Size_Score', 50)
    ]

    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        line_color='#1f77b4'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)


def render_swap_recommendations(df):
    """Render the Swap Recommendations page."""
    st.markdown('<p class="main-header">Swap Recommendations</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Loans that would benefit from reallocation</p>', unsafe_allow_html=True)

    # Reset lender mapping for consistent anonymization
    if ANONYMIZE:
        reset_lender_mapping()

    # Get credit manager
    cm = get_credit_manager()

    # Perspective selector (Seller vs Buyer view)
    st.markdown("### 🎯 View Perspective")
    perspective = st.radio(
        "How do you want to view recommendations?",
        ["📋 Market Overview", "📤 Seller View (Loans to Exit)", "📥 Buyer View (Loans to Acquire)"],
        horizontal=True,
        help="Market Overview shows all mismatched loans. Seller View shows loans you should sell. Buyer View shows loans you could acquire."
    )

    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All Candidates", "Strong Only", "Moderate Only"])
    with col2:
        sector_filter = st.selectbox("Filter by Sector", ["All"] + list(df['Sector'].unique()))
    with col3:
        # Lender selector - only show if not Market Overview
        if perspective != "📋 Market Overview":
            lender_list = list(df['Current_Lender'].unique())
            selected_lender = st.selectbox("Select Your Lender", lender_list)
        else:
            selected_lender = None

    # Apply filters
    filtered_df = df[df['Is_Mismatch'] == True].copy()

    if status_filter == "Strong Only":
        filtered_df = filtered_df[filtered_df['Reallocation_Status'] == 'STRONG REALLOCATION CANDIDATE']
    elif status_filter == "Moderate Only":
        filtered_df = filtered_df[filtered_df['Reallocation_Status'] == 'MODERATE REALLOCATION CANDIDATE']

    if sector_filter != "All":
        filtered_df = filtered_df[filtered_df['Sector'] == sector_filter]

    # Apply perspective-based lender filtering
    if perspective == "📤 Seller View (Loans to Exit)" and selected_lender:
        # Show loans this lender currently holds that are mismatched
        filtered_df = filtered_df[filtered_df['Current_Lender'] == selected_lender]
        st.info(f"📤 **Seller View:** Showing {len(filtered_df)} mismatched loans that {selected_lender} could sell or swap to better-suited lenders.")

    elif perspective == "📥 Buyer View (Loans to Acquire)" and selected_lender:
        # Show loans from OTHER lenders where this lender is the best match
        filtered_df = filtered_df[
            (filtered_df['Best_Match_Lender'] == selected_lender) &
            (filtered_df['Current_Lender'] != selected_lender)
        ]
        st.info(f"📥 **Buyer View:** Showing {len(filtered_df)} acquisition opportunities - loans from other lenders that would be a good fit for {selected_lender}.")

    # Sort by fit gap
    filtered_df = filtered_df.sort_values('Fit_Gap', ascending=False)

    st.markdown(f"**{len(filtered_df)} recommendations found**")
    st.markdown("---")

    # Display recommendations
    for idx, row in filtered_df.head(10).iterrows():
        fit_gap_display = round_score(row['Fit_Gap']) if ANONYMIZE else row['Fit_Gap']
        sme_id = row['SME_ID']

        # Check if user has already paid to view this item
        already_viewed = cm.has_viewed_item('view_details', sme_id)

        with st.expander(f"🔄 {sme_id} | {row['Sector']} | Fit Improvement: +{fit_gap_display}"):
            # Show basic info always (free)
            st.markdown(f"**Sector:** {row['Sector']} | **Region:** {group_region(row['Region']) if ANONYMIZE else row['Region']}")

            # Gate detailed view behind credits
            if already_viewed or not ANONYMIZE:
                show_details = True
            else:
                cost = cm.get_cost('view_details')
                if cm.can_afford('view_details'):
                    if st.button(f"🔓 View Details ({cost} credit)", key=f"view_{sme_id}"):
                        cm.spend('view_details', sme_id)
                        st.rerun()
                    show_details = False
                else:
                    st.warning(f"⚠️ Insufficient credits. Need {cost} credit to view details.")
                    show_details = False

            if show_details or already_viewed:
                col1, col2, col3 = st.columns(3)

                # Apply anonymization
                if ANONYMIZE:
                    current_fit_display = round_score(row['Current_Lender_Fit'])
                    best_fit_display = round_score(row['Best_Match_Fit'])
                    best_lender_display = anonymize_lender(row['Best_Match_Lender'], is_current=False)
                    outstanding_display = band_loan_amount(row['Outstanding_Balance'])
                    price_display = band_loan_amount(row['Suggested_Price'])
                    discount_display = f"{band_percentage(row['Discount_Percent'])}%"
                    roi_display = f"{band_percentage(row['Annualized_ROI'])}%"
                else:
                    current_fit_display = f"{row['Current_Lender_Fit']:.0f}"
                    best_fit_display = f"{row['Best_Match_Fit']:.0f}"
                    best_lender_display = row['Best_Match_Lender']
                    outstanding_display = f"£{row['Outstanding_Balance']:,.0f}"
                    price_display = f"£{row['Suggested_Price']:,.0f}"
                    discount_display = f"{row['Discount_Percent']:.1f}%"
                    roi_display = f"{row['Annualized_ROI']:.1f}%"

                with col1:
                    st.markdown("**Current Situation**")
                    st.markdown(f"Lender: {row['Current_Lender']}")  # Current lender visible
                    st.markdown(f"Fit Score: {current_fit_display}/100")

                with col2:
                    st.markdown("**Recommended**")
                    st.markdown(f"Lender: {best_lender_display}")  # Anonymized
                    st.markdown(f"Fit Score: {best_fit_display}/100")

                with col3:
                    st.markdown("**Transaction**")
                    st.markdown(f"Outstanding: {outstanding_display}")
                    st.markdown(f"Suggested Price: {price_display}")
                    st.markdown(f"Discount: {discount_display}")
                    st.markdown(f"Buyer ROI: {roi_display}")

                # AI Explanation - gated behind additional credits
                st.markdown("---")
                explanation_key = f"explanation_{sme_id}"
                has_explanation = cm.has_viewed_item('generate_explanation', sme_id)

                if has_explanation or not ANONYMIZE:
                    # Generate explanation with anonymized data
                    explainer = Explainer()
                    current_lender = LENDERS.get(row['Current_Lender'], {})
                    recommended_lender = LENDERS.get(row['Best_Match_Lender'], {})

                    pricing_details = {
                        'loan_details': {'outstanding_balance': row['Outstanding_Balance'], 'years_remaining': row['Years_Remaining']},
                        'pricing': {'suggested_price': row['Suggested_Price'], 'discount_from_face': row['Discount_Percent']},
                        'buyer_metrics': {'annualized_roi': row['Annualized_ROI']}
                    }

                    company_data, curr_lender, rec_lender, scores, pricing = prepare_explanation_data(
                        row, current_lender, recommended_lender, pricing_details, anonymize=ANONYMIZE
                    )

                    explanation = explainer.generate_explanation(
                        company_data, curr_lender, rec_lender, scores, pricing
                    )
                    st.markdown("**🤖 AI Explanation:**")
                    st.info(explanation)
                else:
                    cost = cm.get_cost('generate_explanation')
                    if cm.can_afford('generate_explanation'):
                        if st.button(f"🤖 Generate AI Explanation ({cost} credits)", key=explanation_key):
                            cm.spend('generate_explanation', sme_id)
                            st.rerun()
                    else:
                        st.warning(f"⚠️ Need {cost} credits to generate AI explanation.")

                # Express Interest button
                st.markdown("---")
                interest_key = f"interest_{sme_id}"
                has_expressed = cm.has_viewed_item('express_interest', sme_id)

                if has_expressed:
                    st.success("✅ Interest expressed! You will be notified when counterparty responds.")
                else:
                    cost = cm.get_cost('express_interest')
                    if cm.can_afford('express_interest'):
                        if st.button(f"🤝 Express Interest ({cost} credits)", key=interest_key):
                            cm.spend('express_interest', sme_id)
                            st.rerun()
                    else:
                        st.caption(f"💡 Express interest requires {cost} credits")


def render_lender_view(df):
    """Render the Lender View page."""
    st.markdown('<p class="main-header">Lender View</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Portfolio analysis from each lender\'s perspective</p>', unsafe_allow_html=True)

    # Reset lender mapping for this view
    if ANONYMIZE:
        reset_lender_mapping()

    # Lender selector - in anonymized mode, show "Your Portfolio" concept
    selected_lender = st.selectbox("Select Lender", list(LENDERS.keys()))

    lender_info = get_lender_for_display(selected_lender)
    lender_df = df[df['Current_Lender'] == selected_lender]

    # In Lender View, we show "Your Portfolio" for the selected lender
    if ANONYMIZE:
        display_name = "Your Portfolio"
        total_outstanding = band_portfolio_total(lender_df['Outstanding_Balance'].sum())
        avg_fit = round_score(lender_df['Current_Lender_Fit'].mean())
    else:
        display_name = selected_lender
        total_outstanding = f"£{lender_df['Outstanding_Balance'].sum()/1e6:.1f}M"
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
        mismatched = len(lender_df[lender_df['Is_Mismatch'] == True])
        mismatch_pct = band_percentage(mismatched/len(lender_df)*100) if ANONYMIZE and len(lender_df) > 0 else (round(mismatched/len(lender_df)*100) if len(lender_df) > 0 else 0)
        st.markdown(f"**Mismatched Loans:** {mismatched} ({mismatch_pct}%)")

    st.markdown("---")

    # Inbound vs Outbound
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Outbound (Should Release)")
        outbound = lender_df[lender_df['Best_Match_Lender'] != selected_lender].sort_values('Fit_Gap', ascending=False)
        st.markdown(f"{len(outbound)} loans don't fit this lender's profile")

        for idx, row in outbound.head(5).iterrows():
            if ANONYMIZE:
                # Anonymize the destination lender
                dest_lender = anonymize_lender_for_lender_view(row['Best_Match_Lender'], selected_lender)
                fit_gap = round_score(row['Fit_Gap'])
            else:
                dest_lender = row['Best_Match_Lender']
                fit_gap = f"{row['Fit_Gap']:.0f}"
            st.markdown(f"- {row['SME_ID']} ({row['Sector']}) → {dest_lender} (+{fit_gap} fit)")

    with col2:
        st.markdown("### Inbound (Should Acquire)")
        inbound = df[(df['Best_Match_Lender'] == selected_lender) & (df['Current_Lender'] != selected_lender)]
        st.markdown(f"{len(inbound)} loans from other lenders would fit better here")

        for idx, row in inbound.head(5).iterrows():
            if ANONYMIZE:
                # Anonymize the source lender
                source_lender = anonymize_lender_for_lender_view(row['Current_Lender'], selected_lender)
            else:
                source_lender = row['Current_Lender']
            st.markdown(f"- {row['SME_ID']} ({row['Sector']}) from {source_lender}")


def render_market_insights(df):
    """Render the Market Insights page."""
    st.markdown('<p class="main-header">Market Insights</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">System-wide intelligence and inclusion analysis</p>', unsafe_allow_html=True)

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
            f"{market_summary['mismatched_companies']['count']} ({market_summary['mismatched_companies']['percentage']}%)"
        )
    with col2:
        st.metric(
            "Total Reallocation Value",
            market_summary['reallocation_value']['formatted']
        )
    with col3:
        st.metric(
            "Avg Fit Improvement",
            f"+{market_summary['fit_scores']['average_improvement']} pts"
        )
    with col4:
        st.metric(
            "High Inclusion Priority",
            f"{inclusion_insights['high_potential_underserved']['count']} companies"
        )

    st.markdown("---")

    # Inclusion analysis
    st.subheader("Financial Inclusion Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Regional Distribution")
        st.markdown(f"**Underserved Regions:** {inclusion_insights['underserved_regions']['percentage']}% of companies")
        # Show grouped regions if anonymizing
        regions_list = inclusion_insights['underserved_regions']['regions'][:4]
        st.markdown(f"Regions: {', '.join(regions_list)}...")

    with col2:
        st.markdown("### Inclusion Priority")
        priority_dist = inclusion_insights['priority_distribution']
        for category, count in priority_dist.items():
            pct = band_percentage(count / len(df) * 100) if ANONYMIZE else round(count / len(df) * 100)
            st.markdown(f"**{category}:** {count} ({pct}%)")

    # Key insight
    st.info(f"**Key Insight:** {inclusion_insights['key_insight']}")

    st.markdown("---")

    # Lender flow analysis
    st.subheader("Optimal Lender Flows")
    st.markdown("If all recommendations were executed, this is how portfolios would change:")

    flow_data = []
    for lender, stats in market_summary['lender_flows'].items():
        # Lender names are already anonymized in market_summary if ANONYMIZE=True
        flow_data.append({
            'Lender': lender,
            'Current Portfolio': stats['current_portfolio'],
            'Optimal Portfolio': stats['optimal_portfolio'],
            'Net Flow': stats['net_flow']
        })

    flow_df = pd.DataFrame(flow_data)

    fig = go.Figure(data=[
        go.Bar(name='Current', x=flow_df['Lender'], y=flow_df['Current Portfolio'], marker_color='#1f77b4'),
        go.Bar(name='Optimal', x=flow_df['Lender'], y=flow_df['Optimal Portfolio'], marker_color='#2ca02c')
    ])
    fig.update_layout(barmode='group', xaxis_tickangle=-45)
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
    st.markdown('<p class="main-header">Transaction Simulator</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Simulate loan sales and swaps</p>', unsafe_allow_html=True)

    # Reset lender mapping
    if ANONYMIZE:
        reset_lender_mapping()

    # Select a reallocation candidate
    candidates = df[df['Is_Mismatch'] == True].sort_values('Fit_Gap', ascending=False)

    if len(candidates) == 0:
        st.warning("No reallocation candidates found.")
        return

    def format_candidate(x):
        row = candidates[candidates['SME_ID']==x].iloc[0]
        gap = round_score(row['Fit_Gap']) if ANONYMIZE else f"{row['Fit_Gap']:.0f}"
        return f"{x} | {row['Sector']} | Gap: +{gap}"

    selected_id = st.selectbox(
        "Select Reallocation Candidate",
        candidates['SME_ID'].tolist(),
        format_func=format_candidate
    )

    company = candidates[candidates['SME_ID'] == selected_id].iloc[0]

    # Transaction type
    transaction_type = st.radio(
        "Transaction Type",
        ["Loan Sale", "Loan Swap", "Swap + Cash"],
        horizontal=True
    )

    st.markdown("---")

    # Apply anonymization
    if ANONYMIZE:
        current_fit_display = round_score(company['Current_Lender_Fit'])
        best_fit_display = round_score(company['Best_Match_Fit'])
        best_lender_display = anonymize_lender(company['Best_Match_Lender'], is_current=False)
        outstanding_display = format_amount_range(company['Outstanding_Balance'])
        risk_display = round_score(company['Risk_Score'])
        face_value_display = format_amount_range(company['Outstanding_Balance'])
        risk_adj_display = format_amount_range(company['Risk_Adjusted_Value'])
        price_display = format_amount_range(company['Suggested_Price'])
        discount_display = f"{band_percentage(company['Discount_Percent'])}%"
        gross_roi_display = f"{band_percentage(company['Gross_ROI'])}%"
        risk_adj_roi_display = f"{band_percentage(company['Risk_Adjusted_ROI'])}%"
        annual_roi_display = f"{band_percentage(company['Annualized_ROI'])}%"
    else:
        current_fit_display = f"{company['Current_Lender_Fit']:.0f}"
        best_fit_display = f"{company['Best_Match_Fit']:.0f}"
        best_lender_display = company['Best_Match_Lender']
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
        st.markdown(f"**Lender:** {company['Current_Lender']}")  # Current lender visible
        st.markdown(f"**Current Fit:** {current_fit_display}/100")
        st.markdown(f"**Reason to Sell:** Portfolio mismatch")

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
    current_lender = LENDERS.get(company['Current_Lender'], {})
    recommended_lender = LENDERS.get(company['Best_Match_Lender'], {})

    # Build pricing dict for prepare_explanation_data
    pricing_details = {
        'loan_details': {'outstanding_balance': company['Outstanding_Balance'], 'years_remaining': company['Years_Remaining']},
        'pricing': {'suggested_price': company['Suggested_Price'], 'discount_from_face': company['Discount_Percent']},
        'buyer_metrics': {'annualized_roi': company['Annualized_ROI']}
    }

    # Use prepare_explanation_data with anonymization
    company_data, curr_lender, rec_lender, scores, pricing = prepare_explanation_data(
        company, current_lender, recommended_lender, pricing_details, anonymize=ANONYMIZE
    )

    explanation = explainer.generate_explanation(
        company_data, curr_lender, rec_lender, scores, pricing
    )

    st.info(explanation)

    # Execute button (simulated)
    if st.button("🚀 Initiate Transaction (Demo)", type="primary"):
        if ANONYMIZE:
            st.success(f"Transaction initiated! In a production system, this would notify both {company['Current_Lender']} and the matched lender to begin the transfer process.")
        else:
            st.success(f"Transaction initiated! In a production system, this would notify both {company['Current_Lender']} and {company['Best_Match_Lender']} to begin the transfer process.")
        st.balloons()


def main():
    """Main application entry point."""
    # Data path - update this to your actual path
    excel_path = r"c:\Users\user\gfa-loan-sandbox\data\UKFIN Hackathon_sample_file_data_GFA Exchange.xlsx"

    # Check if file exists
    if not Path(excel_path).exists():
        st.error(f"Data file not found at {excel_path}")
        st.info("Please update the excel_path variable in app.py to point to your data file.")
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
    elif page == "🔄 Swap Recommendations":
        render_swap_recommendations(df)
    elif page == "🏛️ Lender View":
        render_lender_view(df)
    elif page == "📈 Market Insights":
        render_market_insights(df)
    elif page == "💰 Transaction Simulator":
        render_transaction_simulator(df)


if __name__ == "__main__":
    main()
