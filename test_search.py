#!/usr/bin/env python3
"""Test search functionality."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3

conn = sqlite3.connect('decisions.db')
conn.row_factory = sqlite3.Row

# Test FTS search
fts_query = 'सम्पत्ति विवाद'
try:
    cursor = conn.execute("""
        SELECT d.id, d.decision_number, d.decision_date, d.bench, d.judges, d.mudda
        FROM decisions_fts fts
        JOIN decisions d ON d.id = fts.rowid
        WHERE decisions_fts MATCH ?
        ORDER BY rank
        LIMIT 5
    """, (fts_query,))
    results = cursor.fetchall()
    print(f'FTS search for "{fts_query}": {len(results)} results')
    for r in results:
        mudda = r["mudda"][:60] if r["mudda"] else "N/A"
        print(f'  {r["decision_number"]} - {mudda}')
except Exception as e:
    print(f'FTS error: {e}')

# Test fallback search
keywords = ['उत्तराधिकार', 'सम्पत्ति', 'विवाह']
conditions = []
params = []
for kw in keywords[:3]:
    conditions.append('(mudda LIKE ? OR full_text LIKE ?)')
    params.extend([f'%{kw}%', f'%{kw}%'])
where = ' OR '.join(conditions)
params.append(5)

cursor = conn.execute(f'SELECT id, decision_number, mudda FROM decisions WHERE {where} LIMIT ?', params)
results = cursor.fetchall()
print(f'\nFallback search: {len(results)} results')
for r in results:
    mudda = r["mudda"][:60] if r["mudda"] else "N/A"
    print(f'  {r["decision_number"]} - {mudda}')

conn.close()
