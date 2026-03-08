"""
Build the Vienna Accommodation Operator Knowledge Graph.

Reads: data/properties_unified.csv, data/wikidata_hotels.json
Writes:
  - Neo4j graph (via bolt driver) — requires running Neo4j instance
  - graph/vienna_accommodation_operator_kg.ttl (RDF Turtle)

Environment variables (optional, for Neo4j):
  NEO4J_URI      default: bolt://localhost:7687
  NEO4J_USER     default: neo4j
  NEO4J_PASSWORD default: password
"""

import os
import re
import json
import pandas as pd
from dotenv import load_dotenv
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, OWL, XSD
from rdflib.namespace import FOAF

load_dotenv()

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(BASE_DIR, "data")
GRAPH_DIR = os.path.join(BASE_DIR, "graph")

INPUT_UNIFIED = os.path.join(DATA_DIR, "properties_unified.csv")
INPUT_WIKIDATA = os.path.join(DATA_DIR, "wikidata_hotels.json")
OUTPUT_TTL = os.path.join(GRAPH_DIR, "vienna_accommodation_operator_kg.ttl")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Source name → canonical label
SOURCE_LABELS = {
    "airbnb": "InsideAirbnb",
    "osm": "OpenStreetMap",
    "wikidata": "Wikidata",
    "datagv": "data.gv.at",
}

# RDF namespaces
VAOK = Namespace("http://example.org/vienna-accommodation-operator-kg/")
SCHEMA = Namespace("http://schema.org/")
GEO = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")


def slugify(s: str) -> str:
    if not isinstance(s, str):
        return "unknown"
    s = re.sub(r"[^\w\s-]", "", s.lower())
    s = re.sub(r"[\s_-]+", "_", s)
    return s.strip("_") or "unknown"


def _operator_id(op_name: str, host_id: str) -> str:
    if host_id and host_id not in ("", "nan", "None"):
        return f"airbnb:{host_id}"
    return f"name:{slugify(op_name)}"


# ──────────────────────────────────────────────────────────────
# Neo4j
# ──────────────────────────────────────────────────────────────

def build_neo4j(df: pd.DataFrame, wikidata: list):
    try:
        from neo4j import GraphDatabase
    except ImportError:
        print("  neo4j driver not installed — skipping Neo4j ingestion")
        print("  Install with: pip install neo4j")
        return

    print(f"Connecting to Neo4j at {NEO4J_URI} ...")
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
    except Exception as e:
        print(f"  Cannot connect to Neo4j: {e}")
        print("  Skipping Neo4j ingestion. Start Neo4j and retry.")
        return

    with driver.session() as session:
        _create_constraints(session)
        _ingest_sources(session)
        _ingest_districts(session, df)
        _ingest_units(session, df)
        _ingest_operators(session, df)
        _ingest_chains(session, df, wikidata)

    driver.close()
    print("Neo4j ingestion complete.")


def _run(session, query, **params):
    session.run(query, **params)


def _create_constraints(session):
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (u:AccommodationUnit) REQUIRE u.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (o:Operator) REQUIRE o.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:HotelChain) REQUIRE c.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (d:District) REQUIRE d.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Source) REQUIRE s.name IS UNIQUE",
        "CREATE INDEX IF NOT EXISTS FOR (o:Operator) ON (o.name)",
    ]
    for c in constraints:
        try:
            session.run(c)
        except Exception:
            pass


def _ingest_sources(session):
    for label in SOURCE_LABELS.values():
        session.run("MERGE (s:Source {name: $name})", name=label)


def _ingest_districts(session, df: pd.DataFrame):
    districts = df["district"].dropna().unique()
    for d in districts:
        d = str(d).strip()
        if d:
            session.run("MERGE (d:District {name: $name})", name=d)


