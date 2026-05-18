This Project is being hosted on an EC2 Instance and is running inside of a docker container  
(the recommended path for reproducability)  

http://13.53.250.7

In case I ran out of Money or Shut OFF the Instance here is a Video:

https://www.youtube.com/watch?v=IErfiRM_OyE

# Vienna Accommodation Operator Knowledge Graph

**Main question:** Which accommodation units in Vienna are operated by the same person or organization, and what other units do they operate?

This project combines public accommodation data for Vienna into a knowledge graph focused on operator relationships, provenance, and data quality. The project is intentionally **not** a legal ownership graph. Its strongest contribution is an Airbnb-centered KG with cautious enrichment from OpenStreetMap, Wikidata, and the official Vienna accommodation registry.

The current application also includes:

- rule-based inferred facts (including a recursive corporate-network rule)
- TransE knowledge graph embeddings
- embedding-ranked candidate links
- snapshot versioning and evolution reports
- a safe natural-language query assistant
- evidence panels for operators and candidate links

For the LO → evidence mapping used in the course portfolio, see [`PORTFOLIO_GUIDE.md`](PORTFOLIO_GUIDE.md).
For the system architecture (LO5) see [`docs/architecture.md`](docs/architecture.md) and the rendered diagram in [`docs/architecture.png`](docs/architecture.png).

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

The rule engine in `src/construct/materialize_rules.py` derives additional edges from the asserted graph and writes them to `graph/inferred_facts.ttl`. They are kept apart so asserted and inferred facts stay distinguishable:

- `(Operator)-[:corporateSibling]->(Operator)` - operators sharing a hotel chain (`shared_chain_corporate_group` rule).
- `(Operator)-[:memberOf]->(OperatorNetwork)` - connected components over `corporateSibling`, the recursive `operator_corporate_network` rule.

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
Inside Airbnb CSV      -> src/collect/download_airbnb.py
OSM Overpass API       -> src/collect/collect_osm.py
Wikidata SPARQL        -> src/collect/collect_wikidata.py
data.gv.at WFS         -> src/collect/collect_datagv.py
                            |
                            v
                     src/construct/resolve_entities.py
                     - merge establishments
                     - classify operator evidence
                     - separate strong listing links from weak candidates
                            |
                            v
                     src/construct/build_graph.py
                     - Neo4j graph
                     - RDF Turtle export
                            |
                            +-> src/audit/audit_quality.py
                            +-> src/audit/validate_graph.py
                            +-> src/construct/materialize_rules.py
                            +-> src/construct/export_triples.py
                            +-> src/learn/train_embeddings.py
                            +-> src/learn/score_candidates.py
                            +-> src/audit/write_financial_comparison.py
                            +-> src/evolve/version_snapshot.py
                            +-> src/evolve/diff_snapshots.py
