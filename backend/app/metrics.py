import numpy as np
import pandas as pd


def compute_metrics(df: pd.DataFrame) -> dict | None:
    """Accuracy metrics on a frame with 'forecast' and 'actual' columns (MW).
    Returns None for empty input. MAPE is deliberately avoided: wind can be near
    zero, which makes percentage error explode."""
    n = len(df)
    if n == 0:
        return None
    err = df["forecast"] - df["actual"]
    abs_err = err.abs()
    mean_actual = float(df["actual"].mean())
    return {
        "n_hours": int(n),
        "bias_mw": float(err.mean()),
        "mae_mw": float(abs_err.mean()),
        "rmse_mw": float(np.sqrt((err ** 2).mean())),
        "p50_abs_error_mw": float(abs_err.quantile(0.50)),
        "p90_abs_error_mw": float(abs_err.quantile(0.90)),
        "p95_abs_error_mw": float(abs_err.quantile(0.95)),
        "mean_actual_mw": mean_actual,
        "mae_pct_of_mean_actual": float(abs_err.mean() / mean_actual * 100) if mean_actual else None,
    }
