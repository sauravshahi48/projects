# Quick-Commerce Rider SLA Breach & Rain-Surge Impact Tracker

Identify which delivery stages and hub shifts drive 30-minute SLA breaches in a Seattle quick-commerce simulation.

## Dataset source

- **NOAA National Climatic Data Center via Vega Datasets (Seattle Weather).** `seattle_weather_daily.csv` contains 92 observed daily precipitation values, in millimetres, from October through December 2015. The file keeps only date and precipitation from the source.
- **Project-generated synthetic delivery orders and rider shifts.** `analyze.py` simulates 46,861 orders and 4,784 scheduled hub-hour slots across four Seattle hubs. Observed rain and simulated staffing pressure influence the generated durations. Hub names refer to Seattle areas, and operations are fictional.

## SQL and measures

- Join orders to the hub dimension, daily precipitation and scheduled staffing. The weather join uses service date, and the staffing join uses hub, service date and hour. Group orders before calculating slot workload so a staffing row is counted once.
- An order breaches when dispatch, pickup and travel add up to more than 30 minutes. Classify daily precipitation as dry (below 1 mm), rain (1 to below 10 mm), or heavy rain (10 mm or more).
- Flag a slot for staffing review when it has at least eight orders, at least three orders per scheduled rider, and a breach rate of at least 20%. The threshold is a triage rule.
- Compute a wet-versus-dry comparison within each hub and peak/off-peak stratum, weighted by combined order counts. This simulation deliberately incorporates rain delays, so the comparison describes the generated scenario.

| Rain band | Simulated orders | SLA breach rate | Mean travel |
| --- | ---: | ---: | ---: |
| Dry | 18,322 | 0.69% | 11.02 min |
| Rain | 16,839 | 5.54% | 13.82 min |
| Heavy rain | 11,700 | 17.98% | 16.19 min |

The hub-and-shift adjusted wet-versus-dry gap was 10.07 percentage points. The staffing rule flagged 362 hub-hour slots for review.

## Run and open the report

- Run `python analyze.py` from this directory for the SQL results and summary in `output/`.
- Open `QuickCommerce.pbip` in recent Power BI Desktop on Windows. Enable Power BI Project and enhanced report format support if the installed version exposes those features as preview options, then refresh to load the embedded snapshots. Use the hub and shift slicers on **Delivery SLA**. The **Rider workload** page shows staffing review counts and workload by hub and hour.
- The checked-in Power BI model stores the generated CSV snapshots as compressed Power Query partitions. Refer to the CSV outputs when inspecting or rebuilding the underlying model.