```

## Repository Structure

```text
knowledge-graph-hotel/
  PORTFOLIO_GUIDE.md                   LO -> evidence mapping for the course portfolio
  README.md                            this file
  SETUP.md                             step-by-step setup notes
  requirements.txt                     python dependencies
  .env.example                         template for neo4j credentials

  docs/                                LO5 architecture
    architecture.md                    written architecture + design rationale
    architecture.png                   rendered diagram
    architecture.dot                   graphviz source
    render_architecture.py             regenerator

  data/                                raw and unified datasets
    inside_airbnb_listings.csv         (downloadable; see src/collect/download_airbnb.py)
    osm_hotels.json
    wikidata_hotels.json
    datagv_accommodations.csv
    properties_unified.csv             unified source-of-truth table
    snapshots/                         timestamped pipeline outputs (LO8)

  graph/
    vienna_accommodation_operator_kg.ttl   asserted RDF graph (~17 MB)
    inferred_facts.ttl                     rule-derived RDF (kept separate)

  ontology/
    accommodation_operator.owl         OWL class hierarchy
    accommodation_operator_shapes.ttl  SHACL shapes

  models/
    embeddings/                        TransE artifacts (matrix + mappings)

  reports/                             grouped by topic - see reports/README.md
    quality/                           data_quality_report.md, shacl_validation_report.{txt,ttl}, quality_summary.json
    logic/                             rule_inference_*.{md,json}, rule_eval_corporate_sibling.{md,json}
    ml/                                embedding_*.{md,json}, candidate_scores.csv, operator_similarity.json
    evolution/                         evolution_*.{md,json}
    reflection/                        data_model_comparison.md, scalable_reasoning.md, ml_logic_interaction.md, financial_kg_comparison.md

  src/                                 grouped by pipeline stage - see src/README.md
    run_pipeline.py                    orchestrator
    common_paths.py  kg_utils.py       shared utilities
    rules.yml                          rule definitions
    queries.cypher  queries.sparql     example queries
    collect/                           download_airbnb · collect_{osm,wikidata,datagv} · optional_collect_firmenbuch
    construct/                         resolve_entities · build_graph · export_triples · materialize_rules
    learn/                             train_embeddings · score_candidates
    audit/                             audit_quality · validate_graph · write_financial_comparison
    evolve/                            version_snapshot · diff_snapshots

  webapp/
    app.py                  Flask backend
    query_templates.py      natural-language assistant query templates
    templates/              minimal server-rendered fallback
    frontend/               Vite/React/Tailwind dashboard
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
python src/construct/resolve_entities.py
python src/construct/build_graph.py
python src/audit/audit_quality.py
python src/audit/validate_graph.py
python src/construct/materialize_rules.py
python src/construct/export_triples.py
python src/learn/train_embeddings.py
python src/learn/score_candidates.py
python src/evolve/version_snapshot.py
python src/evolve/diff_snapshots.py
```

## Outputs

- RDF export (asserted): `graph/vienna_accommodation_operator_kg.ttl`
- RDF export (rule-inferred, kept separate): `graph/inferred_facts.ttl`
- Ontology: `ontology/accommodation_operator.owl`
- SHACL shapes: `ontology/accommodation_operator_shapes.ttl`
- Quality report: `reports/quality/data_quality_report.md`
- SHACL validation report: `reports/quality/shacl_validation_report.txt`
- Rule inference report: `reports/logic/rule_inference_report.md`
- Embedding report: `reports/ml/embedding_report.md`
- Embedding worked examples (5 + TP + FP): `reports/ml/embedding_examples.md`
- Candidate ranking: `reports/ml/candidate_scores.csv`
- Evolution report: `reports/evolution/evolution_report.md`
- Financial KG comparison (LO10): `reports/reflection/financial_kg_comparison.md`
- Data model comparison (LO4): `reports/reflection/data_model_comparison.md`
- Scalable reasoning notes (LO6): `reports/reflection/scalable_reasoning.md`
- ML / logic interaction (LO12): `reports/reflection/ml_logic_interaction.md`

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

## Docker Deployment

The repository ships a `Dockerfile` that builds the Vite/React frontend, starts Neo4j, loads the knowledge graph into Neo4j, and serves the Flask/Gunicorn dashboard from the same container.

```bash
docker build -t vienna-kg-dashboard .
docker run --rm -p 8000:8000 -p 7474:7474 -p 7687:7687 vienna-kg-dashboard
```

- Dashboard: http://localhost:8000
- Neo4j Browser: http://localhost:7474 (user `neo4j`, password `password`)

On startup, the container starts Neo4j, waits for Bolt, and initializes the graph from `data/properties_unified.csv` if the database is empty. Set `FORCE_NEO4J_REBUILD=true` to clear and rebuild on startup. See `SETUP.md` section 6 for the full list of supported environment variables.

## Querying the inferred graph

The inferred RDF is shipped as a separate file so asserted and inferred triples stay distinguishable. To run a SPARQL query that exploits the recursive `corporateSibling` closure (see `src/queries.sparql`), load both graphs:

```python
from rdflib import Graph
g = Graph()
g.parse("graph/vienna_accommodation_operator_kg.ttl", format="turtle")
g.parse("graph/inferred_facts.ttl", format="turtle")
# ~300k triples, then run any of the queries in src/queries.sparql
```

## Scope Boundaries

- Out of scope: legal ownership via Grundbuch or paid Firmenbuch lookups
- Out of scope: Booking.com integration without a public data source
- In scope: operator relationships, provenance, validation, and cautious entity resolution

## Stable links

### Endpoints actually hit by the collectors

The four collectors in `src/collect/` each hit one concrete endpoint. The URLs below are the ones the code actually requests, copied verbatim from the collector source:

1. **Inside Airbnb data download** (`collect/download_airbnb.py`): `http://data.insideairbnb.com/austria/vienna/vienna/{date}/data/listings.csv.gz` (the collector tries several recent snapshot dates).
2. **OpenStreetMap Overpass API** (`collect/collect_osm.py`): https://overpass-api.de/api/interpreter (POST with the Overpass query for Vienna accommodation POIs).
3. **Wikidata Query Service** (`collect/collect_wikidata.py`): https://query.wikidata.org/sparql (GET with the SPARQL query for Vienna hotels and their operator / parent-org / brand links).
4. **Stadt Wien WFS** (`collect/collect_datagv.py`): `https://data.wien.gv.at/daten/geo?service=WFS&typeName=ogdwien:UNTERKUNFTOGD` (GeoJSON output of the official Vienna accommodation registry).

### Attribution and library pages

Project / attribution pages for the source datasets (cited for licence and provenance, **not** hit by the collectors), and the two Python libraries that do the reasoning and ML work:

5. **Inside Airbnb project page**: https://insideairbnb.com/get-the-data/
6. **OpenStreetMap project** (CC-BY-SA): https://www.openstreetmap.org
7. **Wikidata project**: https://www.wikidata.org
8. **data.gv.at portal**: https://www.data.gv.at/
9. **pySHACL** (SHACL validation in `src/audit/validate_graph.py`): https://github.com/RDFLib/pySHACL
10. **PyKEEN** (TransE training in `src/learn/train_embeddings.py`): https://pykeen.github.io/

Architecture diagram source and renderer: see `docs/architecture.md`, `docs/architecture.dot`, `docs/architecture.png`.
