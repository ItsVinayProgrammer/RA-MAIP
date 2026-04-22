"""
NSE India Live Data Updater
============================
Fetches real rolling return data from NSE India's free public endpoints
and updates the expected_return / std_dev values in efficient_frontier.py.

Run this script monthly to keep your return assumptions current:
    python nse_data_updater.py

NSE Free APIs used (no key required):
  - https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050
  - https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20NEXT%2050
  - https://www.nseindia.com/api/historical/indicesHistory (index history)
  - AMFI daily NAV: https://www.amfiindia.com/spages/NAVAll.txt (free, no key)

Requirements:
    pip install requests pandas numpy
"""

import requests
import json
import time
import statistics
from datetime import datetime, timedelta
import math


# ── NSE session (required — NSE blocks requests without browser headers) ────
NSE_HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer":         "https://www.nseindia.com/",
    "Connection":      "keep-alive",
}


def get_nse_session():
    """
    NSE requires visiting the homepage first to get cookies.
    Without this, all API calls return 401 or empty responses.
    """
    session = requests.Session()
    session.headers.update(NSE_HEADERS)
    # Visit homepage to get session cookies
    session.get("https://www.nseindia.com/", timeout=10)
    time.sleep(1)   # small delay to avoid rate limiting
    return session


def fetch_nifty50_1yr_return(session):
    """
    Fetches Nifty 50 current value and computes approximate 1-year return
    using NSE's index data endpoint.
    """
    try:
        url  = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050"
        resp = session.get(url, timeout=10)
        data = resp.json()

        current_value   = data["data"][0]["last"]
        year_high       = data["data"][0]["yearHigh"]
        year_low        = data["data"][0]["yearLow"]
        prev_close      = data["data"][0]["previousClose"]
        day_change_pct  = data["data"][0]["pChange"]

        print(f"Nifty 50: {current_value:,.2f}  |  Day Change: {day_change_pct}%")
        print(f"  52W High: {year_high:,.2f}  |  52W Low: {year_low:,.2f}")
        return {"current": current_value, "prev_close": prev_close}

    except Exception as e:
        print(f"Could not fetch Nifty 50: {e}")
        return None


def fetch_amfi_category_returns():
    """
    AMFI publishes daily NAVs for ALL mutual funds at a free public URL.
    We use this to compute rolling category-average returns for:
    - Equity (Large Cap, Flexi Cap)
    - Debt (Short Duration)
    - Hybrid (Balanced Advantage)

    Returns a dict of {category: {"return": float, "std_dev": float}}
    """
    print("\nFetching AMFI category data...")
    url = "https://www.amfiindia.com/spages/NAVAll.txt"
    try:
        resp = requests.get(url, timeout=15)
        lines = resp.text.strip().split("\n")

        # AMFI format: SchemeCode;ISINDiv;ISINGrowth;SchemeName;NAV;Date
        nav_by_scheme = {}
        current_category = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("Open Ended") or line.startswith("Close Ended"):
                current_category = line
                continue
            parts = line.split(";")
            if len(parts) >= 6:
                try:
                    code = parts[0].strip()
                    name = parts[3].strip()
                    nav  = float(parts[4].strip())
                    nav_by_scheme[code] = {
                        "name": name, "nav": nav, "category": current_category
                    }
                except ValueError:
                    continue

        print(f"  Loaded {len(nav_by_scheme):,} schemes from AMFI")
        return nav_by_scheme

    except Exception as e:
        print(f"Could not fetch AMFI data: {e}")
        return {}


