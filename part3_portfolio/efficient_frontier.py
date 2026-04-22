"""
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
    ("Equity", "Debt"): -0.15,
    ("Equity", "Gold"):  0.05,
    ("Equity", "REITs/InvITs"):  0.45,
    ("Equity", "International"): 0.65,
    ("Equity", "Liquid/Cash"):  -0.05,
    ("Equity", "Arbitrage"):     0.10,
    ("Debt",   "Gold"):          0.10,
    ("Debt",   "REITs/InvITs"):  0.20,
    ("Debt",   "International"): -0.10,
    ("Debt",   "Liquid/Cash"):   0.55,
    ("Debt",   "Arbitrage"):     0.45,
    ("Gold",   "REITs/InvITs"):  0.05,
    ("Gold",   "International"): 0.15,
    ("Gold",   "Liquid/Cash"):  -0.02,
    ("Gold",   "Arbitrage"):     0.02,
    ("REITs/InvITs",  "International"): 0.30,
    ("REITs/InvITs",  "Liquid/Cash"):   0.10,
    ("REITs/InvITs",  "Arbitrage"):     0.15,
    ("International", "Liquid/Cash"):  -0.05,
    ("International", "Arbitrage"):     0.08,
    ("Liquid/Cash",   "Arbitrage"):     0.50,
}


def _get_correlation(a, b):
    if a == b:
        return 1.0
    return CORRELATIONS.get((a, b), CORRELATIONS.get((b, a), 0.0))


def compute_portfolio_metrics(weights):
    assets     = list(weights.keys())
    risk_free  = 0.065
    exp_return = sum(
        weights[a] * INDIAN_ASSET_PARAMS.get(a, {"expected_return": 0.07})["expected_return"]
        for a in assets
    )
    variance = sum(
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
    r_m      = annual_return_pct / 100 / 12
    n        = years * 12
    nom      = (monthly_investment * (((1 + r_m) ** n - 1) / r_m) * (1 + r_m)
                if r_m > 0 else monthly_investment * n)
    r_real   = ((1 + annual_return_pct / 100) / (1 + inflation_pct / 100)) - 1
    r_rm     = r_real / 12
    real     = (monthly_investment * (((1 + r_rm) ** n - 1) / r_rm) * (1 + r_rm)
                if r_rm > 0 else monthly_investment * n)
    invested = monthly_investment * n
    return {
        "total_invested":         round(invested),
        "nominal_value":          round(nom),
        "real_value_today_equiv": round(real),
        "total_gain":             round(nom - invested),
        "wealth_multiplier":      round(nom / max(invested, 1), 2),
    }


def get_efficient_allocation(age, risk_profile, horizon, goal,
                              monthly_income=50000, monthly_expenses=20000, dependents=0):
    from part3_portfolio.portfolio_intelligence import get_intelligent_allocation
    return get_intelligent_allocation(
        age=age, risk_profile=risk_profile, horizon=horizon, goal=goal,
        monthly_income=monthly_income, monthly_expenses=monthly_expenses,
        dependents=dependents,
    )["allocation"]