# UPI Payment Anomaly & Reported Fraud Tracker

Analyze real national UPI payment volumes, transaction values, and reported fraud using Python and SQLite. The monthly analysis flags large changes in payment activity. The annual analysis compares reported fraud with the amount of UPI activity in the same financial year.

## Dataset sources

| File | Coverage | Publisher |
| --- | --- | --- |
| `data/upi_monthly.csv` | 63 months, April 2020 to June 2025, with national UPI transaction count and rupee value in crore | Ministry of Finance, Lok Sabha Question 3493, Annexure II, 11 August 2025. [Source](https://sansad.in/getFile/loksabhaquestions/annex/185/AU3493_IxuDsb.pdf?source=pqals) |
| `data/reported_upi_fraud.csv` | Five complete financial years, 2020–21 to 2024–25, with RBI-reported incident counts in lakh and amounts involved in crore rupees | Ministry of Finance, Rajya Sabha Questions 388 and 3610. [2024 reply](https://rsdebate.nic.in/bitstream/123456789/747527/1/PQ_263_06022024_U388_p331_p332.pdf) · [2026 reply](https://sansad.in/getFile/annex/270/AU3610_lsAdtZ.pdf?source=pqars) |

The CSVs transcribe the published figures at their reported precision. The FY 2025–26 fraud entry is marked partial in the source. Annual rates use complete April-to-March periods with both payments and reported fraud totals.

## Run

From this directory, run `python analyze.py` with Python 3.10 or later. The two source CSVs are included and the script uses the Python standard library. To change the alert threshold, run `python analyze.py --threshold 30`.

| Output | Contents |
| --- | --- |
| `output/monthly_upi_metrics.csv` | Total payments, average daily count and ticket size, month-over-month and year-over-year changes, six-month baseline and volume flags |
| `output/financial_year_fraud_rates.csv` | Matched annual totals, reported incidents per million UPI payments, reported amount as basis points of payment value and average reported amount per incident |

## Method and findings

1. Python checks the source columns, period formats, positive payment totals, duplicate periods and missing months. It converts crore and lakh to base units for SQL.
2. SQL divides each month's count by its days and compares it with the mean daily count across the previous six months. The default flags an absolute gap of at least 25%. This threshold is a review rule. The baseline uses only months before the month being evaluated. Seven months exceeded the threshold in the published sample.
3. SQL sums the monthly figures by Indian financial year and joins the reported fraud totals for the same year. The rate fell from **10.23** reported incidents per million payments in FY 2023–24 to **6.80** in FY 2024–25.

Each input row describes a period at national level. Individual transactions, merchant identifiers and minute-level payment times would require a transaction-level source. The anomaly flags indicate changes in usage. Reported fraud rates describe the published reports and may reflect changes in reporting.
