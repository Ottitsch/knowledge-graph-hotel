# Setup - Vienna Accommodation Operator KG

## 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Configure Neo4j

Set environment variables or use a local `.env` file:

- `NEO4J_URI`
- `NEO4J_USER`
- `NEO4J_PASSWORD`

Neo4j is optional if you only want the RDF export, quality audit, and SHACL validation.

## 3. Run the pipeline

```bash
python src/run_pipeline.py
python src/run_pipeline.py --skip-neo4j
```

Core stages:

1. `collect_datagv.py`
2. `collect_osm.py`
3. `collect_wikidata.py`
4. `download_airbnb.py`
5. `resolve_entities.py`
6. `build_graph.py`
7. `audit_quality.py`
8. `validate_graph.py`

## 4. Review outputs

- RDF graph: `graph/vienna_accommodation_operator_kg.ttl`
- Ontology: `ontology/accommodation_operator.owl`
- SHACL shapes: `ontology/accommodation_operator_shapes.ttl`
- Quality report: `reports/data_quality_report.md`
- SHACL report: `reports/shacl_validation_report.txt`

## 5. Run the webapp

```bash
python webapp/app.py
```

Frontend build:

```bash
cd webapp/frontend
npm install
npm run build
```
