from datetime import date

import pandas as pd
import pytest

from app.forecast_logic import cutoff_timestamp, hourly_actuals, parse_cutoff, select_forecast
from app.metrics import compute_metrics


def ts(s):
    return pd.Timestamp(s, tz="UTC")


def test_forecast_after_cutoff_is_not_used():
    fc = pd.DataFrame({
        "publishTime": [ts("2026-01-04 07:30"), ts("2026-01-04 09:30")],
        "startTime": [ts("2026-01-05 00:00"), ts("2026-01-05 00:00")],
        "generation": [100, 999],
    })
    out = select_forecast(fc, date(2026, 1, 5), "09:20")
    assert out["forecast"].iloc[0] == 100
    assert out["publishTime"].iloc[0] == ts("2026-01-04 07:30")


def test_forecast_published_exactly_at_cutoff_is_used():
    fc = pd.DataFrame({
        "publishTime": [ts("2026-01-04 09:20")],
        "startTime": [ts("2026-01-05 00:00")],
        "generation": [123],
    })
    assert len(select_forecast(fc, date(2026, 1, 5), "09:20")) == 1


def test_no_forecast_before_cutoff_gives_empty():
    fc = pd.DataFrame({
        "publishTime": [ts("2026-01-04 10:00")],
        "startTime": [ts("2026-01-05 00:00")],
        "generation": [1],
    })
    assert select_forecast(fc, date(2026, 1, 5), "09:20").empty


def test_cutoff_is_previous_day():
    assert cutoff_timestamp(date(2026, 1, 5), "09:20") == ts("2026-01-04 09:20")


def test_invalid_cutoff_rejected():
    with pytest.raises(ValueError):
        parse_cutoff("25:99")
    with pytest.raises(ValueError):
        parse_cutoff("abc")


def test_hourly_actuals_average_and_drop_incomplete():
    act = pd.DataFrame({
        "startTime": [ts("2026-01-05 00:00"), ts("2026-01-05 00:30"), ts("2026-01-05 01:00")],
        "generation": [100, 200, 300],
    })
    out = hourly_actuals(act)
    assert len(out) == 1
    assert out["actual"].iloc[0] == 150


def test_metrics_known_values():
    df = pd.DataFrame({"forecast": [110, 90, 130], "actual": [100, 100, 100]})
    m = compute_metrics(df)
    assert m["bias_mw"] == pytest.approx(10.0)
    assert m["mae_mw"] == pytest.approx(50 / 3)
    assert m["rmse_mw"] == pytest.approx((1100 / 3) ** 0.5)


def test_metrics_empty_returns_none():
    assert compute_metrics(pd.DataFrame({"forecast": [], "actual": []})) is None
