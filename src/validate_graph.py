"""
Validate the RDF export against SHACL shapes.

Reads:  graph/vienna_accommodation_operator_kg.ttl
        ontology/accommodation_operator.owl
        ontology/accommodation_operator_shapes.ttl
Writes: reports/shacl_validation_report.txt
        reports/shacl_validation_report.ttl
"""

from pathlib import Path

from pyshacl import validate

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_GRAPH = BASE_DIR / "graph" / "vienna_accommodation_operator_kg.ttl"
ONTOLOGY_GRAPH = BASE_DIR / "ontology" / "accommodation_operator.owl"
SHAPES_GRAPH = BASE_DIR / "ontology" / "accommodation_operator_shapes.ttl"
REPORTS_DIR = BASE_DIR / "reports"
REPORT_TXT = REPORTS_DIR / "shacl_validation_report.txt"
REPORT_TTL = REPORTS_DIR / "shacl_validation_report.ttl"


def main():
    for path in [DATA_GRAPH, ONTOLOGY_GRAPH, SHAPES_GRAPH]:
        if not path.exists():
            raise SystemExit(f"Missing required file: {path}")

    REPORTS_DIR.mkdir(exist_ok=True)

    conforms, report_graph, report_text = validate(
        data_graph=str(DATA_GRAPH),
        shacl_graph=str(SHAPES_GRAPH),
        ont_graph=str(ONTOLOGY_GRAPH),
        inference="rdfs",
        abort_on_first=False,
        allow_infos=True,
        allow_warnings=True,
    )

    with open(REPORT_TXT, "w", encoding="utf-8") as fh:
        fh.write(str(report_text))

    report_graph.serialize(destination=REPORT_TTL, format="turtle")

    print(f"Wrote {REPORT_TXT}")
    print(f"Wrote {REPORT_TTL}")
    print(f"SHACL conforms: {conforms}")

    if not conforms:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
