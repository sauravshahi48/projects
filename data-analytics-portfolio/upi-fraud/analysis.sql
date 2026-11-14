-- Compare average daily volume with the preceding six months' baseline.
-- The window excludes the month being scored.
WITH normalized AS (
    SELECT
        month,
        transaction_count,
        value_inr,
        CAST(strftime('%d', date(month, 'start of month', '+1 month', '-1 day')) AS INTEGER) AS month_days
    FROM upi_monthly
),
daily AS (
    SELECT *,
        1.0 * transaction_count / month_days AS daily_transactions,
        1.0 * value_inr / transaction_count AS average_payment_inr
    FROM normalized
),
comparison AS (
    SELECT *,
        LAG(daily_transactions) OVER (ORDER BY month) AS previous_daily,
        LAG(daily_transactions, 12) OVER (ORDER BY month) AS prior_year_daily,
        COUNT(*) OVER baseline AS baseline_months,
        AVG(daily_transactions) OVER baseline AS baseline_daily
    FROM daily
    WINDOW baseline AS (ORDER BY month ROWS BETWEEN 6 PRECEDING AND 1 PRECEDING)
),
changes AS (
    SELECT *,
        CASE WHEN baseline_months = 6 THEN (daily_transactions / baseline_daily - 1) * 100 END AS baseline_gap_pct
    FROM comparison
)
SELECT
    substr(month, 1, 7) AS month,
    month_days,
    transaction_count,
    value_inr,
    ROUND(daily_transactions) AS avg_daily_transactions,
    ROUND(average_payment_inr, 2) AS avg_payment_inr,
    ROUND((daily_transactions / previous_daily - 1) * 100, 2) AS daily_volume_mom_pct,
    ROUND((daily_transactions / prior_year_daily - 1) * 100, 2) AS daily_volume_yoy_pct,
    baseline_months,
    CASE WHEN baseline_months = 6 THEN ROUND(baseline_daily) END AS prior_six_month_avg_daily,
    ROUND(baseline_gap_pct, 2) AS baseline_gap_pct,
    CASE
        WHEN baseline_gap_pct IS NULL THEN 'Insufficient history'
        WHEN baseline_gap_pct >= :threshold THEN 'Above baseline'
        WHEN baseline_gap_pct <= -:threshold THEN 'Below baseline'
        ELSE 'Within threshold'
    END AS volume_flag
FROM changes
ORDER BY month;
