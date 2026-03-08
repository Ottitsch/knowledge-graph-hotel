"""
Query Wikidata SPARQL for Vienna accommodations with operator, parent organization,
and brand enrichment.
Output: data/wikidata_hotels.json
"""

import json
import os
import sys
from SPARQLWrapper import SPARQLWrapper, JSON

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "wikidata_hotels.json")

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

QUERY = """
SELECT DISTINCT
  ?hotel ?hotelLabel
  ?operator ?operatorLabel
  ?owner ?ownerLabel
  ?parentOrg ?parentOrgLabel
  ?brand ?brandLabel
  ?website
  ?coord
WHERE {
  # Hotels directly located in Vienna (Q1741)
  ?hotel wdt:P131 wd:Q1741.
  # Must be some kind of accommodation
  VALUES ?hotelType { wd:Q27686 wd:Q2876219 wd:Q182228 wd:Q45776 wd:Q2060301 }
  ?hotel wdt:P31/wdt:P279* ?hotelType.

  OPTIONAL { ?hotel wdt:P137 ?operator. }
  OPTIONAL { ?hotel wdt:P127 ?owner. }
  OPTIONAL { ?hotel wdt:P749 ?parentOrg. }
  OPTIONAL { ?hotel wdt:P1716 ?brand. }
  OPTIONAL { ?hotel wdt:P856 ?website. }
  OPTIONAL { ?hotel wdt:P625 ?coord. }

  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,de". }
}
ORDER BY ?hotelLabel
"""


def fetch_wikidata() -> list:
    print("Querying Wikidata SPARQL for Vienna accommodations ...")
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    sparql.addCustomHttpHeader("User-Agent", "ViennaAccommodationOperatorKG/1.0 (academic research)")
    sparql.setQuery(QUERY)
    sparql.setReturnFormat(JSON)

    results = sparql.query().convert()
    bindings = results["results"]["bindings"]
    print(f"  Received {len(bindings)} SPARQL result rows")

    rows = []
    for b in bindings:
        def val(key):
            return b[key]["value"] if key in b else ""

        row = {
            "hotel_uri": val("hotel"),
            "hotel_name": val("hotelLabel"),
            "operator_uri": val("operator"),
            "operator_name": val("operatorLabel"),
            "owner_uri": val("owner"),
            "owner_name": val("ownerLabel"),
            "parent_org_uri": val("parentOrg"),
            "parent_org_name": val("parentOrgLabel"),
            "brand_uri": val("brand"),
            "brand_name": val("brandLabel"),
            "website": val("website"),
            "coord": val("coord"),
        }
        rows.append(row)
    return rows


def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    try:
        rows = fetch_wikidata()
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(rows)} Wikidata rows to {OUTPUT_FILE}")
        if len(rows) < 5:
            print("WARNING: Very few Wikidata results.", file=sys.stderr)
    except Exception as e:
        print(f"ERROR querying Wikidata: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
