from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_selects_primary_available_method() -> None:
    response = client.post(
        "/checkout/simulate",
        json={"country_code": "IN", "currency": "INR", "amount": 1200},
    )
    assert response.status_code == 200
    assert response.json()["selected_method"] == "upi"
    assert response.json()["fallback_used"] is False


def test_returns_not_found_for_unknown_route() -> None:
    response = client.post(
        "/checkout/simulate",
        json={"country_code": "BR", "currency": "BRL", "amount": 400},
    )
    assert response.status_code == 404
