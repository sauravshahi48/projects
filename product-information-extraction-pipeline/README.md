# Product Information Extraction Pipeline

A modular Python data pipeline that cleans noisy product records, extracts standardized attributes with Pandas, and persists curated outputs into SQLite for downstream search and analytics use cases.

## Stack

- Python
- Pandas
- SQLite
- SQL

## Highlights

- Extracts title, category, price, currency, and region from inconsistent raw product records.
- Uses Pandas transformations to normalize fields and improve data quality.
- Persists curated records to SQLite for later reporting and catalog workflows.
- Ships with sample input data plus a small test suite.

## Project Structure

- `pipeline.py`: transformation and persistence logic
- `data/raw_products.csv`: sample raw input data
- `tests/test_pipeline.py`: transformation tests

## Run

```bash
pip install -r requirements.txt
python pipeline.py
```

Running the pipeline writes normalized output into `product_catalog.db`.

## Test

```bash
pytest
```

## Output Fields

- `title`
- `category`
- `currency`
- `price`
- `region`
- `catalog_ready`

## Portfolio Talking Points

- Shows end-to-end ETL thinking from raw ingestion to curated storage.
- Demonstrates practical data cleaning patterns for messy marketplace feeds.
- Keeps transformation logic modular and testable for future scaling.
