#!/usr/bin/env python3
"""Parse individual Najir decisions from extracted text files into SQLite."""

import re
import sqlite3
from pathlib import Path

TEXTS_DIR = Path("texts")
DB_PATH = Path("decisions.db")

DECISION_NUMBER_PATTERN = re.compile(
    r"निर्णय नं\.?\s*\n?\s*([०-९]+)", re.MULTILINE
)

DATE_PATTERN = re.compile(
    r"फैसला\s*मिति\s*[:ः]?\s*\n?\s*([०-९।।\.\s]+)", re.MULTILINE
)

BENCH_PATTERN = re.compile(
    r"(सर्वोच्च\s*अदालत,?\s*(?:पूर्ण|संयुत्तफ)\s*इजलास)", re.MULTILINE
)

JUDGE_PATTERN = re.compile(
    r"(?:माननीय\s*)?(?:न्यायाधीश|नयायाधीश)\s*(?:श्री|श्ी)\s*(.+?)(?:\n|$)",
    re.MULTILINE,
)

MUDDA_PATTERN = re.compile(
    r"मुद्दा\s*[:ः–\-]?\s*\n?\s*(.+?)(?:\n(?:निवेदक|पुनरावेदक|प्रत्यर्थी|वादी|प्रतिवादी|विपक्ी))",
    re.DOTALL,
)


def setup_database(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            decision_number TEXT,
            decision_number_raw TEXT,
            decision_date TEXT,
            bench TEXT,
            judges TEXT,
            mudda TEXT,
            source_file TEXT,
            full_text TEXT,
            char_count INTEGER,
            UNIQUE(decision_number, source_file)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_decision_number
        ON decisions(decision_number)
    """)
    conn.commit()
    return conn


def extract_decision_number(text: str) -> tuple[str, str]:
    match = DECISION_NUMBER_PATTERN.search(text)
    if match:
        raw = match.group(1).strip()
        normalized = raw.replace(" ", "")
        return normalized, raw
    return "", ""


def extract_date(text: str) -> str:
    match = DATE_PATTERN.search(text)
    if match:
        return match.group(1).strip().rstrip("।").strip()
    return ""


def extract_bench(text: str) -> str:
    match = BENCH_PATTERN.search(text)
    if match:
        return match.group(1).strip()
    return ""


def extract_judges(text: str) -> str:
    judges = JUDGE_PATTERN.findall(text)
    cleaned = []
    for j in judges:
        name = j.strip().rstrip("।").strip()
        if len(name) > 3 and len(name) < 80:
            cleaned.append(name)
    return "; ".join(cleaned[:5])


def extract_mudda(text: str) -> str:
    match = MUDDA_PATTERN.search(text)
    if match:
        mudda = match.group(1).strip()
        mudda = re.sub(r"\s+", " ", mudda)
        return mudda[:500]
    return ""


def split_on_boundaries(text: str) -> list[tuple[str, int]]:
    """Split text on decision boundaries, returning (chunk, start_pos) pairs."""
    boundaries = []
    for match in re.finditer(r"निर्णय नं\.?\s*\n", text):
        boundaries.append(match.start())

    if not boundaries:
        return []

    chunks = []
    for i, start in enumerate(boundaries):
        end = boundaries[i + 1] if i + 1 < len(boundaries) else len(text)
        chunk = text[start:end].strip()
        if len(chunk) > 50:
            chunks.append((chunk, start))

    return chunks


def parse_file(file_path: Path) -> list[dict]:
    try:
        text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = file_path.read_text(encoding="utf-8", errors="replace")

    chunks = split_on_boundaries(text)
    decisions = []

    for chunk_text, _ in chunks:
        number, number_raw = extract_decision_number(chunk_text)
        if not number:
            continue

        date = extract_date(chunk_text)
        bench = extract_bench(chunk_text)
        judges = extract_judges(chunk_text)
        mudda = extract_mudda(chunk_text)

        decisions.append({
            "decision_number": number,
            "decision_number_raw": number_raw,
            "decision_date": date,
            "bench": bench,
            "judges": judges,
            "mudda": mudda,
            "source_file": file_path.name,
            "full_text": chunk_text,
            "char_count": len(chunk_text),
        })

    return decisions


def insert_decisions(conn: sqlite3.Connection, decisions: list[dict]) -> int:
    inserted = 0
    for d in decisions:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO decisions
                (decision_number, decision_number_raw, decision_date, bench,
                 judges, mudda, source_file, full_text, char_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                d["decision_number"],
                d["decision_number_raw"],
                d["decision_date"],
                d["bench"],
                d["judges"],
                d["mudda"],
                d["source_file"],
                d["full_text"],
                d["char_count"],
            ))
            inserted += 1
        except sqlite3.Error as e:
            print(f"  DB error: {e}")
    conn.commit()
    return inserted


def main():
    files = sorted(TEXTS_DIR.glob("*.txt"))
    if not files:
        print(f"No .txt files found in '{TEXTS_DIR}'")
        return

    print(f"Found {len(files)} text files\n")

    conn = setup_database(DB_PATH)
    conn.execute("DELETE FROM decisions")
    conn.commit()

    total_decisions = 0
    total_inserted = 0
    files_with_decisions = 0
    files_empty = 0

    for i, fp in enumerate(files, 1):
        decisions = parse_file(fp)
        if decisions:
            files_with_decisions += 1
            inserted = insert_decisions(conn, decisions)
            total_decisions += len(decisions)
            total_inserted += inserted
            if i % 20 == 0 or i == len(files):
                print(f"  [{i}/{len(files)}] {fp.name}: {len(decisions)} decisions")
        else:
            files_empty += 1

    cursor = conn.execute("SELECT COUNT(*) FROM decisions")
    db_count = cursor.fetchone()[0]

    print(f"\n{'=' * 50}")
    print(f"Extraction complete")
    print(f"Files processed:     {len(files)}")
    print(f"Files with decisions: {files_with_decisions}")
    print(f"Files empty/failed:  {files_empty}")
    print(f"Decisions extracted: {total_decisions}")
    print(f"Decisions in DB:     {db_count}")
    print(f"Database:            {DB_PATH}")
    print(f"{'=' * 50}")

    conn.close()


if __name__ == "__main__":
    main()
