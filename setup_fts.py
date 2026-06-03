#!/usr/bin/env python3
"""Set up SQLite FTS5 for efficient text search on decisions."""

import sqlite3
from pathlib import Path

DB_PATH = Path("decisions.db")


def setup_fts():
    conn = sqlite3.connect(str(DB_PATH))

    try:
        conn.execute("DROP TABLE IF EXISTS decisions_fts")
    except Exception:
        pass

    conn.execute("""
        CREATE VIRTUAL TABLE decisions_fts USING fts5(
            decision_number,
            decision_date,
            bench,
            judges,
            mudda,
            full_text,
            content='decisions',
            content_rowid='id',
            tokenize='unicode61'
        )
    """)

    conn.execute("""
        INSERT INTO decisions_fts(rowid, decision_number, decision_date, bench, judges, mudda, full_text)
        SELECT id, decision_number, decision_date, bench, judges, mudda, full_text FROM decisions
    """)

    conn.commit()

    cursor = conn.execute("SELECT COUNT(*) FROM decisions_fts")
    count = cursor.fetchone()[0]
    print(f"FTS index created with {count} entries")

    conn.close()


if __name__ == "__main__":
    setup_fts()
