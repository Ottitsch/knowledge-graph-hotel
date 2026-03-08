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
DEBUG_JSON = os.path.join(os.path.dirname(__file__), "..", "data", "datagv_debug_sample.json")

# data.gv.at WFS endpoint for "Hotels und Unterkünfte Standorte Wien"
WFS_URL = (
    "https://data.wien.gv.at/daten/geo"
    "?service=WFS"
    "&request=GetFeature"
    "&version=1.1.0"
    "&typeName=ogdwien:UNTERKUNFTOGD"
    "&outputFormat=json"
    "&srsName=EPSG:4326"
)


def fetch_datagv(debug: bool = False) -> pd.DataFrame:
    print("Fetching Vienna accommodation data from data.gv.at WFS ...")
    resp = requests.get(WFS_URL, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    features = data.get("features", [])
    print(f"  Received {len(features)} features")

    if not features:
        print("WARNING: No features returned from WFS endpoint.", file=sys.stderr)
        return pd.DataFrame()

    # Inspect available property keys from first feature
    first_props = features[0].get("properties", {})
    print(f"  Available property keys: {list(first_props.keys())}")

    if debug:
        sample = [f.get("properties", {}) for f in features[:5]]
        with open(DEBUG_JSON, "w", encoding="utf-8") as fh:
            json.dump(sample, fh, ensure_ascii=False, indent=2)
        print(f"  Saved debug sample to {DEBUG_JSON}")

    rows = []
    for feat in features:
        props = feat.get("properties", {})
        geom = feat.get("geometry", {})
        coords = geom.get("coordinates", [None, None]) if geom else [None, None]

        # WFS actual field names (verified via --debug): BETRIEB, BETRIEBSART_TXT,
        # ADRESSE, BEZIRK, KONTAKT_EMAIL, KONTAKT_TEL, WEBLINK1
        name = (
            props.get("BETRIEB")
            or props.get("NAME")
            or props.get("BEZEICHNUNG")
            or ""
        )
        category = (
            props.get("BETRIEBSART_TXT")
            or props.get("KATEGORIE_TXT")
            or props.get("BETRIEBSART")
            or props.get("KATEGORIE")
            or ""
        )
        address = props.get("ADRESSE") or props.get("STRASSE") or ""
        district = props.get("BEZIRK") or props.get("BEZIRK_NR") or ""

        rows.append({
            "source": "datagv",
            "name": name,
            "category": category,
            "address": address,
            "district": str(district) if district else "",
            "postal_code": props.get("PLZ", ""),
            "phone": props.get("KONTAKT_TEL", "") or props.get("TELEFON", ""),
            "email": props.get("KONTAKT_EMAIL", "") or props.get("EMAIL", ""),
            "website": props.get("WEBLINK1", "") or props.get("WEBSITE", ""),
            "lon": coords[0] if coords and len(coords) > 0 else None,
            "lat": coords[1] if coords and len(coords) > 1 else None,
            "raw_id": props.get("OBJECTID", "") or props.get("objectid", ""),
        })

    df = pd.DataFrame(rows)

    # Validate name coverage
    empty_names = df["name"].isna() | (df["name"] == "")
    empty_pct = empty_names.sum() / max(len(df), 1)
    if empty_pct > 0.8:
        print(
            f"ERROR: {empty_pct:.0%} of rows have empty names. "
            f"Check WFS property keys above and update field name mapping.",
            file=sys.stderr,
        )
        print(f"  First feature properties: {first_props}", file=sys.stderr)
        sys.exit(1)

    print(f"  Name coverage: {(~empty_names).sum()}/{len(df)} rows have a name")
    return df


def main():
    debug = "--debug" in sys.argv
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df = fetch_datagv(debug=debug)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    print(f"Saved {len(df)} rows to {OUTPUT_FILE}")
    if len(df) < 10:
        print("WARNING: Very few results — check WFS endpoint availability.", file=sys.stderr)


if __name__ == "__main__":
    main()
