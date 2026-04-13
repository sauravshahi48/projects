from __future__ import annotations

from dataclasses import dataclass
from typing import List

from fastapi import HTTPException

from .db import get_connection
from .models import CheckoutSimulationRequest, CheckoutSimulationResponse, MetricsSnapshot


@dataclass
class RoutingMetrics:
    simulation_success: int = 0
    simulation_failure: int = 0


metrics = RoutingMetrics()


def fetch_rules(country_code: str, currency: str) -> List[dict]:
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT country_code, currency, payment_method, priority, available
        FROM routing_rules
        WHERE country_code = ? AND currency = ?
        ORDER BY priority ASC
        """,
        (country_code, currency),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    connection.close()
    return rows


def simulate_checkout(payload: CheckoutSimulationRequest) -> CheckoutSimulationResponse:
    rules = fetch_rules(payload.country_code, payload.currency)
    if not rules:
        metrics.simulation_failure += 1
        raise HTTPException(status_code=404, detail="no routing rules configured")

    primary = rules[0]
    if primary["available"]:
        metrics.simulation_success += 1
        return CheckoutSimulationResponse(
            selected_method=primary["payment_method"],
            fallback_used=False,
            reason="primary rule matched and payment method is available",
        )

    for candidate in rules[1:]:
        if candidate["available"]:
            metrics.simulation_success += 1
            return CheckoutSimulationResponse(
                selected_method=candidate["payment_method"],
                fallback_used=True,
                reason=f"fallback selected after {primary['payment_method']} was unavailable",
            )

    metrics.simulation_failure += 1
    raise HTTPException(status_code=503, detail="all configured payment methods are unavailable")


def get_metrics() -> MetricsSnapshot:
    return MetricsSnapshot(
        simulation_success=metrics.simulation_success,
        simulation_failure=metrics.simulation_failure,
    )
