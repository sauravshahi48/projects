from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_store_onboarding_and_metrics() -> None:
    payload = {
        "country_code": "in",
        "store_name": "India Marketplace",
        "default_language": "en-IN",
        "currency": "INR",
        "tax_rate": 0.18,
        "enabled_features": ["catalog", "checkout", "wallets"],
        "marketplace_domain": "india.example.com",
    }

    response = client.post("/stores/onboard", json=payload)
    assert response.status_code == 201
    assert response.json()["country_code"] == "IN"

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert metrics.json()["onboard_success"] == 1


def test_rejects_missing_required_features() -> None:
    payload = {
        "country_code": "fr",
        "store_name": "France Marketplace",
        "default_language": "fr-FR",
        "currency": "EUR",
        "tax_rate": 0.2,
        "enabled_features": ["catalog"],
        "marketplace_domain": "france.example.com",
    }

    response = client.post("/stores/onboard", json=payload)
    assert response.status_code == 400
    assert "missing required features" in response.json()["detail"]
