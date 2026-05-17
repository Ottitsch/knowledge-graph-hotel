"""
Generate rule-based inferred facts for the Vienna Accommodation Operator KG.

Reads:  data/properties_unified.csv
        src/rules.yml
Writes: reports/rule_inference_report.md
        reports/rule_inference_summary.json
        reports/rule_inference_facts.json
        graph/inferred_facts.ttl
"""

from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import pandas as pd
import yaml
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef

from common_paths import (
    GRAPH_DIR,
    RULES_FILE,
    RULE_FACTS_JSON,
    RULE_REPORT_MD,
    RULE_SUMMARY_JSON,
    UNIFIED_DATA_FILE,
    ensure_directories,
    utc_timestamp,
    write_json,
)
from kg_utils import operator_key_from_row, slugify

VAOK = Namespace("http://example.org/vienna-accommodation-operator-kg/")
INFERRED_TTL = GRAPH_DIR / "inferred_facts.ttl"


def _non_empty(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def load_rule_definitions() -> dict[str, dict]:
    payload = yaml.safe_load(RULES_FILE.read_text(encoding="utf-8"))
    return {rule["id"]: rule for rule in payload.get("rules", [])}


def _operator_groups(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()
    working["operator_key"] = working.apply(operator_key_from_row, axis=1)
    working["operator_name"] = _non_empty(working["operator_name"])
    working["district"] = _non_empty(working["district"])
    working["source_names"] = _non_empty(working["source_names"])
    working["hotel_chain"] = _non_empty(working.get("hotel_chain", pd.Series(dtype=str)))
    working = working[working["operator_name"].ne("")]
    if working.empty:
        return working

    grouped = (
        working.groupby(["operator_key", "operator_name"], dropna=False)
        .agg(
            unit_count=("canonical_id", "count"),
            listing_count=("granularity", lambda s: int((s == "listing").sum())),
            establishment_count=("granularity", lambda s: int((s == "establishment").sum())),
            district_count=("district", lambda s: int(_non_empty(s)[_non_empty(s).ne("")].nunique())),
            districts=("district", lambda s: sorted([x for x in _non_empty(s).unique().tolist() if x])),
            chains=("hotel_chain", lambda s: sorted([x for x in _non_empty(s).unique().tolist() if x])),
            confidence_values=(
                "operator_identity_confidence",
                lambda s: Counter(_non_empty(s)).most_common(),
            ),
            source_values=("source_names", lambda s: sorted(_non_empty(s).unique().tolist())),
        )
        .reset_index()
    )
    return grouped


def _chain_to_operator_map(operator_groups: pd.DataFrame) -> dict[str, list[dict]]:
    """For each chain, collect the operators affiliated with it."""
    chain_to_operators: dict[str, list[dict]] = defaultdict(list)
    for _, row in operator_groups.iterrows():
        for chain in row["chains"]:
            if not chain:
                continue
            chain_to_operators[chain].append(
                {
                    "operator_key": row["operator_key"],
                    "operator_name": row["operator_name"],
                }
            )
    return chain_to_operators


class _UnionFind:
    """Plain union-find for recursive transitive closure over corporateSibling edges."""

    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, key: str) -> str:
        if key not in self.parent:
            self.parent[key] = key
            return key
        while self.parent[key] != key:
            self.parent[key] = self.parent[self.parent[key]]
            key = self.parent[key]
        return key

    def union(self, a: str, b: str) -> None:
        root_a = self.find(a)
        root_b = self.find(b)
        if root_a != root_b:
            self.parent[root_b] = root_a


def build_rule_facts(df: pd.DataFrame, rules: dict[str, dict]) -> list[dict]:
    facts: list[dict] = []
    operator_groups = _operator_groups(df)
    establishments = df[df["granularity"] == "establishment"].copy()
    establishments["source_names"] = _non_empty(establishments["source_names"])
    establishments["hotel_chain"] = _non_empty(establishments.get("hotel_chain", pd.Series(dtype=str)))

    professional_rule = rules["professional_operator"]
    professional_threshold = int(professional_rule.get("threshold", 3))
    for _, row in operator_groups[operator_groups["unit_count"] >= professional_threshold].iterrows():
        facts.append(
            {
                "fact_id": f"{professional_rule['id']}::{row['operator_key']}",
                "rule_id": professional_rule["id"],
                "rule_label": professional_rule["label"],
                "inferred_type": professional_rule["inferred_type"],
                "entity_type": "operator",
                "entity_id": row["operator_key"],
                "entity_label": row["operator_name"],
                "evidence": {
                    "unit_count": int(row["unit_count"]),
                    "listing_count": int(row["listing_count"]),
                    "district_count": int(row["district_count"]),
                },
                "description": professional_rule["description"],
            }
        )

    district_rule = rules["cross_district_operator"]
    district_threshold = int(district_rule.get("threshold", 2))
    for _, row in operator_groups[operator_groups["district_count"] >= district_threshold].iterrows():
        facts.append(
            {
                "fact_id": f"{district_rule['id']}::{row['operator_key']}",
                "rule_id": district_rule["id"],
                "rule_label": district_rule["label"],
                "inferred_type": district_rule["inferred_type"],
                "entity_type": "operator",
                "entity_id": row["operator_key"],
                "entity_label": row["operator_name"],
                "evidence": {
                    "district_count": int(row["district_count"]),
                    "districts": row["districts"],
                },
                "description": district_rule["description"],
            }
        )

    establishment_rule = rules["multi_source_confirmed_establishment"]
    for _, row in establishments[establishments["merge_confidence"].fillna("").astype(str) == "strong"].iterrows():
        facts.append(
            {
                "fact_id": f"{establishment_rule['id']}::{row['canonical_id']}",
                "rule_id": establishment_rule["id"],
                "rule_label": establishment_rule["label"],
                "inferred_type": establishment_rule["inferred_type"],
                "entity_type": "unit",
                "entity_id": str(row["canonical_id"]),
                "entity_label": str(row["name"]),
                "evidence": {
                    "source_names": [part.strip() for part in str(row["source_names"]).split(",") if part.strip()],
                    "merge_confidence": str(row.get("merge_confidence", "")),
                },
                "description": establishment_rule["description"],
            }
        )

    chain_rule = rules["likely_chain_affiliated_operator"]
    chain_affiliated = operator_groups[operator_groups["chains"].map(bool)]
    for _, row in chain_affiliated.iterrows():
        facts.append(
            {
                "fact_id": f"{chain_rule['id']}::{row['operator_key']}",
                "rule_id": chain_rule["id"],
                "rule_label": chain_rule["label"],
                "inferred_type": chain_rule["inferred_type"],
                "entity_type": "operator",
                "entity_id": row["operator_key"],
                "entity_label": row["operator_name"],
                "evidence": {
                    "chains": row["chains"],
                    "establishment_count": int(row["establishment_count"]),
                },
                "description": chain_rule["description"],
            }
        )

    # ──────────────────────────────────────────────────────────────
    # New: corporate sibling pairs derived from shared chain affiliation.
    # This rule materializes NEW edges in the inferred RDF graph.
    # ──────────────────────────────────────────────────────────────
    sibling_rule = rules["shared_chain_corporate_group"]
    chain_to_operators = _chain_to_operator_map(operator_groups)
    sibling_pairs_seen: set[tuple[str, str]] = set()
    for chain, members in chain_to_operators.items():
        if len(members) < 2:
            continue
        for a, b in combinations(sorted(members, key=lambda m: m["operator_key"]), 2):
            pair_key = (a["operator_key"], b["operator_key"])
            if pair_key in sibling_pairs_seen:
                continue
            sibling_pairs_seen.add(pair_key)
            facts.append(
                {
                    "fact_id": f"{sibling_rule['id']}::{pair_key[0]}::{pair_key[1]}::{slugify(chain)}",
                    "rule_id": sibling_rule["id"],
                    "rule_label": sibling_rule["label"],
                    "inferred_type": sibling_rule["inferred_type"],
                    "entity_type": "operator_pair",
                    "entity_id": f"{pair_key[0]}|{pair_key[1]}",
                    "entity_label": f"{a['operator_name']} ↔ {b['operator_name']}",
                    "evidence": {
                        "via_chain": chain,
                        "operator_a": a["operator_name"],
                        "operator_b": b["operator_name"],
                    },
                    "description": sibling_rule["description"],
                }
            )

    # ──────────────────────────────────────────────────────────────
    # New (recursive): connected components over corporateSibling edges.
    # Implemented as union-find — the recursive closure of a symmetric relation.
    # Each component becomes an OperatorNetwork node with member operators.
    # ──────────────────────────────────────────────────────────────
    network_rule = rules["operator_corporate_network"]
    operator_names: dict[str, str] = {
        row["operator_key"]: row["operator_name"] for _, row in operator_groups.iterrows()
    }
    uf = _UnionFind()
    for a, b in sibling_pairs_seen:
        uf.union(a, b)

    component_members: dict[str, list[str]] = defaultdict(list)
    for member in uf.parent:
        component_members[uf.find(member)].append(member)

    for component_id in sorted(component_members):
        members = sorted(component_members[component_id])
        if len(members) < 2:
            continue
        network_slug = f"network_{slugify(component_id)}"
        facts.append(
            {
                "fact_id": f"{network_rule['id']}::{network_slug}",
                "rule_id": network_rule["id"],
                "rule_label": network_rule["label"],
                "inferred_type": network_rule["inferred_type"],
                "entity_type": "network",
                "entity_id": network_slug,
                "entity_label": f"Network of {len(members)} operators",
                "evidence": {
                    "member_count": len(members),
                    "members": [
                        {"operator_key": key, "operator_name": operator_names.get(key, key)}
                        for key in members
                    ],
                },
                "description": network_rule["description"],
            }
        )

    facts.sort(key=lambda fact: (fact["inferred_type"], fact["entity_label"]))
    return facts


def build_summary(df: pd.DataFrame, rules: dict[str, dict], facts: list[dict]) -> dict:
    type_counts = Counter(fact["inferred_type"] for fact in facts)
    rule_counts = Counter(fact["rule_id"] for fact in facts)
    operator_facts = [fact for fact in facts if fact["entity_type"] == "operator"]
    unit_facts = [fact for fact in facts if fact["entity_type"] == "unit"]
    pair_facts = [fact for fact in facts if fact["entity_type"] == "operator_pair"]
    network_facts = [fact for fact in facts if fact["entity_type"] == "network"]

    return {
        "generated_at": utc_timestamp(),
        "input_rows": int(len(df)),
        "rule_count": len(rules),
        "fact_count": len(facts),
        "operator_fact_count": len(operator_facts),
        "unit_fact_count": len(unit_facts),
        "operator_pair_fact_count": len(pair_facts),
        "network_fact_count": len(network_facts),
        "facts_by_type": dict(sorted(type_counts.items())),
        "facts_by_rule": dict(sorted(rule_counts.items())),
        "facts": facts,
    }


def build_markdown(summary: dict) -> str:
    lines = [
        "# Rule Inference Report",
        "",
        f"- Generated at: {summary['generated_at']}",
        f"- Input rows: {summary['input_rows']}",
        f"- Rules applied: {summary['rule_count']}",
        f"- Total inferred facts: {summary['fact_count']}",
        f"- Operator-pair facts (new edges): {summary.get('operator_pair_fact_count', 0)}",
        f"- Network facts (recursive closure): {summary.get('network_fact_count', 0)}",
        "",
        "## Facts by Type",
        "",
    ]

    for inferred_type, count in summary["facts_by_type"].items():
        lines.append(f"- `{inferred_type}`: {count}")

    lines.extend(["", "## Sample Facts", ""])
    for fact in summary["facts"][:12]:
        lines.append(
            f"- `{fact['inferred_type']}` for `{fact['entity_label']}` via `{fact['rule_label']}`: "
            f"{fact['evidence']}"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- These facts are inferred from explicit rules, not imported directly from the raw sources.",
            "- The `CorporateSibling` and `OperatorNetwork` rules produce new edges and nodes in `graph/inferred_facts.ttl`,",
            "  kept separate from `graph/vienna_accommodation_operator_kg.ttl` so asserted and inferred facts stay distinguishable.",
            "- The `OperatorNetwork` rule is recursive: it computes the transitive closure over `corporateSibling` edges via union-find.",
            "- This reasoning layer supports portfolio claims around symbolic reasoning, graph evolution, and explainable KG services.",
            "",
        ]
    )
    return "\n".join(lines)


