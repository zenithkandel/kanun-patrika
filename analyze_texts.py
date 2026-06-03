#!/usr/bin/env python3
"""Analyze Nepali Supreme Court Najir decision text files."""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from tqdm import tqdm

TEXTS_DIR = Path("texts")
ANALYSIS_DIR = Path("analysis")

PATTERNS = [
    "निर्णय नं",
    "निर्णय नं.",
    "फैसला मिति",
    "मुद्दा",
    "अवलम्बित नजिर",
    "कानुन",
    "इजलास",
]

CONTEXT_CHARS = 300


def collect_files(texts_dir: Path) -> list[Path]:
    return sorted(texts_dir.glob("*.txt"))


def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def compute_stats(files: list[Path], contents: dict[Path, str]) -> dict:
    sizes = {p: p.stat().st_size for p in files}
    chars = {p: len(c) for p, c in contents.items()}
    lines = {p: c.count("\n") + (1 if c and not c.endswith("\n") else 0) for p, c in contents.items()}
    words = {p: len(c.split()) for p, c in contents.items()}

    total_size = sum(sizes.values())
    total_chars = sum(chars.values())
    total_lines = sum(lines.values())
    total_words = sum(words.values())

    largest = max(sizes, key=sizes.get)
    smallest = min(sizes, key=sizes.get)
    avg_size = total_size / len(files) if files else 0

    return {
        "total_files": len(files),
        "total_file_size_bytes": total_size,
        "total_file_size_kb": round(total_size / 1024, 2),
        "total_characters": total_chars,
        "total_lines": total_lines,
        "total_words": total_words,
        "largest_file": {"name": largest.name, "size_bytes": sizes[largest], "characters": chars[largest]},
        "smallest_file": {"name": smallest.name, "size_bytes": sizes[smallest], "characters": chars[smallest]},
        "average_file_size_bytes": round(avg_size, 2),
        "average_file_size_kb": round(avg_size / 1024, 2),
    }


def search_patterns(contents: dict[Path, str]) -> dict:
    """Find all occurrences of each pattern and extract surrounding context."""
    pattern_hits: dict[str, list[dict]] = {p: [] for p in PATTERNS}

    for path, text in contents.items():
        for pattern in PATTERNS:
            start = 0
            while True:
                idx = text.find(pattern, start)
                if idx == -1:
                    break
                context_before = text[max(0, idx - CONTEXT_CHARS):idx]
                context_after = text[idx + len(pattern):idx + len(pattern) + CONTEXT_CHARS]
                pattern_hits[pattern].append({
                    "file": path.name,
                    "position": idx,
                    "context_before": context_before,
                    "context_after": context_after,
                })
                start = idx + len(pattern)

    return pattern_hits


def detect_boundaries(contents: dict[Path, str], pattern_hits: dict) -> list[dict]:
    """Heuristic: lines that start with a known pattern are candidate decision boundaries."""
    boundary_markers = ["निर्णय नं", "निर्णय नं."]
    candidate_counts: Counter = Counter()
    candidate_examples: dict[str, list[dict]] = defaultdict(list)

    for path, text in contents.items():
        for line_no, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            for marker in boundary_markers:
                if stripped.startswith(marker):
                    candidate_counts[marker] += 1
                    if len(candidate_examples[marker]) < 5:
                        # grab ~300 chars after the boundary line
                        idx = text.find(line)
                        snippet = text[idx:idx + CONTEXT_CHARS]
                        candidate_examples[marker].append({"file": path.name, "line_no": line_no, "snippet": snippet})
                    break

    results = []
    for marker, count in candidate_counts.most_common():
        reliability = "high" if count > 50 else "medium" if count > 10 else "low"
        results.append({
            "pattern": marker,
            "frequency": count,
            "reliability": reliability,
            "examples": candidate_examples[marker],
        })
    return results


def detect_metadata_blocks(contents: dict[Path, str]) -> dict:
    """Check whether metadata patterns co-occur within small windows."""
    cooccurrence: Counter = Counter()
    block_examples: list[dict] = []

    trio = ["निर्णय नं", "फैसला मिति", "मुद्दा"]
    window = 500  # chars

    for path, text in contents.items():
        for marker in trio:
            start = 0
            while True:
                idx = text.find(marker, start)
                if idx == -1:
                    break
                # check if all three appear within `window` chars of this hit
                segment = text[idx:idx + window]
                found = [m for m in trio if m in segment]
                if len(found) >= 2:
                    cooccurrence[tuple(sorted(found))] += 1
                    if len(block_examples) < 10:
                        block_examples.append({
                            "file": path.name,
                            "position": idx,
                            "patterns_found": found,
                            "snippet": text[idx:idx + 300],
                        })
                start = idx + len(marker)

    return {
        "cooccurrence_counts": {str(k): v for k, v in cooccurrence.most_common()},
        "examples": block_examples,
    }


