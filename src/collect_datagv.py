"""
Fetch Vienna accommodation list from the open data.gv.at API.
Output: data/datagv_accommodations.csv
"""

import requests
import pandas as pd
import json
import os
import sys

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "datagv_accommodations.csv")

# data.gv.at WFS endpoint for "Hotels und Unterkünfte Standorte Wien"
# Resource ID from https://www.data.gv.at/katalog/dataset/hotels-und-unterkunfte-in-wien
WFS_URL = (
    "https://data.wien.gv.at/daten/geo"
    "?service=WFS"
    "&request=GetFeature"
    "&version=1.1.0"
    "&typeName=ogdwien:UNTERKUNFTOGD"
    "&outputFormat=json"
    "&srsName=EPSG:4326"
)


def fetch_datagv() -> pd.DataFrame:
    print("Fetching Vienna accommodation data from data.gv.at WFS ...")
    resp = requests.get(WFS_URL, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    features = data.get("features", [])
    print(f"  Received {len(features)} features")

    rows = []
    for feat in features:
        props = feat.get("properties", {})
        geom = feat.get("geometry", {})
        coords = geom.get("coordinates", [None, None]) if geom else [None, None]
        rows.append({
            "source": "datagv",
            "name": props.get("NAME", ""),
            "category": props.get("KATEGORIE", ""),
            "address": props.get("ADRESSE", ""),
            "district": props.get("BEZIRK", ""),
            "postal_code": props.get("PLZ", ""),
            "phone": props.get("TELEFON", ""),
            "email": props.get("EMAIL", ""),
            "website": props.get("WEBLINK1", ""),
            "lon": coords[0] if len(coords) > 0 else None,
            "lat": coords[1] if len(coords) > 1 else None,
            "raw_id": props.get("OBJECTID", ""),
        })

    df = pd.DataFrame(rows)
    return df


def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df = fetch_datagv()
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    print(f"Saved {len(df)} rows to {OUTPUT_FILE}")
    if len(df) < 10:
        print("WARNING: Very few results — check WFS endpoint availability.", file=sys.stderr)


if __name__ == "__main__":
    main()
