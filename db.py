from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from config import DB_PATH


def ensure_db() -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                municipality TEXT NOT NULL,
                age INTEGER NOT NULL,
                applicant_type TEXT NOT NULL,
                need_category TEXT NOT NULL,
                requested_amount_sek INTEGER NOT NULL,
                monthly_income_sek INTEGER NOT NULL,
                urgency TEXT NOT NULL,
                description TEXT NOT NULL,
                has_quote INTEGER NOT NULL,
                has_invoice INTEGER NOT NULL,
                has_medical_certificate INTEGER NOT NULL,
                has_research_summary INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER NOT NULL,
                foundation_id TEXT NOT NULL,
                foundation_name TEXT NOT NULL,
                score INTEGER NOT NULL,
                reasons TEXT NOT NULL,
                warnings TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(application_id) REFERENCES applications(id)
            )
            """
        )
        connection.commit()


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def utc_now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")
