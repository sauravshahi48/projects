# Global Store Expansion Platform

A FastAPI backend prototype for onboarding country-specific stores with regional configuration, validation, audit logging, and lightweight metrics.

## Highlights

- Onboards new country stores with language, currency, tax, and feature settings.
- Validates regional constraints before activation.
- Tracks onboarding attempts, failures, and feature toggles with in-memory metrics.
- Stores audit events for visibility into setup and rollout changes.

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API

- `POST /stores/onboard`
- `GET /stores/{country_code}`
- `POST /stores/{country_code}/features/{feature_key}`
- `GET /audit/events`
- `GET /metrics`

## Test

```bash
pytest
```
