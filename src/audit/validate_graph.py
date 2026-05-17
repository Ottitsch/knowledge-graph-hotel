"""
Validate the RDF export against SHACL shapes.

Reads:  graph/vienna_accommodation_operator_kg.ttl
        ontology/accommodation_operator.owl
        ontology/accommodation_operator_shapes.ttl
Writes: reports/quality/shacl_validation_report.txt
        reports/quality/shacl_validation_report.ttl
"""

import sys as _sys
from pathlib import Path
from pathlib import Path as _Path

_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from pyshacl import validate  # noqa: E402

from common_paths import (  # noqa: E402
    GRAPH_DIR,
    ONTOLOGY_DIR,
    RDF_GRAPH_FILE,
    SHACL_REPORT_TTL,
    SHACL_REPORT_TXT,
    ensure_directories,
)

DATA_GRAPH = RDF_GRAPH_FILE
ONTOLOGY_GRAPH = ONTOLOGY_DIR / "accommodation_operator.owl"
SHAPES_GRAPH = ONTOLOGY_DIR / "accommodation_operator_shapes.ttl"


def main():
    for path in [DATA_GRAPH, ONTOLOGY_GRAPH, SHAPES_GRAPH]:
        if not path.exists():
            raise SystemExit(f"Missing required file: {path}")

    ensure_directories()

    conforms, report_graph, report_text = validate(
        data_graph=str(DATA_GRAPH),
        shacl_graph=str(SHAPES_GRAPH),
        ont_graph=str(ONTOLOGY_GRAPH),
        inference="rdfs",
        abort_on_first=False,
        allow_infos=True,
        allow_warnings=True,
    )

    with open(SHACL_REPORT_TXT, "w", encoding="utf-8") as fh:
        fh.write(str(report_text))

    report_graph.serialize(destination=SHACL_REPORT_TTL, format="turtle")

    print(f"Wrote {SHACL_REPORT_TXT}")
    print(f"Wrote {SHACL_REPORT_TTL}")
    print(f"SHACL conforms: {conforms}")

    if not conforms:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
