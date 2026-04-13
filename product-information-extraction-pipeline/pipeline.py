from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
RAW_DATA_PATH = BASE_DIR / "data" / "raw_products.csv"
OUTPUT_DB_PATH = BASE_DIR / "product_catalog.db"


def normalize_category(value: str) -> str:
    value = value.strip().lower()
    mapping = {"phones": "smartphones", "audio": "audio", "laptops": "laptops"}
    return mapping.get(value, value)


def split_price(value: str) -> tuple[str, float]:
    cleaned = value.replace("|", " ").replace("-", " ").strip().upper()
    parts = cleaned.split()
    if parts[0].isalpha():
        currency = parts[0]
        amount = float(parts[1])
    else:
        amount = float(parts[0])
        currency = parts[1]
    return currency, amount


def normalize_region(value: str) -> str:
    return value.replace("-", "_").lower()


def transform_products(frame: pd.DataFrame) -> pd.DataFrame:
    transformed = frame.copy()
    transformed["title"] = transformed["raw_title"].str.strip()
    transformed["category"] = transformed["raw_category"].apply(normalize_category)
    transformed[["currency", "price"]] = transformed["raw_price"].apply(split_price).apply(pd.Series)
    transformed["region"] = transformed["raw_region"].apply(normalize_region)
    transformed["catalog_ready"] = transformed["price"].gt(0)
    return transformed[["title", "category", "currency", "price", "region", "catalog_ready"]]


def persist_products(frame: pd.DataFrame, database_path: Path = OUTPUT_DB_PATH) -> None:
    connection = sqlite3.connect(database_path)
    frame.to_sql("normalized_products", connection, if_exists="replace", index=False)
    connection.close()


def run_pipeline() -> pd.DataFrame:
    frame = pd.read_csv(RAW_DATA_PATH)
    transformed = transform_products(frame)
    persist_products(transformed)
    return transformed


if __name__ == "__main__":
    result = run_pipeline()
    print(result.to_string(index=False))
