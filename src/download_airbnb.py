"""
Download the Inside Airbnb Vienna listings CSV.
Output: data/inside_airbnb_listings.csv

Inside Airbnb data is published at https://insideairbnb.com/get-the-data/
The Vienna dataset URL changes with each monthly snapshot.
This script tries known stable URLs and falls back to instructions.
"""

import os
import sys
import requests
import gzip
import shutil

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "inside_airbnb_listings.csv")

# Inside Airbnb stores data at paths like:
# http://data.insideairbnb.com/austria/vienna/vienna/YYYY-MM-DD/data/listings.csv.gz
# The exact date changes; we try recent known snapshots.
CANDIDATE_URLS = [
    "http://data.insideairbnb.com/austria/vienna/vienna/2024-09-21/data/listings.csv.gz",
    "http://data.insideairbnb.com/austria/vienna/vienna/2024-06-22/data/listings.csv.gz",
    "http://data.insideairbnb.com/austria/vienna/vienna/2024-03-23/data/listings.csv.gz",
    "http://data.insideairbnb.com/austria/vienna/vienna/2023-12-23/data/listings.csv.gz",
]


def download_and_extract(url: str, dest: str) -> bool:
    gz_path = dest + ".gz"
    print(f"  Trying {url} ...")
    try:
        resp = requests.get(url, timeout=120, stream=True)
        if resp.status_code == 200:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            with open(gz_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    f.write(chunk)
                    downloaded += len(chunk)
            print(f"  Downloaded {downloaded/1024/1024:.1f} MB")
            with gzip.open(gz_path, "rb") as f_in, open(dest, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
            os.remove(gz_path)
            return True
        else:
            print(f"  HTTP {resp.status_code}")
    except Exception as e:
        print(f"  Error: {e}")
    return False


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    if os.path.exists(OUTPUT_FILE):
        import pandas as pd
        df = pd.read_csv(OUTPUT_FILE, nrows=5)
        print(f"File already exists: {OUTPUT_FILE}")
        print(f"  Columns: {list(df.columns)[:8]}")
        return

    print("Downloading Inside Airbnb Vienna listings ...")
    for url in CANDIDATE_URLS:
        if download_and_extract(url, OUTPUT_FILE):
            import pandas as pd
            df = pd.read_csv(OUTPUT_FILE, nrows=5)
            # Quick count
            with open(OUTPUT_FILE) as f:
                line_count = sum(1 for _ in f) - 1
            print(f"Successfully downloaded: {line_count} listings")
            print(f"Saved to {OUTPUT_FILE}")
            return

    print("\nCould not download automatically (HTTP 403 - site blocks bots).")
    print("Manual steps:")
    print("  1. Open https://insideairbnb.com/get-the-data/ in your browser")
    print("  2. Find 'Vienna, Vienna, Austria' -> download 'listings.csv.gz'")
    print(f"  3. Extract the .gz file and save the CSV to:")
    print(f"     {OUTPUT_FILE}")
    sys.exit(1)


if __name__ == "__main__":
    main()
