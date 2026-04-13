from __future__ import annotations

from fastapi import FastAPI

from .db import initialize_database
from .models import CheckoutSimulationRequest, CheckoutSimulationResponse, MetricsSnapshot
from .service import fetch_rules, get_metrics, simulate_checkout


app = FastAPI(title="Localized Checkout and Payment Routing Simulator", version="1.0.0")
initialize_database()


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/checkout/simulate", response_model=CheckoutSimulationResponse)
def checkout_simulation(payload: CheckoutSimulationRequest) -> CheckoutSimulationResponse:
    return simulate_checkout(payload)


@app.get("/metrics", response_model=MetricsSnapshot)
def metrics() -> MetricsSnapshot:
    return get_metrics()


@app.get("/rules")
def rules() -> list[dict]:
    return fetch_rules("IN", "INR") + fetch_rules("DE", "EUR") + fetch_rules("US", "USD")
