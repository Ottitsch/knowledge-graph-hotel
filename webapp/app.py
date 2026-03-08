"""
Vienna Accommodation Operator KG — Web Dashboard
Flask backend: serves index.html + /api/* endpoints

Main question: Which accommodation units in Vienna are operated by the same
person or organization, and what other units do they operate?
"""

import os
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

app = Flask(__name__)
CORS(app)


def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def run_query(cypher, **params):
    driver = get_driver()
    with driver.session() as session:
        result = session.run(cypher, **params)
        records = [dict(r) for r in result]
    driver.close()
    return records


@app.route("/")
def index():
    return render_template("index.html")


# --- Operator endpoints ---

@app.route("/api/top-operators")
def top_operators():
    records = run_query("""
        MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)
        RETURN o.id AS id, o.name AS operator, count(u) AS count,
               o.operator_type AS operator_type
        ORDER BY count DESC
        LIMIT 20
    """)
    return jsonify(records)


@app.route("/api/operator-units")
def operator_units():
    """All accommodation units for a given operator (main question endpoint).
    Accepts ?id= (operator ID, preferred) or ?name= (fallback, may match multiple operators).
    """
    op_id = request.args.get("id", "")
    name = request.args.get("name", "")
    if op_id:
        records = run_query("""
            MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator {id: $id})
            RETURN u.name AS unit, u.address AS address, u.unit_type AS type,
                   u.unit_type_normalized AS type_normalized,
                   u.granularity AS granularity, u.district AS district,
                   u.lat AS lat, u.lon AS lon, u.source_names AS sources,
                   u.operator_identity_confidence AS operator_identity_confidence
            ORDER BY u.name
        """, id=op_id)
    elif name:
        records = run_query("""
            MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator {name: $name})
            RETURN u.name AS unit, u.address AS address, u.unit_type AS type,
                   u.unit_type_normalized AS type_normalized,
                   u.granularity AS granularity, u.district AS district,
                   u.lat AS lat, u.lon AS lon, u.source_names AS sources,
                   u.operator_identity_confidence AS operator_identity_confidence
            ORDER BY u.name
        """, name=name)
    else:
        records = []
    return jsonify(records)


# --- Chain endpoints ---

@app.route("/api/chains")
def chains():
    records = run_query("""
        MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)-[:AFFILIATED_WITH]->(c:HotelChain)
        RETURN c.name AS chain, count(u) AS count
        ORDER BY count DESC
    """)
    return jsonify(records)


# --- District endpoints ---

@app.route("/api/districts")
def districts():
    records = run_query("""
        MATCH (u:AccommodationUnit)-[:LOCATED_IN]->(d:District)
        RETURN d.name AS district, count(u) AS count
        ORDER BY count DESC
    """)
    return jsonify(records)


@app.route("/api/corporate-vs-individual")
def corporate_vs_individual():
    """Multi-listing vs single-property operators by district.
    Classified by number of units operated in this dataset (>1 = multi_listing).
    """
    records = run_query("""
        MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)
        MATCH (u)-[:LOCATED_IN]->(d:District)
        WITH d,
             sum(CASE WHEN o.operator_type = 'multi_listing' THEN 1 ELSE 0 END) AS multi_listing,
             sum(CASE WHEN o.operator_type <> 'multi_listing' THEN 1 ELSE 0 END) AS single_property
        RETURN d.name AS district, multi_listing, single_property
        ORDER BY (multi_listing + single_property) DESC
    """)
    return jsonify(records)


# --- Unit type endpoint ---

@app.route("/api/property-types")
def property_types():
    records = run_query("""
        MATCH (u:AccommodationUnit)
        WHERE u.unit_type_normalized IS NOT NULL AND u.unit_type_normalized <> ''
        RETURN u.unit_type_normalized AS type, count(u) AS count
        ORDER BY count DESC
    """)
    return jsonify(records)


# --- Source provenance endpoints ---

@app.route("/api/source-overlap")
def source_overlap():
    """Units per source and multi-source overlap summary."""
    records = run_query("""
        MATCH (u:AccommodationUnit)-[:OBSERVED_IN]->(s:Source)
        RETURN s.name AS source, count(u) AS units
        ORDER BY units DESC
    """)
    return jsonify(records)


