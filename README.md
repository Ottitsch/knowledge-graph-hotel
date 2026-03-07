# Vienna Hotel Ownership Knowledge Graph

A knowledge graph answering **"who owns/operates which hotels and apartments listed on booking.com in Vienna?"** using only free, public data sources.

## Architecture

```
knowledge-graph-hotel/
  data/                         # raw + processed datasets (git-ignored)
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
    vienna_hotels.ttl           # RDF Turtle export (generated)
  requirements.txt
  .env.example
```

## Data Sources

| Source | What it provides | Free? |
|--------|-----------------|-------|
| [data.gv.at](https://www.data.gv.at/katalog/dataset/hotels-und-unterkunfte-in-wien) | Official Vienna accommodation registry (name, address, category, district) | Yes |
| [OSM Overpass API](https://overpass-api.de/) | Hotel/apartment POIs with operator, brand, stars tags | Yes |
| [Wikidata SPARQL](https://query.wikidata.org/) | Notable hotels with ownership (P127), parent org (P749) | Yes |
| [Inside Airbnb](https://insideairbnb.com/vienna/) | ~10k Vienna listings with host name, host_id, listing count | Yes |
| [Austrian Firmenbuch](https://api.firmenbuch.at/) | Legal company lookup by name → registration number, legal form | Free tier |

**Not included (requires payment):** Austrian Grundbuch (land registry) individual lookups (~€18/property).

## Knowledge Graph Schema

**Node types:** `Property`, `Operator`, `OwnerCompany`, `HotelChain`, `District`, `Platform`

**Relationships:**
- `(Property)-[:LISTED_ON]->(Platform)`
- `(Property)-[:OPERATED_BY]->(Operator)`
- `(Operator)-[:SUBSIDIARY_OF]->(HotelChain)`
- `(OwnerCompany)-[:OWNS]->(HotelChain)`
- `(Property)-[:LOCATED_IN]->(District)`
- `(Operator)-[:REGISTERED_AS]->(OwnerCompany)`

## Setup

```bash
pip install -r requirements.txt

# Configure Neo4j connection
cp .env.example .env
# Edit .env with your Neo4j credentials
```

Install Neo4j Community Edition: https://neo4j.com/download/

## Running the Pipeline

```bash
# Full pipeline (all steps)
python src/run_pipeline.py

# Skip Neo4j (still produces RDF Turtle in graph/)
python src/run_pipeline.py --skip-neo4j

# Skip Airbnb download (if already downloaded)
python src/run_pipeline.py --skip-airbnb

# Run individual steps
python src/collect_datagv.py
python src/collect_osm.py
python src/collect_wikidata.py
python src/download_airbnb.py        # or manually: see insideairbnb.com/vienna/
python src/resolve_entities.py
python src/collect_firmenbuch.py
python src/build_graph.py
```

## Querying the Graph

Open Neo4j Browser at **http://localhost:7474**, then use queries from `src/queries.cypher`:

```cypher
-- Top operators by property count
MATCH (p:Property)-[:OPERATED_BY]->(o:Operator)
RETURN o.name, count(p) AS properties ORDER BY properties DESC LIMIT 20;

-- Which chains dominate Vienna?
MATCH (p:Property)-[:OPERATED_BY]->(o:Operator)-[:SUBSIDIARY_OF]->(c:HotelChain)
RETURN c.name, count(p) AS properties ORDER BY properties DESC;

-- District breakdown
MATCH (p:Property)-[:LOCATED_IN]->(d:District)
RETURN d.name, count(p) AS properties ORDER BY properties DESC;
```

The RDF Turtle file (`graph/vienna_hotels.ttl`) can be loaded into any triple store or opened in [Protégé](https://protege.stanford.edu/).

The OWL ontology (`ontology/hotel_ownership.owl`) is loadable in Protégé for visualization and reasoning.

## Key Limitations

- **Booking.com operator identity** is inferred (not from the booking.com API directly)
- **Legal property ownership** (Grundbuch) not included — requires paid lookups
- **Inside Airbnb** is Airbnb-primary; many hosts also list on booking.com
- **Wikidata** only covers notable/famous hotels (not the long tail)
- **Firmenbuch API** coverage depends on free-tier rate limits
