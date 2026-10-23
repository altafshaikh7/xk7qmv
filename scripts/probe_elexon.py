import json
from collections import Counter
import requests

BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"

def get(dataset, params):
    resp = requests.get(f"{BASE}/{dataset}/stream", params=params, timeout=60)
    print("\nGET", resp.url, "-> status", resp.status_code)
    resp.raise_for_status()
    return resp.json()

actuals = get("FUELHH", {
    "settlementDateFrom": "2026-01-01",
    "settlementDateTo": "2026-01-02",
    "fuelType": "WIND",
})
print("ACTUALS records:", len(actuals))
if actuals:
    print("keys:", list(actuals[0].keys()))
    print("first:", json.dumps(actuals[0], indent=2))
    print("fuelTypes:", Counter(r.get("fuelType") for r in actuals))

forecasts = get("WINDFOR", {
    "publishDateTimeFrom": "2025-12-31T00:00:00Z",
    "publishDateTimeTo": "2025-12-31T12:00:00Z",
})
print("\nFORECAST records:", len(forecasts))
if forecasts:
    print("keys:", list(forecasts[0].keys()))
    print("first:", json.dumps(forecasts[0], indent=2))
    pubs = sorted({r["publishTime"] for r in forecasts})
    print("distinct publishTimes:", len(pubs), "| first 3:", pubs[:3])
    per_target = Counter(r["startTime"] for r in forecasts)
    print("forecasts per startTime (min/max):", min(per_target.values()), max(per_target.values()))
