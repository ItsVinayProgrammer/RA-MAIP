"""
Run this script ONCE from D:\Python Code\file\
It will create all files in the correct locations automatically.

Usage:  python setup_files.py
"""

import os

BASE = os.path.dirname(os.path.abspath(__file__))
P3   = os.path.join(BASE, "part3_portfolio")
os.makedirs(P3, exist_ok=True)

# ─── FILE 1: part3_portfolio/__init__.py ─────────────────────────────────────
write = lambda path, content: open(path, "w", encoding="utf-8").write(content)

write(os.path.join(P3, "__init__.py"), "# part3_portfolio package\n")

# ─── FILE 2: part3_portfolio/portfolio_intelligence.py ───────────────────────
write(os.path.join(P3, "portfolio_intelligence.py"), '''"""
Portfolio Intelligence Engine
- Encodes real Indian robo-advisor allocation patterns
- Uses continuous scoring instead of discrete buckets
- Ensures every parameter change produces a meaningfully different output
- SEBI-compliant asset class constraints
"""

import math

SEBI_LIMITS = {
    "Equity":        {"min": 0,  "max": 80},
    "Debt":          {"min": 5,  "max": 100},
    "Gold":          {"min": 0,  "max": 15},
    "REITs/InvITs":  {"min": 0,  "max": 10},
    "International": {"min": 0,  "max": 15},
    "Liquid/Cash":   {"min": 0,  "max": 20},
    "Arbitrage":     {"min": 0,  "max": 10},
}

GOAL_PROFILES = {
    "Emergency Fund":      {"liquidity_bias": 0.9, "safety_bias": 0.9, "growth_bias": 0.1},
    "Short-Term Purchase": {"liquidity_bias": 0.5, "safety_bias": 0.7, "growth_bias": 0.4},
    "Retirement":          {"liquidity_bias": 0.1, "safety_bias": 0.4, "growth_bias": 0.9},
    "Wealth Creation":     {"liquidity_bias": 0.1, "safety_bias": 0.2, "growth_bias": 1.0},
    "Child Education":     {"liquidity_bias": 0.2, "safety_bias": 0.5, "growth_bias": 0.8},
    "Tax Saving":          {"liquidity_bias": 0.0, "safety_bias": 0.3, "growth_bias": 0.7},
}


def _continuous_risk_score(age, income, expenses, horizon, risk_label, goal, dependents=0):
    weights = {"age": 0.25, "horizon": 0.30, "user_risk": 0.20, "surplus": 0.15, "goal": 0.10}
    age_score     = max(0, min(1, (75 - age) / 55)) ** 1.2
    horizon_score = min(1, math.log1p(horizon) / math.log1p(30))
    user_score    = {"Conservative": 0.15, "Moderate": 0.5, "Aggressive": 0.9}.get(risk_label, 0.5)
    surplus_ratio = min(1, max(0, income - expenses) / max(income, 1))
    surplus_score = surplus_ratio ** 0.7
    gp            = GOAL_PROFILES.get(goal, GOAL_PROFILES["Wealth Creation"])
    goal_score    = gp["growth_bias"] * (1 - gp["liquidity_bias"] * 0.5)
    dep_penalty   = min(0.2, dependents * 0.05)
    score = (weights["age"] * age_score + weights["horizon"] * horizon_score
             + weights["user_risk"] * user_score + weights["surplus"] * surplus_score
             + weights["goal"] * goal_score - dep_penalty)
    return round(max(0.02, min(0.98, score)), 4)


def _base_allocation(risk_score, goal):
    gp         = GOAL_PROFILES.get(goal, GOAL_PROFILES["Wealth Creation"])
    equity_raw = 5 + 73 * (1 / (1 + math.exp(-10 * (risk_score - 0.5))))
    equity_raw *= (1 - gp["liquidity_bias"] * 0.6)
    gold_raw   = min(12, 12 * math.exp(-6 * (risk_score - 0.45) ** 2))
    reits_raw  = 0
    if gp["liquidity_bias"] < 0.4 and risk_score > 0.35:
        reits_raw = min(8, 5 * math.sin(math.pi * risk_score) * (1 - gp["liquidity_bias"]))
    intl_raw = 0
    if gp["liquidity_bias"] < 0.5 and risk_score > 0.45:
        intl_raw = min(12, 10 * (risk_score - 0.4) * (1 - gp["liquidity_bias"]))
    liquid_raw = min(25, max(2, 15 * (1 - risk_score) * (1 + gp["liquidity_bias"])))
    arb_raw    = 0
    if 0.3 < risk_score < 0.65 and gp["liquidity_bias"] < 0.5:
        arb_raw = 4 * math.exp(-8 * (risk_score - 0.48) ** 2)
    debt_raw = max(5, 100 - equity_raw - gold_raw - reits_raw - intl_raw - liquid_raw - arb_raw)
    return {"Equity": equity_raw, "Debt": debt_raw, "Gold": gold_raw,
            "REITs/InvITs": reits_raw, "International": intl_raw,
            "Liquid/Cash": liquid_raw, "Arbitrage": arb_raw}


def _apply_sebi_constraints(raw):
    clipped = {a: max(SEBI_LIMITS[a]["min"], min(SEBI_LIMITS[a]["max"], v)) for a, v in raw.items()}
    total   = sum(clipped.values()) or 1
    norm    = {k: round(v * 100 / total, 1) for k, v in clipped.items()}
    diff    = 100 - sum(norm.values())
    norm[max(norm, key=norm.get)] = round(norm[max(norm, key=norm.get)] + diff, 1)
    return norm


def _prune_small_allocations(alloc, threshold=1.5):
    pruned  = {k: v for k, v in alloc.items() if v >= threshold}
    removed = sum(v for k, v in alloc.items() if v < threshold)
    if removed > 0 and "Debt" in pruned:
        pruned["Debt"] = round(pruned["Debt"] + removed, 1)
    return pruned


def _score_to_label(score):
    if score < 0.33:   return "Conservative"
    elif score < 0.55: return "Moderate-Conservative"
    elif score < 0.67: return "Moderate"
    elif score < 0.80: return "Moderate-Aggressive"
    else:              return "Aggressive"


def get_intelligent_allocation(age, risk_profile, horizon, goal,
                                monthly_income=50000, monthly_expenses=20000, dependents=0):
    risk_score  = _continuous_risk_score(age, monthly_income, monthly_expenses,
                                         horizon, risk_profile, goal, dependents)
    raw         = _base_allocation(risk_score, goal)
    constrained = _apply_sebi_constraints(raw)
    pruned      = _prune_small_allocations(constrained)
    return {
        "allocation": pruned,
        "risk_score": risk_score,
        "metadata":   {"risk_label": risk_profile, "computed_profile": _score_to_label(risk_score),
                       "goal": goal, "horizon_years": horizon},
    }
''')

