# Vienna Accommodation Operator Knowledge Graph

**Main question:** Which accommodation units in Vienna are operated by the same person or organization, and what other units do they operate?

This project combines public accommodation data for Vienna into a knowledge graph focused on operator relationships, provenance, and data quality. The project is intentionally **not** a legal ownership graph. Its strongest contribution is an Airbnb-centered KG with cautious enrichment from OpenStreetMap, Wikidata, and the official Vienna accommodation registry.

The current application also includes:

- rule-based inferred facts
- TransE knowledge graph embeddings
- embedding-ranked candidate links
- snapshot versioning and evolution reports
- a safe natural-language query assistant
- evidence panels for operators and candidate links

## Project Positioning

- Airbnb provides the large listing-level view.
- OSM, Wikidata, and data.gv.at provide establishment-level context and cross-source confirmation.
- Weak proximity-only listing-establishment matches are **not** asserted as graph facts.
- Operator labels carry explicit provenance and confidence, so fallback venue-name operators are visible instead of implicit.

## Data Sources

| Dataset | Approx. size | Granularity | Contribution |
|---|---:|---|---|
| Inside Airbnb | 31k+ | listing | host identity, host counts, listing type, coordinates |
| OpenStreetMap | 600+ | establishment | accommodation POIs, operator and brand tags, addresses |
| Wikidata | 300+ | establishment | notable hotels, operator, parent organization, brand links |
| data.gv.at / Stadt Wien | 390+ | establishment | official Vienna accommodation registry |

## Graph Model

### Node labels

- `AccommodationUnit`
- `Operator`
- `HotelChain`
- `District`
- `Source`

### Relationships

- `(AccommodationUnit)-[:OPERATED_BY]->(Operator)`
- `(AccommodationUnit)-[:LOCATED_IN]->(District)`
- `(AccommodationUnit)-[:OBSERVED_IN]->(Source)`
- `(Operator)-[:AFFILIATED_WITH]->(HotelChain)`
- `(AccommodationUnit)-[:LISTING_OF]->(AccommodationUnit)`

`LISTING_OF` is only created for evidence-backed listing-to-establishment matches.

### Rule-inferred edges (separate graph)

The rule engine in `src/materialize_rules.py` derives additional edges from the asserted graph and writes them to `graph/inferred_facts.ttl`. They are kept apart so asserted and inferred facts stay distinguishable:

- `(Operator)-[:corporateSibling]->(Operator)` — operators sharing a hotel chain (`shared_chain_corporate_group` rule).
- `(Operator)-[:memberOf]->(OperatorNetwork)` — connected components over `corporateSibling`, the recursive `operator_corporate_network` rule.

## Quality and Provenance Design

Each accommodation unit stores provenance and quality metadata:

- `granularity`: `listing` or `establishment`
- `source_names`: contributing data sources
- `source_record_ids`: original identifiers from the sources
- `merge_confidence`: `strong` for cross-source establishment merges, `single` otherwise
- `operator_name_source`: where the operator label came from
- `operator_identity_confidence`: `high`, `medium`, or `low`

### Operator evidence levels

- `high`: Airbnb host ID / host profile, OSM operator tag, Wikidata operator
- `medium`: Airbnb brand prefix extraction, OSM brand, Wikidata parent organization / brand / owner
- `low`: venue-name fallback used only because no better operator label was available

### Listing-establishment matching

For Airbnb listings near an establishment:

- `high` or `medium` match: added as `LISTING_OF`
- weak proximity-only candidate: kept in the unified CSV for audit purposes, but not asserted in the graph

This keeps the KG usable without overstating uncertain matches.

## Pipeline

