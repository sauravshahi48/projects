# Global Store Expansion Platform

A FastAPI backend prototype for onboarding country-specific stores with regional configuration, validation, audit logging, and lightweight metrics.

## Stack

- Python
- FastAPI
- Pydantic
- REST APIs

## Highlights

- Onboards new country stores with language, currency, tax, and feature settings.
- Validates regional constraints before activation.
- Tracks onboarding attempts, failures, and feature toggles with in-memory metrics.
- Stores audit events for visibility into setup and rollout changes.

## Project Structure

- `app/main.py`: FastAPI routes
- `app/models.py`: request and response models
- `app/services.py`: onboarding, validation, metrics, and audit logic
- `tests/test_app.py`: API tests

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for Swagger UI.

## API

- `POST /stores/onboard`
- `GET /stores/{country_code}`
- `POST /stores/{country_code}/features/{feature_key}`
- `GET /audit/events`
- `GET /metrics`

## Example Request

```bash
curl -X POST http://127.0.0.1:8000/stores/onboard \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "IN",
    "store_name": "India Marketplace",
    "default_language": "en-IN",
    "currency": "INR",
    "tax_rate": 0.18,
    "enabled_features": ["catalog", "checkout", "wallets"],
    "marketplace_domain": "india.example.com"
  }'
```

## Test

```bash
pytest
```

## Portfolio Talking Points

- Demonstrates backend API design for multi-region product expansion.
- Shows configuration validation and rollout-safety checks.
- Includes observability concepts like metrics and audit events.