@app.route("/api/granularity-counts")
def granularity_counts():
    """Listing-level vs establishment-level counts."""
    records = run_query("""
        MATCH (u:AccommodationUnit)
        RETURN u.granularity AS granularity, count(u) AS count
        ORDER BY count DESC
    """)
    return jsonify(records)


@app.route("/api/quality-summary")
def quality_summary():
    totals = run_query("""
        MATCH (u:AccommodationUnit)
        RETURN count(u) AS total,
               sum(CASE WHEN u.granularity = 'listing' THEN 1 ELSE 0 END) AS listings,
               sum(CASE WHEN u.granularity = 'establishment' THEN 1 ELSE 0 END) AS establishments
    """)
    operator_confidence = run_query("""
        MATCH (u:AccommodationUnit)
        RETURN coalesce(u.operator_identity_confidence, 'unknown') AS confidence, count(u) AS count
        ORDER BY count DESC
    """)
    listing_matches = run_query("""
        MATCH (l:AccommodationUnit {granularity: 'listing'})
        OPTIONAL MATCH (l)-[r:LISTING_OF]->(:AccommodationUnit)
        RETURN coalesce(r.confidence, 'unlinked') AS confidence, count(l) AS count
        ORDER BY count DESC
    """)
    source_overlap = run_query("""
        MATCH (u:AccommodationUnit {granularity: 'establishment'})
        RETURN sum(CASE WHEN u.merge_confidence = 'strong' THEN 1 ELSE 0 END) AS multi_source_establishments,
               count(u) AS establishments
    """)
    return jsonify({
        "totals": totals[0] if totals else {},
        "operator_confidence": operator_confidence,
        "listing_matches": listing_matches,
        "source_overlap": source_overlap[0] if source_overlap else {},
    })


# --- Map endpoints ---

@app.route("/api/map-points")
def map_points():
    records = run_query("""
        MATCH (u:AccommodationUnit)
        WHERE u.lat IS NOT NULL AND u.lon IS NOT NULL
        OPTIONAL MATCH (u)-[:OPERATED_BY]->(o:Operator)
        WITH u, head(collect(DISTINCT o.name)) AS operator
        RETURN u.name AS name, u.lat AS lat, u.lon AS lon,
               coalesce(u.unit_type, 'unknown') AS type,
               coalesce(operator, 'Unknown') AS operator,
               u.website AS website, u.picture_url AS picture_url,
               u.granularity AS granularity, u.source_names AS sources
    """)
    return jsonify(records)


@app.route("/api/property-network")
def property_network():
    """All units operated by the same operator as the selected unit."""
    name = request.args.get("name", "")
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    if not name:
        return jsonify({"operator": None, "properties": []})
    records = run_query("""
        MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)
        WHERE u.name = $name
          AND ($lat IS NULL OR abs(u.lat - $lat) < 0.0001)
          AND ($lon IS NULL OR abs(u.lon - $lon) < 0.0001)
        WITH o LIMIT 1
        MATCH (other:AccommodationUnit)-[:OPERATED_BY]->(o)
        WHERE other.lat IS NOT NULL AND other.lon IS NOT NULL
        RETURN o.name AS operator,
               other.name AS name,
               other.lat AS lat,
               other.lon AS lon,
               coalesce(other.unit_type, 'unknown') AS type,
               other.website AS website,
               other.picture_url AS picture_url,
               other.granularity AS granularity
    """, name=name, lat=lat, lon=lon)
    if not records:
        return jsonify({"operator": None, "properties": []})
    operator = records[0]["operator"]
    properties = [
        {
            "name": r["name"],
            "lat": r["lat"],
            "lon": r["lon"],
            "type": r["type"],
            "operator": r.get("operator") or "",
            "website": r.get("website") or "",
            "picture_url": r.get("picture_url") or "",
            "granularity": r.get("granularity") or "",
        }
        for r in records
    ]
    return jsonify({"operator": operator, "properties": properties})


