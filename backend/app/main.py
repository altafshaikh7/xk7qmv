from datetime import date, timedelta

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import DEFAULT_CUTOFF, MARKET_TZ
from .forecast_logic import compare, cutoff_timestamp, load_data, parse_cutoff
from .metrics import compute_metrics

FIRST_DAY = date(2026, 1, 2)   # decision on 1 Jan (D-1)
LAST_DAY = date(2026, 2, 1)    # decision on 31 Jan (D-1)

app = FastAPI(title="Wind Forecast Decision Support")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])

ACTUALS, FORECASTS = load_data()


def _iso(ts: pd.Timestamp) -> str:
    return ts.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")


def _check_cutoff(cutoff: str) -> None:
    try:
        parse_cutoff(cutoff)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


def _days():
    d = FIRST_DAY
    while d <= LAST_DAY:
        yield d
        d += timedelta(days=1)


@app.get("/api/health")
def health():
    return {"status": "ok", "actual_rows": len(ACTUALS), "forecast_rows": len(FORECASTS)}


@app.get("/api/config")
def config():
    return {
        "default_cutoff": DEFAULT_CUTOFF,
        "market_timezone": MARKET_TZ,
        "first_delivery_day": FIRST_DAY.isoformat(),
        "last_delivery_day": LAST_DAY.isoformat(),
    }


@app.get("/api/day")
def day(date_: date = Query(alias="date"), cutoff: str = DEFAULT_CUTOFF):
    if not (FIRST_DAY <= date_ <= LAST_DAY):
        raise HTTPException(status_code=422, detail=f"date must be between {FIRST_DAY} and {LAST_DAY}")
    _check_cutoff(cutoff)
    df = compare(ACTUALS, FORECASTS, date_, cutoff)
    if df.empty:
        raise HTTPException(status_code=404, detail="No forecast available before the cutoff for this day")
    rows = [
        {
            "time": _iso(r.startTime),
            "forecast_mw": float(r.forecast),
            "actual_mw": float(r.actual),
            "error_mw": float(r.error),
            "forecast_published": _iso(r.publishTime),
            "lead_hours": float(r.lead_hours),
        }
        for r in df.itertuples()
    ]
    return {
        "delivery_day": date_.isoformat(),
        "cutoff_utc": _iso(cutoff_timestamp(date_, cutoff)),
        "cutoff_local": cutoff,
        "latest_forecast_published": _iso(df["publishTime"].max()),
        "hours": rows,
        "metrics": compute_metrics(df),
    }


@app.get("/api/metrics")
def metrics(cutoff: str = DEFAULT_CUTOFF):
    _check_cutoff(cutoff)
    frames, daily = [], []
    for d in _days():
        df = compare(ACTUALS, FORECASTS, d, cutoff)
        if df.empty:
            continue
        df = df.assign(delivery_day=d.isoformat(), hour=df["startTime"].dt.hour)
        frames.append(df)
        daily.append({
            "date": d.isoformat(),
            "mae_mw": float(df["error"].abs().mean()),
            "bias_mw": float(df["error"].mean()),
        })
    if not frames:
        raise HTTPException(status_code=404, detail="No data for this cutoff")
    all_df = pd.concat(frames, ignore_index=True)
    by_hour = [
        {"hour_utc": int(h), **compute_metrics(g)}
        for h, g in all_df.groupby("hour")
    ]
    return {
        "cutoff_local": cutoff,
        "days_covered": len(daily),
        "overall": compute_metrics(all_df),
        "daily": daily,
        "by_hour": by_hour,
    }