def _ingest_units(session, df: pd.DataFrame):
    print(f"  Ingesting {len(df)} accommodation units ...")
    for _, row in df.iterrows():
        name = str(row.get("name", "")).strip()
        if not name:
            continue
        unit_id = str(row.get("canonical_id", "")) or slugify(f"{name}_{row.get('raw_id','')}")
        query = """
        MERGE (u:AccommodationUnit {id: $id})
        SET u.name = $name,
            u.address = $address,
            u.unit_type = $unit_type,
            u.granularity = $granularity,
            u.lat = $lat,
            u.lon = $lon,
            u.website = $website,
            u.picture_url = $picture_url,
            u.source_names = $source_names,
            u.source_record_ids = $source_record_ids,
            u.merge_confidence = $merge_confidence
        """
        session.run(
            query,
            id=unit_id,
            name=name,
            address=str(row.get("address", "")),
            unit_type=str(row.get("unit_type", row.get("property_type", ""))),
            granularity=str(row.get("granularity", "")),
            lat=float(row["lat"]) if pd.notna(row.get("lat")) else None,
            lon=float(row["lon"]) if pd.notna(row.get("lon")) else None,
            website=str(row.get("website", "")),
            picture_url=str(row.get("picture_url", "")),
            source_names=str(row.get("source_names", row.get("source", ""))),
            source_record_ids=str(row.get("source_record_ids", row.get("raw_id", ""))),
            merge_confidence=str(row.get("merge_confidence", "")),
        )

        # Link to district
        district = str(row.get("district", "")).strip()
        if district:
            session.run("""
            MATCH (u:AccommodationUnit {id: $uid}), (d:District {name: $dname})
            MERGE (u)-[:LOCATED_IN]->(d)
            """, uid=unit_id, dname=district)

        # Link to sources
        source_names_str = str(row.get("source_names", row.get("source", "")))
        for src_key in source_names_str.split(","):
            src_key = src_key.strip()
            canonical = SOURCE_LABELS.get(src_key, src_key)
            if canonical:
                session.run("""
                MATCH (u:AccommodationUnit {id: $uid}), (s:Source {name: $sname})
                MERGE (u)-[:OBSERVED_IN]->(s)
                """, uid=unit_id, sname=canonical)


def _ingest_operators(session, df: pd.DataFrame):
    op_col = "operator_name"
    op_df = df[df[op_col].notna() & (df[op_col].astype(str).str.strip() != "")]
    print(f"  Ingesting operators for {len(op_df)} units ...")
    for _, row in op_df.iterrows():
        op_name = str(row[op_col]).strip()
        if not op_name:
            continue
        unit_id = str(row.get("canonical_id", "")) or slugify(f"{row.get('name','')}_{row.get('raw_id','')}")
        host_id = str(row.get("host_id", ""))
        op_id = _operator_id(op_name, host_id)
        listings = int(row["host_listings_count"]) if pd.notna(row.get("host_listings_count")) else None
        session.run("""
        MERGE (o:Operator {id: $op_id})
        SET o.name = $name,
            o.airbnb_host_id = $host_id,
            o.observed_unit_count = $listings
        WITH o
        MATCH (u:AccommodationUnit {id: $uid})
        MERGE (u)-[:OPERATED_BY]->(o)
        """, op_id=op_id, name=op_name, host_id=host_id, listings=listings, uid=unit_id)


def _ingest_chains(session, df: pd.DataFrame, wikidata: list):
    if "hotel_chain" not in df.columns:
        return
    chain_df = df[df["hotel_chain"].notna() & (df["hotel_chain"].astype(str).str.strip() != "")]
    print(f"  Ingesting chain affiliations for {len(chain_df)} units ...")
    for _, row in chain_df.iterrows():
        chain_name = str(row["hotel_chain"]).strip()
        op_name = str(row.get("operator_name", "")).strip()
        session.run("MERGE (c:HotelChain {name: $name})", name=chain_name)
        if op_name:
            session.run("""
            MATCH (o:Operator {name: $op}), (c:HotelChain {name: $chain})
            MERGE (o)-[:AFFILIATED_WITH]->(c)
            """, op=op_name, chain=chain_name)

    # Wikidata parent org / brand enrichment
    for row in wikidata:
        parent = row.get("parent_org_name", "").strip()
        brand = row.get("brand_name", "").strip()
        op = row.get("operator_name", "").strip()
        if parent and op:
            session.run("MERGE (c:HotelChain {name: $name})", name=parent)
            session.run("""
            MATCH (o:Operator {name: $op}), (c:HotelChain {name: $chain})
            MERGE (o)-[:AFFILIATED_WITH]->(c)
            """, op=op, chain=parent)
        if brand:
            session.run("MERGE (c:HotelChain {name: $name})", name=brand)


# ──────────────────────────────────────────────────────────────
# RDF / Turtle
# ──────────────────────────────────────────────────────────────

