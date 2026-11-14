-- Use only matched financial years with all twelve months of UPI totals.
WITH dated AS (
    SELECT *,
        CAST(substr(month, 1, 4) AS INTEGER)
          - CASE WHEN substr(month, 6, 2) < '04' THEN 1 ELSE 0 END AS fy_start
    FROM upi_monthly
),
annual AS (
    SELECT
        printf('%04d-%02d', fy_start, (fy_start + 1) % 100) AS financial_year,
        COUNT(*) AS months_covered,
        SUM(transaction_count) AS transaction_count,
        SUM(value_inr) AS value_inr
    FROM dated
    GROUP BY fy_start
    HAVING COUNT(*) = 12
)
SELECT
    f.financial_year,
    a.months_covered,
    a.transaction_count,
    a.value_inr,
    f.reported_incidents,
    f.reported_amount_inr,
    ROUND(1000000.0 * f.reported_incidents / a.transaction_count, 4)
        AS reported_incidents_per_million_transactions,
    ROUND(10000.0 * f.reported_amount_inr / a.value_inr, 4)
        AS reported_amount_basis_points,
    ROUND(1.0 * f.reported_amount_inr / f.reported_incidents, 2)
        AS reported_inr_per_incident
FROM upi_fraud f
JOIN annual a USING (financial_year)
ORDER BY f.financial_year;
