"""Portfolio optimizer — delegates to intelligent allocation engine."""

from part3_portfolio.efficient_frontier import get_efficient_allocation


def get_optimal_allocation(age, risk_profile, horizon, goal,
                           monthly_income=50000, monthly_expenses=20000):
    return get_efficient_allocation(
        age=age,
        risk_profile=risk_profile,
        horizon=horizon,
        goal=goal,
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
    )