"""
Vienna Hotel KG — Web Dashboard
Flask backend: serves index.html + /api/* endpoints
"""

import os
from flask import Flask, jsonify, render_template
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

app = Flask(__name__)

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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
