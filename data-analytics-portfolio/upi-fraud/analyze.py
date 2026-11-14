"""Analyze government-reported UPI payments and reported fraud totals."""

import argparse
import csv
import math
import sqlite3
from contextlib import closing
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CRORE = 10_000_000
LAKH = 100_000


def read_records(path, columns):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(columns):
            raise ValueError(f"{path.name} must contain {', '.join(columns)} in order")
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"{path.name} row {reader.line_num} has an unexpected number of fields")
            yield reader.line_num, tuple(row[column].strip() for column in columns)


def units(value, multiplier):
    """Convert the published lakh or crore figures to whole base units."""
    try:
        total = Decimal(value.replace(",", "")) * multiplier
    except InvalidOperation as error:
        raise ValueError(f"invalid numeric value {value!r}") from error
    if not total.is_finite() or total < 0 or total != total.to_integral_value():
        raise ValueError(f"expected a nonnegative whole-unit count after conversion, got {value!r}")
    return int(total)


def read_monthly(path):
    by_month = {}
    for line, (period, count, value) in read_records(
        path, ("month", "transactions_crore", "value_inr_crore")
    ):
        try:
            month = date.fromisoformat(period + "-01")
            if month.isoformat()[:7] != period:
                raise ValueError("month must use YYYY-MM")
            transactions = units(count, CRORE)
            amount = units(value, CRORE)
            if transactions == 0 or amount == 0:
                raise ValueError("monthly transaction count and value must be positive")
            if month in by_month:
                raise ValueError(f"duplicate month {period}")
        except ValueError as error:
            raise ValueError(f"{path.name} row {line}: {error}") from error
        by_month[month] = (month.isoformat(), transactions, amount)

    if not by_month:
        raise ValueError(f"{path.name} contains no monthly records")
    months = sorted(by_month)
    for previous, current in zip(months, months[1:]):
        if current.year * 12 + current.month != previous.year * 12 + previous.month + 1:
            raise ValueError(f"monthly series has a gap before {current:%Y-%m}")
    return [by_month[month] for month in months]


def read_fraud(path):
    records = {}
    for line, (year, incidents, amount) in read_records(
        path, ("financial_year", "reported_incidents_lakh", "reported_amount_inr_crore")
    ):
        try:
            start = int(year.split("-", 1)[0])
            if start < 1900 or year != f"{start:04d}-{(start + 1) % 100:02d}":
                raise ValueError("financial year must span consecutive years in YYYY-YY form")
            if year in records:
                raise ValueError(f"duplicate financial year {year}")
            counts = units(incidents, LAKH)
            value = units(amount, CRORE)
        except ValueError as error:
            raise ValueError(f"{path.name} row {line}: {error}") from error
        records[year] = (year, counts, value)
    if not records:
        raise ValueError(f"{path.name} contains no fraud records")
    return list(records.values())


def analyze(monthly_records, fraud_records, threshold):
    with closing(sqlite3.connect(":memory:")) as db:
        db.executescript("""
            CREATE TABLE upi_monthly (
                month TEXT PRIMARY KEY,
                transaction_count INTEGER NOT NULL CHECK (transaction_count > 0),
                value_inr INTEGER NOT NULL CHECK (value_inr > 0)
            );
            CREATE TABLE upi_fraud (
                financial_year TEXT PRIMARY KEY,
                reported_incidents INTEGER NOT NULL CHECK (reported_incidents >= 0),
                reported_amount_inr INTEGER NOT NULL CHECK (reported_amount_inr >= 0)
            );
        """)
        db.executemany("INSERT INTO upi_monthly VALUES (?, ?, ?)", monthly_records)
        db.executemany("INSERT INTO upi_fraud VALUES (?, ?, ?)", fraud_records)
        monthly = db.execute(
            (ROOT / "analysis.sql").read_text(encoding="utf-8"), {"threshold": threshold}
        )
        annual = db.execute((ROOT / "fraud_rates.sql").read_text(encoding="utf-8"))
        return (
            ([column[0] for column in monthly.description], monthly.fetchall()),
            ([column[0] for column in annual.description], annual.fetchall()),
        )


def write_csv(path, table):
    columns, rows = table
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--monthly", type=Path, default=ROOT / "data" / "upi_monthly.csv")
    parser.add_argument("--fraud", type=Path, default=ROOT / "data" / "reported_upi_fraud.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "output")
    parser.add_argument("--threshold", type=float, default=25.0, help="absolute percent gap for a monthly flag")
    args = parser.parse_args()
    if not math.isfinite(args.threshold) or args.threshold <= 0:
        parser.error("--threshold must be a finite number greater than zero")

    try:
        monthly, fraud = analyze(read_monthly(args.monthly), read_fraud(args.fraud), args.threshold)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    args.output.mkdir(parents=True, exist_ok=True)
    write_csv(args.output / "monthly_upi_metrics.csv", monthly)
    write_csv(args.output / "financial_year_fraud_rates.csv", fraud)

    flags = sum(row[-1] in ("Above baseline", "Below baseline") for row in monthly[1])
    print(f"Analyzed {len(monthly[1])} official monthly records and {len(fraud[1])} complete financial years.")
    if len(fraud[1]) == 0:
        print("Annual rates require a complete April-to-March payment series and a fraud total for the same year.")
    print(f"Flagged {flags} monthly volume deviations at the {args.threshold:g}% threshold.")
    print(f"Reports written to {args.output}")


if __name__ == "__main__":
    main()