def build_rdf(df: pd.DataFrame, wikidata: list) -> Graph:
    g = Graph()
    g.bind("vaok", VAOK)
    g.bind("schema", SCHEMA)
    g.bind("geo", GEO)
    g.bind("foaf", FOAF)

    # Source nodes
    source_uris = {}
    for key, label in SOURCE_LABELS.items():
        uri = VAOK[f"source/{slugify(label)}"]
        g.add((uri, RDF.type, VAOK.Source))
        g.add((uri, RDFS.label, Literal(label)))
        source_uris[key] = uri

    operators_seen = set()
    chains_seen = set()

    for _, row in df.iterrows():
        name = str(row.get("name", "")).strip()
        if not name:
            continue

        uid = str(row.get("canonical_id", "")) or slugify(f"{name}_{row.get('raw_id','')}")
        unit_uri = VAOK[f"unit/{slugify(uid)}"]
        g.add((unit_uri, RDF.type, VAOK.AccommodationUnit))
        g.add((unit_uri, RDFS.label, Literal(name)))
        g.add((unit_uri, SCHEMA.name, Literal(name)))

        if pd.notna(row.get("address")) and row["address"]:
            g.add((unit_uri, SCHEMA.address, Literal(str(row["address"]))))
        if pd.notna(row.get("lat")) and pd.notna(row.get("lon")):
            g.add((unit_uri, GEO.lat, Literal(float(row["lat"]), datatype=XSD.double)))
            g.add((unit_uri, GEO.long, Literal(float(row["lon"]), datatype=XSD.double)))
        if pd.notna(row.get("website")) and row["website"]:
            g.add((unit_uri, FOAF.homepage, Literal(str(row["website"]))))

        unit_type = str(row.get("unit_type", row.get("property_type", ""))).strip()
        if unit_type:
            g.add((unit_uri, VAOK.unitType, Literal(unit_type)))

        granularity = str(row.get("granularity", "")).strip()
        if granularity:
            g.add((unit_uri, VAOK.granularity, Literal(granularity)))

        merge_conf = str(row.get("merge_confidence", "")).strip()
        if merge_conf:
            g.add((unit_uri, VAOK.mergeConfidence, Literal(merge_conf)))

        # Sources
        source_names_str = str(row.get("source_names", row.get("source", "")))
        for src_key in source_names_str.split(","):
            src_key = src_key.strip()
            if src_key in source_uris:
                g.add((unit_uri, VAOK.observedIn, source_uris[src_key]))

        # District
        district = str(row.get("district", "")).strip()
        if district:
            dist_uri = VAOK[f"district/{slugify(district)}"]
            g.add((dist_uri, RDF.type, VAOK.District))
            g.add((dist_uri, RDFS.label, Literal(district)))
            g.add((unit_uri, VAOK.locatedIn, dist_uri))

        # Operator
        op_name = str(row.get("operator_name", "")).strip()
        if op_name:
            op_id = _operator_id(op_name, str(row.get("host_id", "")))
            op_uri = VAOK[f"operator/{slugify(op_id)}"]
            if op_uri not in operators_seen:
                g.add((op_uri, RDF.type, VAOK.Operator))
                g.add((op_uri, RDFS.label, Literal(op_name)))
                operators_seen.add(op_uri)
            g.add((unit_uri, VAOK.operatedBy, op_uri))

            # Chain
            chain_name = str(row.get("hotel_chain", "")).strip()
            if chain_name:
                chain_uri = VAOK[f"chain/{slugify(chain_name)}"]
                if chain_uri not in chains_seen:
                    g.add((chain_uri, RDF.type, VAOK.HotelChain))
                    g.add((chain_uri, RDFS.label, Literal(chain_name)))
                    chains_seen.add(chain_uri)
                g.add((op_uri, VAOK.affiliatedWith, chain_uri))

    return g


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────

def main():
    os.makedirs(GRAPH_DIR, exist_ok=True)

    if not os.path.exists(INPUT_UNIFIED):
        print(f"ERROR: {INPUT_UNIFIED} not found. Run resolve_entities.py first.")
        return

    df = pd.read_csv(INPUT_UNIFIED, encoding="utf-8")
    print(f"Loaded {len(df)} unified accommodation units")

    wikidata = []
    if os.path.exists(INPUT_WIKIDATA):
        with open(INPUT_WIKIDATA, encoding="utf-8") as f:
            wikidata = json.load(f)
        print(f"Loaded {len(wikidata)} Wikidata records")

    # Build Neo4j graph
    print("\n--- Neo4j ---")
    if os.getenv("SKIP_NEO4J"):
        print("  Skipping Neo4j ingestion (SKIP_NEO4J set).")
    else:
        build_neo4j(df, wikidata)

    # Build RDF graph
    print("\n--- RDF/Turtle ---")
    rdf_graph = build_rdf(df, wikidata)
    rdf_graph.serialize(destination=OUTPUT_TTL, format="turtle")
    triple_count = len(rdf_graph)
    print(f"Saved {triple_count} RDF triples to {OUTPUT_TTL}")

    # Summary
    print("\nDone! Summary:")
    print(f"  Accommodation units: {len(df)}")
    if "granularity" in df.columns:
        for g, cnt in df["granularity"].value_counts().items():
            print(f"    {g}: {cnt}")
    print(f"  Wikidata records:    {len(wikidata)}")
    print(f"  RDF triples:         {triple_count}")


if __name__ == "__main__":
    main()
