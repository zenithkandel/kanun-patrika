import os
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

PDF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdfs")
URLS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "urls.txt")
MAX_WORKERS = 40


def download_pdf(url):
    filename = os.path.basename(urlparse(url).path)
    filepath = os.path.join(PDF_DIR, filename)
    if os.path.exists(filepath):
        return filename, "skipped"
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

    ok = skipped = failed = 0
    pbar = tqdm(total=len(urls), desc="Downloading", unit="file", ncols=100)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(download_pdf, url): url for url in urls}
        for future in as_completed(futures):
            name, status = future.result()
            if status == "ok":
                ok += 1
            elif status == "skipped":
                skipped += 1
            else:
                failed += 1
            pbar.set_postfix(ok=ok, skip=skipped, fail=failed, refresh=False)
            pbar.update(1)

    pbar.close()
    print(f"\nDone. {ok} downloaded, {skipped} skipped, {failed} failed.")


if __name__ == "__main__":
    main()
