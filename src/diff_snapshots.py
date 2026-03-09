"""
Compare the latest two snapshots and generate an evolution report.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from common_paths import (
    EVOLUTION_CHANGES_JSON,
    EVOLUTION_REPORT_MD,
    EVOLUTION_SUMMARY_JSON,
    QUALITY_REPORT_JSON,
    RULE_SUMMARY_JSON,
    SNAPSHOTS_DIR,
    UNIFIED_DATA_FILE,
    ensure_directories,
    read_json,
    utc_timestamp,
    write_json,
)


def _snapshot_dirs() -> list[Path]:
    if not SNAPSHOTS_DIR.exists():
        return []
    return sorted([path for path in SNAPSHOTS_DIR.iterdir() if path.is_dir()])


def _load_snapshot_csv(path: Path) -> pd.DataFrame:
    file_path = path / UNIFIED_DATA_FILE.name
    if not file_path.exists():
        return pd.DataFrame()
    return pd.read_csv(file_path, low_memory=False)


def _load_snapshot_json(path: Path, filename: str):
    return read_json(path / filename, default={})


def _non_empty(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def _string_value(row: pd.Series, column: str) -> str:
    value = row.get(column, "")
    if pd.isna(value):
        return ""
    return str(value).strip()


def _sorted_csv(value: str) -> str:
    parts = [part.strip() for part in str(value).split(",") if part and part.strip()]
    return ",".join(sorted(parts))


def _entity_key(row: pd.Series) -> str:
    granularity = _string_value(row, "granularity") or "unit"
    raw_id = _string_value(row, "raw_id")
    source_names = _sorted_csv(_string_value(row, "source_names"))
    source_record_ids = _sorted_csv(_string_value(row, "source_record_ids"))

    if granularity == "listing" and raw_id:
        return f"listing:airbnb:{raw_id}"
    if source_record_ids:
        return f"{granularity}:{source_names}:{source_record_ids}"

    name = _string_value(row, "name")
    district = _string_value(row, "district")
    lat = _string_value(row, "lat")
    lon = _string_value(row, "lon")
    return f"{granularity}:{source_names}:{name}:{district}:{lat}:{lon}"


def _prepare_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    prepared = df.copy()
    prepared["_snapshot_key"] = prepared.apply(_entity_key, axis=1)
    prepared = prepared[prepared["_snapshot_key"].ne("")].copy()
    prepared = prepared.drop_duplicates(subset="_snapshot_key", keep="first")
    return prepared


def build_diff(previous_df: pd.DataFrame, current_df: pd.DataFrame, previous_path: Path, current_path: Path) -> tuple[dict, dict]:
    previous_df = _prepare_snapshot(previous_df)
    current_df = _prepare_snapshot(current_df)

    prev_ids = set(previous_df.get("_snapshot_key", pd.Series(dtype=str)).dropna().astype(str))
    curr_ids = set(current_df.get("_snapshot_key", pd.Series(dtype=str)).dropna().astype(str))
    added_ids = sorted(curr_ids - prev_ids)
    removed_ids = sorted(prev_ids - curr_ids)

    prev_canonical_to_key = (
        previous_df.set_index("canonical_id")["_snapshot_key"].fillna("").astype(str).to_dict()
        if not previous_df.empty and "canonical_id" in previous_df
        else {}
    )
    curr_canonical_to_key = (
        current_df.set_index("canonical_id")["_snapshot_key"].fillna("").astype(str).to_dict()
        if not current_df.empty and "canonical_id" in current_df
        else {}
    )
    prev_links = (
        previous_df.set_index("_snapshot_key")["linked_establishment_id"].fillna("").astype(str)
        if not previous_df.empty
        else pd.Series(dtype=str)
    )
    curr_links = (
        current_df.set_index("_snapshot_key")["linked_establishment_id"].fillna("").astype(str)
        if not current_df.empty
        else pd.Series(dtype=str)
    )
    link_added = []
    link_removed = []
    changed_operator_labels = []

    shared_ids = sorted(prev_ids & curr_ids)
    for snapshot_key in shared_ids:
        prev_link = prev_canonical_to_key.get(prev_links.get(snapshot_key, ""), "")
        curr_link = curr_canonical_to_key.get(curr_links.get(snapshot_key, ""), "")
        if not prev_link and curr_link:
            link_added.append({"snapshot_key": snapshot_key, "linked_establishment_key": curr_link})
        elif prev_link and not curr_link:
            link_removed.append({"snapshot_key": snapshot_key, "linked_establishment_key": prev_link})

    if not previous_df.empty and not current_df.empty:
        prev_lookup = previous_df.set_index("_snapshot_key")
        curr_lookup = current_df.set_index("_snapshot_key")
        for snapshot_key in shared_ids:
            prev_name = str(prev_lookup.at[snapshot_key, "operator_name"]) if snapshot_key in prev_lookup.index else ""
            curr_name = str(curr_lookup.at[snapshot_key, "operator_name"]) if snapshot_key in curr_lookup.index else ""
            if prev_name != curr_name:
                changed_operator_labels.append(
                    {
                        "snapshot_key": snapshot_key,
                        "unit_name": str(curr_lookup.at[snapshot_key, "name"]),
                        "previous_operator": prev_name,
                        "current_operator": curr_name,
                    }
                )

    previous_quality = _load_snapshot_json(previous_path, QUALITY_REPORT_JSON.name)
    current_quality = _load_snapshot_json(current_path, QUALITY_REPORT_JSON.name)
    previous_rules = _load_snapshot_json(previous_path, RULE_SUMMARY_JSON.name)
    current_rules = _load_snapshot_json(current_path, RULE_SUMMARY_JSON.name)

    summary = {
        "generated_at": utc_timestamp(),
        "previous_snapshot": previous_path.name,
        "current_snapshot": current_path.name,
        "added_units": len(added_ids),
        "removed_units": len(removed_ids),
        "listing_links_added": len(link_added),
        "listing_links_removed": len(link_removed),
        "operator_labels_changed": len(changed_operator_labels),
        "rule_fact_delta": int(current_rules.get("fact_count", 0)) - int(previous_rules.get("fact_count", 0)),
        "linked_listing_delta": int(current_quality.get("listing_matches", {}).get("linked", 0))
        - int(previous_quality.get("listing_matches", {}).get("linked", 0)),
    }

    details = {
        "summary": summary,
        "added_units": added_ids[:50],
        "removed_units": removed_ids[:50],
        "listing_links_added": link_added[:50],
        "listing_links_removed": link_removed[:50],
        "operator_labels_changed": changed_operator_labels[:50],
    }
    return summary, details


def build_markdown(summary: dict, details: dict) -> str:
    lines = [
        "# Evolution Report",
        "",
        f"- Generated at: {summary['generated_at']}",
        f"- Previous snapshot: {summary['previous_snapshot']}",
        f"- Current snapshot: {summary['current_snapshot']}",
        f"- Added units: {summary['added_units']}",
        f"- Removed units: {summary['removed_units']}",
        f"- Listing links added: {summary['listing_links_added']}",
        f"- Listing links removed: {summary['listing_links_removed']}",
        f"- Operator labels changed: {summary['operator_labels_changed']}",
        f"- Rule fact delta: {summary['rule_fact_delta']}",
        f"- Evidence-backed listing delta: {summary['linked_listing_delta']}",
        "",
        "## Sample Operator Label Changes",
        "",
    ]
    if details["operator_labels_changed"]:
        for item in details["operator_labels_changed"][:10]:
            lines.append(
                f"- `{item['unit_name']}`: `{item['previous_operator']}` -> `{item['current_operator']}`"
            )
    else:
        lines.append("- No operator label changes detected in the latest diff.")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This report treats the KG as an evolving artifact rather than a one-off export.",
            "- Changes in links, labels, and inferred facts are visible between snapshots.",
            "- This supports the portfolio narrative around KG evolution and controlled updates.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    ensure_directories()
    snapshots = _snapshot_dirs()
    if len(snapshots) < 2:
        summary = {
            "generated_at": utc_timestamp(),
            "status": "insufficient_snapshots",
            "message": "Need at least two snapshots to compute an evolution diff.",
            "available_snapshots": [path.name for path in snapshots],
        }
        write_json(EVOLUTION_SUMMARY_JSON, summary)
        write_json(EVOLUTION_CHANGES_JSON, {"summary": summary, "changes": []})
        EVOLUTION_REPORT_MD.write_text(
            "# Evolution Report\n\nNeed at least two snapshots to compute an evolution diff.\n",
            encoding="utf-8",
        )
        print("Not enough snapshots for diff generation yet.")
        return

    previous_path, current_path = snapshots[-2], snapshots[-1]
    previous_df = _load_snapshot_csv(previous_path)
    current_df = _load_snapshot_csv(current_path)
    summary, details = build_diff(previous_df, current_df, previous_path, current_path)

    write_json(EVOLUTION_SUMMARY_JSON, summary)
    write_json(EVOLUTION_CHANGES_JSON, details)
    EVOLUTION_REPORT_MD.write_text(build_markdown(summary, details), encoding="utf-8")

    print(f"Wrote {EVOLUTION_SUMMARY_JSON}")
    print(f"Wrote {EVOLUTION_CHANGES_JSON}")
    print(f"Wrote {EVOLUTION_REPORT_MD}")


if __name__ == "__main__":
    main()
