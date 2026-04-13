from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field, field_validator


SUPPORTED_CURRENCIES = {"USD", "EUR", "GBP", "INR", "JPY", "AUD", "CAD"}


class StoreOnboardingRequest(BaseModel):
    country_code: str = Field(min_length=2, max_length=2)
    store_name: str = Field(min_length=3, max_length=80)
    default_language: str = Field(min_length=2, max_length=10)
    currency: str = Field(min_length=3, max_length=3)
    tax_rate: float = Field(ge=0, le=1)
    enabled_features: List[str] = Field(default_factory=list)
    marketplace_domain: str = Field(min_length=4, max_length=100)

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(cls, value: str) -> str:
        return value.upper()

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        value = value.upper()
        if value not in SUPPORTED_CURRENCIES:
            raise ValueError("currency is not supported")
        return value


class StoreConfiguration(BaseModel):
    country_code: str
    store_name: str
    default_language: str
    currency: str
    tax_rate: float
    enabled_features: List[str]
    marketplace_domain: str
    status: str


class FeatureToggleRequest(BaseModel):
    enabled: bool


class AuditEvent(BaseModel):
    action: str
    country_code: str
    details: Dict[str, str]


class MetricsSnapshot(BaseModel):
    onboard_success: int
    onboard_failure: int
    feature_toggle_count: int
    configured_countries: int
