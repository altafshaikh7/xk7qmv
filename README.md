# Wind Forecast Decision Support

Web app for the day-ahead power buying team of a UK energy utility. It shows which national wind generation forecast was available at decision time, and quantifies how accurate that forecast is against actual generation, so purchase decisions can account for the measured error.

**Live app:** TODO_ADD_VERCEL_OR_HEROKU_LINK_HERE

## Problem and scope

The utility buys electricity on the UK day-ahead market one day before delivery. Wind output is weather dependent, so the amount of power to buy from other sources (for example thermal plants) depends on wind forecasts. The app helps the team to:

1. Understand the latest wind forecast available when the day-ahead decision has to be made.
2. Evaluate forecast accuracy quantitatively.

Scope, as defined in the brief:

- Data: Elexon BMRS only, national level, no other data.
  - Actuals: FUELHH dataset, `fuelType = WIND`, fields `startTime` and `generation`.
  - Forecasts: WINDFOR dataset, fields `startTime`, `publishTime` and `generation`.
- Purchase decisions made in January 2026. Decisions are made on D-1, so the delivery days covered are **2 Jan 2026 to 1 Feb 2026** (31 days, 744 hours).

## How it works

1. For a delivery day D, the decision cutoff is D-1 at a configurable UK local time (default 09:20).
2. For each target hour of D, the latest forecast with `publishTime <= cutoff` is selected. Forecasts published after the cutoff are never used, so there is no look-ahead leakage.
3. WINDFOR is hourly and FUELHH is half-hourly. Each actual hour is the mean of its two half-hourly values (generation is power in MW). Hours with a missing half-hour are dropped.
4. Error = forecast minus actual. Positive means the forecast was too high (wind over-counted, so risk of buying too little from other sources).
5. Metrics: bias, MAE, RMSE, P50/P90/P95 absolute error, and MAE as a percentage of mean actual. MAPE is deliberately not used because wind output can be close to zero, which makes percentage error unstable.

## Dashboard

- **Decision day:** pick a delivery day and cutoff. Shows the publish time of the latest forecast available, forecast vs actual chart, hourly error chart, and accuracy cards for that day.
- **Month overview:** overall accuracy cards, daily MAE and bias chart, and error by hour of day.

## Results (January 2026, default 09:20 cutoff)

Taken from the app's `/api/metrics` output:

| Metric | Value |
|---|---|
| Hours evaluated | 744 |
| Bias (forecast minus actual) | +1,748 MW |
| MAE | 2,039 MW (18.1% of mean actual) |
| RMSE | 2,505 MW |
| P90 absolute error | 4,098 MW |
| P95 absolute error | 5,283 MW |

In this dataset the forecast was higher than actual on average, and on several days (for example 11, 12 and 28 Jan) in every hour.

## Assumptions and limitations

- The 09:20 UK time cutoff is an assumption (day-ahead gate closure), not from the brief. It is configurable in the UI and through the `DEFAULT_CUTOFF` environment variable. The client should set its real deadline.
- Averaging two half-hours into one hour is a design decision, not specified in the brief.
- The consistent positive bias was observed but its cause was not investigated (for example, the two datasets may define wind generation differently).
- Metrics are computed on the same month they describe, so they are indicative, not a guarantee of future accuracy.
- Only wind, only January 2026 decisions. No demand or price data, and no forecasting model.
- Data is a fixed snapshot stored in the repo (see "Refresh the data"), so the app does not depend on Elexon being available at runtime.
- Timestamps are UTC. In January UK local time equals UTC.

## Project structure

```
backend/
  app/
    __init__.py
    config.py             data directory, market timezone, default cutoff
    forecast_logic.py     cutoff selection, hourly join of forecast and actual
    metrics.py            accuracy metrics
    main.py               FastAPI app and endpoints
  data/
    actuals.csv           FUELHH wind actuals snapshot (2 Jan to 1 Feb 2026)
    forecasts.csv         WINDFOR forecasts snapshot (with publishTime)
  tests/
    test_logic.py         unit tests for cutoff, hourly actuals and metrics
  Dockerfile
  .dockerignore
  requirements.txt        runtime dependencies
  requirements-dev.txt    test dependencies
frontend/
  src/
    main.jsx              React entry point
    App.jsx               controls, loading and error states
    DayView.jsx           decision day view
    MonthView.jsx         month overview
    api.js                API client
    ui.jsx                formatters and Card component
    styles.css
  index.html
  vite.config.js          dev server with proxy to the backend
  package.json
  package-lock.json
  nginx.conf              serves the built app and proxies /api to the backend
  Dockerfile
  .dockerignore
scripts/
  fetch_data.py           downloads the January snapshot from Elexon
  probe_elexon.py         inspects Elexon response shapes
  probe2.py               checks forecast horizon and resolution
docker-compose.yml
README.md
.gitignore
```

## API

| Endpoint | Description |
|---|---|
| `GET /api/health` | Service status and loaded row counts |
| `GET /api/config` | Default cutoff, timezone, valid delivery days |
| `GET /api/day?date=YYYY-MM-DD&cutoff=HH:MM` | One delivery day: hourly forecast vs actual, forecast publish time, metrics |
| `GET /api/metrics?cutoff=HH:MM` | Overall metrics, daily MAE and bias, error by hour of day |

Invalid dates or cutoffs return HTTP 422. Interactive API docs are available at `/docs` when the backend is running.

## How to start the application

### Option 1: Docker (recommended)

Requires Docker with Compose.

```
docker compose up --build
```

Open http://localhost:8080. The frontend (nginx) proxies `/api` to the backend container.

### Option 2: Run locally without Docker

Requires Python 3.12+ and Node.js 20+ (developed with Python 3.14 and Node 24).

Backend, from the `backend/` folder:

```
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux:        source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Frontend, from the `frontend/` folder, in a second terminal:

```
npm install
npm run dev
```

Open http://localhost:5173. The Vite dev server proxies `/api` to http://127.0.0.1:8000.

### Configuration

| Variable | Default | Purpose |
|---|---|---|
| `DEFAULT_CUTOFF` | `09:20` | Default decision cutoff, UK local time (`HH:MM`) |
| `DATA_DIR` | `backend/data` | Folder containing `actuals.csv` and `forecasts.csv` |
| `VITE_API_BASE` | empty | Frontend build-time API base URL, when the API is hosted separately |

## Tests

From the `backend/` folder:

```
pip install -r requirements-dev.txt
python -m pytest -v
```

The tests cover: a forecast published after the cutoff is not used, a forecast published exactly at the cutoff is used, no forecast before the cutoff gives an empty result, the cutoff is on D-1, invalid cutoff input is rejected, hourly actual averaging and dropping incomplete hours, and metric values on known inputs.

## Refresh the data

From the repo root (needs `requests` and `pandas`):

```
python scripts/fetch_data.py
```

This fetches FUELHH (WIND) and WINDFOR from the Elexon BMRS API and rewrites the CSV files in `backend/data/`.

## Deployment

TODO_DESCRIBE_DEPLOYMENT (platform, what is deployed where, link to the live app above)

## AI tools used

This project was built with the assistance of Claude (Anthropic) for planning, code generation, debugging and documentation. The author ran the code and reviewed the results.
