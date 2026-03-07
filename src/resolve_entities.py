"""
Entity resolution: merge properties from data.gv.at, OSM, Wikidata, and Inside Airbnb
into a single unified CSV with source provenance.

Output: data/properties_unified.csv
"""

import os
import re
import json
import pandas as pd
import unicodedata

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(BASE_DIR, "data")

INPUT_DATAGV = os.path.join(DATA_DIR, "datagv_accommodations.csv")
INPUT_OSM = os.path.join(DATA_DIR, "osm_hotels.json")
INPUT_WIKIDATA = os.path.join(DATA_DIR, "wikidata_hotels.json")
INPUT_AIRBNB = os.path.join(DATA_DIR, "inside_airbnb_listings.csv")
OUTPUT_FILE = os.path.join(DATA_DIR, "properties_unified.csv")

# ------------------------------------------------------------------
# Known hotel chain keyword → canonical chain name mapping
# ------------------------------------------------------------------
CHAIN_KEYWORDS = {
    "marriott": "Marriott International",
    "sheraton": "Marriott International",
    "westin": "Marriott International",
    "renaissance": "Marriott International",
    "hilton": "Hilton Hotels & Resorts",
    "doubletree": "Hilton Hotels & Resorts",
    "hampton inn": "Hilton Hotels & Resorts",
    "accor": "AccorHotels",
    "ibis": "AccorHotels",
    "novotel": "AccorHotels",
    "sofitel": "AccorHotels",
    "mercure": "AccorHotels",
    "ihg": "IHG Hotels & Resorts",
    "holiday inn": "IHG Hotels & Resorts",
    "intercontinental": "IHG Hotels & Resorts",
    "crowne plaza": "IHG Hotels & Resorts",
    "vienna house": "Vienna House",
    "kempinski": "Kempinski Hotels",
    "motel one": "Motel One",
    "25hours": "25hours Hotels",
    "falkensteiner": "Falkensteiner Hotels",
    "austria trend": "Austria Trend Hotels",
    "nh hotel": "NH Hotels",
    "nh ": "NH Hotels",
    "radisson": "Radisson Hotel Group",
    "wyndham": "Wyndham Hotels",
    "premier inn": "Premier Inn",
    "ritz-carlton": "The Ritz-Carlton",
    "ritz carlton": "The Ritz-Carlton",
    "mandarin oriental": "Mandarin Oriental",
    "park hyatt": "Park Hyatt",
    "hyatt": "Park Hyatt",
    "best western": "Best Western",
    "meininger": "Meininger Hotels",
    "a&o": "A&O Hotels and Hostels",
}


def normalize_name(s: str) -> str:
    """Lowercase, remove accents, strip non-alphanumeric for fuzzy matching."""
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def detect_chain(name: str, operator: str = "") -> str:
    """Return canonical chain name if any keyword matches in name or operator."""
    combined = normalize_name(name) + " " + normalize_name(operator)
    for keyword, chain in CHAIN_KEYWORDS.items():
        if keyword in combined:
            return chain
    return ""


def load_datagv() -> pd.DataFrame:
    if not os.path.exists(INPUT_DATAGV):
        print(f"  data.gv.at file not found: {INPUT_DATAGV}")
        return pd.DataFrame()
    df = pd.read_csv(INPUT_DATAGV, encoding="utf-8")
    df["source"] = "datagv"
    df["property_type"] = df.get("category", "")
    df["operator_name"] = ""
    df["host_id"] = ""
    df["host_listings_count"] = None
    return df[["source", "name", "address", "district", "lat", "lon",
               "property_type", "operator_name", "host_id", "host_listings_count",
               "website", "phone", "email", "raw_id"]]


def load_osm() -> pd.DataFrame:
    if not os.path.exists(INPUT_OSM):
        print(f"  OSM file not found: {INPUT_OSM}")
        return pd.DataFrame()
    with open(INPUT_OSM, encoding="utf-8") as f:
        data = json.load(f)
    rows = []
    for el in data:
        address = " ".join(filter(None, [
            el.get("addr_street", ""), el.get("addr_housenumber", ""),
            el.get("addr_postcode", ""), el.get("addr_city", "")
        ]))
        rows.append({
            "source": "osm",
            "name": el.get("name", ""),
            "address": address,
            "district": "",
            "lat": el.get("lat"),
            "lon": el.get("lon"),
            "property_type": el.get("tourism") or el.get("building", ""),
            "operator_name": el.get("operator") or el.get("brand", ""),
            "host_id": "",
            "host_listings_count": None,
            "website": el.get("website", ""),
            "phone": el.get("phone", ""),
            "email": el.get("email", ""),
            "raw_id": f"osm:{el.get('osm_type','')}/{el.get('osm_id','')}",
        })
    return pd.DataFrame(rows)


