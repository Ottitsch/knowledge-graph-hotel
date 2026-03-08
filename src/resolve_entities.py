"""
Entity resolution: merge records from data.gv.at, OSM, Wikidata, and Inside Airbnb
into a single unified CSV with source provenance and granularity labels.

Matching strategy (in priority order):
  1. Strong: same source-specific ID
  2. Strong: normalized name + coordinates within ~100m
  3. Strong: same website domain + coordinates within ~200m
  4. Medium: normalized name + similar address (establishment sources only)
  5. Airbnb listings are kept separate — not merged with establishment records.

Output: data/properties_unified.csv
"""

import os
import re
import json
import math
import uuid
import pandas as pd
import unicodedata
from urllib.parse import urlparse

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(BASE_DIR, "data")

INPUT_DATAGV = os.path.join(DATA_DIR, "datagv_accommodations.csv")
INPUT_OSM = os.path.join(DATA_DIR, "osm_hotels.json")
INPUT_WIKIDATA = os.path.join(DATA_DIR, "wikidata_hotels.json")
INPUT_AIRBNB = os.path.join(DATA_DIR, "inside_airbnb_listings.csv")
OUTPUT_FILE = os.path.join(DATA_DIR, "properties_unified.csv")

# Known hotel chain keyword → canonical chain name mapping
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

