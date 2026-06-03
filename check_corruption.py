#!/usr/bin/env python3
"""Analyze text corruption in decisions database."""
import sqlite3, sys, re
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('decisions.db')
conn.row_factory = sqlite3.Row

print('=== SAMPLE MUDDAS ===')
cursor = conn.execute("SELECT decision_number, mudda FROM decisions WHERE mudda != '' LIMIT 15")
for row in cursor.fetchall():
    print(f'  {row["decision_number"]}: {row["mudda"][:100]}')

print()
print('=== SAMPLE FULL TEXT (first 500 chars of 5 decisions) ===')
cursor = conn.execute('SELECT id, decision_number, full_text FROM decisions LIMIT 5')
for row in cursor.fetchall():
    text = row['full_text'][:500]
    print(f'--- Decision {row["decision_number"]} ---')
    print(text)
    print()

print('=== CHECKING CORRUPTION PATTERNS ===')

cursor = conn.execute('SELECT id, decision_number, full_text, mudda FROM decisions')
total = 0
has_garbled = 0
has_repeated = 0
has_fragmented = 0

for row in cursor.fetchall():
    total += 1
    text = (row['full_text'] or '')[:3000]
    mudda = row['mudda'] or ''
    
    # Check for repeated non-Nepali patterns like ज्ञछढठ
    if re.search(r'ज्ञ[छढत]{2,}', text):
        has_repeated += 1
    
    # Check for characters outside normal ranges
    garbled = re.findall(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', text)
    if len(garbled) > 5:
        has_garbled += 1
    
    # Check for fragmented words (lone consonants without matras)
    if re.search(r'[क-ह][^्\u093C\u0940-\u094D\s\d।,\.।ः]', text[:200]):
        pass  # too common to flag

print(f'  Total decisions: {total}')
print(f'  With repeated garbage patterns: {has_repeated}')
print(f'  With control chars: {has_garbled}')

# Check specific files
print()
print('=== FILE-BY-FILE CORRUPTION CHECK ===')
cursor = conn.execute('''
    SELECT source_file, COUNT(*) as cnt, 
           AVG(char_count) as avg_chars
    FROM decisions 
    GROUP BY source_file
    ORDER BY cnt DESC
''')
for row in cursor.fetchall():
    print(f'  {row["source_file"]}: {row["cnt"]} decisions, avg {row["avg_chars"]:.0f} chars')

conn.close()