def write_sample_file(path: Path, label: str, hits: dict, max_per_pattern: int = 3):
    with open(path, "w", encoding="utf-8") as f:
        for pattern, occurrences in hits.items():
            f.write(f"{'=' * 60}\n")
            f.write(f"PATTERN: {pattern}  (total occurrences: {len(occurrences)})\n")
            f.write(f"{'=' * 60}\n\n")
            for occ in occurrences[:max_per_pattern]:
                f.write(f"--- File: {occ['file']}  Position: {occ['position']} ---\n")
                f.write(f"[...{occ['context_before']}]\n")
                f.write(f"  >>> {pattern} <<<\n")
                f.write(f"[{occ['context_after']}...]\n\n")


def write_boundary_file(path: Path, boundaries: list[dict]):
    with open(path, "w", encoding="utf-8") as f:
        f.write("CANDIDATE DECISION BOUNDARY PATTERNS\n")
        f.write("=" * 60 + "\n\n")
        for b in boundaries:
            f.write(f"Pattern: {b['pattern']}\n")
            f.write(f"Frequency: {b['frequency']}\n")
            f.write(f"Reliability: {b['reliability']}\n\n")
            for ex in b["examples"]:
                f.write(f"  Example from {ex['file']} (line {ex['line_no']}):\n")
                f.write(f"  {ex['snippet'][:200]}...\n\n")


def write_metadata_file(path: Path, metadata: dict):
    with open(path, "w", encoding="utf-8") as f:
        f.write("METADATA BLOCK DETECTION\n")
        f.write("=" * 60 + "\n\n")
        f.write("Co-occurrence of key patterns within 500-char windows:\n\n")
        for combo, count in metadata["cooccurrence_counts"].items():
            f.write(f"  {combo}: {count} times\n")
        f.write(f"\nExamples:\n\n")
        for ex in metadata["examples"]:
            f.write(f"  File: {ex['file']}  Position: {ex['position']}\n")
            f.write(f"  Patterns found together: {ex['patterns_found']}\n")
            f.write(f"  Snippet: {ex['snippet'][:200]}...\n\n")


def recommend_parsing_strategy(boundaries: list[dict], metadata: dict) -> str:
    lines = []
    lines.append("RECOMMENDED PARSING STRATEGY")
    lines.append("=" * 60)
    lines.append("")

    if boundaries:
        best = boundaries[0]
        lines.append(f"Primary split marker: \"{best['pattern']}\" (frequency: {best['frequency']}, reliability: {best['reliability']})")
    else:
        lines.append("No reliable split marker found. Manual review needed.")

    cooc = metadata.get("cooccurrence_counts", {})
    if cooc:
        top = list(cooc.items())[0]
        lines.append(f"Strongest metadata cluster: {top[0]} ({top[1]} co-occurrences)")
        lines.append("Use these patterns to validate extracted decision blocks.")

    lines.append("")
    lines.append("Suggested approach:")
    lines.append("  1. Split on the primary boundary marker.")
    lines.append("  2. Validate each block contains expected metadata patterns.")
    lines.append("  3. For ambiguous cases, use nearest 'फैसला मिति' as secondary anchor.")
    lines.append("  4. Flag blocks missing expected metadata for manual review.")
    return "\n".join(lines)