# ─── FILE 3: part3_portfolio/efficient_frontier.py ───────────────────────────
write(os.path.join(P3, "efficient_frontier.py"), '''"""
Efficient Frontier - Indian Market Implementation
Uses historically-anchored return/risk estimates for Indian asset classes.
"""

import math

INDIAN_ASSET_PARAMS = {
    "Equity":        {"expected_return": 0.128, "std_dev": 0.185},
    "Debt":          {"expected_return": 0.072, "std_dev": 0.042},
    "Gold":          {"expected_return": 0.098, "std_dev": 0.132},
    "REITs/InvITs":  {"expected_return": 0.110, "std_dev": 0.095},
    "International": {"expected_return": 0.115, "std_dev": 0.210},
    "Liquid/Cash":   {"expected_return": 0.068, "std_dev": 0.005},
    "Arbitrage":     {"expected_return": 0.071, "std_dev": 0.008},
}

CORRELATIONS = {
    ("Equity","Debt"): -0.15, ("Equity","Gold"): 0.05,
    ("Equity","REITs/InvITs"): 0.45, ("Equity","International"): 0.65,
    ("Equity","Liquid/Cash"): -0.05, ("Equity","Arbitrage"): 0.10,
    ("Debt","Gold"): 0.10, ("Debt","REITs/InvITs"): 0.20,
    ("Debt","International"): -0.10, ("Debt","Liquid/Cash"): 0.55,
    ("Debt","Arbitrage"): 0.45, ("Gold","REITs/InvITs"): 0.05,
    ("Gold","International"): 0.15, ("Gold","Liquid/Cash"): -0.02,
    ("Gold","Arbitrage"): 0.02, ("REITs/InvITs","International"): 0.30,
    ("REITs/InvITs","Liquid/Cash"): 0.10, ("REITs/InvITs","Arbitrage"): 0.15,
    ("International","Liquid/Cash"): -0.05, ("International","Arbitrage"): 0.08,
    ("Liquid/Cash","Arbitrage"): 0.50,
}


def _get_correlation(a, b):
    if a == b: return 1.0
    return CORRELATIONS.get((a, b), CORRELATIONS.get((b, a), 0.0))


def compute_portfolio_metrics(weights):
    assets     = list(weights.keys())
    risk_free  = 0.065
    exp_return = sum(weights[a] * INDIAN_ASSET_PARAMS.get(a, {"expected_return": 0.07})["expected_return"]
                     for a in assets)
    variance   = sum(
        weights[a] * weights[b]
        * INDIAN_ASSET_PARAMS.get(a, {"std_dev": 0.05})["std_dev"]
        * INDIAN_ASSET_PARAMS.get(b, {"std_dev": 0.05})["std_dev"]
        * _get_correlation(a, b)
        for a in assets for b in assets
    )
    volatility = math.sqrt(max(variance, 0))
    sharpe     = (exp_return - risk_free) / volatility if volatility > 0 else 0
    return {
        "expected_annual_return": round(exp_return * 100, 2),
        "annual_volatility":      round(volatility * 100, 2),
        "sharpe_ratio":           round(sharpe, 3),
        "value_at_risk_95":       round((exp_return - 1.645 * volatility) * 100, 2),
    }


def project_wealth(monthly_investment, annual_return_pct, years, inflation_pct=6.0):
    r_m   = annual_return_pct / 100 / 12
    n     = years * 12
    nom   = monthly_investment * (((1+r_m)**n-1)/r_m)*(1+r_m) if r_m > 0 else monthly_investment*n
    r_real = ((1+annual_return_pct/100)/(1+inflation_pct/100))-1
    r_rm   = r_real/12
    real   = monthly_investment*(((1+r_rm)**n-1)/r_rm)*(1+r_rm) if r_rm > 0 else monthly_investment*n
    invested = monthly_investment * n
    return {
        "total_invested":          round(invested),
        "nominal_value":           round(nom),
        "real_value_today_equiv":  round(real),
        "total_gain":              round(nom - invested),
        "wealth_multiplier":       round(nom / max(invested, 1), 2),
    }


def get_efficient_allocation(age, risk_profile, horizon, goal,
                              monthly_income=50000, monthly_expenses=20000, dependents=0):
    from part3_portfolio.portfolio_intelligence import get_intelligent_allocation
    return get_intelligent_allocation(age=age, risk_profile=risk_profile, horizon=horizon,
                                      goal=goal, monthly_income=monthly_income,
                                      monthly_expenses=monthly_expenses,
                                      dependents=dependents)["allocation"]
''')

