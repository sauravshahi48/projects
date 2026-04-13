from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "routing.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS routing_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_code TEXT NOT NULL,
            currency TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            priority INTEGER NOT NULL,
            available INTEGER NOT NULL
        )
        """
    )
    cursor.execute("DELETE FROM routing_rules")
    cursor.executemany(
        """
        INSERT INTO routing_rules (country_code, currency, payment_method, priority, available)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("IN", "INR", "upi", 1, 1),
            ("IN", "INR", "card", 2, 1),
            ("DE", "EUR", "sepa", 1, 1),
            ("DE", "EUR", "card", 2, 1),
            ("US", "USD", "card", 1, 1),
            ("US", "USD", "paypal", 2, 0),
        ],
    )
    connection.commit()
    connection.close()
