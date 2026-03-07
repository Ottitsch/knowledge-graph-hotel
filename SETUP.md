# Setup

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

## 4. Run the pipeline
```bash
python src/run_pipeline.py
# skip Neo4j: python src/run_pipeline.py --skip-neo4j
# skip Airbnb download: python src/run_pipeline.py --skip-airbnb
```

## 5. Explore results
- Neo4j Browser: http://localhost:7474
- Cypher queries: `src/queries.cypher`
- RDF output: `graph/vienna_hotels.ttl`

## 6. Run the webapp (optional)
```bash
python webapp/app.py
```
