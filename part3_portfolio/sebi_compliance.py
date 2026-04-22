"""
SEBI Compliance & Indian Market Regulation Engine
Implements real regulatory constraints from SEBI circulars
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ComplianceResult:
    is_compliant: bool
    violations: list
    warnings: list
    adjusted_allocation: dict
    sebi_notes: list


# SEBI Circular references (real)
SEBI_RULES = {
    "REIT_INVIT_CAP": {
        "limit": 10,
        "reference": "SEBI/HO/IMD/IMD-I/DOF1/P/CIR/2021/563",
        "description": "REITs & InvITs: max 10% of portfolio per SEBI 2021 circular",
    },
    "INTERNATIONAL_FUND": {
        "limit": 15,
        "reference": "SEBI overseas investment limit monitoring",
        "description": "International MFs: industry-wide ₹7B limit → practical max 15%",
    },
    "LIQUID_FUND_OVERNIGHT": {
        "reference": "SEBI/HO/IMD/DF3/CIR/2019/064",
        "description": "Liquid funds cannot invest in risky assets beyond 20% haircut",
    },
    "DEBT_CREDIT_QUALITY": {
        "reference": "SEBI Circular March 2020 credit risk framework",
        "description": "Debt allocation should prefer AAA/AA+ rated instruments for conservative investors",
    },
    "ELSS_LOCK_IN": {
        "reference": "Section 80C Income Tax Act + SEBI ELSS guidelines",
        "description": "ELSS funds have 3-year mandatory lock-in period",
    },
    "DIVERSIFICATION": {
        "reference": "SEBI MF Regulations 1996, Regulation 44",
        "description": "No single stock/issuer to exceed 10% of NAV",
    },
}


def get_indian_tax_optimized_split(
    annual_investable: float,
    risk_score: float,
    tax_bracket_percent: int = 30
) -> dict:
    """
    Suggests tax-efficient instruments available to Indian retail investors.
    80C, 80CCD, NPS, ELSS logic.
    """
    tax_saving_80c_limit = 150000      # Section 80C
    nps_additional_80ccd = 50000       # 80CCD(1B)

    tax_instruments = {}

    # ELSS (Equity Linked Saving Scheme) - 3yr lock-in, up to 80C
    if risk_score > 0.35 and annual_investable > 50000:
        elss_amount = min(annual_investable * 0.20, tax_saving_80c_limit * 0.5)
        tax_instruments["ELSS (80C, 3yr lock-in)"] = round(elss_amount)

    # PPF (ultra-safe, 80C, 15yr, EEE)
    if risk_score < 0.6:
        ppf_amount = min(annual_investable * 0.15, 150000)
        tax_instruments["PPF (80C, 15yr, EEE)"] = round(ppf_amount)

    # NPS Tier-1 (additional 80CCD)
    if annual_investable > 100000:
        nps_amount = min(annual_investable * 0.10, nps_additional_80ccd)
        tax_instruments["NPS Tier-1 (80CCD, additional ₹50k deduction)"] = round(nps_amount)

    # SGBs (Sovereign Gold Bonds) - 8yr maturity, tax-free on redemption
    if risk_score > 0.25:
        sgb_amount = min(annual_investable * 0.05, 48000)   # 4 units * ₹6000 approx
        tax_instruments["Sovereign Gold Bonds (tax-free on maturity)"] = round(sgb_amount)

    return tax_instruments


def run_compliance_check(allocation: dict, risk_score: float, goal: str, horizon: int) -> ComplianceResult:
    """
    Checks allocation against SEBI rules and returns violations + adjusted allocation.
    """
    violations = []
    warnings = []
    sebi_notes = []
    adjusted = dict(allocation)

    # 1. REITs/InvITs cap
    if adjusted.get("REITs/InvITs", 0) > 10:
        violations.append(f"REITs/InvITs exceeds SEBI 10% limit: {adjusted['REITs/InvITs']}%")
        excess = adjusted["REITs/InvITs"] - 10
        adjusted["REITs/InvITs"] = 10
        adjusted["Debt"] = adjusted.get("Debt", 0) + excess
        sebi_notes.append(SEBI_RULES["REIT_INVIT_CAP"]["reference"])

    # 2. International cap
    if adjusted.get("International", 0) > 15:
        violations.append(f"International allocation exceeds 15% industry limit")
        excess = adjusted["International"] - 15
        adjusted["International"] = 15
        adjusted["Equity"] = adjusted.get("Equity", 0) + excess
        sebi_notes.append(SEBI_RULES["INTERNATIONAL_FUND"]["reference"])

    # 3. Conservative investors in high equity (risk-suitability warning)
    if risk_score < 0.3 and adjusted.get("Equity", 0) > 30:
        warnings.append(
            f"Equity ({adjusted['Equity']}%) is high for your risk profile. "
            "Consider increasing Debt allocation."
        )

    # 4. Horizon mismatch for goal
    if goal == "Emergency Fund" and adjusted.get("Equity", 0) > 20:
        warnings.append(
            "Emergency funds should have <20% equity for liquidity. "
            "Recommend liquid/debt-heavy portfolio."
        )

    # 5. Short horizon equity check
    if horizon <= 3 and adjusted.get("Equity", 0) > 40:
        warnings.append(
            f"Equity ({adjusted['Equity']}%) is risky for {horizon}-year horizon. "
            "Market downturns may not recover in time."
        )

    # 6. Debt quality reminder
    if risk_score < 0.35 and adjusted.get("Debt", 0) > 0:
        sebi_notes.append(
            "For conservative profiles, prefer AAA/AA+ debt instruments. "
            f"Ref: {SEBI_RULES['DEBT_CREDIT_QUALITY']['reference']}"
        )

    # 7. ELSS lock-in warning
    if goal == "Emergency Fund":
        warnings.append(
            "ELSS funds are NOT suitable for emergency funds due to 3-year lock-in. "
            "Use liquid/overnight funds instead."
        )

    is_compliant = len(violations) == 0

    return ComplianceResult(
        is_compliant=is_compliant,
        violations=violations,
        warnings=warnings,
        adjusted_allocation=adjusted,
        sebi_notes=list(set(sebi_notes)),
    )


def get_instrument_recommendations(allocation: dict, risk_score: float) -> dict:
    """
    Maps each asset class to specific Indian market instruments/fund categories.
    """
    recs = {}

    if allocation.get("Equity", 0) > 0:
        if risk_score > 0.7:
            recs["Equity"] = [
                "Small Cap MFs (e.g. Nippon India Small Cap, SBI Small Cap)",
                "Mid Cap MFs (e.g. Kotak Emerging Equity, Axis Midcap)",
                "Sectoral/Thematic (tech, pharma — high risk)",
            ]
        elif risk_score > 0.45:
            recs["Equity"] = [
                "Flexi Cap MFs (e.g. Parag Parikh, HDFC Flexi Cap)",
                "Large & Mid Cap MFs",
                "Nifty 50 Index Fund",
            ]
        else:
            recs["Equity"] = [
                "Large Cap Index Fund (Nifty 50 / Sensex)",
                "Balanced Advantage Fund",
            ]

    if allocation.get("Debt", 0) > 0:
        if risk_score < 0.35:
            recs["Debt"] = [
                "Overnight / Liquid Funds",
                "Short Duration Debt Funds",
                "Bank FDs (DICGC insured up to ₹5L)",
                "RBI Floating Rate Bonds",
            ]
        else:
            recs["Debt"] = [
                "Corporate Bond Funds (AAA-rated)",
                "Medium Duration Funds",
                "Dynamic Bond Funds",
            ]

    if allocation.get("Gold", 0) > 0:
        recs["Gold"] = [
            "Sovereign Gold Bonds (SGB) — best for 8yr+ horizon, tax-free",
            "Gold ETFs (Nippon Gold ETF, SBI Gold ETF)",
            "Gold Savings Fund (SIP-friendly)",
        ]

    if allocation.get("REITs/InvITs", 0) > 0:
        recs["REITs/InvITs"] = [
            "Embassy Office Parks REIT",
            "Mindspace Business Parks REIT",
            "PowerGrid InvIT",
            "India Grid Trust InvIT",
        ]

    if allocation.get("International", 0) > 0:
        recs["International"] = [
            "Parag Parikh Flexi Cap (partial international exposure)",
            "Motilal Oswal Nasdaq 100 FOF",
            "ICICI Pru US Bluechip Equity Fund",
        ]

    if allocation.get("Liquid/Cash", 0) > 0:
        recs["Liquid/Cash"] = [
            "Liquid Mutual Funds (Mirae Asset, HDFC Liquid Fund)",
            "Overnight Funds",
            "High-yield Savings Account (DFI/small finance banks)",
        ]

    if allocation.get("Arbitrage", 0) > 0:
        recs["Arbitrage"] = [
            "Arbitrage Funds (Nippon India Arbitrage, ICICI Pru Arbitrage)",
            "Note: Taxed as equity; ideal for 30% bracket investors",
        ]

    return recs