def write_inferred_ttl(facts: list[dict]) -> int:
    """Emit corporate-sibling edges and operator-network nodes into an RDF graph."""
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    graph = Graph()
    graph.bind("vaok", VAOK)
    triple_count = 0

    for fact in facts:
        if fact["inferred_type"] == "CorporateSibling":
            a_key, b_key = fact["entity_id"].split("|", 1)
            op_a = VAOK[f"operator/{slugify(a_key)}"]
            op_b = VAOK[f"operator/{slugify(b_key)}"]
            graph.add((op_a, VAOK.corporateSibling, op_b))
            graph.add((op_b, VAOK.corporateSibling, op_a))
            triple_count += 2

        elif fact["inferred_type"] == "OperatorNetwork":
            network_uri = VAOK[f"operatorNetwork/{fact['entity_id']}"]
            graph.add((network_uri, RDF.type, VAOK.OperatorNetwork))
            graph.add((network_uri, RDFS.label, Literal(fact["entity_label"])))
            triple_count += 2
            for member in fact["evidence"]["members"]:
                key = member["operator_key"]
                op_uri = VAOK[f"operator/{slugify(key)}"]
                graph.add((op_uri, VAOK.memberOf, network_uri))
                triple_count += 1

    graph.serialize(destination=str(INFERRED_TTL), format="turtle")
    return triple_count


def main() -> None:
    ensure_directories()
    if not UNIFIED_DATA_FILE.exists():
        raise SystemExit(f"Missing input file: {UNIFIED_DATA_FILE}")
    if not RULES_FILE.exists():
        raise SystemExit(f"Missing rule file: {RULES_FILE}")

    df = pd.read_csv(UNIFIED_DATA_FILE, low_memory=False)
    rules = load_rule_definitions()
    facts = build_rule_facts(df, rules)
    summary = build_summary(df, rules, facts)

    write_json(RULE_SUMMARY_JSON, summary)
    write_json(RULE_FACTS_JSON, {"facts": facts})
    RULE_REPORT_MD.write_text(build_markdown(summary), encoding="utf-8")
    inferred_triple_count = write_inferred_ttl(facts)

    print(f"Wrote {RULE_REPORT_MD}")
    print(f"Wrote {RULE_SUMMARY_JSON}")
    print(f"Wrote {RULE_FACTS_JSON}")
    print(f"Wrote {INFERRED_TTL} ({inferred_triple_count} triples)")
    print(f"Inferred facts: {summary['fact_count']}")


if __name__ == "__main__":
    main()