def generate_report(stats: dict, boundaries: list[dict], metadata: dict, pattern_hits: dict) -> str:
    lines = []
    lines.append("NAJIR CORPUS ANALYSIS REPORT")
    lines.append("=" * 60)
    lines.append("")

    # Corpus statistics
    lines.append("1. CORPUS STATISTICS")
    lines.append("-" * 40)
    lines.append(f"  Total files:           {stats['total_files']}")
    lines.append(f"  Total size:            {stats['total_file_size_kb']} KB")
    lines.append(f"  Total characters:      {stats['total_characters']}")
    lines.append(f"  Total lines:          {stats['total_lines']}")
    lines.append(f"  Total words:          {stats['total_words']}")
    lines.append(f"  Largest file:         {stats['largest_file']['name']} ({stats['largest_file']['size_bytes']} bytes)")
    lines.append(f"  Smallest file:        {stats['smallest_file']['name']} ({stats['smallest_file']['size_bytes']} bytes)")
    lines.append(f"  Average file size:    {stats['average_file_size_kb']} KB")
    lines.append("")

    # Pattern frequency
    lines.append("2. PATTERN FREQUENCY")
    lines.append("-" * 40)
    for pattern in PATTERNS:
        count = len(pattern_hits[pattern])
        lines.append(f"  {pattern:<20s}  occurrences: {count}")
    lines.append("")

    # Boundary detection
    lines.append("3. CANDIDATE DECISION BOUNDARIES")
    lines.append("-" * 40)
    for b in boundaries:
        lines.append(f"  {b['pattern']:<20s}  freq: {b['frequency']:<6d}  reliability: {b['reliability']}")
    lines.append("")

    # Metadata blocks
    lines.append("4. METADATA BLOCK CO-OCCURRENCE")
    lines.append("-" * 40)
    for combo, count in metadata.get("cooccurrence_counts", {}).items():
        lines.append(f"  {combo}: {count} times")
    lines.append("")

    # Sample excerpts
    lines.append("5. SAMPLE EXCERPTS (first 2 hits per pattern)")
    lines.append("-" * 40)
    for pattern in PATTERNS:
        hits = pattern_hits[pattern][:2]
        if hits:
            lines.append(f"\n  Pattern: {pattern}")
            for h in hits:
                lines.append(f"    [{h['file']}] ...{h['context_before'][-80:]}||{h['context_after'][:80]}...")
    lines.append("")

    # Risks
    lines.append("6. POTENTIAL PARSING RISKS")
    lines.append("-" * 40)
    lines.append("  - Some decisions may not contain all expected metadata fields.")
    lines.append("  - Pattern 'मुद्दा' is generic and may appear outside decision headers.")
    lines.append("  - Inconsistent formatting across files may cause split errors.")
    lines.append("  - Very large files may contain multiple decisions merged together.")
    lines.append("  - OCR or encoding issues may corrupt some characters.")
    lines.append("")

    lines.append(recommend_parsing_strategy(boundaries, metadata))
    return "\n".join(lines)


def main():
    if not TEXTS_DIR.is_dir():
        print(f"Error: '{TEXTS_DIR}' directory not found.")
        return

    files = collect_files(TEXTS_DIR)
    if not files:
        print(f"No .txt files found in '{TEXTS_DIR}'.")
        return

    print(f"Found {len(files)} text files. Analyzing...\n")

    contents: dict[Path, str] = {}
    for path in tqdm(files, desc="Reading files", unit="file"):
        contents[path] = read_file(path)

    stats = compute_stats(files, contents)
    pattern_hits = search_patterns(contents)
    boundaries = detect_boundaries(contents, pattern_hits)
    metadata = detect_metadata_blocks(contents)

    ANALYSIS_DIR.mkdir(exist_ok=True)

    report = generate_report(stats, boundaries, metadata, pattern_hits)
    (ANALYSIS_DIR / "report.txt").write_text(report, encoding="utf-8")

    report_json = {
        "corpus_statistics": stats,
        "pattern_frequency": {p: len(hits) for p, hits in pattern_hits.items()},
        "candidate_boundaries": boundaries,
        "metadata_blocks": metadata,
    }
    (ANALYSIS_DIR / "report.json").write_text(json.dumps(report_json, ensure_ascii=False, indent=2), encoding="utf-8")

    write_sample_file(ANALYSIS_DIR / "decision_samples.txt", "Decision", {
        "निर्णय नं": pattern_hits["निर्णय नं"],
        "निर्णय नं.": pattern_hits["निर्णय नं."],
        "फैसला मिति": pattern_hits["फैसला मिति"],
    })

    write_sample_file(ANALYSIS_DIR / "metadata_samples.txt", "Metadata", {
        "मुद्दा": pattern_hits["मुद्दा"],
        "अवलम्बित नजिर": pattern_hits["अवलम्बित नजिर"],
        "कानुन": pattern_hits["कानुन"],
        "इजलास": pattern_hits["इजलास"],
    })

    write_boundary_file(ANALYSIS_DIR / "structure_samples.txt", boundaries)
    write_metadata_file(ANALYSIS_DIR / "structure_samples.txt", metadata)

    print(f"\nAnalysis complete. Results saved to '{ANALYSIS_DIR}/'.")


if __name__ == "__main__":
    main()
