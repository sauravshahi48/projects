# EV Charging Station Demand & Grid Peak-Load Optimizer

Estimate hourly charging demand, check a planning capacity, and test a controlled charging schedule over observed plug-in windows.

## Dataset source

**City of Boulder Open Data (Electric Vehicle Charging Station Energy Consumption).** The public-domain historical snapshot is mirrored in the RedCASTLE research repository. `boulder_sessions.csv` is a cleaned subset of positive-energy sessions overlapping January 2020 at the five stations with the most January session starts in that snapshot. Station labels were shortened and timestamps were normalized to Boulder local wall time. The subset contains session IDs, plug-in and unplug times, charging durations and delivered kWh.

## Method

- Allocate each session's recorded energy across its reported active charging duration, starting at plug-in and clipping the duration to the connected window. Weight each hourly bucket by overlap. Each bucket is one hour, so kWh in the bucket equals its average kW over that hour. This produces an estimated hourly profile from session totals.
- Include all 744 hours, even when demand is zero. Measure time above an illustrative **24 kW** planning threshold for the selected five-station group.
- Reschedule sessions with at least one hour of idle time inside their observed plug-in window. For each eligible session, choose the smallest feasible hourly peak against the current schedule and retain the original rate limit and delivered energy. This sequential what-if analysis allows partial charging across different hours.
- January dates avoid the daylight-saving transition. The capacity threshold and charging sequence are modeled assumptions. The five stations are treated as a planning group, and the source does not identify a shared feeder or contain grid telemetry.

| Metric | Baseline estimate | Controlled charging scenario |
| --- | ---: | ---: |
| Network hourly peak | 27.92 kW | 26.96 kW |
| Hours above the 24 kW planning threshold | 2 | 1 |
| Energy delivered in January | 3,664.915 kWh | 3,664.915 kWh |

The scenario rescheduled 51 of 427 included sessions and reduced estimated peak demand by 3.45%. The result describes this sample and assumes each eligible session can be controlled within its original connection window.

## Run and open the report

- Run `python analyze.py` from this directory. See `output/network_hourly.csv`, `output/station_hourly.csv` and `output/metrics.json`.
- Open `EVCharging.pbip` in recent Power BI Desktop on Windows. Enable Power BI Project and enhanced report format support if your version exposes those features as preview options, then refresh to load the embedded snapshots. **Network demand** compares peak and above-capacity hours. **Station demand** compares daily energy and peak hours for individual stations.
