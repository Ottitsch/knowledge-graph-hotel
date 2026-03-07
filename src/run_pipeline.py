"""
Master pipeline runner — executes all collection, resolution, and graph-building steps.
Run from the project root: python src/run_pipeline.py

Pass --skip-neo4j to skip Neo4j ingestion (still produces RDF Turtle).
Pass --skip-airbnb to skip Inside Airbnb download (useful if already downloaded).
"""

import subprocess
import sys
import os
import argparse

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(SRC_DIR, "..")


def run(script: str, description: str) -> bool:
    path = os.path.join(SRC_DIR, script)
    print(f"\n{'='*60}", flush=True)
    print(f"STEP: {description}", flush=True)
    print(f"{'='*60}", flush=True)
    result = subprocess.run([sys.executable, "-u", path], cwd=PROJECT_DIR)
    if result.returncode != 0:
        print(f"WARNING: {script} exited with code {result.returncode}", flush=True)
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Run the Vienna Hotel KG pipeline")
    parser.add_argument("--skip-neo4j", action="store_true", help="Skip Neo4j ingestion")
    parser.add_argument("--skip-airbnb", action="store_true", help="Skip Airbnb download")
    args = parser.parse_args()

    steps = [
        ("collect_datagv.py", "Fetch data.gv.at Vienna accommodations"),
        ("collect_osm.py", "Fetch OSM hotel POIs via Overpass"),
        ("collect_wikidata.py", "Fetch Wikidata hotel ownership"),
    ]

    if not args.skip_airbnb:
        steps.append(("download_airbnb.py", "Download Inside Airbnb Vienna listings"))

    steps += [
        ("resolve_entities.py", "Entity resolution & deduplication"),
        ("collect_firmenbuch.py", "Firmenbuch company lookups"),
        ("build_graph.py", "Build Knowledge Graph (Neo4j + RDF Turtle)"),
    ]

    if args.skip_neo4j:
        os.environ["SKIP_NEO4J"] = "1"

    failed = []
    for script, desc in steps:
        ok = run(script, desc)
        if not ok:
            failed.append(script)

    print(f"\n{'='*60}")
    print("PIPELINE COMPLETE")
    print(f"{'='*60}")
    if failed:
        print(f"Steps with errors: {failed}")
        print("Check output above for details.")
    else:
        print("All steps completed successfully.")

    print("\nNext steps:")
    print("  1. Open Neo4j Browser: http://localhost:7474")
    print("  2. Run Cypher queries from src/queries.cypher")
    print("  3. View RDF graph: graph/vienna_hotels.ttl")
    print("  4. Open ontology: ontology/hotel_ownership.owl (in Protege)")


if __name__ == "__main__":
    main()
