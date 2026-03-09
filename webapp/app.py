"""
Vienna Accommodation Operator KG - Web Dashboard backend.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from neo4j import GraphDatabase

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
WEBAPP_DIR = Path(__file__).resolve().parent
if str(WEBAPP_DIR) not in sys.path:
    sys.path.insert(0, str(WEBAPP_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from common_paths import (  # noqa: E402
    CANDIDATE_SCORES_CSV,
    EMBEDDING_METRICS_JSON,
    EMBEDDING_MAPPINGS_JSON,
    EMBEDDING_MATRIX_FILE,
    EVOLUTION_CHANGES_JSON,
    EVOLUTION_SUMMARY_JSON,
    FINANCIAL_KG_REPORT_MD,
    OPERATOR_SIMILARITY_JSON,
    QUALITY_REPORT_JSON,
    REPORTS_DIR,
    RULE_FACTS_JSON,
    RULE_SUMMARY_JSON,
    SNAPSHOTS_DIR,
    UNIFIED_DATA_FILE,
    read_json,
)
from diff_snapshots import build_diff  # noqa: E402
from kg_utils import operator_key_from_row  # noqa: E402
from query_templates import list_templates, match_query  # noqa: E402

load_dotenv(BASE_DIR / ".env")

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
        records = [dict(record) for record in result]
    driver.close()
    return records


def load_unified_df() -> pd.DataFrame:
    if not UNIFIED_DATA_FILE.exists():
        return pd.DataFrame()
    return pd.read_csv(UNIFIED_DATA_FILE, low_memory=False)


def load_candidate_scores() -> pd.DataFrame:
    if not CANDIDATE_SCORES_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(CANDIDATE_SCORES_CSV, low_memory=False)


def load_rule_facts() -> list[dict]:
    payload = read_json(RULE_FACTS_JSON, default={}) or {}
    return payload.get("facts", [])


def load_embedding_artifacts():
    if not EMBEDDING_MATRIX_FILE.exists() or not EMBEDDING_MAPPINGS_JSON.exists():
        return None, None
    arrays = np.load(EMBEDDING_MATRIX_FILE)
    mappings = read_json(EMBEDDING_MAPPINGS_JSON, default={})
    return arrays, mappings


def latest_snapshot_dirs() -> list[Path]:
    if not SNAPSHOTS_DIR.exists():
        return []
    return sorted([path for path in SNAPSHOTS_DIR.iterdir() if path.is_dir()])


def _empty_evolution_changes(summary: dict) -> dict:
    return {
        "summary": summary,
        "added_units": [],
        "removed_units": [],
        "listing_links_added": [],
        "listing_links_removed": [],
        "operator_labels_changed": [],
    }


def _load_snapshot_df(path: Path) -> pd.DataFrame:
    file_path = path / UNIFIED_DATA_FILE.name
    if not file_path.exists():
        return pd.DataFrame()
    return pd.read_csv(file_path, low_memory=False)


def compare_snapshots(previous_name: str = "", current_name: str = "") -> tuple[dict, dict]:
    snapshots = latest_snapshot_dirs()
    snapshot_names = [path.name for path in snapshots]
    default_previous = snapshot_names[-2] if len(snapshot_names) >= 2 else ""
    default_current = snapshot_names[-1] if len(snapshot_names) >= 1 else ""
    base_summary = {
        "available_snapshots": snapshot_names,
        "default_previous": default_previous,
        "default_current": default_current,
    }

    if len(snapshots) < 2:
        summary = {
            **base_summary,
            "status": "insufficient_snapshots",
            "message": "Need at least two snapshots to compute an evolution diff.",
        }
        return summary, _empty_evolution_changes(summary)

    previous_name = previous_name or default_previous
    current_name = current_name or default_current
    snapshot_map = {path.name: path for path in snapshots}

    if previous_name not in snapshot_map or current_name not in snapshot_map:
        summary = {
            **base_summary,
            "status": "invalid_snapshot",
            "message": "Select two valid snapshot ids from the available list.",
            "previous_snapshot": previous_name,
            "current_snapshot": current_name,
        }
        return summary, _empty_evolution_changes(summary)

    if snapshot_names.index(previous_name) >= snapshot_names.index(current_name):
        summary = {
            **base_summary,
            "status": "invalid_order",
            "message": "The previous snapshot must be older than the current snapshot.",
            "previous_snapshot": previous_name,
            "current_snapshot": current_name,
        }
        return summary, _empty_evolution_changes(summary)

    previous_path = snapshot_map[previous_name]
    current_path = snapshot_map[current_name]
    summary, details = build_diff(
        _load_snapshot_df(previous_path),
        _load_snapshot_df(current_path),
        previous_path,
        current_path,
    )
    summary.update(base_summary)
    details["summary"] = summary
    return summary, details


def _operator_summary_from_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    working = df.copy()
    working["operator_key"] = working.apply(operator_key_from_row, axis=1)
    working["operator_name"] = working["operator_name"].fillna("").astype(str).str.strip()
    working["district"] = working["district"].fillna("").astype(str).str.strip()
    working["hotel_chain"] = working.get("hotel_chain", pd.Series(dtype=str)).fillna("").astype(str).str.strip()
    working = working[working["operator_name"].ne("")]
    if working.empty:
        return working
    return (
        working.groupby(["operator_key", "operator_name"], dropna=False)
        .agg(
            unit_count=("canonical_id", "count"),
            district_count=("district", lambda s: int(pd.Series(s)[pd.Series(s).astype(str).str.strip().ne("")].nunique())),
            chains=("hotel_chain", lambda s: sorted([x for x in pd.Series(s).astype(str).str.strip().unique().tolist() if x])),
        )
        .reset_index()
    )


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def compute_similar_operators(operator_id: str | None = None, limit: int = 5):
    arrays, mappings = load_embedding_artifacts()
    if arrays is None or not mappings:
        return []

    df = load_unified_df()
    operator_summary = _operator_summary_from_df(df)
    if operator_summary.empty:
        return []

    entity_embeddings = arrays["entity_embeddings"]
    entity_to_id = mappings.get("entity_to_id", {})
    operator_summary["entity_label"] = operator_summary["operator_key"].apply(lambda key: f"operator:{key}")
    operator_summary = operator_summary[operator_summary["entity_label"].isin(entity_to_id)]
    if operator_summary.empty:
        return []

    if operator_id:
        base_row = operator_summary[operator_summary["operator_key"] == operator_id]
        if base_row.empty:
            return []
        base_row = base_row.iloc[0]
        base_vector = entity_embeddings[entity_to_id[base_row["entity_label"]]]
        scored = []
        for _, other in operator_summary.iterrows():
            if other["operator_key"] == operator_id:
                continue
            other_vector = entity_embeddings[entity_to_id[other["entity_label"]]]
            scored.append(
                {
                    "operator_id": other["operator_key"],
                    "operator_name": other["operator_name"],
                    "unit_count": int(other["unit_count"]),
                    "similarity": round(_cosine_similarity(base_vector, other_vector), 4),
                }
            )
        scored.sort(key=lambda item: item["similarity"], reverse=True)
        return scored[:limit]

    payload = read_json(OPERATOR_SIMILARITY_JSON, default={}) or {}
    return payload.get("operators", [])[:limit]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/top-operators")
def top_operators():
    records = run_query(
        """
        MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)
        RETURN o.id AS id, o.name AS operator, count(u) AS count,
               o.operator_type AS operator_type
        ORDER BY count DESC
        LIMIT 20
        """
    )
    return jsonify(records)


@app.route("/api/operator-units")
def operator_units():
    op_id = request.args.get("id", "")
    name = request.args.get("name", "")
    if op_id:
        records = run_query(
            """
            MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator {id: $id})
            RETURN u.id AS unit_id, u.name AS unit, u.address AS address, u.unit_type AS type,
                   u.unit_type_normalized AS type_normalized, u.granularity AS granularity,
                   u.district AS district, u.lat AS lat, u.lon AS lon, u.source_names AS sources,
                   u.operator_identity_confidence AS operator_identity_confidence
            ORDER BY u.name
            """,
            id=op_id,
        )
    elif name:
        records = run_query(
            """
            MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator {name: $name})
            RETURN u.id AS unit_id, u.name AS unit, u.address AS address, u.unit_type AS type,
                   u.unit_type_normalized AS type_normalized, u.granularity AS granularity,
                   u.district AS district, u.lat AS lat, u.lon AS lon, u.source_names AS sources,
                   u.operator_identity_confidence AS operator_identity_confidence
            ORDER BY u.name
            """,
            name=name,
        )
    else:
        records = []
    return jsonify(records)


@app.route("/api/chains")
def chains():
    records = run_query(
        """
        MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)-[:AFFILIATED_WITH]->(c:HotelChain)
        RETURN c.name AS chain, count(u) AS count
        ORDER BY count DESC
        """
    )
    return jsonify(records)


@app.route("/api/districts")
def districts():
    records = run_query(
        """
        MATCH (u:AccommodationUnit)-[:LOCATED_IN]->(d:District)
        RETURN d.name AS district, count(u) AS count
        ORDER BY count DESC
        """
    )
    return jsonify(records)


@app.route("/api/corporate-vs-individual")
def corporate_vs_individual():
    records = run_query(
        """
        MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)
        MATCH (u)-[:LOCATED_IN]->(d:District)
        WITH d,
             sum(CASE WHEN o.operator_type = 'multi_listing' THEN 1 ELSE 0 END) AS multi_listing,
             sum(CASE WHEN o.operator_type <> 'multi_listing' THEN 1 ELSE 0 END) AS single_property
        RETURN d.name AS district, multi_listing, single_property
        ORDER BY (multi_listing + single_property) DESC
        """
    )
    return jsonify(records)


@app.route("/api/property-types")
def property_types():
    records = run_query(
        """
        MATCH (u:AccommodationUnit)
        WHERE u.unit_type_normalized IS NOT NULL AND u.unit_type_normalized <> ''
        RETURN u.unit_type_normalized AS type, count(u) AS count
        ORDER BY count DESC
        """
    )
    return jsonify(records)


@app.route("/api/source-overlap")
def source_overlap():
    records = run_query(
        """
        MATCH (u:AccommodationUnit)-[:OBSERVED_IN]->(s:Source)
        RETURN s.name AS source, count(u) AS units
        ORDER BY units DESC
        """
    )
    return jsonify(records)


@app.route("/api/granularity-counts")
def granularity_counts():
    records = run_query(
        """
        MATCH (u:AccommodationUnit)
        RETURN u.granularity AS granularity, count(u) AS count
        ORDER BY count DESC
        """
    )
    return jsonify(records)


@app.route("/api/quality-summary")
def quality_summary():
    return jsonify(read_json(QUALITY_REPORT_JSON, default={}) or {})


@app.route("/api/map-points")
def map_points():
    records = run_query(
        """
        MATCH (u:AccommodationUnit)
        WHERE u.lat IS NOT NULL AND u.lon IS NOT NULL
        OPTIONAL MATCH (u)-[:OPERATED_BY]->(o:Operator)
        WITH u, head(collect(DISTINCT o.name)) AS operator
        RETURN u.id AS id, u.name AS name, u.lat AS lat, u.lon AS lon,
               coalesce(u.unit_type, 'unknown') AS type,
               coalesce(operator, 'Unknown') AS operator,
               u.website AS website, u.picture_url AS picture_url,
               u.granularity AS granularity, u.source_names AS sources
        """
    )
    return jsonify(records)


@app.route("/api/property-network")
def property_network():
    name = request.args.get("name", "")
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    if not name:
        return jsonify({"operator": None, "properties": []})
    records = run_query(
        """
        MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)
        WHERE u.name = $name
          AND ($lat IS NULL OR abs(u.lat - $lat) < 0.0001)
          AND ($lon IS NULL OR abs(u.lon - $lon) < 0.0001)
        WITH o LIMIT 1
        MATCH (other:AccommodationUnit)-[:OPERATED_BY]->(o)
        WHERE other.lat IS NOT NULL AND other.lon IS NOT NULL
        RETURN o.name AS operator, other.id AS id, other.name AS name, other.lat AS lat,
               other.lon AS lon, coalesce(other.unit_type, 'unknown') AS type,
               other.website AS website, other.picture_url AS picture_url,
               other.granularity AS granularity
        """,
        name=name,
        lat=lat,
        lon=lon,
    )
    if not records:
        return jsonify({"operator": None, "properties": []})
    operator_name = records[0]["operator"]
    return jsonify({"operator": operator_name, "properties": records})


@app.route("/api/graph")
def graph():
    min_units = request.args.get("min_units", default=1, type=int)
    if min_units is None or min_units < 1:
        min_units = 1
    limit = request.args.get("limit", default=0, type=int)
    limit_clause = "LIMIT $limit" if limit and limit > 0 else ""

    records = run_query(
        f"""
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
        """,
        min_units=min_units,
        limit=limit,
    )

    nodes = {}
    links = []
    link_keys = set()

    def add_node(node_id, label, node_type, count=None, operator_id=None):
        if node_id not in nodes:
            nodes[node_id] = {"id": node_id, "label": label, "type": node_type}
            if count is not None:
                nodes[node_id]["count"] = count
            if operator_id is not None:
                nodes[node_id]["operator_id"] = operator_id

    def add_link(source, target, relation_type):
        key = (source, target, relation_type)
        if key not in link_keys:
            link_keys.add(key)
            links.append({"source": source, "target": target, "type": relation_type})

    for row in records:
        operator = row["o"]
        operator_node_id = f"op_{operator.element_id}"
        add_node(
            operator_node_id,
            operator.get("name", "Unknown"),
            "operator",
            row["propCount"],
            operator_id=operator.get("id"),
        )

        for chain in row["chains"]:
            if chain is None:
                continue
            chain_node_id = f"chain_{chain.element_id}"
            add_node(chain_node_id, chain.get("name", "Unknown"), "chain")
            add_link(operator_node_id, chain_node_id, "AFFILIATED_WITH")

        for district in row["districts"]:
            if district is None:
                continue
            district_node_id = f"dist_{district.element_id}"
            add_node(district_node_id, district.get("name", "Unknown"), "district")
            add_link(operator_node_id, district_node_id, "LOCATED_IN")

    return jsonify(
        {
            "nodes": list(nodes.values()),
            "links": links,
            "meta": {
                "operator_count": sum(1 for node in nodes.values() if node["type"] == "operator"),
                "node_count": len(nodes),
                "link_count": len(links),
                "min_units": min_units,
                "limit": limit,
            },
        }
    )


@app.route("/api/chain-map")
def chain_map():
    name = request.args.get("name", "")
    if not name:
        return jsonify([])
    records = run_query(
        """
        MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)-[:AFFILIATED_WITH]->(c:HotelChain {name: $name})
        WHERE u.lat IS NOT NULL AND u.lon IS NOT NULL
        RETURN u.id AS id, u.name AS name, u.lat AS lat, u.lon AS lon,
               coalesce(u.unit_type, 'unknown') AS type,
               u.website AS website, u.picture_url AS picture_url,
               u.granularity AS granularity
        """,
        name=name,
    )
    return jsonify(records)


@app.route("/api/operator-map")
def operator_map():
    op_id = request.args.get("id", "")
    name = request.args.get("name", "")
    if op_id:
        records = run_query(
            """
            MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator {id: $id})
            WHERE u.lat IS NOT NULL AND u.lon IS NOT NULL
            RETURN u.id AS id, u.name AS name, u.lat AS lat, u.lon AS lon,
                   coalesce(u.unit_type_normalized, u.unit_type, 'unknown') AS type,
                   u.website AS website, u.picture_url AS picture_url,
                   u.granularity AS granularity
            """,
            id=op_id,
        )
    elif name:
        records = run_query(
            """
            MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator {name: $name})
            WHERE u.lat IS NOT NULL AND u.lon IS NOT NULL
            RETURN u.id AS id, u.name AS name, u.lat AS lat, u.lon AS lon,
                   coalesce(u.unit_type_normalized, u.unit_type, 'unknown') AS type,
                   u.website AS website, u.picture_url AS picture_url,
                   u.granularity AS granularity
            """,
            name=name,
        )
    else:
        records = []
    return jsonify(records)


@app.route("/api/reasoning/summary")
def reasoning_summary():
    rules = read_json(RULE_SUMMARY_JSON, default={}) or {}
    embeddings = read_json(EMBEDDING_METRICS_JSON, default={}) or {}
    candidates = load_candidate_scores()
    return jsonify(
        {
            "rules": rules,
            "embeddings": embeddings,
            "candidate_count": int(len(candidates)),
            "strong_review_count": int((candidates.get("embedding_suggestion", pd.Series(dtype=str)) == "strong_review").sum())
            if not candidates.empty
            else 0,
        }
    )


@app.route("/api/reasoning/facts")
def reasoning_facts():
    inferred_type = request.args.get("inferred_type", "").strip()
    entity_id = request.args.get("entity_id", "").strip()
    limit = request.args.get("limit", default=100, type=int)
    facts = load_rule_facts()
    if inferred_type:
        facts = [fact for fact in facts if fact.get("inferred_type") == inferred_type]
    if entity_id:
        facts = [fact for fact in facts if fact.get("entity_id") == entity_id]
    return jsonify(facts[: max(limit, 1)])


@app.route("/api/reasoning/entity")
def reasoning_entity():
    entity_id = request.args.get("entity_id", "").strip()
    facts = [fact for fact in load_rule_facts() if fact.get("entity_id") == entity_id]
    return jsonify({"entity_id": entity_id, "facts": facts})


@app.route("/api/embeddings/summary")
def embeddings_summary():
    metrics = read_json(EMBEDDING_METRICS_JSON, default={}) or {}
    candidates = load_candidate_scores()
    return jsonify(
        {
            "metrics": metrics,
            "candidate_count": int(len(candidates)),
            "top_candidates": candidates.sort_values("embedding_score", ascending=False)
            .head(10)
            .fillna("")
            .to_dict(orient="records")
            if not candidates.empty
            else [],
        }
    )


@app.route("/api/embeddings/candidates")
def embedding_candidates():
    limit = request.args.get("limit", default=50, type=int)
    suggestion = request.args.get("suggestion", "").strip()
    candidates = load_candidate_scores()
    if candidates.empty:
        return jsonify([])
    if suggestion:
        candidates = candidates[candidates["embedding_suggestion"] == suggestion]
    candidates = candidates.sort_values("embedding_score", ascending=False)
    return jsonify(candidates.head(max(limit, 1)).fillna("").to_dict(orient="records"))


@app.route("/api/embeddings/similar-operators")
def embedding_similar_operators():
    operator_id = request.args.get("operator_id", "").strip() or None
    limit = request.args.get("limit", default=5, type=int)
    rows = compute_similar_operators(operator_id=operator_id, limit=max(limit, 1))
    return jsonify(
        {
            "mode": "similar_to_operator" if operator_id else "top_operator_neighborhoods",
            "operator_id": operator_id,
            "rows": rows,
        }
    )


@app.route("/api/embeddings/metrics")
def embedding_metrics():
    return jsonify(read_json(EMBEDDING_METRICS_JSON, default={}) or {})


@app.route("/api/evolution/summary")
def evolution_summary():
    previous_name = request.args.get("previous", "").strip()
    current_name = request.args.get("current", "").strip()
    summary, _ = compare_snapshots(previous_name=previous_name, current_name=current_name)
    return jsonify(summary)


@app.route("/api/evolution/snapshots")
def evolution_snapshots():
    summary, _ = compare_snapshots()
    return jsonify(
        {
            "snapshots": summary.get("available_snapshots", []),
            "default_previous": summary.get("default_previous", ""),
            "default_current": summary.get("default_current", ""),
            "status": summary.get("status", "ok"),
            "message": summary.get("message", ""),
        }
    )


@app.route("/api/evolution/changes")
def evolution_changes():
    previous_name = request.args.get("previous", "").strip()
    current_name = request.args.get("current", "").strip()
    _, details = compare_snapshots(previous_name=previous_name, current_name=current_name)
    return jsonify(details)


@app.route("/api/evolution/entity")
def evolution_entity():
    canonical_id = request.args.get("id", "").strip()
    snapshots = latest_snapshot_dirs()
    if len(snapshots) < 2 or not canonical_id:
        return jsonify({"id": canonical_id, "previous": None, "current": None})

    previous_df = pd.read_csv(snapshots[-2] / UNIFIED_DATA_FILE.name, low_memory=False)
    current_df = pd.read_csv(snapshots[-1] / UNIFIED_DATA_FILE.name, low_memory=False)
    previous_row = previous_df[previous_df["canonical_id"].astype(str) == canonical_id]
    current_row = current_df[current_df["canonical_id"].astype(str) == canonical_id]

    return jsonify(
        {
            "id": canonical_id,
            "previous_snapshot": snapshots[-2].name,
            "current_snapshot": snapshots[-1].name,
            "previous": previous_row.fillna("").iloc[0].to_dict() if not previous_row.empty else None,
            "current": current_row.fillna("").iloc[0].to_dict() if not current_row.empty else None,
        }
    )


@app.route("/api/query-templates")
def query_templates():
    return jsonify(list_templates())


@app.route("/api/query-assistant", methods=["GET"])
def query_assistant():
    question = request.args.get("q", "").strip()
    if not question:
        return jsonify(
            {
                "matched": False,
                "message": "Provide a question. Use /api/query-templates for supported patterns.",
            }
        )
    match = match_query(question)
    if not match:
        return jsonify(
            {
                "matched": False,
                "message": "This question does not match a supported query template yet.",
                "templates": list_templates(),
            }
        )

    rows = run_query(match["cypher"], **match["params"])
    return jsonify(
        {
            "matched": True,
            "template_id": match["template_id"],
            "label": match["label"],
            "question": question,
            "cypher": match["cypher"],
            "params": match["params"],
            "explanation": match["explanation"],
            "rows": rows,
            "row_count": len(rows),
        }
    )


@app.route("/api/entity-evidence")
def entity_evidence():
    unit_id = request.args.get("unit_id", "").strip()
    operator_id = request.args.get("operator_id", "").strip()
    df = load_unified_df()
    facts = load_rule_facts()

    if unit_id:
        row = df[df["canonical_id"].astype(str) == unit_id]
        if row.empty:
            return jsonify({"kind": "unit", "found": False})
        payload = row.fillna("").iloc[0].to_dict()
        return jsonify(
            {
                "kind": "unit",
                "found": True,
                "entity": payload,
                "sources": [item.strip() for item in str(payload.get("source_names", "")).split(",") if item.strip()],
                "source_record_ids": [item.strip() for item in str(payload.get("source_record_ids", "")).split(",") if item.strip()],
                "rule_facts": [fact for fact in facts if fact.get("entity_id") == unit_id],
            }
        )

    if operator_id:
        working = df.copy()
        working["operator_key"] = working.apply(operator_key_from_row, axis=1)
        working["operator_name"] = working["operator_name"].fillna("").astype(str).str.strip()
        operator_rows = working[working["operator_key"] == operator_id]
        if operator_rows.empty:
            return jsonify({"kind": "operator", "found": False})
        unit_sample = (
            operator_rows[["canonical_id", "name", "granularity", "district", "operator_identity_confidence"]]
            .fillna("")
            .head(20)
            .to_dict(orient="records")
        )
        confidence_counts = (
            operator_rows["operator_identity_confidence"].fillna("unknown").astype(str).value_counts().to_dict()
        )
        chains = sorted(
            [
                value
                for value in operator_rows.get("hotel_chain", pd.Series(dtype=str)).fillna("").astype(str).unique().tolist()
                if value
            ]
        )
        return jsonify(
            {
                "kind": "operator",
                "found": True,
                "operator_id": operator_id,
                "operator_name": operator_rows["operator_name"].iloc[0],
                "unit_count": int(len(operator_rows)),
                "districts": sorted(
                    [value for value in operator_rows["district"].fillna("").astype(str).unique().tolist() if value]
                ),
                "chains": chains,
                "confidence_counts": {str(key): int(value) for key, value in confidence_counts.items()},
                "rule_facts": [fact for fact in facts if fact.get("entity_id") == operator_id],
                "units": unit_sample,
            }
        )

    return jsonify({"found": False, "message": "Provide unit_id or operator_id."})


@app.route("/api/link-evidence")
def link_evidence():
    listing_id = request.args.get("listing_id", "").strip()
    establishment_id = request.args.get("establishment_id", "").strip()
    df = load_unified_df()
    if df.empty or not listing_id:
        return jsonify({"found": False})

    listing = df[df["canonical_id"].astype(str) == listing_id]
    if listing.empty:
        return jsonify({"found": False})
    listing_row = listing.fillna("").iloc[0].to_dict()

    linked_id = str(listing_row.get("linked_establishment_id", "")).strip()
    candidate_id = str(listing_row.get("candidate_establishment_id", "")).strip()
    target_id = establishment_id or linked_id or candidate_id
    target = df[df["canonical_id"].astype(str) == target_id]
    target_row = target.fillna("").iloc[0].to_dict() if not target.empty else None

    if linked_id:
        status = "asserted"
    elif candidate_id:
        status = "candidate_only"
    else:
        status = "none"

    return jsonify(
        {
            "found": True,
            "status": status,
            "listing": listing_row,
            "target": target_row,
            "distance_m": listing_row.get("candidate_establishment_distance_m", ""),
            "linked_confidence": listing_row.get("linked_establishment_confidence", ""),
            "linked_evidence": listing_row.get("linked_establishment_evidence", ""),
            "candidate_evidence": listing_row.get("candidate_establishment_evidence", ""),
        }
    )


@app.route("/api/financial-kg-comparison")
def financial_kg_comparison():
    if not FINANCIAL_KG_REPORT_MD.exists():
        return jsonify({"markdown": ""})
    return jsonify({"markdown": FINANCIAL_KG_REPORT_MD.read_text(encoding="utf-8")})


@app.route("/legacy")
def legacy():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
