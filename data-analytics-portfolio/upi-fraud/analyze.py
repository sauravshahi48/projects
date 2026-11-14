"""Generate fictional UPI-style activity and evaluate a review queue."""
import csv
import json
import random
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parent
DAY = 24 * 60 * 60
EVAL_START = 18 * DAY
EPOCH = datetime(2025, 7, 1, tzinfo=timezone(timedelta(hours=5, minutes=30)))
SEED = 83
CATEGORIES = {"Cafe": 12_000, "Grocery": 30_000, "Transit": 3_500, "Retail": 60_000}
PAIR_LIMIT = 4
MERCHANT_LIMIT = 9
OUTLIER_LIMIT = 4.5


def generate():
    rng = random.Random(SEED)
    merchants = [
        (f"M{i + 1:02}", category, typical)
        for i, (category, typical) in enumerate(list(CATEGORIES.items()) * 8)
    ]
    transactions = []

    def add(second, customer, merchant, paise, label="normal"):
        transactions.append(
            (len(transactions) + 1, second, customer, merchant, paise, label)
        )

    for day in range(30):
        for _ in range(390):
            merchant, _, typical = rng.choice(merchants)
            hour = rng.choices([9, 12, 15, 19, 21], [12, 24, 11, 36, 17])[0]
            second = day * DAY + hour * 3600 + rng.randrange(3600)
            paise = max(200, round(typical * rng.lognormvariate(0, 0.45) / 50) * 50)
            add(second, rng.randrange(1, 481), merchant, paise)

        # Legitimate group purchases and busy counters can also trip a rule.
        for _ in range(3):
            merchant, _, typical = rng.choice(merchants)
            start = day * DAY + rng.randrange(11, 21) * 3600 + rng.randrange(2400)
            customer = rng.randrange(1, 481)
            for i in range(rng.randint(3, 6)):
                add(start + i * 34, customer, merchant, rng.choice([2500, 3500, 4500]))
            for i in range(rng.randint(4, 8)):
                add(start + i * 38, rng.randrange(1, 481), merchant, typical)

        if day >= 18:
            for _ in range(2):
                merchant, _, typical = rng.choice(merchants)
                start = day * DAY + rng.randrange(9, 21) * 3600 + rng.randrange(2400)
                customer = rng.randrange(1, 481)
                for i in range(rng.randint(6, 10)):
                    add(start + i * 22, customer, merchant, 900 + 100 * (i % 5), "micro_burst")
                add(start + 310, customer, merchant, typical * 9, "amount_spike")
            merchant, _, typical = rng.choice(merchants)
            start = day * DAY + 22 * 3600 + rng.randrange(2400)
            for i in range(12):
                add(start + i * 29, rng.randrange(1, 481), merchant, 2000, "merchant_burst")
    return merchants, transactions


def features(merchants, transactions):
    with sqlite3.connect(":memory:") as db:
        db.row_factory = sqlite3.Row
        db.executescript("""
            CREATE TABLE merchants (
                merchant_id TEXT PRIMARY KEY, category TEXT NOT NULL, typical_paise INTEGER
            );
            CREATE TABLE transactions (
                transaction_id INTEGER PRIMARY KEY, txn_second INTEGER NOT NULL,
                customer_id INTEGER NOT NULL, merchant_id TEXT NOT NULL,
                amount_paise INTEGER NOT NULL, scenario TEXT NOT NULL
            );
        """)
        db.executemany("INSERT INTO merchants VALUES (?, ?, ?)", merchants)
        db.executemany("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?)", transactions)
        return db.execute((ROOT / "analysis.sql").read_text(encoding="utf-8")).fetchall()


def fit_baseline(rows):
    amounts = defaultdict(list)
    for row in rows:
        if row["txn_second"] < EVAL_START:
            amounts[row["category"]].append(row["amount_paise"])
    baseline = {}
    for category, values in amounts.items():
        center = median(values)
        mad = median(abs(value - center) for value in values)
        baseline[category] = (center, mad)
    return baseline


def score(rows, baseline, labels):
    alerts = []
    merchant_results = defaultdict(lambda: {"transactions": 0, "alerts": 0, "signal_points": 0})
    actual = 0
    for row in rows:
        if row["txn_second"] < EVAL_START:
            continue
        merchant = row["merchant_id"]
        stats = merchant_results[merchant]
        stats["transactions"] += 1
        scenario = labels[row["transaction_id"]]
        actual += scenario != "normal"

        center, mad = baseline[row["category"]]
        amount_score = 0.67449 * (row["amount_paise"] - center) / mad if mad else 0.0
        reasons = []
        points = 0
        if row["amount_paise"] <= 5000 and row["pair_micro_5m"] >= PAIR_LIMIT:
            reasons.append("repeat micro-payments")
            points += 2
        if row["merchant_txns_10m"] >= MERCHANT_LIMIT:
            reasons.append("merchant velocity")
            points += 1
        if amount_score >= OUTLIER_LIMIT:
            reasons.append("high amount vs category")
            points += 2
        if not reasons:
            continue

        stats["alerts"] += 1
        stats["signal_points"] += points
        alerts.append({
            "transaction_id": row["transaction_id"],
            "timestamp_ist": (EPOCH + timedelta(seconds=row["txn_second"])).isoformat(),
            "merchant": merchant,
            "amount_inr": row["amount_paise"] / 100,
            "pair_micro_5m": row["pair_micro_5m"],
            "merchant_txns_10m": row["merchant_txns_10m"],
            "amount_robust_z": round(amount_score, 2),
            "signals": " / ".join(reasons),
            "injected_scenario": scenario,
        })

    # Shrink small samples toward zero using 20 additional zero-signal transactions.
    risk = [
        {
            "merchant": merchant, **stats,
            "review_priority": round(100 * stats["signal_points"] / (5 * (stats["transactions"] + 20)), 2),
        }
        for merchant, stats in merchant_results.items()
    ]
    risk.sort(key=lambda row: (-row["review_priority"], row["merchant"]))
    true_positive = sum(alert["injected_scenario"] != "normal" for alert in alerts)
    metrics = {
        "transactions": len(rows),
        "baseline_transactions": sum(row["txn_second"] < EVAL_START for row in rows),
        "evaluation_transactions": sum(row["txn_second"] >= EVAL_START for row in rows),
        "merchants": len(risk),
        "injected_evaluation_transactions": actual,
        "alerts": len(alerts),
        "true_positive": true_positive,
        "false_positive": len(alerts) - true_positive,
        "false_negative": actual - true_positive,
        "precision": round(true_positive / len(alerts), 4) if alerts else None,
        "recall": round(true_positive / actual, 4) if actual else None,
    }
    return alerts, risk, metrics


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    output = ROOT / "output"
    output.mkdir(exist_ok=True)
    merchants, transactions = generate()
    rows = features(merchants, transactions)
    labels = {transaction[0]: transaction[-1] for transaction in transactions}
    alerts, risk, metrics = score(rows, fit_baseline(rows), labels)
    write_csv(output / "transaction_alerts.csv", alerts)
    write_csv(output / "merchant_risk.csv", risk)
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
