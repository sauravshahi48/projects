# UPI Micro-Transaction & Merchant Fraud Anomaly Tracker

Prioritize suspicious payment activity for analyst review. The pipeline checks for repeated small payments, sudden merchant volume, and unusually high amounts for the merchant category.

## Dataset source

**Project-generated synthetic UPI-style transactions.** The fixed-seed generator in `analyze.py` produces 30 days of fictional rupee payments across 32 fictional merchants. It includes legitimate purchase bursts and three labeled simulated patterns: repeated micro-payments, merchant bursts, and high amounts. No actual customer, merchant, bank, or NPCI transaction records are used.

## Method

1. Load integer-paise transactions and merchant categories into SQLite. Window functions calculate five-minute micro-payment counts per customer–merchant pair and ten-minute counts per merchant. Counts include the current transaction second.
2. Fit category medians and median absolute deviations on days 1–18. Score days 19–30 using fixed rules: at least four micro-payments of ₹50 or less in five minutes, at least nine merchant transactions in ten minutes, or a category-adjusted high amount with a robust z-score of 4.5 or higher.
3. Rank merchants using 2 points for the micro-payment rule, 1 for merchant velocity, and 2 for the high-amount rule. Review priority is the points total divided by five times (transaction count + 20), multiplied by 100. The 20-transaction adjustment shrinks small samples. Higher scores warrant earlier review.

## Results

| Metric | Value |
| --- | ---: |
| Simulated transactions | 12,991 |
| Later-period transactions evaluated | 5,414 |
| Injected transactions in evaluation | 367 |
| Alerts raised | 343 |
| True positives / false positives / false negatives | 199 / 144 / 168 |
| Precision / recall against injected scenarios | 58.0% / 54.2% |

Thresholds are illustrative. Injected labels measure how the rules find the patterns defined in the generator. Merchant review priority is a heuristic score.

Run `python analyze.py` from this directory. See `output/transaction_alerts.csv`, `output/merchant_risk.csv` and `output/metrics.json`.
