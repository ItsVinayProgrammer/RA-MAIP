import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from data_engine import get_mf_performance, select_scheme_by_risk
from part3_portfolio.portfolio_intelligence import get_intelligent_allocation
from part3_portfolio.efficient_frontier import compute_portfolio_metrics, project_wealth
from part3_portfolio.sebi_compliance import (
    run_compliance_check,
    get_instrument_recommendations,
    get_indian_tax_optimized_split,
)

st.set_page_config(
    page_title="RA-MAIP | Investment Planner",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ══════════════════════════════════════════
   FORCE LIGHT MAIN AREA
══════════════════════════════════════════ */
html, body { background: #F0F4F8 !important; }
.stApp,
[data-testid="stAppViewContainer"],
.main, .main > div, section.main,
[data-testid="stAppViewContainer"] > section:nth-child(2) {
    background: #F0F4F8 !important;
}
.block-container {
    background: #F0F4F8 !important;
    padding: 0rem 2.5rem 3rem 2.5rem !important;
    max-width: 1300px !important;
}

/* ══════════════════════════════════════════
   SIDEBAR — full dark, all text visible
══════════════════════════════════════════ */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div,
[data-testid="stSidebar"] > div > div,
[data-testid="stSidebar"] section {
    background: #0B2545 !important;
}

/* Every text element in sidebar — white */
[data-testid="stSidebar"] *:not(button):not(.stButton > button) {
    color: #E2E8F0 !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] strong,
[data-testid="stSidebar"] .sidebar-title {
    color: #FFFFFF !important;
    font-size: 1rem !important;
}
/* Section subheadings like "Personal Details" */
[data-testid="stSidebar"] p {
    color: #CBD5E1 !important;
    font-weight: 600;
    font-size: 0.85rem;
}
/* Input labels */
[data-testid="stSidebar"] label {
    color: #94A3B8 !important;
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.7px !important;
}
/* Slider value numbers */
[data-testid="stSidebar"] [data-testid="stTickBarMin"],
[data-testid="stSidebar"] [data-testid="stTickBarMax"],
[data-testid="stSidebar"] .stSlider span,
[data-testid="stSidebar"] [data-testid="stThumbValue"] {
    color: #93C5FD !important;
    font-weight: 700 !important;
}
/* Number input text */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] input[type="number"] {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    background: #162D4E !important;
    border: 1.5px solid #2D4A6E !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    caret-color: #FFFFFF !important;
}
/* Input wrapper */
[data-testid="stSidebar"] [data-baseweb="base-input"],
[data-testid="stSidebar"] [data-baseweb="input"],
[data-testid="stSidebar"] .stNumberInput > div > div {
    background: #162D4E !important;
    border: 1.5px solid #2D4A6E !important;
    border-radius: 8px !important;
}
/* +/- buttons */
[data-testid="stSidebar"] button {
    background: #162D4E !important;
    color: #FFFFFF !important;
    border: 1px solid #2D4A6E !important;
    border-radius: 6px !important;
}
/* Selectbox */
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #162D4E !important;
    border: 1.5px solid #2D4A6E !important;
    border-radius: 8px !important;
    color: #FFFFFF !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] span,
[data-testid="stSidebar"] [data-baseweb="select"] div,
[data-testid="stSidebar"] [data-baseweb="select"] svg {
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
}
/* Divider */
[data-testid="stSidebar"] hr {
    border-color: #1E3A5F !important;
    margin: 0.9rem 0 !important;
}
/* GENERATE BUTTON — glowing blue CTA */
[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.4px !important;
    padding: 0.8rem 1rem !important;
    width: 100% !important;
    box-shadow: 0 4px 18px rgba(37,99,235,0.5) !important;
    margin-top: 0.5rem !important;
    cursor: pointer !important;
    -webkit-text-fill-color: #FFFFFF !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%) !important;
    box-shadow: 0 6px 24px rgba(37,99,235,0.65) !important;
}

/* ══════════════════════════════════════════
   MAIN CONTENT — all text dark
══════════════════════════════════════════ */
.main p, .main li { color: #334155 !important; }
.main h1, .main h2, .main h3, .main h4 { color: #0F172A !important; }

/* ══════════════════════════════════════════
   PAGE HEADER
══════════════════════════════════════════ */
.ra-header {
    background: linear-gradient(135deg, #0B2545 0%, #1e3a6e 55%, #1D4ED8 100%);
    border-radius: 16px;
    padding: 36px 44px 32px 44px;
    margin: 1.5rem 0 28px 0;
    box-shadow: 0 4px 24px rgba(11,37,69,0.2);
}
.ra-tag {
    font-size: 0.68rem; font-weight: 800; letter-spacing: 2.5px;
    text-transform: uppercase; color: #60A5FA !important;
    margin-bottom: 10px; display: block;
}
.ra-title {
    color: #FFFFFF !important; font-size: 2rem; font-weight: 800;
    letter-spacing: -0.5px; margin: 0 0 10px 0; line-height: 1.1;
}
.ra-sub { color: #93C5FD !important; font-size: 0.84rem; letter-spacing: 0.5px; }

/* ══════════════════════════════════════════
   KPI CARDS
══════════════════════════════════════════ */
.kpi {
    background: #FFFFFF; border-radius: 14px; padding: 22px 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.05);
    border-top: 3.5px solid #3B82F6;
}
.kpi.g { border-top-color: #10B981; }
.kpi.a { border-top-color: #F59E0B; }
.kpi.r { border-top-color: #EF4444; }
.kpi-lbl {
    font-size: 0.67rem !important; font-weight: 800 !important;
    color: #64748B !important; text-transform: uppercase;
    letter-spacing: 0.9px; margin-bottom: 10px; display: block;
}
.kpi-val {
    font-size: 1.7rem !important; font-weight: 800 !important;
    color: #0F172A !important; line-height: 1; display: block;
}
.kpi-val.gn { color: #059669 !important; }
.kpi-val.am { color: #D97706 !important; }
.kpi-val.rd { color: #DC2626 !important; }
.kpi-sub {
    font-size: 0.7rem !important; color: #94A3B8 !important;
    margin-top: 6px; display: block; line-height: 1.4;
}

/* ══════════════════════════════════════════
   SECTION TITLES
══════════════════════════════════════════ */
.stitle {
    font-size: 0.68rem !important; font-weight: 800 !important;
    color: #94A3B8 !important; text-transform: uppercase; letter-spacing: 1.4px;
    padding-bottom: 10px; border-bottom: 1.5px solid #E2E8F0;
    margin: 36px 0 20px 0; display: block;
}

/* ══════════════════════════════════════════
   WHITE CARDS
══════════════════════════════════════════ */
.white-card {
    background: white; border-radius: 14px; padding: 24px 28px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.05);
}
.pcard {
    background: white; border-radius: 14px; padding: 20px 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.05);
    height: 100%;
}
.pcard-t {
    font-size: 0.72rem !important; font-weight: 800 !important;
    color: #475569 !important; text-transform: uppercase; letter-spacing: 1px;
    margin-bottom: 14px; display: block;
    border-bottom: 1px solid #F1F5F9; padding-bottom: 10px;
}
.prow {
    display: flex; justify-content: space-between; align-items: center;
    padding: 7px 0; border-bottom: 1px solid #F8FAFC;
}
.prow:last-child { border: none; }
.pl { font-size: 0.82rem !important; color: #64748B !important; }
.pv { font-size: 0.82rem !important; font-weight: 700 !important; color: #0F172A !important; }

/* Risk bar */
.risk-bar {
    height: 10px; border-radius: 5px;
    background: linear-gradient(to right, #10B981, #F59E0B, #EF4444);
    margin: 14px 0 5px 0;
}
.risk-bar-lbl {
    display: flex; justify-content: space-between;
    font-size: 0.72rem; color: #94A3B8 !important;
}

/* ══════════════════════════════════════════
   BADGES
══════════════════════════════════════════ */
.bdg {
    display: inline-block; padding: 5px 12px; border-radius: 6px;
    font-size: 0.74rem; font-weight: 700;
}
.bdg.gn { background: #DCFCE7; color: #166534; }
.bdg.rd { background: #FEE2E2; color: #991B1B; }
.bdg.am { background: #FEF3C7; color: #92400E; }
.bdg.bl { background: #DBEAFE; color: #1E40AF; }
.bdg.blk { display: block; margin: 6px 0; padding: 8px 14px; }

/* ══════════════════════════════════════════
   DATAFRAME
══════════════════════════════════════════ */
[data-testid="stDataFrame"] {
    background: white !important; border-radius: 12px !important;
    overflow: hidden !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07) !important;
}

/* ══════════════════════════════════════════
   EXPANDERS
══════════════════════════════════════════ */
[data-testid="stExpander"] {
    background: white !important; border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important; margin-bottom: 8px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}
[data-testid="stExpander"] > div > div { background: white !important; }
[data-testid="stExpander"] summary p {
    font-weight: 600 !important; font-size: 0.88rem !important;
    color: #0F172A !important;
}

/* ══════════════════════════════════════════
   HIDE CHROME
══════════════════════════════════════════ */
#MainMenu, footer,
[data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ra-header">
    <span class="ra-tag">RA-MAIP</span>
    <div class="ra-title">Investment Portfolio Planner</div>
    <div class="ra-sub">SEBI-Compliant &nbsp;·&nbsp; Indian Market Calibrated &nbsp;·&nbsp; Adaptive Multi-Asset Allocation Engine</div>
</div>
""", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Investor Profile")
    st.markdown("---")

    st.markdown("**Personal Details**")
    age        = st.slider("Age", 18, 75, 28)
    dependents = st.number_input("Dependents", min_value=0, max_value=8, value=0)

    st.markdown("---")
    st.markdown("**Financial Details**")
    monthly_salary   = st.number_input("Monthly Income (Rs)",   min_value=10000, max_value=2000000, value=75000, step=5000)
    monthly_expenses = st.number_input("Monthly Expenses (Rs)", min_value=5000,  max_value=1000000, value=30000, step=5000)
    tax_bracket      = st.selectbox("Income Tax Bracket (%)", [0, 5, 10, 15, 20, 30], index=5)

    st.markdown("---")
    st.markdown("**Investment Goals**")
    investment_goal  = st.selectbox("Primary Goal", [
        "Wealth Creation", "Retirement", "Child Education",
        "Emergency Fund", "Short-Term Purchase", "Tax Saving",
    ])
    investment_years = st.slider("Time Horizon (Years)", 1, 30, 10)
    risk_level       = st.select_slider(
        "Risk Appetite",
        options=["Conservative", "Moderate", "Aggressive"],
        value="Moderate",
    )
    st.markdown("---")
    generate = st.button("Generate Portfolio")

# ── LANDING ───────────────────────────────────────────────────────────────────
if not generate:
    c1, c2, c3 = st.columns(3)
    c1.markdown("""<div class="kpi g">
        <span class="kpi-lbl">Asset Classes</span>
        <span class="kpi-val gn">7</span>
        <span class="kpi-sub">Equity · Debt · Gold · REITs · International · Liquid · Arbitrage</span>
    </div>""", unsafe_allow_html=True)
    c2.markdown("""<div class="kpi">
        <span class="kpi-lbl">Regulatory Framework</span>
        <span class="kpi-val">SEBI</span>
        <span class="kpi-sub">Hard caps and compliance checks enforced on every allocation</span>
    </div>""", unsafe_allow_html=True)
    c3.markdown("""<div class="kpi a">
        <span class="kpi-lbl">Risk Engine</span>
        <span class="kpi-val am">Adaptive</span>
        <span class="kpi-sub">Continuous scoring — every input change produces a unique allocation</span>
    </div>""", unsafe_allow_html=True)
    st.markdown('<span class="stitle" style="margin-top:28px">About This Tool</span>', unsafe_allow_html=True)
    st.markdown("""
    Complete your investor profile in the sidebar and click **Generate Portfolio**.
    The engine computes a personalised, SEBI-compliant multi-asset allocation,
    projects wealth growth over your chosen horizon, and maps each asset class
    to specific Indian market instruments with tax-efficiency overlays.
    """)
    st.stop()

# ── CALCULATIONS ──────────────────────────────────────────────────────────────
monthly_investable = monthly_salary - monthly_expenses
annual_investable  = monthly_investable * 12
if monthly_investable <= 0:
    st.error("Monthly expenses exceed income. Please review your inputs.")
    st.stop()

goal_split = {
    "Emergency Fund":      (0.80, 0.20),
    "Short-Term Purchase": (0.65, 0.35),
    "Retirement":          (0.45, 0.55),
    "Wealth Creation":     (0.40, 0.60),
    "Child Education":     (0.50, 0.50),
    "Tax Saving":          (0.35, 0.65),
}
mr, yr             = goal_split.get(investment_goal, (0.5, 0.5))
monthly_investment = monthly_investable * mr
yearly_investment  = annual_investable  * yr

result     = get_intelligent_allocation(
    age=age, risk_profile=risk_level, horizon=investment_years,
    goal=investment_goal, monthly_income=monthly_salary,
    monthly_expenses=monthly_expenses, dependents=dependents,
)
allocation = result["allocation"]
risk_score = result["risk_score"]
meta       = result["metadata"]

compliance      = run_compliance_check(allocation, risk_score, investment_goal, investment_years)
allocation      = compliance.adjusted_allocation
weights_decimal = {k: v/100 for k,v in allocation.items()}
metrics         = compute_portfolio_metrics(weights_decimal)
projection      = project_wealth(
    monthly_investment=monthly_investment,
    annual_return_pct=metrics["expected_annual_return"],
    years=investment_years,
)
instruments     = get_instrument_recommendations(allocation, risk_score)
tax_instruments = get_indian_tax_optimized_split(
    annual_investable=annual_investable,
    risk_score=risk_score,
    tax_bracket_percent=tax_bracket,
)

# ── PORTFOLIO SUMMARY ─────────────────────────────────────────────────────────
st.markdown('<span class="stitle">Portfolio Summary</span>', unsafe_allow_html=True)
k1, k2, k3, k4 = st.columns(4)
k1.markdown(f"""<div class="kpi g">
    <span class="kpi-lbl">Expected Annual Return</span>
    <span class="kpi-val gn">{metrics['expected_annual_return']}%</span>
    <span class="kpi-sub">Historical Indian market calibration</span>
</div>""", unsafe_allow_html=True)
k2.markdown(f"""<div class="kpi">
    <span class="kpi-lbl">Annual Volatility</span>
    <span class="kpi-val">{metrics['annual_volatility']}%</span>
    <span class="kpi-sub">Portfolio standard deviation</span>
</div>""", unsafe_allow_html=True)
k3.markdown(f"""<div class="kpi a">
    <span class="kpi-lbl">Sharpe Ratio</span>
    <span class="kpi-val am">{metrics['sharpe_ratio']}</span>
    <span class="kpi-sub">Risk-free rate: 6.5% (RBI repo)</span>
</div>""", unsafe_allow_html=True)
k4.markdown(f"""<div class="kpi r">
    <span class="kpi-lbl">95% Value at Risk</span>
    <span class="kpi-val rd">{metrics['value_at_risk_95']}%</span>
    <span class="kpi-sub">Max expected annual drawdown</span>
</div>""", unsafe_allow_html=True)

# ── RISK ASSESSMENT ───────────────────────────────────────────────────────────
st.markdown('<span class="stitle">Risk Assessment</span>', unsafe_allow_html=True)
ra_l, ra_r = st.columns([2.6, 1])
with ra_l:
    ptr = int(risk_score * 100)
    st.markdown(f"""
    <div class="white-card">
        <div style="display:flex;align-items:center;gap:14px;margin-bottom:4px">
            <span style="font-size:1.35rem;font-weight:800;color:#0F172A">Risk Score: {risk_score:.2f}</span>
            <span class="bdg bl">{meta['computed_profile']}</span>
        </div>
        <div class="risk-bar"></div>
        <div class="risk-bar-lbl">
            <span>Conservative</span><span>Moderate</span><span>Aggressive</span>
        </div>
        <div style="margin-left:calc({ptr}% - 7px);font-size:1rem;color:#0F172A;line-height:1.4">&#9650;</div>
    </div>
    """, unsafe_allow_html=True)
with ra_r:
    st.markdown(f"""
    <div class="pcard">
        <span class="pcard-t">Profile Inputs</span>
        <div class="prow"><span class="pl">Age</span><span class="pv">{age} yrs</span></div>
        <div class="prow"><span class="pl">Horizon</span><span class="pv">{investment_years} yrs</span></div>
        <div class="prow"><span class="pl">Monthly Surplus</span><span class="pv">Rs {monthly_investable:,.0f}</span></div>
        <div class="prow"><span class="pl">Goal</span><span class="pv">{investment_goal}</span></div>
        <div class="prow"><span class="pl">Tax Bracket</span><span class="pv">{tax_bracket}%</span></div>
        <div class="prow"><span class="pl">Dependents</span><span class="pv">{dependents}</span></div>
    </div>
    """, unsafe_allow_html=True)

# ── RECOMMENDED ALLOCATION ────────────────────────────────────────────────────
st.markdown('<span class="stitle">Recommended Allocation</span>', unsafe_allow_html=True)
al_l, al_r = st.columns([1.2, 0.8])
with al_l:
    rows = []
    for asset, pct in allocation.items():
        if pct > 0:
            ya = yearly_investment * pct / 100
            rows.append({
                "Asset Class":      asset,
                "Weight (%)":       pct,
                "Annual (Rs)":      f"Rs {ya:,.0f}",
                "Monthly SIP (Rs)": f"Rs {ya/12:,.0f}",
            })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.markdown("<div style='margin-top:10px'>", unsafe_allow_html=True)
    if compliance.is_compliant:
        st.markdown('<span class="bdg gn">SEBI Compliant — All limits satisfied</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="bdg rd">Adjusted for SEBI Compliance</span>', unsafe_allow_html=True)
        for v in compliance.violations:
            st.warning(v)
    for w in compliance.warnings:
        st.markdown(f'<span class="bdg am blk">{w}</span>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with al_r:
    COLORS = ["#1D4ED8","#0891B2","#059669","#D97706","#7C3AED","#DC2626","#9CA3AF"]
    labels = [k for k,v in allocation.items() if v > 0]
    sizes  = [v for k,v in allocation.items() if v > 0]
    fig, ax = plt.subplots(figsize=(4.5, 4.8))
    fig.patch.set_facecolor("white"); ax.set_facecolor("white")
    wedges, _, autotexts = ax.pie(
        sizes, labels=None, colors=COLORS[:len(labels)],
        autopct=lambda p: f"{p:.1f}%" if p > 4 else "",
        startangle=130, pctdistance=0.76,
        wedgeprops={"edgecolor":"white","linewidth":3},
    )
    for at in autotexts:
        at.set_fontsize(8.5); at.set_color("white"); at.set_fontweight("bold")
    ax.legend(wedges, labels, loc="lower center",
              bbox_to_anchor=(0.5, -0.12), ncol=2,
              fontsize=8, frameon=False, labelcolor="#0F172A")
    fig.tight_layout()
    st.pyplot(fig)

# ── WEALTH PROJECTION ─────────────────────────────────────────────────────────
st.markdown(f'<span class="stitle">Wealth Projection — {investment_years}-Year Horizon</span>',
            unsafe_allow_html=True)
w1, w2, w3, w4 = st.columns(4)
w1.markdown(f"""<div class="kpi">
    <span class="kpi-lbl">Total Invested</span>
    <span class="kpi-val" style="font-size:1.3rem!important">Rs {projection['total_invested']:,.0f}</span>
    <span class="kpi-sub">Rs {monthly_investment:,.0f} / month SIP</span>
</div>""", unsafe_allow_html=True)
w2.markdown(f"""<div class="kpi g">
    <span class="kpi-lbl">Expected Corpus</span>
    <span class="kpi-val gn" style="font-size:1.3rem!important">Rs {projection['nominal_value']:,.0f}</span>
    <span class="kpi-sub">Gain: Rs {projection['total_gain']:,.0f}</span>
</div>""", unsafe_allow_html=True)
w3.markdown(f"""<div class="kpi">
    <span class="kpi-lbl">Real Value (6% Inflation)</span>
    <span class="kpi-val" style="font-size:1.3rem!important">Rs {projection['real_value_today_equiv']:,.0f}</span>
    <span class="kpi-sub">Today's purchasing power equivalent</span>
</div>""", unsafe_allow_html=True)
w4.markdown(f"""<div class="kpi a">
    <span class="kpi-lbl">Wealth Multiplier</span>
    <span class="kpi-val am">{projection['wealth_multiplier']}x</span>
    <span class="kpi-sub">Return on total capital deployed</span>
</div>""", unsafe_allow_html=True)

# Growth chart — separate container, no overlap
st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
months     = list(range(0, investment_years * 12 + 1))
r_m        = metrics["expected_annual_return"] / 100 / 12
sip        = monthly_investment
corpus_v   = [(sip * (((1+r_m)**m-1)/r_m) * (1+r_m) if r_m > 0 else sip*m) / 1e5 for m in months]
invested_v = [sip * m / 1e5 for m in months]

fig2, ax2 = plt.subplots(figsize=(12, 4))
fig2.patch.set_facecolor("white"); ax2.set_facecolor("white")
ax2.fill_between(months, invested_v, alpha=0.10, color="#1D4ED8")
ax2.fill_between(months, corpus_v, invested_v, alpha=0.13, color="#059669")
ax2.plot(months, invested_v, color="#1D4ED8", linewidth=1.6, linestyle="--",
         label="Amount Invested", zorder=3)
ax2.plot(months, corpus_v,   color="#059669", linewidth=2.4,
         label="Expected Corpus", zorder=4)
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"Rs {x:.0f}L"))
ax2.set_xlabel("Month", fontsize=10, color="#64748B", labelpad=8)
ax2.set_ylabel("Value (Rs Lakhs)", fontsize=10, color="#64748B", labelpad=8)
ax2.set_title(
    f"SIP Growth   ·   Rs {monthly_investment:,.0f}/month   ·   "
    f"{metrics['expected_annual_return']}% p.a. expected return",
    fontsize=10.5, color="#0F172A", fontweight="700", pad=18
)
ax2.legend(fontsize=9.5, frameon=False, labelcolor="#0F172A",
           loc="upper left", bbox_to_anchor=(0.01, 0.97))
for spine in ["top","right"]:
    ax2.spines[spine].set_visible(False)
ax2.spines["left"].set_color("#E2E8F0")
ax2.spines["bottom"].set_color("#E2E8F0")
ax2.tick_params(labelsize=9, colors="#64748B")
ax2.grid(axis="y", color="#F1F5F9", linewidth=1.2)
fig2.tight_layout(pad=2.0)
st.pyplot(fig2)

# ── INSTRUMENT RECOMMENDATIONS ────────────────────────────────────────────────
st.markdown('<span class="stitle">Instrument Recommendations</span>', unsafe_allow_html=True)
items = [(ac, recs) for ac, recs in instruments.items() if allocation.get(ac, 0) > 0]
ic = st.columns(2)
for i, (ac, recs) in enumerate(items):
    pct = allocation.get(ac, 0)
    with ic[i % 2]:
        with st.expander(f"{ac}  —  {pct}% weight", expanded=pct >= 20):
            for r in recs:
                st.markdown(
                    f"<span style='color:#374151;font-size:0.87rem'>— {r}</span>",
                    unsafe_allow_html=True
                )

# ── TAX-EFFICIENT INSTRUMENTS ─────────────────────────────────────────────────
st.markdown('<span class="stitle">Tax-Efficient Instruments (Section 80C / 80CCD)</span>',
            unsafe_allow_html=True)
if tax_instruments:
    tdf = pd.DataFrame([
        {"Instrument": k, "Suggested Annual Amount": f"Rs {v:,}"}
        for k, v in tax_instruments.items()
    ])
    st.dataframe(tdf, use_container_width=True, hide_index=True)
    total_ts = sum(tax_instruments.values())
    st.markdown(
        f'<span class="bdg gn" style="margin-top:10px;display:inline-block;padding:8px 16px">'
        f'Estimated tax saving: Rs {int(total_ts * tax_bracket / 100):,} '
        f'at {tax_bracket}% bracket on Rs {total_ts:,} invested'
        f'</span>', unsafe_allow_html=True
    )

# ── BENCHMARK MUTUAL FUND ─────────────────────────────────────────────────────
st.markdown('<span class="stitle">Benchmark Mutual Fund</span>', unsafe_allow_html=True)
cp = meta["computed_profile"]
fp = "Conservative" if "Conservative" in cp else ("Aggressive" if "Aggressive" in cp else "Moderate")
scheme_info = select_scheme_by_risk(fp)

with st.spinner("Fetching NAV data ..."):
    mf   = get_mf_performance(scheme_info["code"])
    live = mf.get("source") == "live"
    lbdg = ('<span class="bdg gn" style="font-size:0.66rem;padding:2px 8px">Live</span>'
            if live else
            '<span class="bdg am" style="font-size:0.66rem;padding:2px 8px">Cached</span>')
    m1, m2, m3 = st.columns(3)
    m1.markdown(f"""<div class="kpi">
        <span class="kpi-lbl">Fund Category &nbsp;{lbdg}</span>
        <span class="kpi-val" style="font-size:0.97rem!important">{scheme_info['category']}</span>
        <span class="kpi-sub">{mf['scheme_name'][:60]}</span>
    </div>""", unsafe_allow_html=True)
    m2.markdown(f"""<div class="kpi g">
        <span class="kpi-lbl">Avg Daily Return</span>
        <span class="kpi-val gn" style="font-size:1.4rem!important">{mf['avg_daily_return']:.4%}</span>
        <span class="kpi-sub">{'Live NAV — mfapi.in' if live else 'Historical average'}</span>
    </div>""", unsafe_allow_html=True)
    m3.markdown(f"""<div class="kpi a">
        <span class="kpi-lbl">Daily Volatility</span>
        <span class="kpi-val am" style="font-size:1.4rem!important">{mf['risk']:.5f}</span>
        <span class="kpi-sub">Std dev of daily NAV returns</span>
    </div>""", unsafe_allow_html=True)
    if not live:
        st.markdown("""
        <div style="background:#FFFBEB;border:1px solid #FCD34D;border-radius:8px;
                    padding:10px 16px;margin-top:12px;font-size:0.79rem;color:#92400E">
            Showing historical averages — mfapi.in was unreachable.
            Open <strong>api.mfapi.in/mf/120503</strong> in your browser to verify connectivity.
            Portfolio calculations are not affected.
        </div>
        """, unsafe_allow_html=True)

# ── REGULATORY COMPLIANCE NOTES ───────────────────────────────────────────────
st.markdown('<span class="stitle">Regulatory Compliance Notes</span>', unsafe_allow_html=True)
if compliance.sebi_notes:
    for note in compliance.sebi_notes:
        st.markdown(f'<span class="bdg bl blk">{note}</span>', unsafe_allow_html=True)
else:
    st.markdown(
        '<span class="bdg gn">All allocations within SEBI regulatory limits. No adjustments required.</span>',
        unsafe_allow_html=True
    )

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="background:white;border:1px solid #E2E8F0;border-radius:12px;padding:18px 26px">
    <div style="font-size:0.66rem;font-weight:800;color:#94A3B8;text-transform:uppercase;
                letter-spacing:1px;margin-bottom:8px">Disclaimer</div>
    <div style="font-size:0.77rem;color:#64748B;line-height:1.75">
    This tool is for informational and educational purposes only. It does not constitute
    investment advice under SEBI (Investment Advisers) Regulations, 2013. Return assumptions
    are based on historical Indian market data and are not guaranteed. Consult a SEBI-registered
    Investment Adviser (RIA) before making investment decisions. Mutual fund investments are
    subject to market risks. Read all scheme-related documents carefully before investing.
    </div>
</div><br>
""", unsafe_allow_html=True)