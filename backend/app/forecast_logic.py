"""Core logic: which forecast was available at decision time, and how it compares to actuals."""
from datetime import date, timedelta

import pandas as pd

from .config import DATA_DIR, MARKET_TZ


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    actuals = pd.read_csv(DATA_DIR / "actuals.csv")
    forecasts = pd.read_csv(DATA_DIR / "forecasts.csv")
    actuals["startTime"] = pd.to_datetime(actuals["startTime"], utc=True)
    forecasts["publishTime"] = pd.to_datetime(forecasts["publishTime"], utc=True)
    forecasts["startTime"] = pd.to_datetime(forecasts["startTime"], utc=True)
    return actuals, forecasts


def parse_cutoff(cutoff: str) -> tuple[int, int]:
    try:
        h, m = cutoff.split(":")
        h, m = int(h), int(m)
    except ValueError:
        raise ValueError(f"cutoff must look like 'HH:MM', got {cutoff!r}")
    if not (0 <= h < 24 and 0 <= m < 60):
        raise ValueError(f"cutoff out of range: {cutoff!r}")
    return h, m


def cutoff_timestamp(delivery_day: date, cutoff: str) -> pd.Timestamp:
    """Decision cutoff = D-1 at `cutoff` UK local time, returned in UTC."""
    h, m = parse_cutoff(cutoff)
    d1 = delivery_day - timedelta(days=1)
    local = pd.Timestamp(d1.year, d1.month, d1.day, h, m, tz=MARKET_TZ)
    return local.tz_convert("UTC")


def day_bounds(delivery_day: date) -> tuple[pd.Timestamp, pd.Timestamp]:
    """[start, end) of the delivery day in UTC (UK local midnight to midnight)."""
    start = pd.Timestamp(delivery_day.year, delivery_day.month, delivery_day.day, tz=MARKET_TZ)
    nxt = delivery_day + timedelta(days=1)
    end = pd.Timestamp(nxt.year, nxt.month, nxt.day, tz=MARKET_TZ)
    return start.tz_convert("UTC"), end.tz_convert("UTC")


def select_forecast(forecasts: pd.DataFrame, delivery_day: date, cutoff: str) -> pd.DataFrame:
    """For each target hour of the delivery day, pick the latest forecast with
    publishTime <= cutoff. Forecasts published after the cutoff are never used
    (no look-ahead leakage)."""
    cutoff_ts = cutoff_timestamp(delivery_day, cutoff)
    start, end = day_bounds(delivery_day)
    w = forecasts[
        (forecasts["publishTime"] <= cutoff_ts)
        & (forecasts["startTime"] >= start)
        & (forecasts["startTime"] < end)
    ]
    w = w.sort_values("publishTime").groupby("startTime", as_index=False).last()
    w = w.rename(columns={"generation": "forecast"})
    return w[["startTime", "forecast", "publishTime"]].sort_values("startTime").reset_index(drop=True)


def hourly_actuals(actuals: pd.DataFrame) -> pd.DataFrame:
    """Forecasts are hourly, actuals half-hourly. Generation is power (MW), so the
    hourly value is the mean of the two half-hours. Incomplete hours are dropped."""
    a = actuals.copy()
    a["hour"] = a["startTime"].dt.floor("h")
    g = a.groupby("hour")["generation"].agg(["mean", "count"]).reset_index()
    g = g[g["count"] == 2]
    return g.rename(columns={"hour": "startTime", "mean": "actual"})[["startTime", "actual"]]


def compare(actuals: pd.DataFrame, forecasts: pd.DataFrame, delivery_day: date, cutoff: str) -> pd.DataFrame:
    """Hourly forecast vs actual for one delivery day. Error = forecast - actual."""
    sel = select_forecast(forecasts, delivery_day, cutoff)
    df = sel.merge(hourly_actuals(actuals), on="startTime", how="inner")
    df["error"] = df["forecast"] - df["actual"]
    df["lead_hours"] = (df["startTime"] - df["publishTime"]).dt.total_seconds() / 3600
    return df