```text
Inside Airbnb CSV      -> download_airbnb.py
OSM Overpass API       -> collect_osm.py
Wikidata SPARQL        -> collect_wikidata.py
data.gv.at WFS         -> collect_datagv.py
                           |
                           v
                    resolve_entities.py
                    - merge establishments
                    - classify operator evidence
                    - separate strong listing links from weak candidates
                           |
                           v
                    build_graph.py
                    - Neo4j graph
                    - RDF Turtle export
                           |
                           +-> audit_quality.py
                           +-> validate_graph.py
                           +-> materialize_rules.py
                           +-> export_triples.py
                           +-> train_embeddings.py
                           +-> score_candidates.py
                           +-> write_financial_comparison.py
                           +-> version_snapshot.py
                           +-> diff_snapshots.py
```

## Repository Structure

```text
knowledge-graph-hotel/
  data/                                raw and processed datasets
  graph/                               generated RDF export
  ontology/
    accommodation_operator.owl         ontology
    accommodation_operator_shapes.ttl  SHACL shapes
  reports/
    data_quality_report.md             generated quality report
    shacl_validation_report.txt        generated SHACL validation output
  src/
    collect_datagv.py
    collect_osm.py
    collect_wikidata.py
    download_airbnb.py
    resolve_entities.py
    build_graph.py
    audit_quality.py
    validate_graph.py
    materialize_rules.py
    export_triples.py
    train_embeddings.py
    score_candidates.py
    version_snapshot.py
    diff_snapshots.py
    write_financial_comparison.py
    run_pipeline.py
    rules.yml
    queries.cypher
  webapp/
    app.py
    query_templates.py
    frontend/
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Configure Neo4j via environment variables if needed:

- `NEO4J_URI`
- `NEO4J_USER`
- `NEO4J_PASSWORD`

## Running

```bash
# Full pipeline
python src/run_pipeline.py

# Skip Neo4j and only build RDF, reports, and validation outputs
python src/run_pipeline.py --skip-neo4j

# Faster rerun without embeddings
python src/run_pipeline.py --skip-airbnb --skip-embeddings

# Faster rerun without snapshots
python src/run_pipeline.py --skip-airbnb --skip-snapshots

# Individual steps
python src/resolve_entities.py
python src/build_graph.py
python src/audit_quality.py
python src/validate_graph.py
python src/materialize_rules.py
python src/export_triples.py
python src/train_embeddings.py
python src/score_candidates.py
python src/version_snapshot.py
python src/diff_snapshots.py
```

## Outputs

- RDF export (asserted): `graph/vienna_accommodation_operator_kg.ttl`
- RDF export (rule-inferred, kept separate): `graph/inferred_facts.ttl`
- Ontology: `ontology/accommodation_operator.owl`
- SHACL shapes: `ontology/accommodation_operator_shapes.ttl`
- Quality report: `reports/data_quality_report.md`
- SHACL validation report: `reports/shacl_validation_report.txt`
- Rule inference report: `reports/rule_inference_report.md`
- Embedding report: `reports/embedding_report.md`
- Embedding worked examples (5 + TP + FP): `reports/embedding_examples.md`
- Candidate ranking: `reports/candidate_scores.csv`
- Evolution report: `reports/evolution_report.md`
- Financial KG comparison (LO10): `reports/financial_kg_comparison.md`
- Data model comparison (LO4): `reports/data_model_comparison.md`
- Scalable reasoning notes (LO6): `reports/scalable_reasoning.md`
- ML / logic interaction (LO12): `reports/ml_logic_interaction.md`

## Dashboard

Run:

```bash
python webapp/app.py
```

The dashboard provides:

- operator exploration
- map view
- top operators and chain analysis
- district analysis
- quality and validation summary panel
- reasoning lab with inferred facts and embedding suggestions
- evolution tab with snapshot diffs
- natural-language query assistant
- evidence panels for operators and weak candidate links

## Scope Boundaries

- Out of scope: legal ownership via Grundbuch or paid Firmenbuch lookups
- Out of scope: Booking.com integration without a public data source
- In scope: operator relationships, provenance, validation, and cautious entity resolution
