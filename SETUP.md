# Setup — Vienna Accommodation Operator KG Pipeline

## 1. Install dependencies
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Configure environment
```bash
cp .env.example .env
# edit .env with your Neo4j credentials
```

## 3. Start Neo4j
Start a local Neo4j instance (default: `bolt://localhost:7687`).
The graph can be built without Neo4j using `--skip-neo4j` (produces RDF Turtle only).

## 4. Run the pipeline
```bash
python src/run_pipeline.py
# skip Neo4j: python src/run_pipeline.py --skip-neo4j
# skip Airbnb download: python src/run_pipeline.py --skip-airbnb
```

Core pipeline steps:
1. `collect_datagv.py` — official Vienna accommodation registry
2. `collect_osm.py` — OpenStreetMap accommodation POIs
3. `collect_wikidata.py` — Wikidata operator/chain enrichment
4. `download_airbnb.py` — Inside Airbnb listings (listing-level)
5. `resolve_entities.py` — entity resolution with granularity and provenance
6. `build_graph.py` — Neo4j + RDF Turtle

Optional scripts (not in default pipeline):
- `src/optional_collect_firmenbuch.py` — future work, no live API available

## 5. Explore results
- Neo4j Browser: http://localhost:7474
- Cypher queries: `src/queries.cypher`
- RDF output: `graph/vienna_accommodation_operator_kg.ttl`
- Ontology: `ontology/accommodation_operator.owl`

## 6. Build the frontend
```bash
cd webapp/frontend
npm install
npm run build
cd ../..
```

## 7. Run the webapp
```bash
python webapp/app.py
```
Open http://localhost:5000 in your browser.
