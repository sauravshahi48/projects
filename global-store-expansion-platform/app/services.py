from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from fastapi import HTTPException

from .models import (
    AuditEvent,
    FeatureToggleRequest,
    MetricsSnapshot,
    StoreConfiguration,
    StoreOnboardingRequest,
)


REQUIRED_FEATURES = {"catalog", "checkout"}


@dataclass
class StoreRegistry:
    stores: Dict[str, StoreConfiguration] = field(default_factory=dict)
    audit_events: List[AuditEvent] = field(default_factory=list)
    onboard_success: int = 0
    onboard_failure: int = 0
    feature_toggle_count: int = 0

    def validate_request(self, payload: StoreOnboardingRequest) -> None:
        missing = REQUIRED_FEATURES.difference(payload.enabled_features)
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"missing required features: {', '.join(sorted(missing))}",
            )
        if payload.marketplace_domain.count(".") < 1:
            raise HTTPException(status_code=400, detail="marketplace_domain must be valid")

    def onboard_store(self, payload: StoreOnboardingRequest) -> StoreConfiguration:
        try:
            self.validate_request(payload)
        except HTTPException:
            self.onboard_failure += 1
            raise

        configuration = StoreConfiguration(
            country_code=payload.country_code,
            store_name=payload.store_name,
            default_language=payload.default_language,
            currency=payload.currency,
            tax_rate=payload.tax_rate,
            enabled_features=sorted(set(payload.enabled_features)),
            marketplace_domain=payload.marketplace_domain,
            status="active",
        )
        self.stores[payload.country_code] = configuration
        self.audit_events.append(
            AuditEvent(
                action="store_onboarded",
                country_code=payload.country_code,
                details={"store_name": payload.store_name, "currency": payload.currency},
            )
        )
        self.onboard_success += 1
        return configuration

    def get_store(self, country_code: str) -> StoreConfiguration:
        country_code = country_code.upper()
        if country_code not in self.stores:
            raise HTTPException(status_code=404, detail="store configuration not found")
        return self.stores[country_code]

    def toggle_feature(self, country_code: str, feature_key: str, payload: FeatureToggleRequest) -> StoreConfiguration:
        store = self.get_store(country_code)
        features = set(store.enabled_features)
        if payload.enabled:
            features.add(feature_key)
        else:
            features.discard(feature_key)
        store.enabled_features = sorted(features)
        self.feature_toggle_count += 1
        self.audit_events.append(
            AuditEvent(
                action="feature_toggled",
                country_code=store.country_code,
                details={"feature_key": feature_key, "enabled": str(payload.enabled).lower()},
            )
        )
        return store

    def list_audit_events(self) -> List[AuditEvent]:
        return self.audit_events

    def metrics(self) -> MetricsSnapshot:
        return MetricsSnapshot(
            onboard_success=self.onboard_success,
            onboard_failure=self.onboard_failure,
            feature_toggle_count=self.feature_toggle_count,
            configured_countries=len(self.stores),
        )
