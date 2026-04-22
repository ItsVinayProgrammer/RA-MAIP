import requests
import statistics


# Fallback NAV data in case API is unreachable
# These are real approximate values so the UI still works offline
FALLBACK_MF_DATA = {
    119551: {
        "scheme_name": "HDFC Short Duration Fund - Direct Growth",
        "avg_daily_return": 0.000278,
        "risk": 0.00121,
    },
    102885: {
        "scheme_name": "ICICI Prudential Balanced Advantage Fund - Direct Growth",
        "avg_daily_return": 0.000412,
        "risk": 0.00634,
    },
    120503: {
        "scheme_name": "Parag Parikh Flexi Cap Fund - Direct Growth",
        "avg_daily_return": 0.000721,
        "risk": 0.00913,
    },
}

# Multiple API endpoints to try in order
MF_API_ENDPOINTS = [
    "https://api.mfapi.in/mf/{code}",
    "https://mfapi.in/mf/{code}",          # alternate subdomain
]


def get_mf_performance(scheme_code):
    """
    Fetch live NAV data from mfapi.in with fallback to cached values.
    Tries multiple endpoints and returns fallback if all fail.
    """
    last_error = None

    for endpoint_template in MF_API_ENDPOINTS:
        url = endpoint_template.format(code=scheme_code)
        try:
            response = requests.get(url, timeout=6)
            response.raise_for_status()
            data = response.json()

            # mfapi returns newest-first — reverse for chronological order
            navs = [float(entry["nav"]) for entry in data["data"]]
            navs_chrono = list(reversed(navs))

            daily_returns = []
            for i in range(1, len(navs_chrono)):
                prev = navs_chrono[i - 1]
                if prev == 0:
                    continue
                daily_returns.append((navs_chrono[i] - prev) / prev)

            if len(daily_returns) < 2:
                break  # bad data — use fallback

            return {
                "scheme_name":      data["meta"]["scheme_name"],
                "avg_daily_return": sum(daily_returns) / len(daily_returns),
                "risk":             statistics.stdev(daily_returns),
                "source":           "live",
            }

        except Exception as e:
            last_error = e
            continue   # try next endpoint

    # All endpoints failed — return fallback
    fallback = FALLBACK_MF_DATA.get(int(scheme_code), {
        "scheme_name":      "Benchmark Fund (offline data)",
        "avg_daily_return": 0.0004,
        "risk":             0.007,
    })
    return {**fallback, "source": "fallback"}


def select_scheme_by_risk(risk_level):
    schemes = {
        "Conservative": {
            "code":     119551,
            "category": "Short Duration Debt Fund",
        },
        "Moderate": {
            "code":     102885,
            "category": "Balanced Advantage / Dynamic Asset Allocation",
        },
        "Aggressive": {
            "code":     120503,
            "category": "Flexi Cap Equity Fund",
        },
    }
    return schemes.get(risk_level, schemes["Moderate"])