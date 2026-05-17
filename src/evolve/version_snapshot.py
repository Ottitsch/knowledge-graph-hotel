"""
Persist the current pipeline outputs as a timestamped snapshot.
"""

from __future__ import annotations

import shutil


# >>> kg-hotel src-bootstrap
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
# <<< kg-hotel src-bootstrap

from common_paths import (
    CANDIDATE_SCORES_CSV,
    EMBEDDING_METRICS_JSON,
    EVOLUTION_SUMMARY_JSON,
    QUALITY_REPORT_JSON,
    RDF_GRAPH_FILE,
    RULE_SUMMARY_JSON,
    SNAPSHOTS_DIR,
    UNIFIED_DATA_FILE,
    ensure_directories,
    read_json,
    snapshot_id,
    utc_timestamp,
    write_json,
)


def copy_if_exists(source, destination_dir) -> None:
    if source.exists():
        shutil.copy2(source, destination_dir / source.name)


def main() -> None:
    ensure_directories()
    if not UNIFIED_DATA_FILE.exists():
        raise SystemExit(f"Missing input file: {UNIFIED_DATA_FILE}")

    current_snapshot_id = snapshot_id()
    destination = SNAPSHOTS_DIR / current_snapshot_id
    destination.mkdir(parents=True, exist_ok=True)

    for artifact in [
        UNIFIED_DATA_FILE,
        QUALITY_REPORT_JSON,
        RULE_SUMMARY_JSON,
        EMBEDDING_METRICS_JSON,
        CANDIDATE_SCORES_CSV,
        RDF_GRAPH_FILE,
    ]:
        copy_if_exists(artifact, destination)

    summary = {
        "snapshot_id": current_snapshot_id,
        "generated_at": utc_timestamp(),
        "files": sorted(path.name for path in destination.iterdir() if path.is_file()),
        "quality": read_json(destination / QUALITY_REPORT_JSON.name, default={}),
        "rules": read_json(destination / RULE_SUMMARY_JSON.name, default={}),
        "embeddings": read_json(destination / EMBEDDING_METRICS_JSON.name, default={}),
    }
    write_json(destination / "snapshot_summary.json", summary)
    print(f"Wrote snapshot: {destination}")
    print(f"Snapshot files: {len(summary['files'])}")


if __name__ == "__main__":
    main()
