"""
Score weak listing-establishment candidates and operator similarity using trained embeddings.

Reads:  data/properties_unified.csv
        models/embeddings/transe_embeddings.npz
        models/embeddings/transe_mappings.json
Writes: reports/ml/candidate_scores.csv
        reports/ml/operator_similarity.json
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


# >>> kg-hotel src-bootstrap
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
# <<< kg-hotel src-bootstrap

from common_paths import (
    CANDIDATE_SCORES_CSV,
    EMBEDDING_MAPPINGS_JSON,
    EMBEDDING_MATRIX_FILE,
    OPERATOR_SIMILARITY_JSON,
    UNIFIED_DATA_FILE,
    ensure_directories,
    read_json,
    utc_timestamp,
    write_json,
)
from kg_utils import operator_entity_label, operator_key_from_row, unit_entity_label


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _normalized_scores(values: np.ndarray) -> np.ndarray:
    if len(values) == 0:
        return values
    min_value = float(values.min())
    max_value = float(values.max())
    if math.isclose(min_value, max_value):
        return np.ones_like(values)
    return (values - min_value) / (max_value - min_value)


def load_embeddings():
    mappings = read_json(EMBEDDING_MAPPINGS_JSON, default={})
    if not mappings:
        raise SystemExit(f"Missing embedding mappings: {EMBEDDING_MAPPINGS_JSON}")
    arrays = np.load(EMBEDDING_MATRIX_FILE)
    return (
        arrays["entity_embeddings"],
        arrays["relation_embeddings"],
        mappings["entity_to_id"],
        mappings["relation_to_id"],
    )


def score_listing_candidates(df: pd.DataFrame, entity_embeddings, relation_embeddings, entity_to_id, relation_to_id):
    candidate_rows = df[
        df["candidate_establishment_id"].fillna("").astype(str).str.strip().ne("")
        & df["linked_establishment_id"].fillna("").astype(str).str.strip().eq("")
    ].copy()
    if candidate_rows.empty:
        candidate_rows.to_csv(CANDIDATE_SCORES_CSV, index=False)
        return candidate_rows

    relation_idx = relation_to_id.get("listingOf")
    if relation_idx is None:
        raise SystemExit("Missing relation embedding for listingOf")
    relation_vector = relation_embeddings[relation_idx]

    scores = []
    for _, row in candidate_rows.iterrows():
        listing_label = unit_entity_label(str(row["canonical_id"]))
        establishment_label = unit_entity_label(str(row["candidate_establishment_id"]))
        if listing_label not in entity_to_id or establishment_label not in entity_to_id:
            scores.append(float("nan"))
            continue
        head = entity_embeddings[entity_to_id[listing_label]]
        tail = entity_embeddings[entity_to_id[establishment_label]]
        score = -float(np.linalg.norm(head + relation_vector - tail))
        scores.append(score)

    candidate_rows["embedding_score_raw"] = scores
    valid_mask = candidate_rows["embedding_score_raw"].notna()
    candidate_rows.loc[valid_mask, "embedding_score"] = _normalized_scores(
        candidate_rows.loc[valid_mask, "embedding_score_raw"].to_numpy(dtype=float)
    )
    candidate_rows["embedding_suggestion"] = candidate_rows["embedding_score"].fillna(0).apply(
        lambda value: "strong_review" if value >= 0.8 else ("review" if value >= 0.55 else "weak")
    )
    candidate_rows = candidate_rows.sort_values(
        ["embedding_score", "candidate_establishment_distance_m"],
        ascending=[False, True],
    )
    candidate_rows.to_csv(CANDIDATE_SCORES_CSV, index=False, encoding="utf-8")
    return candidate_rows


def build_operator_similarity(df: pd.DataFrame, entity_embeddings, entity_to_id):
    working = df.copy()
    working["operator_key"] = working.apply(operator_key_from_row, axis=1)
    working["operator_name"] = working["operator_name"].fillna("").astype(str).str.strip()
    working = working[working["operator_name"].ne("")]
    operator_counts = (
        working.groupby(["operator_key", "operator_name"])
        .size()
        .reset_index(name="unit_count")
        .sort_values("unit_count", ascending=False)
    )
    top_operators = operator_counts.head(120).copy()
    top_operators["entity_label"] = top_operators["operator_key"].apply(operator_entity_label)
    top_operators = top_operators[top_operators["entity_label"].isin(entity_to_id)]

    vectors = {}
    for _, row in top_operators.iterrows():
        vectors[row["operator_key"]] = entity_embeddings[entity_to_id[row["entity_label"]]]

    payload = {
        "generated_at": utc_timestamp(),
        "operators": [],
    }

    operator_rows = top_operators.to_dict(orient="records")
    for row in operator_rows:
        base_vector = vectors.get(row["operator_key"])
        if base_vector is None:
            continue
        scored = []
        for other in operator_rows:
            if other["operator_key"] == row["operator_key"]:
                continue
            other_vector = vectors.get(other["operator_key"])
            if other_vector is None:
                continue
            scored.append(
                {
                    "operator_id": other["operator_key"],
                    "operator_name": other["operator_name"],
                    "unit_count": int(other["unit_count"]),
                    "similarity": round(_cosine_similarity(base_vector, other_vector), 4),
                }
            )
        scored.sort(key=lambda item: item["similarity"], reverse=True)
        payload["operators"].append(
            {
                "operator_id": row["operator_key"],
                "operator_name": row["operator_name"],
                "unit_count": int(row["unit_count"]),
                "similar": scored[:5],
            }
        )

    write_json(OPERATOR_SIMILARITY_JSON, payload)
    return payload


def main() -> None:
    ensure_directories()
    if not UNIFIED_DATA_FILE.exists():
        raise SystemExit(f"Missing input file: {UNIFIED_DATA_FILE}")
    if not EMBEDDING_MATRIX_FILE.exists():
        raise SystemExit(f"Missing embedding matrix: {EMBEDDING_MATRIX_FILE}")

    df = pd.read_csv(UNIFIED_DATA_FILE, low_memory=False)
    entity_embeddings, relation_embeddings, entity_to_id, relation_to_id = load_embeddings()
    candidate_rows = score_listing_candidates(
        df, entity_embeddings, relation_embeddings, entity_to_id, relation_to_id
    )
    similarity_payload = build_operator_similarity(df, entity_embeddings, entity_to_id)

    print(f"Wrote {CANDIDATE_SCORES_CSV}")
    print(f"Wrote {OPERATOR_SIMILARITY_JSON}")
    print(f"Candidate rows scored: {len(candidate_rows)}")
    print(f"Operators with similarity results: {len(similarity_payload['operators'])}")


if __name__ == "__main__":
    main()
