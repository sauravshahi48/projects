# Data Analytics Portfolio

| Project | Analysis | Dataset source |
| --- | --- | --- |
| [UPI Payment Anomaly & Reported Fraud Tracker](upi-fraud/) | Python, SQLite window functions, monthly anomaly flags, reported fraud rates | Ministry of Finance parliamentary replies with NPCI and RBI figures |
| [Quick-Commerce Rider SLA Breach & Rain-Surge Impact Tracker](quick-commerce-sla/) | SQL joins, SLA and staffing KPIs, Power BI | NOAA National Climatic Data Center via Vega Datasets (Seattle Weather), plus simulated orders and rider shifts |
| [EV Charging Station Demand & Grid Peak-Load Optimizer](ev-charging/) | Python hourly load estimates, capacity scenarios, Power BI | City of Boulder Open Data (Electric Vehicle Charging Station Energy Consumption) |

## Reproduce the results

From this directory, run the three commands below with Python 3.10 or later. On Windows use `py` if `python` is unavailable. The analysis scripts use the Python standard library and SQLite. Each project writes CSVs and summary metrics to its own `output` folder.

```bash
python upi-fraud/analyze.py
python quick-commerce-sla/analyze.py
python ev-charging/analyze.py
```

The delivery and EV projects each include a Power BI Project (`.pbip`) with embedded data. See their READMEs for report pages, metric definitions, assumptions and instructions for opening the report in Power BI Desktop.