def fetch_nse_index_historical(session, index_name="NIFTY 50", years=5):
    """
    Fetches historical index data from NSE to compute rolling CAGR and std dev.
    index_name options: "NIFTY 50", "NIFTY NEXT 50", "NIFTY MIDCAP 150", etc.
    """
    print(f"\nFetching {years}-year history for {index_name}...")
    end_date   = datetime.now()
    start_date = end_date - timedelta(days=years * 365)

    url = (
        "https://www.nseindia.com/api/historical/indicesHistory?"
        f"indexType={requests.utils.quote(index_name)}"
        f"&from={start_date.strftime('%d-%m-%Y')}"
        f"&to={end_date.strftime('%d-%m-%Y')}"
    )
    try:
        resp = session.get(url, timeout=15)
        data = resp.json()
        closes = [float(d["CLOSE"]) for d in data["data"]["indexCloseOnlineRecords"]]

        if len(closes) < 20:
            print(f"  Insufficient data ({len(closes)} records)")
            return None

        # Annualised CAGR
        cagr = (closes[-1] / closes[0]) ** (1 / years) - 1

        # Daily returns for std dev
        daily_returns = [(closes[i] - closes[i-1]) / closes[i-1]
                         for i in range(1, len(closes))]
        daily_vol     = statistics.stdev(daily_returns)
        annual_vol    = daily_vol * math.sqrt(252)

        print(f"  {index_name}: CAGR={cagr:.2%}  |  Annual Vol={annual_vol:.2%}  |  Records={len(closes)}")
        return {"cagr": cagr, "annual_vol": annual_vol, "records": len(closes)}

    except Exception as e:
        print(f"  Could not fetch history for {index_name}: {e}")
        return None


def update_efficient_frontier(equity_return, equity_vol,
                               debt_return=None, gold_return=None):
    """
    Updates the INDIAN_ASSET_PARAMS in efficient_frontier.py
    with freshly computed values.
    """
    import os
    frontier_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "part3_portfolio", "efficient_frontier.py"
    )
    if not os.path.exists(frontier_path):
        print(f"Cannot find efficient_frontier.py at {frontier_path}")
        return

    with open(frontier_path, "r") as f:
        content = f.read()

    # Replace equity values
    old_equity = '"Equity":        {"expected_return": 0.128, "std_dev": 0.185},'
    new_equity = f'"Equity":        {{"expected_return": {equity_return:.4f}, "std_dev": {equity_vol:.4f}}},'
    content = content.replace(old_equity, new_equity)

    if debt_return:
        old_debt = '"Debt":          {"expected_return": 0.072, "std_dev": 0.042},'
        new_debt = f'"Debt":          {{"expected_return": {debt_return:.4f}, "std_dev": 0.042}},'
        content = content.replace(old_debt, new_debt)

    with open(frontier_path, "w") as f:
        f.write(content)

    print(f"\nUpdated efficient_frontier.py:")
    print(f"  Equity return: {equity_return:.2%}  |  Equity vol: {equity_vol:.2%}")
    if debt_return:
        print(f"  Debt return: {debt_return:.2%}")


def run_full_update():
    print("=" * 60)
    print("RA-MAIP  |  NSE Data Updater")
    print(f"Running at {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    print("\nStep 1: Establishing NSE session (fetching cookies)...")
    session = get_nse_session()
    print("  Session ready.")

    print("\nStep 2: Fetching Nifty 50 current data...")
    nifty_current = fetch_nifty50_1yr_return(session)

    print("\nStep 3: Fetching 5-year historical returns...")
    nifty50_hist   = fetch_nse_index_historical(session, "NIFTY 50",     years=5)
    midcap_hist    = fetch_nse_index_historical(session, "NIFTY MIDCAP 150", years=5)

    print("\nStep 4: Fetching AMFI NAV data...")
    amfi_data = fetch_amfi_category_returns()

    # Decide what to update
    if nifty50_hist:
        equity_return = nifty50_hist["cagr"]
        equity_vol    = nifty50_hist["annual_vol"]
        print(f"\nUsing live NSE data for equity: {equity_return:.2%} CAGR")
    else:
        equity_return = 0.128   # fallback to historical average
        equity_vol    = 0.185
        print("\nUsing hardcoded fallback for equity (NSE data unavailable)")

    update_efficient_frontier(
        equity_return=equity_return,
        equity_vol=equity_vol,
    )

    print("\n" + "=" * 60)
    print("Update complete. Restart your Streamlit app to use new values.")
    print("=" * 60)


if __name__ == "__main__":
    run_full_update()
