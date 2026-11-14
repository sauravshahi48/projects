-- Run by analyze.py after loading the synthetic transactions into SQLite.
-- Count transactions at or before the current second within each window.
WITH velocity AS (
    SELECT *,
        SUM(CASE WHEN amount_paise <= 5000 THEN 1 ELSE 0 END) OVER (
            PARTITION BY customer_id, merchant_id ORDER BY txn_second
            RANGE BETWEEN 299 PRECEDING AND CURRENT ROW
        ) AS pair_micro_5m,
        COUNT(*) OVER (
            PARTITION BY merchant_id ORDER BY txn_second
            RANGE BETWEEN 599 PRECEDING AND CURRENT ROW
        ) AS merchant_txns_10m
    FROM transactions
)
SELECT t.transaction_id, t.txn_second, t.customer_id, t.merchant_id,
       m.category, t.amount_paise, t.pair_micro_5m, t.merchant_txns_10m
FROM velocity t
JOIN merchants m ON t.merchant_id = m.merchant_id
ORDER BY t.txn_second, t.transaction_id;
