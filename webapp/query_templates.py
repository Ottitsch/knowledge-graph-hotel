from __future__ import annotations

import re


TEMPLATES = [
    {
        "id": "operators_more_than_n",
        "label": "Operators with many units",
        "description": "Find operators with more than N accommodation units, optionally filtered by district.",
        "example": "Which operators manage more than 5 units in Leopoldstadt?",
    },
    {
        "id": "operators_in_district",
        "label": "Operators in a district",
        "description": "Find operators active in a chosen Vienna district.",
        "example": "Which operators are active in Neubau?",
    },
    {
        "id": "chain_affiliated_with_listings",
        "label": "Chain-affiliated establishments with listings",
        "description": "Find chain-affiliated establishments that have linked Airbnb listings nearby.",
        "example": "Show chain-affiliated establishments with nearby Airbnb listings.",
    },
    {
        "id": "low_confidence_operators",
        "label": "Low-confidence operators",
        "description": "Find operators whose identity is mainly based on low-confidence evidence.",
        "example": "Which operators have low-confidence identities?",
    },
    {
        "id": "multi_source_establishments",
        "label": "Multi-source confirmed establishments",
        "description": "List establishments merged from multiple public sources.",
        "example": "Show multi-source confirmed establishments.",
    },
]


def list_templates() -> list[dict]:
    return TEMPLATES


def _clean_question(question: str) -> str:
    return " ".join(question.strip().split())


def match_query(question: str):
    question = _clean_question(question)
    lowered = question.lower()

    match = re.search(
        r"(?:more than|over|at least)\s+(\d+)\s+(?:units|listings|accommodation units)(?:\s+in\s+([a-zA-ZäöüÄÖÜß\-\s]+))?",
        lowered,
    )
    if match:
        min_units = int(match.group(1))
        district = match.group(2).strip() if match.group(2) else ""
        where_clause = ""
        params = {"min_units": min_units}
        if district:
            where_clause = "WHERE toLower(d.name) CONTAINS toLower($district)"
            params["district"] = district
        query = f"""
            MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)
            OPTIONAL MATCH (u)-[:LOCATED_IN]->(d:District)
            {where_clause}
            WITH o, count(DISTINCT u) AS unit_count, collect(DISTINCT d.name) AS districts
            WHERE unit_count > $min_units
            RETURN o.name AS operator, o.id AS operator_id, unit_count, districts
            ORDER BY unit_count DESC
            LIMIT 25
        """
        return {
            "template_id": "operators_more_than_n",
            "label": "Operators with many units",
            "cypher": query,
            "params": params,
            "explanation": "This query counts units per operator and optionally filters by district before ranking the result.",
        }

    match = re.search(r"(?:operators|hosts).*(?:active|in)\s+([a-zA-ZäöüÄÖÜß\-\s]+)\??$", question, flags=re.IGNORECASE)
    if match:
        district = match.group(1).strip()
        query = """
            MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)
            MATCH (u)-[:LOCATED_IN]->(d:District)
            WHERE toLower(d.name) CONTAINS toLower($district)
            RETURN o.name AS operator, o.id AS operator_id, count(DISTINCT u) AS unit_count
            ORDER BY unit_count DESC
            LIMIT 25
        """
        return {
            "template_id": "operators_in_district",
            "label": "Operators in a district",
            "cypher": query,
            "params": {"district": district},
            "explanation": "This query finds operators with at least one unit in the requested district.",
        }

    if "chain" in lowered and "listing" in lowered:
        query = """
            MATCH (est:AccommodationUnit {granularity: 'establishment'})<-[:LISTING_OF]-(listing:AccommodationUnit {granularity: 'listing'})
            MATCH (est)-[:OPERATED_BY]->(o:Operator)-[:AFFILIATED_WITH]->(c:HotelChain)
            RETURN est.name AS establishment, c.name AS chain, count(DISTINCT listing) AS listing_count
            ORDER BY listing_count DESC, establishment ASC
            LIMIT 25
        """
        return {
            "template_id": "chain_affiliated_with_listings",
            "label": "Chain-affiliated establishments with listings",
            "cypher": query,
            "params": {},
            "explanation": "This query joins linked Airbnb listings to chain-affiliated establishments.",
        }

    if "low-confidence" in lowered or "low confidence" in lowered:
        query = """
            MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)
            WHERE u.operator_identity_confidence = 'low'
            RETURN o.name AS operator, o.id AS operator_id, count(DISTINCT u) AS affected_units
            ORDER BY affected_units DESC
            LIMIT 25
        """
        return {
            "template_id": "low_confidence_operators",
            "label": "Low-confidence operators",
            "cypher": query,
            "params": {},
            "explanation": "This query lists operators attached to units whose operator identity confidence is low.",
        }

    if "multi-source" in lowered or "multi source" in lowered:
        query = """
            MATCH (u:AccommodationUnit {granularity: 'establishment'})
            WHERE u.merge_confidence = 'strong'
            RETURN u.name AS establishment, u.source_names AS sources, u.district AS district
            ORDER BY establishment ASC
            LIMIT 25
        """
        return {
            "template_id": "multi_source_establishments",
            "label": "Multi-source confirmed establishments",
            "cypher": query,
            "params": {},
            "explanation": "This query lists establishments merged from multiple public sources.",
        }

    return None
