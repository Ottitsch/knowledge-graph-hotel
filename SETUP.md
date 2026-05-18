# Setup - Vienna Accommodation Operator KG

There are two supported setups: a local Python virtual environment (sections 1 to 5 below) or the bundled Docker image (section 6). The Docker path is fastest if you only want to view the dashboard against the shipped artifacts.

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
9. `materialize_rules.py`
10. `export_triples.py`
11. `train_embeddings.py`
12. `score_candidates.py`
13. `write_financial_comparison.py`
14. `version_snapshot.py`
15. `diff_snapshots.py`

Useful flags:

- `--skip-neo4j`
- `--skip-airbnb`
- `--skip-rules`
- `--skip-embeddings`
- `--skip-snapshots`

## 4. Review outputs

- RDF graph (asserted): `graph/vienna_accommodation_operator_kg.ttl`
- RDF graph (rule-inferred): `graph/inferred_facts.ttl`
- Ontology: `ontology/accommodation_operator.owl`
- SHACL shapes: `ontology/accommodation_operator_shapes.ttl`
- Quality report: `reports/quality/data_quality_report.md`
- SHACL report: `reports/quality/shacl_validation_report.txt`
- Rule report: `reports/logic/rule_inference_report.md`
- Embedding report: `reports/ml/embedding_report.md`
- Embedding worked examples: `reports/ml/embedding_examples.md`
- Candidate scores: `reports/ml/candidate_scores.csv`
- Evolution report: `reports/evolution/evolution_report.md`
- Reflection notes (LO4 / LO6 / LO12): `reports/reflection/data_model_comparison.md`, `reports/reflection/scalable_reasoning.md`, `reports/reflection/ml_logic_interaction.md`
- Financial KG comparison (LO10): `reports/reflection/financial_kg_comparison.md`
- Example Cypher queries: `src/queries.cypher`
- Example SPARQL queries: `src/queries.sparql`

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

Main dashboard areas:

- `Graph Explorer`
- `Analytics`
- `Map`
- `Reasoning Lab`
- `Evolution`
- `Query Assistant`

## 6. Run via Docker (alternative)

The repository ships a `Dockerfile` that builds the Vite/React frontend, installs the Python pipeline dependencies (`requirements-docker.txt`), starts Neo4j, loads the knowledge graph from `data/properties_unified.csv`, and serves the Flask/Gunicorn dashboard, all from one image.

```bash
docker build -t vienna-kg-dashboard .
docker run --rm -p 8000:8000 -p 7474:7474 -p 7687:7687 vienna-kg-dashboard
```

Then open:

- Dashboard: http://localhost:8000
- Neo4j Browser: http://localhost:7474 (user `neo4j`, password `password`)

Useful environment variables (see `docker/entrypoint.sh`):

- `FORCE_NEO4J_REBUILD=true` clears and rebuilds the graph on startup
- `NEO4J_INIT_ON_START=false` skips the graph load (useful when mounting a volume)
- `NEO4J_PASSWORD`, `NEO4J_USER`, `NEO4J_URI` override the defaults
- `PORT`, `WEB_CONCURRENCY`, `WEB_THREADS`, `WEB_TIMEOUT` tune the Gunicorn server
