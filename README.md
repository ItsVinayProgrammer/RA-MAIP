# RA-MAIP

**Regulation-Aware Multi-Asset Investment Planner**

RA-MAIP is a Streamlit-based wealth intelligence application designed to translate investor inputs into a disciplined, multi-asset portfolio recommendation. The system combines live mutual fund data, risk-suitability logic, and SEBI-aware allocation constraints to deliver a portfolio view that is analytical, current, and regulation-conscious.

<img width="1919" height="1078" alt="Screenshot 2026-04-26 132350" src="https://github.com/user-attachments/assets/f70dfe7c-e173-4b85-916f-d95bca5f755a" />


## Institutional Overview

RA-MAIP is built for investors and practitioners who want a structured decision layer rather than static asset suggestions. It evaluates personal profile inputs, computes a continuous risk score, applies regulatory allocation limits, and then maps the result into an actionable portfolio with instrument-level guidance.

The project is centered on three principles:

- **Wealth Intelligence**: convert investor data into a coherent portfolio allocation framework.
- **Regulatory Compliance**: enforce hard caps and suitability checks inspired by SEBI-style advisory logic.
- **Live Market Context**: use current NAV data to avoid stale or purely hypothetical recommendations.

## Core Capabilities

- **Risk-Adjusted Returns**: estimates expected return, volatility, Sharpe ratio, and downside risk for the recommended mix.
- **Volatility Assessment**: derives portfolio-level volatility from Indian market asset assumptions and correlation structure.
- **Dynamic Asset Allocation**: adjusts the blend across Equity, Debt, Gold, REITs/InvITs, International, Liquid/Cash, and Arbitrage based on user profile and goal.
- **Live Portfolio Health Check**: fetches current mutual fund NAV data to compare benchmark fund behavior against the selected risk profile.
- **Compliance-First Portfolio Design**: applies SEBI-style caps and suitability checks before recommendations are displayed.
- **Tax-Aware Instrument Mapping**: overlays Indian tax-efficient instruments such as ELSS, PPF, NPS Tier-1, and Sovereign Gold Bonds.

## Architecture

RA-MAIP uses a simple but opinionated pipeline:

1. **Investor Profile Capture**
   - The Streamlit UI in [app.py](app.py) collects age, dependents, income, expenses, tax bracket, goal, horizon, and risk appetite.

2. **Risk Scoring and Allocation Engine**
   - [part3_portfolio/portfolio_intelligence.py](part3_portfolio/portfolio_intelligence.py) transforms profile inputs into a continuous risk score.
   - The engine then creates a raw multi-asset allocation and applies SEBI-oriented limits and pruning rules.

3. **Compliance Review**
   - [part3_portfolio/sebi_compliance.py](part3_portfolio/sebi_compliance.py) checks the allocation against regulatory constraints, suitability warnings, and tax-aware instrument logic.

4. **Metrics and Projection Layer**
   - [part3_portfolio/efficient_frontier.py](part3_portfolio/efficient_frontier.py) calculates expected return, volatility, Sharpe ratio, value-at-risk, and wealth projection.

5. **Live Data Engine**
   - [data_engine.py](data_engine.py) pulls mutual fund NAV history from MFAPI.
   - If the API is unavailable, the app falls back to cached benchmark data so the experience remains usable offline.
   - The live NAV series is used to compute historical volatility and average daily returns for benchmark fund analysis.

6. **Portfolio Presentation**
   - The app renders allocation tables, a pie chart, wealth projection visuals, compliance messages, and recommended instruments.

## Data Pipeline

RA-MAIP is intentionally not a static calculator. It operates as a live portfolio review workflow:

- The user profile defines the suitability context.
- The allocation engine converts that context into a weighted multi-asset portfolio.
- The data engine fetches current mutual fund NAVs to provide a market-linked benchmark check.
- The UI surfaces a **Live Portfolio Health Check** instead of a one-time answer.

This design keeps the recommendation layer anchored to current fund behavior while still maintaining deterministic compliance logic.

## Compliance Framework

RA-MAIP is built around a **regulation-aware** framework that mirrors the reasoning style of a professional Indian advisory workflow.

The system:

- Enforces allocation caps for regulated asset classes.
- Flags risk-suitability mismatches for conservative profiles, short horizons, and emergency fund goals.
- Encourages conservative debt quality for lower-risk investors.
- Surfaces tax-efficient structures only when they are contextually appropriate.

This is a design framework, not a claim of registration or licensure. The objective is to emulate disciplined SEBI-style logic in software.

## Visual Gallery

Add your rendered assets here once you export them from Streamlit or your plotting layer.

### Asset Allocation Pie Chart

![Asset Allocation Pie Chart](docs/images/asset-allocation-pie-chart.png)

### NAV Trend Analysis

![NAV Trend Analysis](docs/images/nav-trend-analysis.png)

## Tech Stack

- Python
- Streamlit
- Pandas
- Matplotlib
- Requests

## Installation

### 1. Create a virtual environment

```bash
python -m venv .venv
```

### 2. Activate the environment

**Windows PowerShell**

```powershell
.venv\\Scripts\\Activate.ps1
```

**Command Prompt**

```bat
.venv\\Scripts\\activate.bat
```

### 3. Install dependencies

```bash
pip install streamlit pandas matplotlib requests
```

### 4. Launch the application

```bash
streamlit run app.py
```

## Project Structure

```text
RA-MAIP/
├── app.py
├── data_engine.py
├── main.py
├── nse_data_updater.py
├── setup_files.py
├── part1_basics/
│   └── user_profile.py
├── part2_data/
│   └── mf_data.py
└── part3_portfolio/
    ├── efficient_frontier.py
    ├── portfolio_intelligence.py
    ├── portfolio_optimizer.py
    └── sebi_compliance.py
```

## How to Read the Output

- **Portfolio Summary** shows expected return, volatility, Sharpe ratio, and 95% VaR.
- **Risk Assessment** visualizes the computed risk score and investor profile context.
- **Recommended Allocation** breaks the portfolio into asset-class weights and SIP amounts.
- **Instrument Recommendations** maps each allocation bucket to Indian market instruments.
- **Tax-Efficient Instruments** highlights context-specific options for Indian investors.
- **Benchmark Mutual Fund** compares the selected profile against a live or cached MFAPI-backed benchmark.

## Notes

- Live NAV data depends on external API availability.
- Cached fallback data is included to keep the application functional when the API is unreachable.
- Allocation outputs are designed for educational and analytical use and should be reviewed with appropriate professional judgment before making investment decisions.
