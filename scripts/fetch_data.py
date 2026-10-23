"""Fetch Jan 2026 wind actuals (FUELHH) and forecasts (WINDFOR) from Elexon.

Saves CSV snapshots to backend/data/. Run from repo root:
    python scripts/fetch_data.py
"""
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
OUT = Path(__file__).resolve().parent.parent / "backend" / "data"
OUT.mkdir(parents=True, exist_ok=True)

# Delivery days: January 2026. Forecasts for D are published from D-2 onwards,
# so we fetch publishes from 30 Dec 2025 to 31 Jan 2026.
DELIVERY_START = date(2026, 1, 2)
DELIVERY_END = date(2026, 2, 1)
PUBLISH_START = datetime(2025, 12, 30, tzinfo=timezone.utc)
PUBLISH_END = datetime(2026, 2, 1, tzinfo=timezone.utc)

# ASSUMPTION (unverified): day-ahead gate closure 09:20 UK time (= UTC in January).
CUTOFF_HM = (9, 20)


def fetch(dataset: str, params: dict) -> list:
    resp = requests.get(f"{BASE}/{dataset}/stream", params=params, timeout=120)
    resp.raise_for_status()
    return resp.json()


def fetch_actuals() -> pd.DataFrame:
    rows, a = [], DELIVERY_START
    while a <= DELIVERY_END:
        b = min(a + timedelta(days=6), DELIVERY_END)
        chunk = fetch("FUELHH", {
            "settlementDateFrom": a.isoformat(),
            "settlementDateTo": b.isoformat(),
            "fuelType": "WIND",
        })
        print(f"  FUELHH {a} -> {b}: {len(chunk)} rows")
        rows += chunk
        a = b + timedelta(days=1)
    df = pd.DataFrame(rows)
    df = df[df["fuelType"] == "WIND"]
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df = df.drop_duplicates(subset=["startTime"]).sort_values("startTime")
    return df[["startTime", "settlementDate", "settlementPeriod", "generation"]]


def fetch_forecasts() -> pd.DataFrame:
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    rows, a = [], PUBLISH_START
    while a < PUBLISH_END:
        b = min(a + timedelta(days=3), PUBLISH_END)
        chunk = fetch("WINDFOR", {
            "publishDateTimeFrom": a.strftime(fmt),
            "publishDateTimeTo": b.strftime(fmt),
        })
        print(f"  WINDFOR {a:%Y-%m-%d %H:%M} -> {b:%Y-%m-%d %H:%M}: {len(chunk)} rows")
        rows += chunk
        a = b
    df = pd.DataFrame(rows)
    df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True)
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df = df.drop_duplicates(subset=["publishTime", "startTime"])
    df = df.sort_values(["publishTime", "startTime"])
    return df[["publishTime", "startTime", "generation"]]


def validate(act: pd.DataFrame, fc: pd.DataFrame) -> None:
    print("\n=== VALIDATION ===")
    expected = pd.date_range("2026-01-02 00:00", "2026-02-01 23:30", freq="30min", tz="UTC")
    missing = expected.difference(pd.DatetimeIndex(act["startTime"]))
    print(f"Actuals: {len(act)} rows (expected {len(expected)}), missing half-hours: {len(missing)}")
    if len(missing):
        print("  first missing:", list(missing[:5]))
    print("Actuals generation min/max:", act["generation"].min(), act["generation"].max())
    print("Actuals nulls:", int(act["generation"].isna().sum()))

    print(f"Forecasts: {len(fc)} rows, {fc['publishTime'].nunique()} distinct publishTimes")
    print("Forecast nulls:", int(fc["generation"].isna().sum()))
    print("Publish times seen:", sorted(fc["publishTime"].dt.strftime("%H:%M").unique()))

    # Sanity preview only (final logic will live in backend/app/forecast_logic.py)
    print(f"\nCoverage check with cutoff {CUTOFF_HM[0]:02d}:{CUTOFF_HM[1]:02d} on D-1:")
    bad = 0
    for d in pd.date_range("2026-01-02", "2026-02-01", tz="UTC"):
        cutoff = d - pd.Timedelta(days=1) + pd.Timedelta(hours=CUTOFF_HM[0], minutes=CUTOFF_HM[1])
        avail = fc[fc["publishTime"] <= cutoff]
        if avail.empty:
            print(f"  {d.date()}: NO forecast available"); bad += 1; continue
        latest = avail["publishTime"].max()
        n = ((fc["publishTime"] == latest) & (fc["startTime"] >= d)
             & (fc["startTime"] < d + pd.Timedelta(days=1))).sum()
        if n != 24:
            print(f"  {d.date()}: latest publish {latest} covers only {n}/24 hours"); bad += 1
    print("  days with problems:", bad, "of 31")


if __name__ == "__main__":
    print("Fetching actuals...")
    actuals = fetch_actuals()
    print("Fetching forecasts...")
    forecasts = fetch_forecasts()
    actuals.to_csv(OUT / "actuals.csv", index=False)
    forecasts.to_csv(OUT / "forecasts.csv", index=False)
    print(f"\nSaved to {OUT}")
    validate(actuals, forecasts)

