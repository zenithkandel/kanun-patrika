#!/usr/bin/env python3
"""Check remaining corruption after cleaning."""
import sqlite3, sys, re
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('decisions.db')
conn.row_factory = sqlite3.Row

cursor = conn.execute('SELECT id, decision_number, full_text FROM decisions')
for row in cursor.fetchall():
    text = row['full_text'][:1000]
    if re.search(r'(.)\1{4,}', text):
        print(f'Decision {row["decision_number"]} (id={row["id"]}):')
        matches = re.findall(r'(.)\1{4,}', text)
        for m in matches[:3]:
            print(f'  Repeated: "{m}"')
        print(f'  First 200 chars: {text[:200]}')
        print()
