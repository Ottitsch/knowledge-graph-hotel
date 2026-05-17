"""
Vienna Accommodation Operator KG master pipeline runner.
Executes collection, resolution, graph-building, audit, and validation steps.

Run from the project root: python src/run_pipeline.py

Flags:
  --skip-neo4j    Skip Neo4j ingestion (still produces RDF Turtle)
  --skip-airbnb   Skip Inside Airbnb download (useful if already downloaded)
  --with-optional Run optional enrichment scripts (for example Firmenbuch placeholder)
"""

import argparse
import os
import subprocess
import sys

from common_paths import ensure_directories

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(SRC_DIR, "..")


def run(script: str, description: str) -> bool:
    # `script` is now a relative path inside src/ (e.g. "collect/collect_osm.py").
    path = os.path.join(SRC_DIR, script)
    print(f"\n{'=' * 60}", flush=True)
    print(f"STEP: {description} ({script})", flush=True)
    print(f"{'=' * 60}", flush=True)
    result = subprocess.run([sys.executable, "-u", path], cwd=PROJECT_DIR)
    if result.returncode != 0:
        print(f"WARNING: {script} exited with code {result.returncode}", flush=True)
        return False
    return True


def main():
    ensure_directories()

    parser = argparse.ArgumentParser(
        description="Run the Vienna Accommodation Operator KG pipeline"
    )
    parser.add_argument("--skip-neo4j", action="store_true", help="Skip Neo4j ingestion")
    parser.add_argument("--skip-airbnb", action="store_true", help="Skip Airbnb download")
    parser.add_argument("--skip-rules", action="store_true", help="Skip rule materialization")
    parser.add_argument("--skip-embeddings", action="store_true", help="Skip embedding export, training, and scoring")
    parser.add_argument("--skip-snapshots", action="store_true", help="Skip snapshot versioning and diff generation")
    parser.add_argument(
        "--with-optional",
        action="store_true",
        help="Run optional enrichment scripts (Firmenbuch placeholder)",
    )
    parser.add_argument(
        "--skip-assistant-cache",
        action="store_true",
        help="Reserved flag for future query-assistant caching; currently a no-op",
    )
    args = parser.parse_args()

    steps = [
        ("collect/collect_datagv.py", "Fetch data.gv.at Vienna accommodations"),
        ("collect/collect_osm.py", "Fetch OSM accommodation POIs via Overpass"),
        ("collect/collect_wikidata.py", "Fetch Wikidata accommodation and operator enrichment"),
    ]

    if not args.skip_airbnb:
        steps.append(("collect/download_airbnb.py", "Download Inside Airbnb Vienna listings"))

    steps += [
        (
            "construct/resolve_entities.py",
            "Resolve entities, normalize districts, and classify listing-establishment matches",
        ),
        ("construct/build_graph.py", "Build Knowledge Graph (Neo4j and RDF Turtle)"),
        ("audit/audit_quality.py", "Generate data quality audit report"),
        ("audit/validate_graph.py", "Validate RDF export with SHACL"),
    ]

    if not args.skip_rules:
        steps.append(("construct/materialize_rules.py", "Generate rule-based inferred facts and reports"))

    if not args.skip_embeddings:
        steps.extend(
            [
                ("construct/export_triples.py", "Export labeled triples for embedding training"),
                ("learn/train_embeddings.py", "Train KG embeddings and write metrics"),
                ("learn/score_candidates.py", "Score weak candidate links and operator similarity"),
            ]
        )

    steps.append(("audit/write_financial_comparison.py", "Write comparative financial KG case-study report"))

    if not args.skip_snapshots:
        steps.extend(
            [
                ("evolve/version_snapshot.py", "Version the current pipeline outputs as a snapshot"),
                ("evolve/diff_snapshots.py", "Compare the latest two snapshots"),
            ]
        )

    if args.with_optional:
        steps.append(
            (
                "collect/optional_collect_firmenbuch.py",
                "Optional: record operator names for future Firmenbuch enrichment",
            )
        )

    if args.skip_neo4j:
        os.environ["SKIP_NEO4J"] = "1"

    failed = []
    for script, desc in steps:
        ok = run(script, desc)
        if not ok:
            failed.append(script)

    print(f"\n{'=' * 60}")
    print("PIPELINE COMPLETE - Vienna Accommodation Operator KG")
    print(f"{'=' * 60}")
    if failed:
        print(f"Steps with errors: {failed}")
        print("Check output above for details.")
    else:
        print("All steps completed successfully.")

    print("\nNext steps:")
    print("  1. Open Neo4j Browser: http://localhost:7474")
    print("  2. Run Cypher queries from src/queries.cypher")
    print("  3. View RDF graph: graph/vienna_accommodation_operator_kg.ttl")
    print("  4. Open ontology: ontology/accommodation_operator.owl (in Protege)")
    print("  5. Review reports: reports/quality/data_quality_report.md and reports/quality/shacl_validation_report.txt")
    print("  6. Review reasoning, embedding, and evolution reports in reports/")
    print("  7. Run the dashboard: python webapp/app.py")


if __name__ == "__main__":
    main()
