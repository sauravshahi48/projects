# Localized Checkout and Payment Routing Simulator

A Python payment-routing simulator that uses FastAPI for the simulation API, Flask for a lightweight operations dashboard, and SQLite-backed rules for configurable routing decisions.

## Stack

- Python
- FastAPI
- Flask
- SQLite
- SQL

## Highlights

- Simulates localized checkout routing using country, currency, and availability rules.
- Applies fallback routing when a preferred method is unavailable.
- Tracks success and failure metrics for route evaluations.
- Exposes a small Flask dashboard for reviewing configured methods and routing rules.

## Project Structure

- `api/main.py`: FastAPI endpoints
- `api/db.py`: SQLite setup and seed data
- `api/service.py`: rule lookup and routing logic
- `dashboard.py`: lightweight Flask dashboard
- `tests/test_api.py`: API tests

## Run

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload
python dashboard.py
```

Open `http://127.0.0.1:8000/docs` for the API and `http://127.0.0.1:5000` for the dashboard.

## API

- `POST /checkout/simulate`
- `GET /metrics`
- `GET /rules`

## Example Request

```bash
curl -X POST http://127.0.0.1:8000/checkout/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "DE",
    "currency": "EUR",
    "amount": 149.99
  }'
```

## Test

```bash
pytest
```

## Portfolio Talking Points

- Models configurable routing behavior with a SQL-backed rule table.
- Demonstrates fallback logic for real-world payment method availability issues.
- Surfaces operational thinking through validation, metrics, and route inspection.
