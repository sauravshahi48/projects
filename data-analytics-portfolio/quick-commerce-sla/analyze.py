"""Join observed daily rain to fictional orders and staffing by Seattle service date."""
import csv
import json
import random
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
START = "2015-10-01"
END = "2015-12-31"
HUBS = [(1, "Ballard"), (2, "Capitol Hill"), (3, "Downtown"), (4, "West Seattle")]
PEAK = (12, 13, 18, 19, 20)
SEED = 64


def load_weather():
    with (ROOT / "seattle_weather_daily.csv").open(encoding="utf-8", newline="") as stream:
        return [(row["date"], float(row["precipitation_mm"])) for row in csv.DictReader(stream)
                if START <= row["date"] <= END]


def simulate(weather):
    rng = random.Random(SEED)
    slots = []
    orders = []
    for day, rain_mm in weather:
        rain_penalty = 5.2 if rain_mm >= 10 else (2.8 if rain_mm >= 1 else 0.0)
        for hub_id, _ in HUBS:
            for hour in range(9, 22):
                peak = hour in PEAK
                staffing = (4 if peak else 3) + rng.choice([-1, 0, 0, 0, 1])
                if hub_id == 3:
                    staffing += 1
                slots.append((hub_id, day, hour, staffing))
                planned = 12 if peak else 6
                volume = max(0, round(rng.gauss(planned + hub_id - 2 + rain_penalty * 0.48, 3.5)))
                pressure = max(0, volume / staffing - 2.0)
                for _ in range(volume):
                    dispatch = round(max(0.5, rng.gauss(2.3 + 1.2 * pressure, 1.15)), 2)
                    pickup = round(max(1, rng.gauss(5.0 + 1.15 * peak + (hub_id == 3) * 1.5, 1.7)), 2)
                    travel = round(max(2, rng.gauss(10.5 + rain_penalty + (hub_id == 4) * 1.7, 2.6)), 2)
                    orders.append((len(orders) + 1, hub_id, day, hour, 30, dispatch, pickup, travel))
    return slots, orders


def query(db, sql):
    return [dict(row) for row in db.execute(sql)]


def standardized_gap(strata):
    # Use the combined order mix over hub/shift pairs represented in both groups.
    groups = {}
    for row in strata:
        band = "Wet" if row["rain_band"] in ("Rain", "Heavy rain") else "Dry"
        counts = groups.setdefault((row["hub_name"], row["shift_band"]), {})
        numerator, denominator = counts.get(band, (0, 0))
        counts[band] = (numerator + row["breaches"], denominator + row["orders"])
    gap = weight = 0
    for counts in groups.values():
        if counts.keys() != {"Wet", "Dry"}:
            continue
        wet_breaches, wet_orders = counts["Wet"]
        dry_breaches, dry_orders = counts["Dry"]
        combined = wet_orders + dry_orders
        gap += combined * (wet_breaches / wet_orders - dry_breaches / dry_orders)
        weight += combined
    return round(100 * gap / weight, 2) if weight else None


def run(weather):
    slots, orders = simulate(weather)
    with sqlite3.connect(":memory:") as db:
        db.row_factory = sqlite3.Row
        db.executescript("""
            CREATE TABLE hubs (hub_id INTEGER PRIMARY KEY, hub_name TEXT NOT NULL);
            CREATE TABLE weather_daily (service_date TEXT PRIMARY KEY, precipitation_mm REAL);
            CREATE TABLE rider_slots (
                hub_id INTEGER, service_date TEXT, order_hour INTEGER,
                scheduled_riders INTEGER CHECK(scheduled_riders > 0),
                PRIMARY KEY (hub_id, service_date, order_hour)
            );
            CREATE TABLE orders (
                order_id INTEGER PRIMARY KEY, hub_id INTEGER, service_date TEXT,
                order_hour INTEGER, promised_minutes INTEGER, dispatch_minutes REAL,
                pickup_minutes REAL, travel_minutes REAL
            );
        """)
        db.executemany("INSERT INTO hubs VALUES (?, ?)", HUBS)
        db.executemany("INSERT INTO weather_daily VALUES (?, ?)", weather)
        db.executemany("INSERT INTO rider_slots VALUES (?, ?, ?, ?)", slots)
        db.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?)", orders)
        db.executescript((ROOT / "analysis.sql").read_text(encoding="utf-8"))
        # Daily hub-hour rows keep exact counts and stage totals for weighted Power BI measures.
        order_metrics = query(db, """
            SELECT service_date, order_hour, hub_name, shift_band, rain_band,
                   COUNT(*) AS orders, SUM(breached) AS breaches,
                   ROUND(SUM(dispatch_minutes), 2) AS dispatch_total,
                   ROUND(SUM(pickup_minutes), 2) AS pickup_total,
                   ROUND(SUM(travel_minutes), 2) AS travel_total
            FROM order_metrics
            GROUP BY service_date, order_hour, hub_name, shift_band, rain_band
            ORDER BY service_date, order_hour, hub_name
        """)
        slot_metrics = query(db, "SELECT * FROM slot_metrics ORDER BY service_date, order_hour, hub_name")
        rain = query(db, """
            SELECT rain_band, COUNT(*) AS orders, SUM(breached) AS breaches,
                   ROUND(AVG(1.0 * breached) * 100, 2) AS breach_pct,
                   ROUND(AVG(dispatch_minutes), 2) AS dispatch_avg,
                   ROUND(AVG(pickup_minutes), 2) AS pickup_avg,
                   ROUND(AVG(travel_minutes), 2) AS travel_avg
            FROM order_metrics GROUP BY rain_band ORDER BY MIN(precipitation_mm)
        """)
        strata = query(db, "SELECT * FROM rain_by_hub_and_shift ORDER BY hub_name, shift_band, rain_band")
        uncovered = query(db, """
            SELECT COUNT(*) AS n FROM order_metrics WHERE precipitation_mm IS NULL OR scheduled_riders IS NULL
        """)[0]["n"]
    assert sum(row["orders"] for row in order_metrics) == len(orders)
    assert sum(row["orders"] for row in slot_metrics) == len(orders)
    return order_metrics, slot_metrics, {
        "days": len(weather),
        "weather_days": {
            "Dry (<1 mm)": sum(mm < 1 for _, mm in weather),
            "Rain": sum(1 <= mm < 10 for _, mm in weather),
            "Heavy rain": sum(mm >= 10 for _, mm in weather),
        },
        "orders": len(orders), "hub_slots": len(slots), "orders_missing_join_data": uncovered,
        "staffing_review_slots": sum(row["staffing_review"] for row in slot_metrics),
        "breaches": sum(row["breaches"] for row in order_metrics),
        "rain_vs_dry_adjusted_gap_pp": standardized_gap(strata),
        "rain_results": rain,
    }


def save_rows(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    output = ROOT / "output"
    output.mkdir(exist_ok=True)
    orders, slots, summary = run(load_weather())
    save_rows(output / "sla_by_hub_hour.csv", orders)
    save_rows(output / "staffing_slots.csv", slots)
    (output / "metrics.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