# District name corrections for encoding problems from Airbnb data
DISTRICT_FIXES = {
    "landstra\u00a7e": "Landstraße",
    "landstrae": "Landstraße",
    "landstra§e": "Landstraße",
    "rudolfsheim f\u00fcnfhaus": "Rudolfsheim-Fünfhaus",
    "rudolfsheim funfhaus": "Rudolfsheim-Fünfhaus",
    "rudolfsheim-f\u00fcnfhaus": "Rudolfsheim-Fünfhaus",
    "favoriten": "Favoriten",
    "hernals": "Hernals",
    "wahring": "Währing",
    "w\u00e4hring": "Währing",
    "donaustadt": "Donaustadt",
    "floridsdorf": "Floridsdorf",
    "liesing": "Liesing",
    "simmering": "Simmering",
    "meidling": "Meidling",
    "penzing": "Penzing",
    "ottakring": "Ottakring",
    "brigittenau": "Brigittenau",
    "leopoldstadt": "Leopoldstadt",
    "alsergrund": "Alsergrund",
    "josefstadt": "Josefstadt",
    "neubau": "Neubau",
    "mariahilf": "Mariahilf",
    "innere stadt": "Innere Stadt",
    "wieden": "Wieden",
    "margareten": "Margareten",
    "hietzing": "Hietzing",
    "d\u00f6bling": "Döbling",
    "dobling": "Döbling",
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


def normalize_district(s: str) -> str:
    """Fix known encoding problems and normalize district names."""
    if not isinstance(s, str) or not s.strip():
        return ""
    # Try direct fix after lowercasing
    lower = s.strip().lower()
    if lower in DISTRICT_FIXES:
        return DISTRICT_FIXES[lower]
    # Try to fix § → ß (latin small letter sharp s)
    fixed = s.replace("§", "ß")
    lower_fixed = fixed.strip().lower()
    if lower_fixed in DISTRICT_FIXES:
        return DISTRICT_FIXES[lower_fixed]
    return s.strip()


def extract_domain(url: str) -> str:
    """Extract bare domain from a URL for matching."""
    if not isinstance(url, str) or not url.strip():
        return ""
    try:
        parsed = urlparse(url if "://" in url else "http://" + url)
        domain = parsed.netloc.lower().lstrip("www.")
        return domain
    except Exception:
        return ""


def haversine_m(lat1, lon1, lat2, lon2) -> float:
    """Distance in metres between two lat/lon points."""
    if any(x is None for x in [lat1, lon1, lat2, lon2]):
        return float("inf")
    R = 6371000
    phi1, phi2 = math.radians(float(lat1)), math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlam = math.radians(float(lon2) - float(lon1))
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def detect_chain(name: str, operator: str = "") -> str:
    combined = normalize_name(name) + " " + normalize_name(operator)
    for keyword, chain in CHAIN_KEYWORDS.items():
        if keyword in combined:
            return chain
    return ""


# ──────────────────────────────────────────────────────────────
# Loaders
# ──────────────────────────────────────────────────────────────

ESTABLISHMENT_COLS = [
    "source", "granularity", "name", "address", "district", "lat", "lon",
    "unit_type", "operator_name", "host_id", "host_listings_count",
    "website", "picture_url", "phone", "email", "raw_id",
]

LISTING_COLS = ESTABLISHMENT_COLS  # same schema


def _empty_frame():
    return pd.DataFrame(columns=ESTABLISHMENT_COLS)


def load_datagv() -> pd.DataFrame:
    if not os.path.exists(INPUT_DATAGV):
        print(f"  data.gv.at file not found: {INPUT_DATAGV}")
        return _empty_frame()
    df = pd.read_csv(INPUT_DATAGV, encoding="utf-8")
    # Drop rows where name is empty
    df = df[df["name"].notna() & (df["name"].astype(str).str.strip() != "")]
    out = pd.DataFrame()
    out["source"] = "datagv"
    out["granularity"] = "establishment"
    out["name"] = df["name"].astype(str)
    out["address"] = df.get("address", "").fillna("").astype(str)
    out["district"] = df.get("district", "").fillna("").astype(str).apply(normalize_district)
    out["lat"] = pd.to_numeric(df.get("lat"), errors="coerce")
    out["lon"] = pd.to_numeric(df.get("lon"), errors="coerce")
    out["unit_type"] = df.get("category", "").fillna("").astype(str)
    out["operator_name"] = ""
    out["host_id"] = ""
    out["host_listings_count"] = None
    out["website"] = df.get("website", "").fillna("").astype(str)
    out["picture_url"] = ""
    out["phone"] = df.get("phone", "").fillna("").astype(str)
    out["email"] = df.get("email", "").fillna("").astype(str)
    out["raw_id"] = df.get("raw_id", "").fillna("").astype(str).apply(lambda x: f"datagv:{x}")
    return out.reset_index(drop=True)


def load_osm() -> pd.DataFrame:
    if not os.path.exists(INPUT_OSM):
        print(f"  OSM file not found: {INPUT_OSM}")
        return _empty_frame()
    with open(INPUT_OSM, encoding="utf-8") as f:
        data = json.load(f)
    rows = []
    for el in data:
        address = el.get("address", "") or " ".join(filter(None, [
            el.get("addr_street", ""), el.get("addr_housenumber", ""),
            el.get("addr_postcode", ""), el.get("addr_city", "")
        ]))
        rows.append({
            "source": "osm",
            "granularity": "establishment",
            "name": el.get("name", ""),
            "address": address.strip(),
            "district": "",
            "lat": el.get("lat"),
            "lon": el.get("lon"),
            "unit_type": el.get("tourism") or el.get("building", ""),
            "operator_name": el.get("operator") or el.get("brand", ""),
            "host_id": "",
            "host_listings_count": None,
            "website": el.get("website", ""),
            "picture_url": "",
            "phone": el.get("phone", ""),
            "email": el.get("email", ""),
            "raw_id": f"osm:{el.get('osm_type','')}/{el.get('osm_id','')}",
        })
    return pd.DataFrame(rows, columns=ESTABLISHMENT_COLS)


def load_wikidata() -> pd.DataFrame:
    if not os.path.exists(INPUT_WIKIDATA):
        print(f"  Wikidata file not found: {INPUT_WIKIDATA}")
        return _empty_frame()
    with open(INPUT_WIKIDATA, encoding="utf-8") as f:
        data = json.load(f)
    rows = []
    for el in data:
        lat, lon = None, None
        coord = el.get("coord", "")
        if coord:
            m = re.match(r"Point\(([0-9.\-]+)\s+([0-9.\-]+)\)", coord)
            if m:
                lon, lat = float(m.group(1)), float(m.group(2))
        operator = (
            el.get("operator_name")
            or el.get("parent_org_name")
            or el.get("brand_name")
            or el.get("owner_name")
            or ""
        )
        rows.append({
            "source": "wikidata",
            "granularity": "establishment",
            "name": el.get("hotel_name", ""),
            "address": "",
            "district": "",
            "lat": lat,
            "lon": lon,
            "unit_type": "hotel",
            "operator_name": operator,
            "host_id": el.get("hotel_uri", ""),
            "host_listings_count": None,
            "website": el.get("website", ""),
            "picture_url": "",
            "phone": "",
            "email": "",
            "raw_id": el.get("hotel_uri", ""),
        })
    return pd.DataFrame(rows, columns=ESTABLISHMENT_COLS)


def load_airbnb() -> pd.DataFrame:
    if not os.path.exists(INPUT_AIRBNB):
        print(f"  Inside Airbnb file not found: {INPUT_AIRBNB}")
        print("  Download from https://insideairbnb.com/vienna/ -> listings.csv")
        return _empty_frame()
    df = pd.read_csv(INPUT_AIRBNB, encoding="utf-8", low_memory=False)
    col_map = {
        "listing_url": "website",
        "picture_url": "picture_url",
        "name": "name",
        "host_id": "host_id",
        "host_name": "operator_name",
        "host_listings_count": "host_listings_count",
        "neighbourhood_cleansed": "district",
        "latitude": "lat",
        "longitude": "lon",
        "property_type": "unit_type",
        "id": "raw_id",
    }
    rename = {k: v for k, v in col_map.items() if k in df.columns}
    df = df.rename(columns=rename)
    df["source"] = "airbnb"
    df["granularity"] = "listing"
    df["address"] = df.get("district", "")
    df["phone"] = ""
    df["email"] = ""
    if "district" in df.columns:
        df["district"] = df["district"].fillna("").astype(str).apply(normalize_district)

    keep = LISTING_COLS
    for col in keep:
        if col not in df.columns:
            df[col] = ""
    df["raw_id"] = df["raw_id"].astype(str).apply(lambda x: f"airbnb:{x}")
    return df[keep].copy()


# ──────────────────────────────────────────────────────────────
# Entity resolution
# ──────────────────────────────────────────────────────────────

def _is_generic_name(name_norm: str) -> bool:
    """Return True if the normalized name is too generic to merge on alone."""
    generic = {
        "modern apartment", "cozy apartment", "nice apartment", "studio apartment",
        "beautiful apartment", "central apartment", "bright apartment", "lovely apartment",
        "spacious apartment", "comfortable apartment", "apartment", "room", "studio",
        "private room", "entire apartment", "home", "flat", "holiday apartment",
    }
    return name_norm in generic or len(name_norm) < 4


def merge_establishment_sources(frames: list) -> pd.DataFrame:
    """
    Merge establishment-level records (OSM, Wikidata, datagv) using staged matching.
    Returns a deduplicated DataFrame with provenance fields.
    """
    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    combined["name_norm"] = combined["name"].apply(normalize_name)
    combined["domain"] = combined["website"].apply(extract_domain)
    combined = combined[combined["name_norm"].str.len() > 2].copy()

    # Union-find for grouping
    n = len(combined)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        parent[find(x)] = find(y)

    rows = combined.reset_index(drop=True)

    # Build indices for fast lookup
    name_index = {}   # name_norm → list of row indices
    domain_index = {} # domain → list of row indices

    for i, row in rows.iterrows():
        nn = row["name_norm"]
        dom = row["domain"]
        name_index.setdefault(nn, []).append(i)
        if dom:
            domain_index.setdefault(dom, []).append(i)

    # Pass 1: same normalized name + coordinates within ~100m
    for nn, idxs in name_index.items():
        if _is_generic_name(nn):
            continue
        for a in range(len(idxs)):
            for b in range(a + 1, len(idxs)):
                ia, ib = idxs[a], idxs[b]
                ra, rb = rows.iloc[ia], rows.iloc[ib]
                dist = haversine_m(ra["lat"], ra["lon"], rb["lat"], rb["lon"])
                if dist < 100:
                    union(ia, ib)

    # Pass 2: same website domain + coordinates within ~200m
    for dom, idxs in domain_index.items():
        if len(dom) < 5:
            continue
        for a in range(len(idxs)):
            for b in range(a + 1, len(idxs)):
                ia, ib = idxs[a], idxs[b]
                ra, rb = rows.iloc[ia], rows.iloc[ib]
                dist = haversine_m(ra["lat"], ra["lon"], rb["lat"], rb["lon"])
                if dist < 200:
                    union(ia, ib)

    # Build merged groups
    groups = {}
    for i in range(n):
        root = find(i)
        groups.setdefault(root, []).append(i)

    merged_rows = []
    for root, idxs in groups.items():
        group = rows.iloc[idxs]
        # Pick row with most non-empty fields
        scores = group.apply(lambda r: r.notna().sum() + (r.astype(str) != "").sum(), axis=1)
        base = group.loc[scores.idxmax()].copy()

        source_names = sorted(group["source"].unique().tolist())
        source_ids = sorted(group["raw_id"].dropna().unique().tolist())

        base["source_names"] = ",".join(source_names)
        base["source_record_ids"] = ",".join(str(x) for x in source_ids)
        base["merge_confidence"] = "strong" if len(idxs) > 1 else "single"
        base["canonical_id"] = str(uuid.uuid4())

        # Fill missing fields from other rows
        for col in ["address", "lat", "lon", "operator_name", "website", "phone", "district"]:
            val = base.get(col)
            if not val or (isinstance(val, float) and math.isnan(val)):
                for _, row in group.iterrows():
                    v = row.get(col)
                    if v and not (isinstance(v, float) and math.isnan(v)):
                        base[col] = v
                        break

        merged_rows.append(base)

    return pd.DataFrame(merged_rows)


def keep_airbnb_listings(df: pd.DataFrame) -> pd.DataFrame:
    """
    Airbnb listings are kept as-is (listing granularity).
    We deduplicate only true duplicates within Airbnb (same raw_id).
    """
    df = df.drop_duplicates(subset=["raw_id"])
    df["name_norm"] = df["name"].apply(normalize_name)
    df["source_names"] = "airbnb"
    df["source_record_ids"] = df["raw_id"].astype(str)
    df["merge_confidence"] = "single"
    df["canonical_id"] = [str(uuid.uuid4()) for _ in range(len(df))]
    df["domain"] = df["website"].apply(extract_domain)
    return df


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    print("Loading data sources ...")

    establishment_frames = []
    for loader, label in [
        (load_datagv, "data.gv.at"),
        (load_osm, "OSM"),
        (load_wikidata, "Wikidata"),
    ]:
        df = loader()
        if not df.empty:
            print(f"  {label}: {len(df)} records")
            establishment_frames.append(df)
        else:
            print(f"  {label}: 0 records (skipped)")

    airbnb_df = load_airbnb()
    if not airbnb_df.empty:
        print(f"  Inside Airbnb: {len(airbnb_df)} records")
    else:
        print("  Inside Airbnb: 0 records (skipped)")

    if not establishment_frames and airbnb_df.empty:
        print("ERROR: No data loaded. Run collection scripts first.")
        return

    # Merge establishment sources
    establishment_unified = pd.DataFrame()
    if establishment_frames:
        print("\nResolving establishment-level records ...")
        establishment_unified = merge_establishment_sources(establishment_frames)
        print(f"  After merging: {len(establishment_unified)} unique establishments")

    # Keep Airbnb listings separate
    airbnb_unified = pd.DataFrame()
    if not airbnb_df.empty:
        airbnb_unified = keep_airbnb_listings(airbnb_df)
        print(f"  Airbnb listings kept: {len(airbnb_unified)}")

    # Combine
    all_frames = [f for f in [establishment_unified, airbnb_unified] if not f.empty]
    if not all_frames:
        print("ERROR: No unified data to save.")
        return

    unified = pd.concat(all_frames, ignore_index=True)

    # Add operator_name_normalized
    unified["operator_name_normalized"] = unified["operator_name"].apply(normalize_name)

    # Detect chain membership
    unified["hotel_chain"] = unified.apply(
        lambda r: detect_chain(r.get("name", ""), r.get("operator_name", "")), axis=1
    )
    chain_count = (unified["hotel_chain"] != "").sum()
    print(f"  Chain membership detected for {chain_count} units")

    # Summary
    print(f"\nTotal unified records: {len(unified)}")
    if "granularity" in unified.columns:
        for g, cnt in unified["granularity"].value_counts().items():
            print(f"  {g}: {cnt}")
    if "source_names" in unified.columns:
        source_counts = {}
        for sources in unified["source_names"].dropna():
            for s in sources.split(","):
                s = s.strip()
                if s:
                    source_counts[s] = source_counts.get(s, 0) + 1
        for s, cnt in sorted(source_counts.items(), key=lambda x: -x[1]):
            print(f"  observed in {s}: {cnt}")

    unified.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    print(f"\nSaved unified dataset to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
