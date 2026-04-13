# Product Information Extraction Pipeline

A modular Python data pipeline that cleans noisy product records, extracts standardized attributes with Pandas, and persists curated outputs into SQLite for downstream search and analytics use cases.

## Highlights

- Extracts title, category, price, currency, and region from inconsistent raw product records.
- Uses Pandas transformations to normalize fields and improve data quality.
- Persists curated records to SQLite for later reporting and catalog workflows.
- Ships with sample input data plus a small test suite.

## Run

```bash
pip install -r requirements.txt
python pipeline.py
```

## Test

```bash
pytest
```
