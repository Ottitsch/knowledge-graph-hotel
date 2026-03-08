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
        RETURN o.name AS operator, count(u) AS count
        ORDER BY count DESC
        LIMIT 20
    """)
    return jsonify(records)


@app.route("/api/operator-units")
def operator_units():
    """All accommodation units for a given operator (main question endpoint)."""
    name = request.args.get("name", "")
    if not name:
        return jsonify([])
    records = run_query("""
        MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator {name: $name})
        RETURN u.name AS unit, u.address AS address, u.unit_type AS type,
               u.granularity AS granularity, u.district AS district,
               u.lat AS lat, u.lon AS lon, u.source_names AS sources
        ORDER BY u.name
    """, name=name)
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
    records = run_query("""
        MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)
        MATCH (u)-[:LOCATED_IN]->(d:District)
        WITH d, o, count(u) AS unit_count
        WITH d,
             sum(CASE WHEN unit_count > 3 THEN unit_count ELSE 0 END) AS professional,
             sum(CASE WHEN unit_count <= 3 THEN unit_count ELSE 0 END) AS individual
        RETURN d.name AS district, professional, individual
        ORDER BY (professional + individual) DESC
    """)
    return jsonify(records)


# --- Unit type endpoint ---

@app.route("/api/property-types")
def property_types():
    records = run_query("""
        MATCH (u:AccommodationUnit)
        WHERE u.unit_type IS NOT NULL AND u.unit_type <> ''
        RETURN u.unit_type AS type, count(u) AS count
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


# --- Map endpoints ---

@app.route("/api/map-points")
def map_points():
    records = run_query("""
        MATCH (u:AccommodationUnit)
        WHERE u.lat IS NOT NULL AND u.lon IS NOT NULL
        RETURN u.name AS name, u.lat AS lat, u.lon AS lon,
               coalesce(u.unit_type, 'unknown') AS type,
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
            "website": r.get("website") or "",
            "picture_url": r.get("picture_url") or "",
            "granularity": r.get("granularity") or "",
        }
        for r in records
    ]
    return jsonify({"operator": operator, "properties": properties})


@app.route("/api/graph")
def graph():
    records = run_query("""
        MATCH (o:Operator)
        WHERE o.observed_unit_count > 3
           OR exists { (u:AccommodationUnit)-[:OPERATED_BY]->(o) }
        WITH o
        MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o)
        WITH o, count(u) AS propCount
        WHERE propCount > 3
        OPTIONAL MATCH (o)-[:AFFILIATED_WITH]->(c:HotelChain)
        OPTIONAL MATCH (u2:AccommodationUnit)-[:OPERATED_BY]->(o)
        OPTIONAL MATCH (u2)-[:LOCATED_IN]->(d:District)
        WITH o, c, collect(DISTINCT d)[0..5] AS districts, propCount
        RETURN o, c, districts, propCount
        LIMIT 150
    """)

    nodes = {}
    links = []

    def add_node(nid, label, ntype, count=None):
        if nid not in nodes:
            nodes[nid] = {"id": nid, "label": label, "type": ntype}
            if count is not None:
                nodes[nid]["count"] = count

    for row in records:
        o = row["o"]
        c = row["c"]
        districts = row["districts"]
        prop_count = row["propCount"]

        o_id = f"op_{o.element_id}"
        add_node(o_id, o.get("name", "Unknown"), "operator", prop_count)

        if c is not None:
            c_id = f"chain_{c.element_id}"
            add_node(c_id, c.get("name", "Unknown"), "chain")
            links.append({"source": o_id, "target": c_id, "type": "AFFILIATED_WITH"})

        for d in districts:
            if d is not None:
                d_id = f"dist_{d.element_id}"
                add_node(d_id, d.get("name", "Unknown"), "district")
                links.append({"source": o_id, "target": d_id, "type": "LOCATED_IN"})

    return jsonify({"nodes": list(nodes.values()), "links": links})


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
    name = request.args.get("name", "")
    if not name:
        return jsonify([])
    records = run_query("""
        MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator {name: $name})
        WHERE u.lat IS NOT NULL AND u.lon IS NOT NULL
        RETURN u.name AS name, u.lat AS lat, u.lon AS lon,
               coalesce(u.unit_type, 'unknown') AS type,
               u.website AS website, u.picture_url AS picture_url,
               u.granularity AS granularity
    """, name=name)
    return jsonify(records)


@app.route("/legacy")
def legacy():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
