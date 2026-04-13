# Localized Checkout and Payment Routing Simulator

A Python payment-routing simulator that uses FastAPI for the simulation API, Flask for a lightweight operations dashboard, and SQLite-backed rules for configurable routing decisions.

## Highlights

- Simulates localized checkout routing using country, currency, and availability rules.
- Applies fallback routing when a preferred method is unavailable.
- Tracks success and failure metrics for route evaluations.
- Exposes a small Flask dashboard for reviewing configured methods and routing rules.

## Run

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload
python dashboard.py
```

## API

- `POST /checkout/simulate`
- `GET /metrics`
- `GET /rules`

## Test

```bash
pytest
```
