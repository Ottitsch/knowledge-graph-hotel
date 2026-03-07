"""
Vienna Hotel KG — Web Dashboard
Flask backend: serves index.html + /api/* endpoints
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


@app.route("/api/top-operators")
def top_operators():
    records = run_query("""
        MATCH (p:Property)-[:OPERATED_BY]->(o:Operator)
        RETURN o.name AS operator, count(p) AS count
        ORDER BY count DESC
        LIMIT 20
    """)
    return jsonify(records)


@app.route("/api/chains")
def chains():
    records = run_query("""
        MATCH (p:Property)-[:OPERATED_BY]->(o:Operator)-[:SUBSIDIARY_OF]->(c:HotelChain)
        RETURN c.name AS chain, count(p) AS count
        ORDER BY count DESC
    """)
    return jsonify(records)


@app.route("/api/districts")
def districts():
    records = run_query("""
        MATCH (p:Property)-[:LOCATED_IN]->(d:District)
        RETURN d.name AS district, count(p) AS count
        ORDER BY count DESC
    """)
    return jsonify(records)


@app.route("/api/corporate-vs-individual")
def corporate_vs_individual():
    records = run_query("""
        MATCH (p:Property)-[:OPERATED_BY]->(o:Operator)
        MATCH (p)-[:LOCATED_IN]->(d:District)
        WITH d, o, count(p) AS listings
        WITH d,
             sum(CASE WHEN listings > 3 THEN listings ELSE 0 END) AS corporate,
             sum(CASE WHEN listings <= 3 THEN listings ELSE 0 END) AS individual
        RETURN d.name AS district, corporate, individual
        ORDER BY (corporate + individual) DESC
    """)
    return jsonify(records)


@app.route("/api/property-types")
def property_types():
    records = run_query("""
        MATCH (p:Property)
        WHERE p.property_type IS NOT NULL AND p.property_type <> ''
        RETURN p.property_type AS type, count(p) AS count
        ORDER BY count DESC
    """)
    return jsonify(records)


@app.route("/api/map-points")
def map_points():
    records = run_query("""
        MATCH (p:Property)
        WHERE p.lat IS NOT NULL AND p.lon IS NOT NULL
        RETURN p.name AS name, p.lat AS lat, p.lon AS lon,
               coalesce(p.property_type, 'unknown') AS type
    """)
    return jsonify(records)


@app.route("/api/graph")
def graph():
    records = run_query("""
        MATCH (o:Operator)
        WHERE o.listings_count > 3
        OPTIONAL MATCH (o)-[:SUBSIDIARY_OF]->(c:HotelChain)
        WITH o, c
        MATCH (p:Property)-[:OPERATED_BY]->(o)
        OPTIONAL MATCH (p)-[:LOCATED_IN]->(d:District)
        WITH o, c, collect(DISTINCT d)[0..5] AS districts, count(p) AS propCount
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
            links.append({"source": o_id, "target": c_id, "type": "SUBSIDIARY_OF"})

        for d in districts:
            if d is not None:
                d_id = f"dist_{d.element_id}"
                add_node(d_id, d.get("name", "Unknown"), "district")
                links.append({"source": o_id, "target": d_id, "type": "LOCATED_IN"})

    return jsonify({"nodes": list(nodes.values()), "links": links})


@app.route("/api/operator-map")
def operator_map():
    name = request.args.get("name", "")
    if not name:
        return jsonify([])
    records = run_query("""
        MATCH (p:Property)-[:OPERATED_BY]->(o:Operator {name: $name})
        WHERE p.lat IS NOT NULL AND p.lon IS NOT NULL
        RETURN p.name AS name, p.lat AS lat, p.lon AS lon,
               coalesce(p.property_type, 'unknown') AS type
    """, name=name)
    return jsonify(records)


@app.route("/legacy")
def legacy():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
