#!/usr/bin/env python3
"""Check source text corruption patterns."""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path

fp = Path('texts/100258.txt')
text = fp.read_text(encoding='utf-8', errors='replace')

# Find repeated garbage patterns
patterns = re.findall(r'(.)\1{5,}', text)
print('Repeated chars in 100258.txt:')
for p in set(patterns):
    count = len(re.findall(f'({re.escape(p)})' + r'{5,}', text))
    print(f'  "{p}": {count} occurrences')

# Check for common encoding issues
issues = {
    'ज्ञछढ': text.count('ज्ञछढ'),
    'ज्ञछड': text.count('ज्ञछड'),
    'भ§': text.count('भ§'),
    'सर्वाे': text.count('सर्वाे'),
    'गनर्ु': text.count('गनर्ु'),
    'श्री': text.count('श्री'),
}
print()
print('Encoding issues:')
for k, v in issues.items():
    if v > 0:
        print(f'  "{k}": {v} times')

# Show context around issues
print()
print('=== Sample corrupted areas ===')
for match in re.finditer(r'ज्ञछढ', text):
    start = max(0, match.start()-30)
    end = min(len(text), match.end()+30)
    snippet = text[start:end].replace('\n', '|')
    print(f'  pos {match.start()}: ...{snippet}...')
    break

for match in re.finditer(r'भ§', text):
    start = max(0, match.start()-30)
    end = min(len(text), match.end()+30)
    snippet = text[start:end].replace('\n', '|')
    print(f'  pos {match.start()}: ...{snippet}...')
    break
