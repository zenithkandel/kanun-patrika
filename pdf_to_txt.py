import fitz
from pathlib import Path
from preeti_unicode import convert_text

PDF_DIR = Path("pdfs")
OUTPUT_DIR = Path("texts")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def looks_like_preeti(text: str) -> bool:
    """
    Heuristic detection for Preeti-encoded text.
    """
    sample = text[:10000]

    indicators = [
        "g]kfn",
        "sfg" ,
        "k|",
        "df",
        "nfO{",
        "cg';f/",
        "lj",
        "clwsf/",
    ]

    score = sum(sample.count(x) for x in indicators)

    return score >= 10


pdf_files = sorted(PDF_DIR.glob("*.pdf"))

if not pdf_files:
    print(f"No PDFs found in '{PDF_DIR}'")
    raise SystemExit(1)

print(f"Found {len(pdf_files)} PDF files\n")

success = 0
failed = 0

for index, pdf_path in enumerate(pdf_files, start=1):

    txt_path = OUTPUT_DIR / f"{pdf_path.stem}.txt"

    if txt_path.exists():
        print(f"[{index}/{len(pdf_files)}] Skipping {pdf_path.name}")
        continue

    try:
        print(f"[{index}/{len(pdf_files)}] Extracting {pdf_path.name}")

        doc = fitz.open(pdf_path)

        pages = []

        for page_num in range(len(doc)):
            page = doc[page_num]

            page_text = page.get_text("text")

            if page_text:
                pages.append(page_text)

        doc.close()

        text = "\n".join(pages)

        if not text.strip():
            raise Exception("No text extracted")

        if looks_like_preeti(text):
            print("    -> Preeti detected, converting to Unicode")

            try:
                text = convert_text(text)
            except Exception as e:
                print(f"    -> Conversion failed: {e}")

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)

        size_mb = txt_path.stat().st_size / (1024 * 1024)

        print(
            f"    -> Saved {txt_path.name} "
            f"({size_mb:.2f} MB)"
        )

        success += 1

    except Exception as e:
        failed += 1
        print(f"    -> FAILED: {e}")

print("\n" + "=" * 50)
print(f"Completed")
print(f"Successful: {success}")
print(f"Failed: {failed}")
print("=" * 50)