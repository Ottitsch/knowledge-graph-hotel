"""
Generate a reproducible quality report for the unified accommodation dataset.

Reads:  data/properties_unified.csv
Writes: reports/quality/data_quality_report.md
        reports/quality/quality_summary.json
"""

import json
import sys as _sys
from pathlib import Path
from pathlib import Path as _Path

_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from common_paths import (  # noqa: E402
    QUALITY_REPORT_JSON,
    QUALITY_REPORT_MD,
    UNIFIED_DATA_FILE,
    ensure_directories,
)

DATA_FILE = UNIFIED_DATA_FILE
REPORT_MD = QUALITY_REPORT_MD
REPORT_JSON = QUALITY_REPORT_JSON


def _series_counts(series: pd.Series) -> dict:
    return {str(k): int(v) for k, v in series.value_counts(dropna=False).items()}


def _non_empty(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def build_summary(df: pd.DataFrame) -> dict:
    listings = df[df["granularity"] == "listing"].copy()
    establishments = df[df["granularity"] == "establishment"].copy()

    linked_mask = _non_empty(listings.get("linked_establishment_id", pd.Series(dtype=str))).ne("")
    candidate_mask = _non_empty(listings.get("candidate_establishment_id", pd.Series(dtype=str))).ne("")
    candidate_only_mask = candidate_mask & ~linked_mask

    summary = {
        "totals": {
            "rows": int(len(df)),
            "listings": int(len(listings)),
            "establishments": int(len(establishments)),
        },
        "granularity": _series_counts(df["granularity"]),
        "source_combinations": _series_counts(df["source_names"]),
        "establishment_merge_confidence": _series_counts(establishments["merge_confidence"]),
        "operator_identity_confidence": _series_counts(df["operator_identity_confidence"]),
        "operator_name_source": _series_counts(df["operator_name_source"]),
        "listing_matches": {
            "linked": int(linked_mask.sum()),
            "candidate_only": int(candidate_only_mask.sum()),
            "no_candidate": int((~candidate_mask).sum()),
            "linked_confidence": _series_counts(
                _non_empty(listings.get("linked_establishment_confidence", pd.Series(dtype=str)))
            ),
        },
        "establishment_operator_fallbacks": {
            "venue_name_fallback_rows": int(
                (_non_empty(establishments["operator_name_source"]) == "venue_name_fallback").sum()
            ),
            "share_percent": round(
                100
                * (
                    (_non_empty(establishments["operator_name_source"]) == "venue_name_fallback").sum()
                    / max(len(establishments), 1)
                ),
                1,
            ),
        },
        "multi_source_establishments": {
            "rows": int((_non_empty(establishments["source_names"]).str.contains(",")).sum()),
            "share_percent": round(
                100
                * ((_non_empty(establishments["source_names"]).str.contains(",")).sum() / max(len(establishments), 1)),
                1,
            ),
        },
    }
    return summary


def build_markdown(summary: dict) -> str:
    totals = summary["totals"]
    lines = [
        "# Data Quality Report",
        "",
        "## Snapshot",
        "",
        f"- Total rows: {totals['rows']}",
        f"- Listing-level rows: {totals['listings']}",
        f"- Establishment-level rows: {totals['establishments']}",
        "",
        "## Merge Quality",
        "",
        f"- Multi-source establishments: {summary['multi_source_establishments']['rows']} "
        f"({summary['multi_source_establishments']['share_percent']}%)",
    ]

    for key, value in summary["establishment_merge_confidence"].items():
        lines.append(f"- Establishment merge confidence `{key}`: {value}")

    lines += [
        "",
        "## Operator Evidence",
        "",
        f"- Establishment rows using venue-name fallback operators: "
        f"{summary['establishment_operator_fallbacks']['venue_name_fallback_rows']} "
        f"({summary['establishment_operator_fallbacks']['share_percent']}%)",
    ]
    for key, value in summary["operator_identity_confidence"].items():
        lines.append(f"- Operator identity confidence `{key}`: {value}")

    lines += [
        "",
        "## Airbnb to Establishment Matching",
        "",
        f"- Evidence-backed listing links asserted in graph: {summary['listing_matches']['linked']}",
        f"- Nearby candidates kept out of graph: {summary['listing_matches']['candidate_only']}",
        f"- Listings without nearby candidate: {summary['listing_matches']['no_candidate']}",
    ]
    for key, value in summary["listing_matches"]["linked_confidence"].items():
        if key:
            lines.append(f"- Linked listing confidence `{key}`: {value}")

    lines += [
        "",
        "## Top Source Combinations",
        "",
    ]
    for key, value in list(summary["source_combinations"].items())[:10]:
        lines.append(f"- `{key}`: {value}")

    lines += [
        "",
        "## Interpretation",
        "",
        "- The KG now distinguishes evidence-backed listing-establishment matches from weak proximity-only candidates.",
        "- Operator labels carry explicit provenance and confidence, which makes low-confidence venue-name fallbacks visible instead of implicit.",
        "- This report is intended to be referenced in the course portfolio as evidence of KG quality control.",
        "",
    ]
    return "\n".join(lines)


def main():
    if not DATA_FILE.exists():
        raise SystemExit(f"Missing input file: {DATA_FILE}")

    ensure_directories()
    df = pd.read_csv(DATA_FILE, low_memory=False)
    summary = build_summary(df)

    with open(REPORT_JSON, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)

    with open(REPORT_MD, "w", encoding="utf-8") as fh:
        fh.write(build_markdown(summary))

    print(f"Wrote {REPORT_MD}")
    print(f"Wrote {REPORT_JSON}")
    print("Key metrics:")
    print(f"  rows: {summary['totals']['rows']}")
    print(f"  linked listings: {summary['listing_matches']['linked']}")
    print(f"  candidate-only listings: {summary['listing_matches']['candidate_only']}")
    print(
        "  establishment fallback operators: "
        f"{summary['establishment_operator_fallbacks']['share_percent']}%"
    )


if __name__ == "__main__":
    main()
