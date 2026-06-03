import os
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

PDF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdfs")
URLS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "urls.txt")
MAX_WORKERS = 10


def download_pdf(url):
    filename = os.path.basename(urlparse(url).path)
    filepath = os.path.join(PDF_DIR, filename)
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(resp.content)
        return filename, "ok"
    except Exception as e:
        return filename, str(e)


def main():
    os.makedirs(PDF_DIR, exist_ok=True)

    with open(URLS_FILE, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    existing = set(os.listdir(PDF_DIR))
    failed_urls = [
        url for url in urls
        if os.path.basename(urlparse(url).path) not in existing
    ]

    if not failed_urls:
        print("No failed downloads found. All files exist.")
        return

    print(f"Found {len(failed_urls)} failed/missing PDFs. Retrying...")

    ok = failed = 0
    pbar = tqdm(total=len(failed_urls), desc="Retrying", unit="file", ncols=100)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(download_pdf, url): url for url in failed_urls}
        for future in as_completed(futures):
            name, status = future.result()
            if status == "ok":
                ok += 1
            else:
                failed += 1
                print(f"  FAILED: {name} -> {status}")
            pbar.set_postfix(ok=ok, fail=failed, refresh=False)
            pbar.update(1)

    pbar.close()
    print(f"\nDone. {ok} downloaded, {failed} still failed.")


if __name__ == "__main__":
    main()
