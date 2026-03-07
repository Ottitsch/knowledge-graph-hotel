"""
Fetch hotel/accommodation POIs in Vienna from OpenStreetMap via the Overpass API.
Output: data/osm_hotels.json
"""

import requests
import json
import os
import sys
import time

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "osm_hotels.json")

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Query all nodes/ways/relations tagged as tourism accommodation in Wien
OVERPASS_QUERY = """
[out:json][timeout:60];
area["name"="Wien"]["admin_level"="4"]->.wien;
(
  node["tourism"~"hotel|apartment|hostel|guest_house|motel|chalet|alpine_hut"](area.wien);
  way["tourism"~"hotel|apartment|hostel|guest_house|motel|chalet|alpine_hut"](area.wien);
  node["building"="hotel"](area.wien);
  way["building"="hotel"](area.wien);
);
out body center;
"""


def fetch_osm() -> list:
    print("Querying OpenStreetMap Overpass API for Vienna accommodations ...")
    for attempt in range(3):
        try:
            resp = requests.post(OVERPASS_URL, data={"data": OVERPASS_QUERY}, timeout=90)
            resp.raise_for_status()
            data = resp.json()
            elements = data.get("elements", [])
            print(f"  Received {len(elements)} OSM elements")
            return elements
        except requests.exceptions.Timeout:
            wait = (attempt + 1) * 10
            print(f"  Timeout on attempt {attempt + 1}, waiting {wait}s ...")
            time.sleep(wait)
        except requests.exceptions.RequestException as e:
            print(f"  Request error: {e}", file=sys.stderr)
            if attempt == 2:
                raise
            time.sleep(5)
    return []


def normalize_elements(elements: list) -> list:
    """Extract useful fields from raw OSM elements."""
    results = []
    for el in elements:
        tags = el.get("tags", {})
        # For ways, Overpass 'out center' puts centroid in el["center"]
        center = el.get("center", {})
        lat = el.get("lat") or center.get("lat")
        lon = el.get("lon") or center.get("lon")
        results.append({
            "osm_type": el.get("type"),
            "osm_id": el.get("id"),
            "name": tags.get("name", ""),
            "tourism": tags.get("tourism", ""),
            "building": tags.get("building", ""),
            "operator": tags.get("operator", ""),
            "brand": tags.get("brand", ""),
            "stars": tags.get("stars", ""),
            "rooms": tags.get("rooms", ""),
            "addr_street": tags.get("addr:street", ""),
            "addr_housenumber": tags.get("addr:housenumber", ""),
            "addr_postcode": tags.get("addr:postcode", ""),
            "addr_city": tags.get("addr:city", ""),
            "website": tags.get("website", ""),
            "phone": tags.get("phone", ""),
            "email": tags.get("email", ""),
            "wikidata": tags.get("wikidata", ""),
            "wikipedia": tags.get("wikipedia", ""),
            "lat": lat,
            "lon": lon,
        })
    return results


def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    elements = fetch_osm()
    normalized = normalize_elements(elements)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(normalized)} OSM records to {OUTPUT_FILE}")
    if len(normalized) < 50:
        print("WARNING: Fewer than 50 results — Overpass may be rate-limiting or query needs adjustment.", file=sys.stderr)


if __name__ == "__main__":
    main()
