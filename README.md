# Vienna Accommodation Knowledge Graph

A knowledge graph of the Vienna short-term rental and hotel market, built from free, public data sources. The graph connects accommodation listings to their operators, enabling analysis of **host concentration, hotel chain presence, and geographic distribution** across Vienna's 23 districts.

## What's in the graph

| Dataset | Records | What it provides |
|---|---|---|
| [Inside Airbnb](https://insideairbnb.com/vienna/) | ~31,300 listings | Host identity, listing counts per host, property type, coordinates |
| [OSM Overpass API](https://overpass-api.de/) | 650 POIs | Hotel/apartment locations with operator, brand, and star-rating tags |
| [Wikidata SPARQL](https://query.wikidata.org/) | 333 hotels | Notable hotels with operator, brand, and (sparse) ownership links |
| [data.gv.at](https://www.data.gv.at/katalog/dataset/hotels-und-unterkunfte-in-wien) | 394 listings | Official Vienna accommodation registry (address, category, district) |

**Unified graph:** 14,238 property nodes (13,494 Airbnb + 501 OSM + 243 Wikidata), stored in Neo4j and exported as RDF Turtle.

### Key findings the graph can answer

- **Host concentration:** 168 Airbnb hosts control more than 10 listings each; the top host has 396 listings
- **Corporate vs. individual operators:** operators with >3 listings account for the majority of Airbnb supply in central districts
- **Hotel chains:** ~102 properties linked to named chains (Hilton, Marriott, etc.) via OSM/Wikidata
- **District breakdown:** District 1 (Innere Stadt) has the densest official accommodation count (80); Airbnb density peaks in districts 1–9

### What's not in the graph

- **Legal property ownership** — Austrian Grundbuch lookups cost ~€18/property; not included
- **Booking.com listings** — no public API; operator identity for booking.com properties is not available
- **Firmenbuch company matches** — the free-tier API returned no usable matches for queried operator names
- **Wikidata ownership** — only 7 of 333 Wikidata hotels have an `owner` triple; coverage is very sparse

## Architecture

```
knowledge-graph-hotel/
  data/                         # raw + processed datasets (git-ignored)
    inside_airbnb_listings.csv  # ~31k Airbnb listings
    osm_hotels.json             # 650 OSM POIs
    wikidata_hotels.json        # 333 Wikidata hotels
    datagv_accommodations.csv   # 394 official registrations
    firmenbuch_companies.json   # 2,804 company lookups (0 matched)
    properties_unified.csv      # 14,238 merged records
  src/
    collect_datagv.py           # data.gv.at WFS → accommodations CSV
    collect_osm.py              # OSM Overpass API → hotels JSON
    collect_wikidata.py         # Wikidata SPARQL → hotel ownership JSON
    download_airbnb.py          # Inside Airbnb Vienna CSV download
    collect_firmenbuch.py       # Austrian Firmenbuch company lookups
    resolve_entities.py         # entity resolution → properties_unified.csv
    build_graph.py              # Neo4j + RDF Turtle graph construction
    run_pipeline.py             # master pipeline runner
    queries.cypher              # example Cypher queries for Neo4j Browser
  ontology/
    hotel_ownership.owl         # OWL ontology definition
  graph/
    vienna_hotels.ttl           # RDF Turtle export (8.8 MB, generated)
  webapp/
    app.py                      # Flask API backend (Neo4j queries)
    frontend/                   # Vite/React dashboard
```

## Graph Schema

**Node types:** `Property`, `Operator`, `HotelChain`, `District`, `Platform`

**Relationships:**
- `(Property)-[:OPERATED_BY]->(Operator)`
- `(Operator)-[:SUBSIDIARY_OF]->(HotelChain)`
- `(Property)-[:LOCATED_IN]->(District)`
- `(Property)-[:LISTED_ON]->(Platform)`

The `Operator` node represents whoever manages/lists the property — for Airbnb this is the host, for traditional hotels it is the named operator from OSM or Wikidata.

## Setup

```bash
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

# Individual steps
python src/collect_datagv.py
python src/collect_osm.py
python src/collect_wikidata.py
python src/download_airbnb.py    # or download manually from insideairbnb.com/vienna/
python src/resolve_entities.py
python src/collect_firmenbuch.py
python src/build_graph.py
```

## Querying the Graph

Open Neo4j Browser at **http://localhost:7474**, then use queries from `src/queries.cypher`:

```cypher
-- Hosts/operators by property count (identifies large-scale operators)
MATCH (p:Property)-[:OPERATED_BY]->(o:Operator)
RETURN o.name, count(p) AS listings ORDER BY listings DESC LIMIT 20;

-- Corporate vs. individual operators per district
MATCH (p:Property)-[:OPERATED_BY]->(o:Operator)-[:LOCATED_IN]->(d:District)
WITH d, o, count(p) AS n
RETURN d.name,
  sum(CASE WHEN n > 3 THEN n ELSE 0 END) AS corporate,
  sum(CASE WHEN n <= 3 THEN n ELSE 0 END) AS individual
ORDER BY (corporate + individual) DESC;

-- Hotel chains present in Vienna
MATCH (p:Property)-[:OPERATED_BY]->(o:Operator)-[:SUBSIDIARY_OF]->(c:HotelChain)
RETURN c.name, count(p) AS properties ORDER BY properties DESC;
```

The RDF Turtle file (`graph/vienna_hotels.ttl`) can be loaded into any triple store or opened in [Protégé](https://protege.stanford.edu/).

## Web Dashboard

```bash
cd webapp
python app.py          # Flask backend on :5000

cd frontend
npm install && npm run dev   # Vite dev server
```

The dashboard provides a map view, operator network graph, district breakdown, and corporate-vs-individual analysis.
