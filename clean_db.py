#!/usr/bin/env python3
"""
Clean and fix Nepali text corruption in decisions database.

Known issues:
1. Repeated header/footer artifacts (ज्ञछढठ, etc.)
2. Broken ligatures (भ§, सर्वाे, गनर्ु)
3. Control characters and garbage
4. Page numbers and decorative text
"""

import re
import sqlite3
import unicodedata
from pathlib import Path

DB_PATH = Path("decisions.db")


def clean_nepali_text(text: str) -> str:
    """Apply all cleaning fixes to Nepali text."""

    # 1. Remove repeated decorative patterns (page headers/footers)
    # Pattern: same 3+ chars repeated 5+ times
    text = re.sub(r'(.)\1{4,}', '', text)

    # 2. Remove isolated page numbers and decorative lines
    text = re.sub(r'^\s*[०-९]+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)

    # 3. Fix broken ligatures and encoding issues
    replacements = {
        # Common broken ligature: half-character + garble
        'भ§': 'भाई',
        'भ<': 'भाई',
        'भ>': 'भाई',
        'श§': 'श्री',
        'श<': 'श्री',

        # सर्वोच्च variants
        'सर्वाेच्च': 'सर्वोच्च',
        'सर्वोाच्च': 'सर्वोच्च',
        'सर्वौच्च': 'सर्वोच्च',

        # Common garbled sequences from PDF extraction
        'गनर्ु': 'गर्नु',
        'गनर्े': 'गर्ने',
        'गनर्ो': 'गर्नो',
        'गनर्ुपर्न': 'गर्नुपर्न',
        'गनर्ुपनर्े': 'गर्नुपर्ने',
        'गनर्': 'गर्न',
        'लगाउँदागराउँदै': 'लगाउँदै',

        # Fix half-letter issues
        'न्ित्र': 'न्त्र',
        'प्रि्रया': 'प्रक्रिया',
        'प्रकि्रया': 'प्रक्रिया',
        '्रप': 'क्रप',
        '्रपमा': 'रूपमा',

        # Fix निर्णय variants
        'निणªय': 'निर्णय',
        'निणFय': 'निर्णय',

        # Fix common word fragments
        'व्यत्ति': 'व्यक्ति',
        'व्यत्तिफ': 'व्यक्तिफ',
        'कायाª': 'कार्य',
        'कायA': 'कार्य',

        # Fix possessive/particle issues
        'लार्इ': 'लाई',
        'लाइ': 'लाई',
        'गरिपाउँफ': 'गरिपाउनुहोस्',
        'पाउँफ': 'पाउनुहोस्',

        # Fix common letter substitutions from Preeti remnant
        'Oत': 'उत',
        'Iत': 'इत',
        'Nरट': 'रिट',
        'Mत': 'मिति',
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # 4. Remove control characters (but keep newlines and tabs)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # 5. Remove repeated spaces (keep single space)
    text = re.sub(r' {2,}', ' ', text)

    # 6. Fix multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 7. Remove lines that are just decorative symbols
    text = re.sub(r'^\s*[§•·\-–—]+\s*$', '', text, flags=re.MULTILINE)

    # 8. Remove very short lines that are likely artifacts (1-2 chars, not Nepali digits)
    text = re.sub(r'^\s*[^\u0900-\u097F\d\s]{1,2}\s*$', '', text, flags=re.MULTILINE)

    return text.strip()


def clean_database():
    """Clean all decisions in the database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # Get all decisions
    cursor = conn.execute('SELECT id, full_text, mudda, judges, bench FROM decisions')
    rows = cursor.fetchall()

    print(f"Cleaning {len(rows)} decisions...")

    updated = 0
    for row in rows:
        old_text = row['full_text']
        new_text = clean_nepali_text(old_text)

        # Also clean mudda and judges
        new_mudda = clean_nepali_text(row['mudda'] or '')
        new_judges = clean_nepali_text(row['judges'] or '')
        new_bench = clean_nepali_text(row['bench'] or '')

        if new_text != old_text:
            conn.execute("""
                UPDATE decisions
                SET full_text = ?, mudda = ?, judges = ?, bench = ?, char_count = ?
                WHERE id = ?
            """, (new_text, new_mudda, new_judges, new_bench, len(new_text), row['id']))
            updated += 1

    conn.commit()
    print(f"Updated {updated} decisions")

    # Rebuild FTS index
    print("Rebuilding FTS index...")
    try:
        conn.execute("DROP TABLE IF EXISTS decisions_fts")
    except Exception:
        pass
    conn.execute("""
        CREATE VIRTUAL TABLE decisions_fts USING fts5(
            decision_number, decision_date, bench, judges, mudda, full_text,
            content='decisions', content_rowid='id', tokenize='unicode61'
        )
    """)
    conn.execute("""
        INSERT INTO decisions_fts(rowid, decision_number, decision_date, bench, judges, mudda, full_text)
        SELECT id, decision_number, decision_date, bench, judges, mudda, full_text FROM decisions
    """)
    conn.commit()
    print("FTS index rebuilt")

    conn.close()


if __name__ == "__main__":
    clean_database()
