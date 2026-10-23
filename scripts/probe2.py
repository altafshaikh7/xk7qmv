import requests, pandas as pd

BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
r = requests.get(f"{BASE}/WINDFOR/stream", params={
    "publishDateTimeFrom": "2025-12-31T00:00:00Z",
    "publishDateTimeTo": "2025-12-31T23:59:59Z",
}, timeout=60)
r.raise_for_status()
df = pd.DataFrame(r.json())
df["publishTime"] = pd.to_datetime(df["publishTime"])
df["startTime"] = pd.to_datetime(df["startTime"])
df["lead_h"] = (df["startTime"] - df["publishTime"]).dt.total_seconds() / 3600

print("rows:", len(df))
print("distinct publishTimes:", df["publishTime"].nunique())
print("lead hours  min/max:", df["lead_h"].min(), df["lead_h"].max())

p = df["publishTime"].min()
one = df[df["publishTime"] == p].sort_values("startTime")
print("\nOne publish:", p, "| targets:", len(one))
print("first/last target:", one["startTime"].iloc[0], one["startTime"].iloc[-1])
print("step between targets:", one["startTime"].diff().dropna().value_counts().head(3).to_dict())

print("\nPublish times of the day:")
print(sorted(df["publishTime"].dt.strftime("%H:%M").unique()))