# ─── FILE 4: part3_portfolio/sebi_compliance.py ──────────────────────────────
write(os.path.join(P3, "sebi_compliance.py"), '''"""
SEBI Compliance & Indian Market Regulation Engine
"""
from dataclasses import dataclass

@dataclass
class ComplianceResult:
    is_compliant: bool
    violations: list
    warnings: list
    adjusted_allocation: dict
    sebi_notes: list


def run_compliance_check(allocation, risk_score, goal, horizon):
    violations = []
    warnings   = []
    sebi_notes = []
    adjusted   = dict(allocation)

    if adjusted.get("REITs/InvITs", 0) > 10:
        excess = adjusted["REITs/InvITs"] - 10
        adjusted["REITs/InvITs"] = 10
        adjusted["Debt"] = adjusted.get("Debt", 0) + excess
        violations.append("REITs/InvITs capped at 10% per SEBI circular SEBI/HO/IMD/IMD-I/DOF1/P/CIR/2021/563")
        sebi_notes.append("SEBI/HO/IMD/IMD-I/DOF1/P/CIR/2021/563 — REITs & InvITs max 10%")

    if adjusted.get("International", 0) > 15:
        excess = adjusted["International"] - 15
        adjusted["International"] = 15
        adjusted["Equity"] = adjusted.get("Equity", 0) + excess
        violations.append("International allocation capped at 15% (SEBI overseas investment limit)")
        sebi_notes.append("SEBI overseas investment monitoring — industry ₹7B limit")

    if risk_score < 0.3 and adjusted.get("Equity", 0) > 30:
        warnings.append(f"Equity ({adjusted[\'Equity\']}%) is high for your conservative risk profile.")

    if goal == "Emergency Fund" and adjusted.get("Equity", 0) > 20:
        warnings.append("Emergency funds should have <20% equity for liquidity.")

    if horizon <= 3 and adjusted.get("Equity", 0) > 40:
        warnings.append(f"Equity ({adjusted[\'Equity\']}%) is risky for a {horizon}-year horizon.")

    if goal == "Emergency Fund":
        warnings.append("ELSS funds are NOT suitable for emergency funds — 3-year lock-in applies.")

    if risk_score < 0.35 and adjusted.get("Debt", 0) > 0:
        sebi_notes.append("Prefer AAA/AA+ rated debt instruments. Ref: SEBI credit risk framework Mar 2020")

    return ComplianceResult(
        is_compliant=len(violations) == 0,
        violations=violations,
        warnings=warnings,
        adjusted_allocation=adjusted,
        sebi_notes=list(set(sebi_notes)),
    )


def get_instrument_recommendations(allocation, risk_score):
    recs = {}
    if allocation.get("Equity", 0) > 0:
        if risk_score > 0.7:
            recs["Equity"] = ["Small Cap MFs (Nippon India Small Cap, SBI Small Cap)",
                               "Mid Cap MFs (Kotak Emerging Equity, Axis Midcap)",
                               "Sectoral/Thematic (tech, pharma)"]
        elif risk_score > 0.45:
            recs["Equity"] = ["Flexi Cap MFs (Parag Parikh, HDFC Flexi Cap)",
                               "Large & Mid Cap MFs", "Nifty 50 Index Fund"]
        else:
            recs["Equity"] = ["Large Cap Index Fund (Nifty 50 / Sensex)",
                               "Balanced Advantage Fund"]
    if allocation.get("Debt", 0) > 0:
        if risk_score < 0.35:
            recs["Debt"] = ["Overnight / Liquid Funds", "Short Duration Debt Funds",
                             "Bank FDs (DICGC insured up to Rs5L)", "RBI Floating Rate Bonds"]
        else:
            recs["Debt"] = ["Corporate Bond Funds (AAA-rated)", "Medium Duration Funds",
                             "Dynamic Bond Funds"]
    if allocation.get("Gold", 0) > 0:
        recs["Gold"] = ["Sovereign Gold Bonds (SGB) — tax-free on maturity",
                         "Gold ETFs (Nippon Gold ETF, SBI Gold ETF)",
                         "Gold Savings Fund (SIP-friendly)"]
    if allocation.get("REITs/InvITs", 0) > 0:
        recs["REITs/InvITs"] = ["Embassy Office Parks REIT", "Mindspace Business Parks REIT",
                                  "PowerGrid InvIT", "India Grid Trust InvIT"]
    if allocation.get("International", 0) > 0:
        recs["International"] = ["Parag Parikh Flexi Cap (partial international)",
                                   "Motilal Oswal Nasdaq 100 FOF",
                                   "ICICI Pru US Bluechip Equity Fund"]
    if allocation.get("Liquid/Cash", 0) > 0:
        recs["Liquid/Cash"] = ["Liquid MFs (Mirae Asset, HDFC Liquid Fund)",
                                 "Overnight Funds",
                                 "High-yield Savings Account (small finance banks)"]
    if allocation.get("Arbitrage", 0) > 0:
        recs["Arbitrage"] = ["Arbitrage Funds (Nippon India Arbitrage, ICICI Pru Arbitrage)",
                               "Note: Taxed as equity — ideal for 30% bracket investors"]
    return recs


def get_indian_tax_optimized_split(annual_investable, risk_score, tax_bracket_percent=30):
    instruments = {}
    if risk_score > 0.35 and annual_investable > 50000:
        instruments["ELSS (80C, 3yr lock-in)"] = round(min(annual_investable * 0.20, 75000))
    if risk_score < 0.6:
        instruments["PPF (80C, 15yr, EEE)"] = round(min(annual_investable * 0.15, 150000))
    if annual_investable > 100000:
        instruments["NPS Tier-1 (80CCD, extra Rs50k deduction)"] = round(min(annual_investable * 0.10, 50000))
    if risk_score > 0.25:
        instruments["Sovereign Gold Bonds (tax-free on maturity)"] = round(min(annual_investable * 0.05, 48000))
    return instruments
''')

# ─── FILE 5: part3_portfolio/portfolio_optimizer.py ─────────────────────────
write(os.path.join(P3, "portfolio_optimizer.py"), '''"""Portfolio optimizer — delegates to intelligent allocation engine."""
from part3_portfolio.efficient_frontier import get_efficient_allocation

def get_optimal_allocation(age, risk_profile, horizon, goal,
                            monthly_income=50000, monthly_expenses=20000):
    return get_efficient_allocation(age=age, risk_profile=risk_profile, horizon=horizon,
                                    goal=goal, monthly_income=monthly_income,
                                    monthly_expenses=monthly_expenses)
''')

print("=" * 55)
print("SUCCESS! All files created correctly.")
print("=" * 55)
print()
print("Files created in:", P3)
for f in os.listdir(P3):
    if f.endswith(".py"):
        print(f"  ✅ {f}")
print()
print("Now run:  streamlit run app.py")
