from __future__ import annotations

from fastapi import FastAPI

from .models import FeatureToggleRequest, MetricsSnapshot, StoreConfiguration, StoreOnboardingRequest
from .services import StoreRegistry


app = FastAPI(title="Global Store Expansion Platform", version="1.0.0")
registry = StoreRegistry()


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/stores/onboard", response_model=StoreConfiguration, status_code=201)
def onboard_store(payload: StoreOnboardingRequest) -> StoreConfiguration:
    return registry.onboard_store(payload)


@app.get("/stores/{country_code}", response_model=StoreConfiguration)
def get_store(country_code: str) -> StoreConfiguration:
    return registry.get_store(country_code)


@app.post("/stores/{country_code}/features/{feature_key}", response_model=StoreConfiguration)
def toggle_feature(country_code: str, feature_key: str, payload: FeatureToggleRequest) -> StoreConfiguration:
    return registry.toggle_feature(country_code, feature_key, payload)


@app.get("/audit/events")
def audit_events() -> list[dict]:
    return [event.model_dump() for event in registry.list_audit_events()]


@app.get("/metrics", response_model=MetricsSnapshot)
def metrics() -> MetricsSnapshot:
    return registry.metrics()
