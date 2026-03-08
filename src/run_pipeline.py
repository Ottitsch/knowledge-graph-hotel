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

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(SRC_DIR, "..")


def run(script: str, description: str) -> bool:
    path = os.path.join(SRC_DIR, script)
    print(f"\n{'=' * 60}", flush=True)
    print(f"STEP: {description}", flush=True)
    print(f"{'=' * 60}", flush=True)
    result = subprocess.run([sys.executable, "-u", path], cwd=PROJECT_DIR)
    if result.returncode != 0:
        print(f"WARNING: {script} exited with code {result.returncode}", flush=True)
        return False
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Run the Vienna Accommodation Operator KG pipeline"
    )
    parser.add_argument("--skip-neo4j", action="store_true", help="Skip Neo4j ingestion")
    parser.add_argument("--skip-airbnb", action="store_true", help="Skip Airbnb download")
    parser.add_argument(
        "--with-optional",
        action="store_true",
        help="Run optional enrichment scripts (Firmenbuch placeholder)",
    )
    args = parser.parse_args()

    steps = [
        ("collect_datagv.py", "Fetch data.gv.at Vienna accommodations"),
        ("collect_osm.py", "Fetch OSM accommodation POIs via Overpass"),
        ("collect_wikidata.py", "Fetch Wikidata accommodation and operator enrichment"),
    ]

    if not args.skip_airbnb:
        steps.append(("download_airbnb.py", "Download Inside Airbnb Vienna listings"))

    steps += [
        (
            "resolve_entities.py",
            "Resolve entities, normalize districts, and classify listing-establishment matches",
        ),
        ("build_graph.py", "Build Knowledge Graph (Neo4j and RDF Turtle)"),
        ("audit_quality.py", "Generate data quality audit report"),
        ("validate_graph.py", "Validate RDF export with SHACL"),
    ]

    if args.with_optional:
        steps.append(
            (
                "optional_collect_firmenbuch.py",
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
    print("  5. Review reports: reports/data_quality_report.md and reports/shacl_validation_report.txt")
    print("  6. Run the dashboard: python webapp/app.py")


if __name__ == "__main__":
    main()
