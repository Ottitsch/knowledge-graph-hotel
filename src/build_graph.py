"""
Build the Vienna Hotel Ownership Knowledge Graph.

Reads: data/properties_unified.csv, data/wikidata_hotels.json, data/firmenbuch_companies.json
Writes:
  - Neo4j graph (via bolt driver) — requires running Neo4j instance
  - graph/vienna_hotels.ttl (RDF Turtle)

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
INPUT_FIRMENBUCH = os.path.join(DATA_DIR, "firmenbuch_companies.json")
OUTPUT_TTL = os.path.join(GRAPH_DIR, "vienna_hotels.ttl")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# ------------------------------------------------------------------
# RDF namespaces
# ------------------------------------------------------------------
VHK = Namespace("http://example.org/vienna-hotel-kg/")
SCHEMA = Namespace("http://schema.org/")
GEO = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")


def slugify(s: str) -> str:
    if not isinstance(s, str):
        return "unknown"
    s = re.sub(r"[^\w\s-]", "", s.lower())
    s = re.sub(r"[\s_-]+", "_", s)
    return s.strip("_") or "unknown"


# ------------------------------------------------------------------
# Neo4j graph builder
# ------------------------------------------------------------------

def build_neo4j(df: pd.DataFrame, wikidata: list, firmenbuch: list):
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
        _ingest_platform(session)
        _ingest_districts(session, df)
        _ingest_properties(session, df)
        _ingest_operators(session, df)
        _ingest_chains(session, df, wikidata)
        _ingest_firmenbuch(session, firmenbuch)
        _ingest_wikidata_ownership(session, wikidata)

    driver.close()
    print("Neo4j ingestion complete.")


def _run(session, query, **params):
    session.run(query, **params)


def _create_constraints(session):
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Property) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (o:Operator) REQUIRE o.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:HotelChain) REQUIRE c.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (d:District) REQUIRE d.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (pl:Platform) REQUIRE pl.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (oc:OwnerCompany) REQUIRE oc.name IS UNIQUE",
    ]
    for c in constraints:
        try:
            session.run(c)
        except Exception:
            pass  # constraint may already exist


def _ingest_platform(session):
    _run(session,
         "MERGE (p:Platform {name: 'booking.com'}) SET p.url = 'https://www.booking.com'")
    _run(session,
         "MERGE (p:Platform {name: 'Airbnb'}) SET p.url = 'https://www.airbnb.com'")


def _ingest_districts(session, df: pd.DataFrame):
    districts = df["district"].dropna().unique()
    for d in districts:
        d = str(d).strip()
        if d:
            session.run("MERGE (d:District {name: $name})", name=d)


def _ingest_properties(session, df: pd.DataFrame):
    print(f"  Ingesting {len(df)} properties ...")
    for _, row in df.iterrows():
        name = str(row.get("name", "")).strip()
        if not name:
            continue
        prop_id = slugify(f"{name}_{row.get('raw_id','')}")
        query = """
        MERGE (p:Property {id: $id})
        SET p.name = $name,
            p.address = $address,
            p.property_type = $property_type,
            p.lat = $lat,
            p.lon = $lon,
            p.website = $website,
            p.picture_url = $picture_url,
            p.sources = $sources
        """
        session.run(query,
                    id=prop_id,
                    name=name,
                    address=str(row.get("address", "")),
                    property_type=str(row.get("property_type", "")),
                    lat=float(row["lat"]) if pd.notna(row.get("lat")) else None,
                    lon=float(row["lon"]) if pd.notna(row.get("lon")) else None,
                    website=str(row.get("website", "")),
                    picture_url=str(row.get("picture_url", "")),
                    sources=str(row.get("sources", row.get("source", ""))))

        # Link to district
        district = str(row.get("district", "")).strip()
        if district:
            session.run("""
            MATCH (p:Property {id: $pid}), (d:District {name: $dname})
            MERGE (p)-[:LOCATED_IN]->(d)
            """, pid=prop_id, dname=district)

        # Link to platform (booking.com for hotel/apart, airbnb for airbnb source)
        platform = "Airbnb" if "airbnb" in str(row.get("sources", "")) else "booking.com"
        session.run("""
        MATCH (p:Property {id: $pid}), (pl:Platform {name: $pname})
        MERGE (p)-[:LISTED_ON]->(pl)
        """, pid=prop_id, pname=platform)


def _ingest_operators(session, df: pd.DataFrame):
    op_df = df[df["operator_name"].notna() & (df["operator_name"] != "")]
    print(f"  Ingesting operators for {len(op_df)} properties ...")
    for _, row in op_df.iterrows():
        op_name = str(row["operator_name"]).strip()
        if not op_name:
            continue
        prop_id = slugify(f"{row.get('name','')}_{row.get('raw_id','')}")
        host_id = str(row.get("host_id", ""))
        listings = int(row["host_listings_count"]) if pd.notna(row.get("host_listings_count")) else None
        session.run("""
        MERGE (o:Operator {name: $name})
        SET o.host_id = $host_id,
            o.listings_count = $listings
        WITH o
        MATCH (p:Property {id: $pid})
        MERGE (p)-[:OPERATED_BY]->(o)
        """, name=op_name, host_id=host_id, listings=listings, pid=prop_id)


def _ingest_chains(session, df: pd.DataFrame, wikidata: list):
    chain_df = df[df.get("hotel_chain", pd.Series()) != ""]
    if "hotel_chain" in df.columns:
        chain_df = df[df["hotel_chain"].notna() & (df["hotel_chain"] != "")]
    else:
        return
    print(f"  Ingesting chain memberships for {len(chain_df)} properties ...")
    for _, row in chain_df.iterrows():
        chain_name = str(row["hotel_chain"]).strip()
        op_name = str(row.get("operator_name", "")).strip()
        session.run("MERGE (c:HotelChain {name: $name})", name=chain_name)
        if op_name:
            session.run("""
            MATCH (o:Operator {name: $op}), (c:HotelChain {name: $chain})
            MERGE (o)-[:SUBSIDIARY_OF]->(c)
            """, op=op_name, chain=chain_name)

    # Also process wikidata parent org / brand
    for row in wikidata:
        parent = row.get("parent_org_name", "").strip()
        brand = row.get("brand_name", "").strip()
        op = row.get("operator_name", "").strip()
        hotel = row.get("hotel_name", "").strip()
        if parent and op:
            session.run("MERGE (c:HotelChain {name: $name})", name=parent)
            session.run("""
            MATCH (o:Operator {name: $op}), (c:HotelChain {name: $chain})
            MERGE (o)-[:SUBSIDIARY_OF]->(c)
            """, op=op, chain=parent)
        if brand and hotel:
            session.run("MERGE (c:HotelChain {name: $name})", name=brand)


def _ingest_firmenbuch(session, firmenbuch: list):
    matched = [r for r in firmenbuch if r.get("firmenbuch_match")]
    print(f"  Ingesting {len(matched)} Firmenbuch company matches ...")
    for entry in matched:
        match = entry["firmenbuch_match"]
        name = match.get("name") or entry["query_name"]
        fn_number = match.get("firmenbuchnummer") or match.get("fn") or ""
        legal_form = match.get("rechtsform") or match.get("legal_form", "")
        session.run("""
        MERGE (oc:OwnerCompany {name: $name})
        SET oc.firmenbuch_number = $fn, oc.legal_form = $lf
        WITH oc
        OPTIONAL MATCH (o:Operator {name: $qname})
        FOREACH (_ IN CASE WHEN o IS NOT NULL THEN [1] ELSE [] END |
          MERGE (o)-[:REGISTERED_AS]->(oc)
        )
        """, name=name, fn=fn_number, lf=legal_form, qname=entry["query_name"])


def _ingest_wikidata_ownership(session, wikidata: list):
    print(f"  Ingesting Wikidata ownership for {len(wikidata)} records ...")
    for row in wikidata:
        owner = row.get("owner_name", "").strip()
        op = row.get("operator_name", "").strip()
        if owner and op:
            session.run("""
            MERGE (oc:OwnerCompany {name: $owner})
            WITH oc
            MATCH (o:Operator {name: $op})
            MERGE (oc)-[:OWNS]->(o)
            """, owner=owner, op=op)


# ------------------------------------------------------------------
# RDF / Turtle graph builder
# ------------------------------------------------------------------

def build_rdf(df: pd.DataFrame, wikidata: list) -> Graph:
    g = Graph()
    g.bind("vhk", VHK)
    g.bind("schema", SCHEMA)
    g.bind("geo", GEO)
    g.bind("foaf", FOAF)

    platform_bc = VHK["platform/booking_com"]
    platform_ab = VHK["platform/airbnb"]
    g.add((platform_bc, RDF.type, VHK.Platform))
    g.add((platform_bc, RDFS.label, Literal("booking.com")))
    g.add((platform_ab, RDF.type, VHK.Platform))
    g.add((platform_ab, RDFS.label, Literal("Airbnb")))

    operators_seen = set()
    chains_seen = set()

    for _, row in df.iterrows():
        name = str(row.get("name", "")).strip()
        if not name:
            continue

        prop_uri = VHK[f"property/{slugify(name)}_{slugify(str(row.get('raw_id','')))}"]
        g.add((prop_uri, RDF.type, VHK.Property))
        g.add((prop_uri, RDFS.label, Literal(name)))
        g.add((prop_uri, SCHEMA.name, Literal(name)))

        if pd.notna(row.get("address")) and row["address"]:
            g.add((prop_uri, SCHEMA.address, Literal(str(row["address"]))))
        if pd.notna(row.get("lat")) and pd.notna(row.get("lon")):
            g.add((prop_uri, GEO.lat, Literal(float(row["lat"]), datatype=XSD.double)))
            g.add((prop_uri, GEO.long, Literal(float(row["lon"]), datatype=XSD.double)))
        if pd.notna(row.get("website")) and row["website"]:
            g.add((prop_uri, FOAF.homepage, Literal(str(row["website"]))))
        if pd.notna(row.get("property_type")) and row["property_type"]:
            g.add((prop_uri, VHK.propertyType, Literal(str(row["property_type"]))))

        # Platform
        platform = platform_ab if "airbnb" in str(row.get("sources", "")) else platform_bc
        g.add((prop_uri, VHK.listedOn, platform))

        # District
        district = str(row.get("district", "")).strip()
        if district:
            dist_uri = VHK[f"district/{slugify(district)}"]
            g.add((dist_uri, RDF.type, VHK.District))
            g.add((dist_uri, RDFS.label, Literal(district)))
            g.add((prop_uri, VHK.locatedIn, dist_uri))

        # Operator
        op_name = str(row.get("operator_name", "")).strip()
        if op_name:
            op_uri = VHK[f"operator/{slugify(op_name)}"]
            if op_uri not in operators_seen:
                g.add((op_uri, RDF.type, VHK.Operator))
                g.add((op_uri, RDFS.label, Literal(op_name)))
                operators_seen.add(op_uri)
            g.add((prop_uri, VHK.operatedBy, op_uri))

            # Chain
            chain_name = str(row.get("hotel_chain", "")).strip()
            if chain_name:
                chain_uri = VHK[f"chain/{slugify(chain_name)}"]
                if chain_uri not in chains_seen:
                    g.add((chain_uri, RDF.type, VHK.HotelChain))
                    g.add((chain_uri, RDFS.label, Literal(chain_name)))
                    chains_seen.add(chain_uri)
                g.add((op_uri, VHK.subsidiaryOf, chain_uri))

    # Wikidata enrichment
    for row in wikidata:
        owner = row.get("owner_name", "").strip()
        op_name = row.get("operator_name", "").strip()
        if owner and op_name:
            owner_uri = VHK[f"owner/{slugify(owner)}"]
            g.add((owner_uri, RDF.type, VHK.OwnerCompany))
            g.add((owner_uri, RDFS.label, Literal(owner)))
            op_uri = VHK[f"operator/{slugify(op_name)}"]
            if op_uri not in operators_seen:
                g.add((op_uri, RDF.type, VHK.Operator))
                g.add((op_uri, RDFS.label, Literal(op_name)))
                operators_seen.add(op_uri)
            g.add((owner_uri, VHK.owns, op_uri))

    return g


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():
    os.makedirs(GRAPH_DIR, exist_ok=True)

    # Load data
    if not os.path.exists(INPUT_UNIFIED):
        print(f"ERROR: {INPUT_UNIFIED} not found. Run resolve_entities.py first.")
        return

    df = pd.read_csv(INPUT_UNIFIED, encoding="utf-8")
    print(f"Loaded {len(df)} unified properties")

    wikidata = []
    if os.path.exists(INPUT_WIKIDATA):
        with open(INPUT_WIKIDATA, encoding="utf-8") as f:
            wikidata = json.load(f)
        print(f"Loaded {len(wikidata)} Wikidata records")

    firmenbuch = []
    if os.path.exists(INPUT_FIRMENBUCH):
        with open(INPUT_FIRMENBUCH, encoding="utf-8") as f:
            firmenbuch = json.load(f)
        print(f"Loaded {len(firmenbuch)} Firmenbuch entries")

    # Build Neo4j graph
    print("\n--- Neo4j ---")
    if os.getenv("SKIP_NEO4J"):
        print("  Skipping Neo4j ingestion (SKIP_NEO4J set).")
    else:
        build_neo4j(df, wikidata, firmenbuch)

    # Build RDF graph
    print("\n--- RDF/Turtle ---")
    rdf_graph = build_rdf(df, wikidata)
    rdf_graph.serialize(destination=OUTPUT_TTL, format="turtle")
    triple_count = len(rdf_graph)
    print(f"Saved {triple_count} RDF triples to {OUTPUT_TTL}")

    print("\nDone! Summary:")
    print(f"  Properties:      {len(df)}")
    print(f"  Wikidata hotels: {len(wikidata)}")
    print(f"  Firmenbuch:      {len(firmenbuch)}")
    print(f"  RDF triples:     {triple_count}")


if __name__ == "__main__":
    main()
