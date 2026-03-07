"""
Look up known hotel operator names in the Austrian Firmenbuch (company registry)
via the free opendata.host API.
Input:  data/properties_unified.csv  (operator_name column)
Output: data/firmenbuch_companies.json
"""

import requests
import json
import os
import sys
import time
import pandas as pd

INPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "properties_unified.csv")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "firmenbuch_companies.json")

# Austrian Firmenbuch — no free public API exists.
# The official portal is https://justizonline.gv.at/jop/web/firmenbuchabfrage
# which requires manual interaction or a paid subscription.
# This script records known operators for future enrichment when an API is available.
FIRMENBUCH_URL = None  # placeholder — DNS does not resolve to a real endpoint


def search_company(name: str, session: requests.Session) -> dict:
    """Placeholder: no free Firmenbuch API is available. Returns empty dict."""
    # The official Firmenbuch portal (justizonline.gv.at) requires a paid subscription
    # or manual lookup. When a real endpoint becomes available, implement here.
    return {}


def get_operator_names() -> list:
    """Load unique operator names from unified properties CSV."""
    if not os.path.exists(INPUT_FILE):
        print(f"  {INPUT_FILE} not found — using built-in known operators list")
        return KNOWN_OPERATORS

    df = pd.read_csv(INPUT_FILE, encoding="utf-8")
    if "operator_name" not in df.columns:
        print("  No 'operator_name' column found, using known operators list")
        return KNOWN_OPERATORS

    names = df["operator_name"].dropna().unique().tolist()
    # Also add known major operators
    names = list(set(names + KNOWN_OPERATORS))
    return [n for n in names if n.strip()]


# Well-known Vienna hotel operators to always look up
KNOWN_OPERATORS = [
    "Marriott International",
    "Hilton Hotels & Resorts",
    "AccorHotels",
    "IHG Hotels & Resorts",
    "Vienna House",
    "Kempinski Hotels",
    "Motel One",
    "25hours Hotels",
    "Falkensteiner Hotels",
    "Austria Trend Hotels",
    "Hotel de France Wien",
    "NH Hotels",
    "Radisson Hotel Group",
    "Wyndham Hotels",
    "Premier Inn",
    "ibis Hotels",
    "Novotel",
    "Sofitel",
    "The Ritz-Carlton",
    "Mandarin Oriental",
    "Park Hyatt",
]


def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    operator_names = get_operator_names()
    print(f"Looking up {len(operator_names)} operators in Firmenbuch ...")

    results = []
    session = requests.Session()
    session.headers.update({"User-Agent": "ViennaHotelKG/1.0 (academic research)"})

    print("  NOTE: No free Firmenbuch API is available.")
    print("  Recording operator names for future manual/paid enrichment.")
    for name in operator_names:
        results.append({
            "query_name": name,
            "firmenbuch_match": {},
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    matched = sum(1 for r in results if r["firmenbuch_match"])
    print(f"Saved {len(results)} lookups ({matched} matched) to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
