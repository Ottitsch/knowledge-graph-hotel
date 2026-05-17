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
- Quality report: `reports/data_quality_report.md`
- SHACL report: `reports/shacl_validation_report.txt`
- Rule report: `reports/rule_inference_report.md`
- Embedding report: `reports/embedding_report.md`
- Embedding worked examples: `reports/embedding_examples.md`
- Candidate scores: `reports/candidate_scores.csv`
- Evolution report: `reports/evolution_report.md`
- Reflection notes (LO4 / LO6 / LO12): `reports/data_model_comparison.md`, `reports/scalable_reasoning.md`, `reports/ml_logic_interaction.md`
- Financial KG comparison (LO10): `reports/financial_kg_comparison.md`
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