@app.route("/api/graph")
def graph():
    min_units = request.args.get("min_units", default=1, type=int)
    if min_units is None or min_units < 1:
        min_units = 1
    limit = request.args.get("limit", default=0, type=int)
    limit_clause = "LIMIT $limit" if limit and limit > 0 else ""

    records = run_query(f"""
        MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o)
        WITH o, count(u) AS propCount
        WHERE propCount >= $min_units
        ORDER BY propCount DESC
        {limit_clause}
        OPTIONAL MATCH (o)-[:AFFILIATED_WITH]->(c:HotelChain)
        OPTIONAL MATCH (u2:AccommodationUnit)-[:OPERATED_BY]->(o)
        OPTIONAL MATCH (u2)-[:LOCATED_IN]->(d:District)
        WITH o, propCount, collect(DISTINCT c) AS chains, collect(DISTINCT d) AS districts
        RETURN o, chains, districts, propCount
        ORDER BY propCount DESC
    """, min_units=min_units, limit=limit)

    nodes = {}
    links = []
    link_keys = set()

    def add_node(nid, label, ntype, count=None, operator_id=None):
        if nid not in nodes:
            nodes[nid] = {"id": nid, "label": label, "type": ntype}
            if count is not None:
                nodes[nid]["count"] = count
            if operator_id is not None:
                nodes[nid]["operator_id"] = operator_id

    def add_link(source, target, rel_type):
        key = (source, target, rel_type)
        if key not in link_keys:
            link_keys.add(key)
            links.append({"source": source, "target": target, "type": rel_type})

    for row in records:
        o = row["o"]
        chains = row["chains"]
        districts = row["districts"]
        prop_count = row["propCount"]

        o_id = f"op_{o.element_id}"
        add_node(o_id, o.get("name", "Unknown"), "operator", prop_count,
                 operator_id=o.get("id"))

        for c in chains:
            if c is not None:
                c_id = f"chain_{c.element_id}"
                add_node(c_id, c.get("name", "Unknown"), "chain")
                add_link(o_id, c_id, "AFFILIATED_WITH")

        for d in districts:
            if d is not None:
                d_id = f"dist_{d.element_id}"
                add_node(d_id, d.get("name", "Unknown"), "district")
                add_link(o_id, d_id, "LOCATED_IN")

    operator_count = sum(1 for node in nodes.values() if node["type"] == "operator")
    return jsonify({
        "nodes": list(nodes.values()),
        "links": links,
        "meta": {
            "operator_count": operator_count,
            "node_count": len(nodes),
            "link_count": len(links),
            "min_units": min_units,
            "limit": limit,
        },
    })


@app.route("/api/chain-map")
def chain_map():
    name = request.args.get("name", "")
    if not name:
        return jsonify([])
    records = run_query("""
        MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)-[:AFFILIATED_WITH]->(c:HotelChain {name: $name})
        WHERE u.lat IS NOT NULL AND u.lon IS NOT NULL
        RETURN u.name AS name, u.lat AS lat, u.lon AS lon,
               coalesce(u.unit_type, 'unknown') AS type,
               u.website AS website, u.picture_url AS picture_url,
               u.granularity AS granularity
    """, name=name)
    return jsonify(records)


@app.route("/api/operator-map")
def operator_map():
    op_id = request.args.get("id", "")
    name = request.args.get("name", "")
    if op_id:
        records = run_query("""
            MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator {id: $id})
            WHERE u.lat IS NOT NULL AND u.lon IS NOT NULL
            RETURN u.name AS name, u.lat AS lat, u.lon AS lon,
                   coalesce(u.unit_type_normalized, u.unit_type, 'unknown') AS type,
                   u.website AS website, u.picture_url AS picture_url,
                   u.granularity AS granularity
        """, id=op_id)
    elif name:
        records = run_query("""
            MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator {name: $name})
            WHERE u.lat IS NOT NULL AND u.lon IS NOT NULL
            RETURN u.name AS name, u.lat AS lat, u.lon AS lon,
                   coalesce(u.unit_type_normalized, u.unit_type, 'unknown') AS type,
                   u.website AS website, u.picture_url AS picture_url,
                   u.granularity AS granularity
        """, name=name)
    else:
        records = []
    return jsonify(records)


@app.route("/legacy")
def legacy():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
