from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class CheckoutSimulationRequest(BaseModel):
    country_code: str = Field(min_length=2, max_length=2)
    currency: str = Field(min_length=3, max_length=3)
    amount: float = Field(gt=0)

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(cls, value: str) -> str:
        return value.upper()

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class CheckoutSimulationResponse(BaseModel):
    selected_method: str
    fallback_used: bool
    reason: str


class MetricsSnapshot(BaseModel):
    simulation_success: int
    simulation_failure: int