def load_wikidata() -> pd.DataFrame:
    if not os.path.exists(INPUT_WIKIDATA):
        print(f"  Wikidata file not found: {INPUT_WIKIDATA}")
        return pd.DataFrame()
    with open(INPUT_WIKIDATA, encoding="utf-8") as f:
        data = json.load(f)
    rows = []
    for el in data:
        # Parse coordinate: "Point(lon lat)" format from Wikidata
        lat, lon = None, None
        coord = el.get("coord", "")
        if coord:
            m = re.match(r"Point\(([0-9.\-]+)\s+([0-9.\-]+)\)", coord)
            if m:
                lon, lat = float(m.group(1)), float(m.group(2))
        rows.append({
            "source": "wikidata",
            "name": el.get("hotel_name", ""),
            "address": "",
            "district": "",
            "lat": lat,
            "lon": lon,
            "property_type": "hotel",
            "operator_name": el.get("operator_name") or el.get("owner_name") or el.get("parent_org_name", ""),
            "host_id": el.get("hotel_uri", ""),
            "host_listings_count": None,
            "website": el.get("website", ""),
            "phone": "",
            "email": "",
            "raw_id": el.get("hotel_uri", ""),
        })
    return pd.DataFrame(rows)


def load_airbnb() -> pd.DataFrame:
    if not os.path.exists(INPUT_AIRBNB):
        print(f"  Inside Airbnb file not found: {INPUT_AIRBNB}")
        print("  Download from https://insideairbnb.com/vienna/ -> listings.csv")
        return pd.DataFrame()
    df = pd.read_csv(INPUT_AIRBNB, encoding="utf-8", low_memory=False)
    # Column names vary by snapshot; handle both naming conventions
    col_map = {
        "listing_url": "website",
        "name": "name",
        "host_id": "host_id",
        "host_name": "operator_name",
        "host_listings_count": "host_listings_count",
        "neighbourhood_cleansed": "district",
        "latitude": "lat",
        "longitude": "lon",
        "property_type": "property_type",
        "room_type": "room_type",
        "id": "raw_id",
    }
    rename = {k: v for k, v in col_map.items() if k in df.columns}
    df = df.rename(columns=rename)
    df["source"] = "airbnb"
    df["address"] = df.get("neighbourhood_cleansed", "")
    df["phone"] = ""
    df["email"] = ""

    keep = ["source", "name", "address", "district", "lat", "lon",
            "property_type", "operator_name", "host_id", "host_listings_count",
            "website", "phone", "email", "raw_id"]
    for col in keep:
        if col not in df.columns:
            df[col] = ""
    return df[keep]


def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Simple deduplication: group by normalized name. Keep row with most data.
    Mark all merged source provenance in a 'sources' column.
    """
    df = df.copy()
    df["name_norm"] = df["name"].apply(normalize_name)
    # Remove unnamed rows
    df = df[df["name_norm"].str.len() > 2].copy()

    # Group duplicates
    groups = df.groupby("name_norm")
    merged_rows = []
    for name_norm, group in groups:
        # Pick the row with the most non-empty fields as base
        scores = group.apply(lambda r: r.notna().sum() + (r != "").sum(), axis=1)
        base = group.loc[scores.idxmax()].copy()
        base["sources"] = ",".join(group["source"].unique())
        # Fill missing fields from other rows
        for col in ["address", "lat", "lon", "operator_name", "website", "phone"]:
            if not base[col] or pd.isna(base[col]):
                for _, row in group.iterrows():
                    if row[col] and not pd.isna(row[col]):
                        base[col] = row[col]
                        break
        merged_rows.append(base)

    result = pd.DataFrame(merged_rows)
    return result


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    print("Loading data sources ...")
    frames = []
    for loader, label in [(load_datagv, "data.gv.at"), (load_osm, "OSM"),
                          (load_wikidata, "Wikidata"), (load_airbnb, "Inside Airbnb")]:
        df = loader()
        if not df.empty:
            print(f"  {label}: {len(df)} records")
            frames.append(df)

    if not frames:
        print("ERROR: No data loaded. Run collection scripts first.", flush=True)
        return

    combined = pd.concat(frames, ignore_index=True)
    print(f"Combined: {len(combined)} total records before deduplication")

    unified = deduplicate(combined)
    print(f"After deduplication: {len(unified)} unique properties")

    # Detect chain membership
    unified["hotel_chain"] = unified.apply(
        lambda r: detect_chain(r.get("name", ""), r.get("operator_name", "")), axis=1
    )
    chain_count = (unified["hotel_chain"] != "").sum()
    print(f"Chain membership detected for {chain_count} properties")

    unified.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    print(f"Saved unified dataset to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
