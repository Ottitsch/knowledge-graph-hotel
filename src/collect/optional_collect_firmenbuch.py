"""
OPTIONAL / FUTURE WORK - Austrian Firmenbuch (company registry) enrichment.

This script is NOT part of the default pipeline. It is kept here for future use
when a free or institutional API becomes available.

Background: The official Firmenbuch portal (justizonline.gv.at) requires a paid
subscription (~€18/lookup) or manual interaction. Legal ownership via Firmenbuch
is therefore out of scope for the current project.

If/when an API is available, implement search_company() below and run this script
manually as an optional enrichment step after resolve_entities.py.

Input:  data/properties_unified.csv  (operator_name column)
Output: data/firmenbuch_companies.json
"""

import requests
import json
import os
import sys
import pandas as pd

INPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "properties_unified.csv")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "firmenbuch_companies.json")


def search_company(name: str, session: requests.Session) -> dict:
    """Placeholder: no free Firmenbuch API is available. Returns empty dict."""
    return {}


def get_operator_names() -> list:
    if not os.path.exists(INPUT_FILE):
        print(f"  {INPUT_FILE} not found.")
        return []
    df = pd.read_csv(INPUT_FILE, encoding="utf-8")
    if "operator_name" not in df.columns:
        return []
    names = df["operator_name"].dropna().unique().tolist()
    return [n for n in names if str(n).strip()]


def main():
    print("NOTE: Firmenbuch enrichment is optional and currently non-functional.")
    print("      No free Firmenbuch API is available. This script records operator")
    print("      names for future manual/paid enrichment only.")
    print()

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    operator_names = get_operator_names()
    print(f"Found {len(operator_names)} operators in unified dataset.")

    results = [{"query_name": name, "firmenbuch_match": {}} for name in operator_names]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(results)} operator names to {OUTPUT_FILE}")
    print("To add real data, implement search_company() when an API is available.")


if __name__ == "__main__":
    main()
