# Vienna Accommodation Operator Knowledge Graph

**Main question:** Which accommodation units in Vienna are operated by the same person or organization, and what other units do they operate?

This knowledge graph combines public data sources to study operator relationships in Vienna's accommodation market. It focuses on identifying which units share an operator, not on legal property ownership.

## What's in the graph

| Dataset | Records | Granularity | What it provides |
|---|---|---|---|
| [Inside Airbnb](https://insideairbnb.com/vienna/) | ~31,300 listings | listing | Host identity, listing count per host, property type, coordinates |
| [OSM Overpass API](https://overpass-api.de/) | ~650 POIs | establishment | Hotel/apartment locations with operator, brand, and address tags |
| [Wikidata SPARQL](https://query.wikidata.org/) | ~333 hotels | establishment | Notable hotels with operator, parent organization, brand links |
| [data.gv.at](https://www.data.gv.at/katalog/dataset/hotels-und-unterkunfte-in-wien) | ~394 registrations | establishment | Official Vienna accommodation registry (name, category, address, district) |

**Important:** Airbnb contributes listing-level data (one record per Airbnb listing). OSM, Wikidata, and data.gv.at contribute establishment-level data (one record per physical location). The graph makes this distinction explicit via a `granularity` field.

### Key questions the graph answers

- Which operators control the most accommodation units?
- Which units are co-operated by the same host or organization?
- How concentrated is operator supply in each district?
- Which establishments are affiliated with named hotel chains?
- Which units are confirmed by multiple independent sources?

## Graph Schema

**Node types:** `AccommodationUnit`, `Operator`, `HotelChain`, `District`, `Source`

**Relationships:**
- `(AccommodationUnit)-[:OPERATED_BY]->(Operator)`
- `(AccommodationUnit)-[:LOCATED_IN]->(District)`
- `(AccommodationUnit)-[:OBSERVED_IN]->(Source)`
- `(Operator)-[:AFFILIATED_WITH]->(HotelChain)`

**Key properties on `AccommodationUnit`:** `name`, `address`, `lat`, `lon`, `unit_type`, `granularity`, `source_names`, `source_record_ids`, `merge_confidence`

**Key properties on `Operator`:** `name`, `airbnb_host_id`, `observed_unit_count`

## Data Provenance and Confidence

Each `AccommodationUnit` node carries explicit provenance metadata so you can trace every record back to its origin:

| Property | Description |
|---|---|
| `granularity` | `listing` (Airbnb, one record per listing) or `establishment` (OSM/Wikidata/data.gv.at, one record per physical location) |
| `source_names` | Comma-separated list of contributing sources, e.g. `OpenStreetMap,Wikidata` |
| `source_record_ids` | Original IDs from each contributing source |
| `merge_confidence` | `high` (strong name+coordinate or website+coordinate match) · `medium` (name+address match) · `single` (only one source) |

**Merge strategy:** Establishment-level records (OSM, Wikidata, data.gv.at) are matched in two stages using a Union-Find algorithm:
1. Same normalized name + coordinates within ~100 m → `high` confidence merge
2. Same website domain + coordinates within ~200 m → `high` confidence merge

Airbnb listings are never merged with establishment records — they are always `granularity=listing` with `merge_confidence=single`.

Multi-source records (e.g. a hotel confirmed by both OSM and Wikidata) have `merge_confidence=high` and list both sources in `source_names`.

## Pipeline

```
Raw sources                  Collection scripts        Intermediate data
───────────────────────────────────────────────────────────────────────────
Inside Airbnb (CSV)    ──►  download_airbnb.py   ──►  inside_airbnb_listings.csv
OSM Overpass API       ──►  collect_osm.py        ──►  osm_hotels.json
Wikidata SPARQL        ──►  collect_wikidata.py   ──►  wikidata_hotels.json
data.gv.at WFS         ──►  collect_datagv.py     ──►  datagv_accommodations.csv
                                   │
                                   ▼
                          resolve_entities.py
                          (Union-Find merge,
                           granularity labels,
                           provenance tracking)
                                   │
                                   ▼
                          properties_unified.csv
                                   │
                          ┌────────┴────────┐
                          ▼                 ▼
                     build_graph.py    build_graph.py
                          │                 │
                          ▼                 ▼
                    Neo4j graph      RDF Turtle (.ttl)
                   (bolt://7687)    (graph/*.ttl)
                          │
                          ▼
                     webapp/app.py
                    (Flask API :5000)
                          │
                          ▼
                   React Dashboard
```

## Architecture

```
knowledge-graph-hotel/
  data/                                   # raw + processed datasets (git-ignored)
    inside_airbnb_listings.csv            # ~31k Airbnb listings
    osm_hotels.json                       # OSM accommodation POIs
    wikidata_hotels.json                  # Wikidata hotels with operator/chain info
    datagv_accommodations.csv             # Official Vienna registry
    properties_unified.csv               # Merged records with provenance
  src/
    collect_datagv.py                     # data.gv.at WFS → CSV
    collect_osm.py                        # OSM Overpass API → JSON
    collect_wikidata.py                   # Wikidata SPARQL → JSON
    download_airbnb.py                    # Inside Airbnb Vienna CSV download
    resolve_entities.py                   # Entity resolution → properties_unified.csv
    build_graph.py                        # Neo4j + RDF Turtle graph construction
    run_pipeline.py                       # Master pipeline runner
    queries.cypher                        # Example Cypher queries for Neo4j Browser
    optional_collect_firmenbuch.py        # Future work: Austrian registry enrichment
  ontology/
    accommodation_operator.owl            # OWL ontology definition
  graph/
    vienna_accommodation_operator_kg.ttl  # RDF Turtle export (generated)
  webapp/
    app.py                                # Flask API backend (Neo4j queries)
    frontend/                             # Vite/React dashboard
```

## Out of scope

- **Legal property ownership** — Austrian Grundbuch/Firmenbuch lookups are paid and not freely available at this scale
- **Booking.com listings** — no public API; the current dataset does not contain booking.com data
- **Financial or investment analysis** — this is an operator identity and co-operation graph, not a financial KG

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your Neo4j credentials
```

Install Neo4j Community Edition and start it before running the pipeline.

## Running the Pipeline

```bash
# Full pipeline
python src/run_pipeline.py

# Skip Neo4j (produces RDF Turtle only)
python src/run_pipeline.py --skip-neo4j

# Skip Airbnb download (if already downloaded)
python src/run_pipeline.py --skip-airbnb

# Individual steps
python src/collect_datagv.py
python src/collect_osm.py
python src/collect_wikidata.py
python src/download_airbnb.py
python src/resolve_entities.py
python src/build_graph.py
```

## Querying the Graph

Open Neo4j Browser at **http://localhost:7474**, then use queries from `src/queries.cypher`:

```cypher
-- Top operators by accommodation unit count
MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)
RETURN o.name AS operator, count(u) AS unit_count
ORDER BY unit_count DESC LIMIT 20;

-- All units operated by the same operator
MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator {name: 'Example Host'})
RETURN u.name, u.granularity, u.district, u.unit_type;

-- Professional operator candidates (more than 3 units)
MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)
WITH o, count(u) AS cnt WHERE cnt > 3
RETURN o.name AS operator, cnt ORDER BY cnt DESC;

-- Chain-affiliated establishments by district
MATCH (u:AccommodationUnit)-[:LOCATED_IN]->(d:District),
      (u)-[:OPERATED_BY]->(o:Operator)-[:AFFILIATED_WITH]->(c:HotelChain)
RETURN d.name AS district, c.name AS chain, count(u) AS units
ORDER BY district, units DESC;
```

The RDF Turtle file (`graph/vienna_accommodation_operator_kg.ttl`) can be loaded into any triple store or opened in [Protégé](https://protege.stanford.edu/). The ontology is at `ontology/accommodation_operator.owl`.

## Web Dashboard

```bash
cd webapp
python app.py          # Flask backend on :5000

cd frontend
npm install && npm run build
```

Open **http://localhost:5000** in your browser. The dashboard provides:
- Operator network graph (force-directed, click to explore)
- Map view with operator network highlighting
- Top operators, chain affiliations, district breakdown
- Professional vs smaller operator distribution
