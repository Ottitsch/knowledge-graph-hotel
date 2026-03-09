"""
Export labeled triples from the current KG view for embedding training.

Reads:  data/properties_unified.csv
Writes: models/embeddings/triples.tsv
        models/embeddings/triples_metadata.json
"""

from __future__ import annotations

from collections import Counter

import pandas as pd

from common_paths import (
    TRIPLES_FILE,
    TRIPLES_METADATA_JSON,
    UNIFIED_DATA_FILE,
    ensure_directories,
    utc_timestamp,
    write_json,
)
from kg_utils import (
    chain_entity_label,
    district_entity_label,
    operator_entity_label,
    operator_key_from_row,
    source_entity_label,
    split_sources,
    unit_entity_label,
)


def build_triples(df: pd.DataFrame) -> list[tuple[str, str, str]]:
    triples: set[tuple[str, str, str]] = set()

    for _, row in df.iterrows():
        canonical_id = str(row.get("canonical_id", "")).strip()
        if not canonical_id:
            continue

        unit = unit_entity_label(canonical_id)
        triples.add((unit, "hasGranularity", f"granularity:{row.get('granularity', 'unknown')}"))

        unit_type = str(row.get("unit_type_normalized", "")).strip()
        if unit_type:
            triples.add((unit, "hasUnitType", f"unitType:{unit_type}"))

        district = str(row.get("district", "")).strip()
        if district:
            triples.add((unit, "locatedIn", district_entity_label(district)))

        for source_name in split_sources(str(row.get("source_names", row.get("source", "")))):
            triples.add((unit, "observedIn", source_entity_label(source_name)))

        operator_name = str(row.get("operator_name", "")).strip()
        if operator_name:
            operator = operator_entity_label(operator_key_from_row(row))
            triples.add((unit, "operatedBy", operator))

            chain_name = str(row.get("hotel_chain", "")).strip()
            if chain_name:
                triples.add((operator, "affiliatedWith", chain_entity_label(chain_name)))

        linked_id = str(row.get("linked_establishment_id", "")).strip()
        if linked_id and linked_id != "nan":
            triples.add((unit, "listingOf", unit_entity_label(linked_id)))

    return sorted(triples)


def main() -> None:
    ensure_directories()
    if not UNIFIED_DATA_FILE.exists():
        raise SystemExit(f"Missing input file: {UNIFIED_DATA_FILE}")

    df = pd.read_csv(UNIFIED_DATA_FILE, low_memory=False)
    triples = build_triples(df)
    triples_df = pd.DataFrame(triples, columns=["head", "relation", "tail"])
    triples_df.to_csv(TRIPLES_FILE, sep="\t", index=False)

    relation_counts = Counter(triples_df["relation"])
    metadata = {
        "generated_at": utc_timestamp(),
        "triple_count": int(len(triples_df)),
        "entity_count_estimate": int(len(set(triples_df["head"]).union(set(triples_df["tail"])))),
        "relation_count": int(triples_df["relation"].nunique()),
        "relations": dict(sorted((str(k), int(v)) for k, v in relation_counts.items())),
    }
    write_json(TRIPLES_METADATA_JSON, metadata)

    print(f"Wrote {TRIPLES_FILE}")
    print(f"Wrote {TRIPLES_METADATA_JSON}")
    print(f"Triples exported: {metadata['triple_count']}")


if __name__ == "__main__":
    main()
