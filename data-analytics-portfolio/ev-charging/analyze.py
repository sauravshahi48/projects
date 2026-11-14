"""Estimate hourly load from charging records and test controlled charging."""
import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from math import fsum, isclose
from pathlib import Path

ROOT = Path(__file__).resolve().parent
START = datetime(2020, 1, 1)
END = datetime(2020, 2, 1)
HOUR = timedelta(hours=1)
CAPACITY_KW = 24.0
MIN_SLACK_HOURS = 1.0
EPSILON = 1e-7


@dataclass(frozen=True)
class Session:
    session_id: str
    station: str
    start: datetime
    end: datetime
    charging_hours: float
    energy: float

    @property
    def rate(self):
        return self.energy / self.charging_hours


def load_sessions():
    sessions = []
    with (ROOT / "boulder_sessions.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            start = datetime.fromisoformat(row["plug_in"])
            end = datetime.fromisoformat(row["unplug"])
            connected_hours = (end - start) / HOUR
            # Timestamps are rounded to the minute. Never allocate past unplugging.
            charging_hours = min(float(row["charging_seconds"]) / 3600, connected_hours)
            sessions.append(Session(
                row["session_id"], row["station"], start, end,
                charging_hours, float(row["energy_kwh"]),
            ))
    return sessions


def hour_limits(start, end, rate):
    bucket = start.replace(minute=0, second=0, microsecond=0)
    amounts = {}
    while bucket < end:
        overlap = min(bucket + HOUR, end) - max(bucket, start)
        if overlap > timedelta(0):
            amounts[bucket] = rate * (overlap / HOUR)
        bucket += HOUR
    return amounts


def lowest_peak_schedule(base, limits, energy, cap):
    """Find the smallest local peak that can fit all energy in this plug-in window."""
    lower, upper = min(base[hour] for hour in limits), cap

    def room_at(ceiling):
        return {hour: min(limit, max(0.0, ceiling - base[hour]))
                for hour, limit in limits.items()}

    assert fsum(room_at(cap).values()) + EPSILON >= energy
    for _ in range(40):
        middle = (lower + upper) / 2
        if fsum(room_at(middle).values()) >= energy:
            upper = middle
        else:
            lower = middle
    rooms = room_at(upper)
    # Remove numerical surplus without changing hourly limits or total energy.
    remaining = energy
    allocation = {}
    for hour, room in rooms.items():
        take = min(remaining, room)
        if take > 0:
            allocation[hour] = take
        remaining -= take
    assert abs(remaining) < EPSILON
    return allocation


def analyze(sessions):
    baseline = defaultdict(float)
    by_station = defaultdict(float)
    allocations = {}
    hours = [START + i * HOUR for i in range((END - START) // HOUR)]
    for session in sessions:
        active_end = session.start + timedelta(hours=session.charging_hours)
        original = hour_limits(session.start, active_end, session.rate)
        assert isclose(fsum(original.values()), session.energy, abs_tol=EPSILON)
        allocations[session.session_id] = original
        for hour, kwh in original.items():
            if START <= hour < END:
                baseline[hour] += kwh
                by_station[session.station, hour] += kwh

    scenario = baseline.copy()
    scenario_by_station = by_station.copy()
    flexible = [
        s for s in sessions if START <= s.start and s.end <= END
        and (s.end - s.start) / HOUR - s.charging_hours >= MIN_SLACK_HOURS
    ]
    # Tackle the largest originally exposed peaks first and use chronological tie-breaking.
    flexible.sort(key=lambda s: (-max(baseline[h] for h in allocations[s.session_id]), s.start, s.session_id))
    for session in flexible:
        original = allocations[session.session_id]
        cap = max(scenario[hour] for hour in original)
        for hour, kwh in original.items():
            scenario[hour] -= kwh
            scenario_by_station[session.station, hour] -= kwh
        limits = hour_limits(session.start, session.end, session.rate)
        revised = lowest_peak_schedule(scenario, limits, session.energy, cap)
        assert all(kwh <= limits[hour] + EPSILON for hour, kwh in revised.items())
        for hour, kwh in revised.items():
            scenario[hour] += kwh
            scenario_by_station[session.station, hour] += kwh

    baseline_total = fsum(baseline.values())
    scenario_total = fsum(scenario.values())
    assert isclose(baseline_total, scenario_total, abs_tol=EPSILON)
    for station in {session.station for session in sessions}:
        original = fsum(by_station[station, hour] for hour in hours)
        planned = fsum(scenario_by_station[station, hour] for hour in hours)
        assert isclose(original, planned, abs_tol=EPSILON)
    peak = max(baseline.values())
    optimized_peak = max(scenario.values())
    assert optimized_peak <= peak + EPSILON
    summary = {
        "stations": len({session.station for session in sessions}),
        "positive_energy_sessions": len(sessions),
        "flexible_sessions": len(flexible),
        "hours": len(hours),
        "capacity_kw": CAPACITY_KW,
        "baseline_peak_kw": round(peak, 3),
        "scenario_peak_kw": round(optimized_peak, 3),
        "peak_reduction_pct": round((1 - optimized_peak / peak) * 100, 2),
        "baseline_hours_above_capacity": sum(baseline[hour] > CAPACITY_KW for hour in hours),
        "scenario_hours_above_capacity": sum(scenario[hour] > CAPACITY_KW for hour in hours),
        "energy_kwh": round(baseline_total, 3),
    }
    return hours, baseline, scenario, by_station, scenario_by_station, summary


def output_rows(hours, original, revised, station_original, station_revised, stations):
    network = []
    sites = []
    for timestamp in hours:
        hour = timestamp.isoformat(sep=" ", timespec="minutes")
        day = timestamp.date().isoformat()
        hour_of_day = timestamp.strftime("%H:00")
        network.append((hour, day, hour_of_day, round(original[timestamp], 8),
                        round(revised[timestamp], 8), CAPACITY_KW,
                        int(original[timestamp] > CAPACITY_KW),
                        int(revised[timestamp] > CAPACITY_KW)))
        for station in stations:
            key = station, timestamp
            sites.append((day, hour_of_day, station, round(station_original[key], 8),
                          round(station_revised[key], 8)))
    return network, sites


def write_csv(path, columns, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        writer.writerows(rows)


def main():
    output = ROOT / "output"
    output.mkdir(exist_ok=True)
    sessions = load_sessions()
    hours, baseline, scenario, by_station, scenario_by_station, summary = analyze(sessions)
    stations = sorted({session.station for session in sessions})
    network, sites = output_rows(hours, baseline, scenario, by_station, scenario_by_station, stations)
    write_csv(output / "network_hourly.csv",
              ("hour_local", "date", "hour_of_day", "baseline_kw", "scenario_kw", "capacity_kw",
               "baseline_over_capacity", "scenario_over_capacity"), network)
    write_csv(output / "station_hourly.csv",
              ("date", "hour_of_day", "station", "baseline_kw", "scenario_kw"), sites)
    (output / "metrics.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
