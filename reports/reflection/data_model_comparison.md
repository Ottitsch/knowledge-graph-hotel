# Data Model Comparison

Portfolio reference: this document supports **LO4 - compare different Knowledge Graph data models from the database, semantic web, machine learning and data science communities**.

## What this project uses

The Vienna Accommodation Operator KG stores the same facts in three representations at the same time:

| Representation | Where | Used for |
|---|---|---|
| Labeled property graph (Neo4j) | `build_graph.py` → Neo4j | Interactive Cypher queries, dashboard backend |
| RDF / Turtle (semantic web) | `graph/vienna_accommodation_operator_kg.ttl` (~17 MB) | SHACL validation, portable export, ontology alignment |
| Vector embeddings (TransE) | `models/embeddings/transe_embeddings.npz` | Similarity ranking, weak candidate scoring |

A fourth representation - the **tabular CSV** `data/properties_unified.csv` - is the source of truth that all three are derived from. It is itself a data-science-community representation (rows + provenance columns), and is what `materialize_rules.py` reasons over directly.

## Side-by-side comparison

### 1. Property graph vs RDF on the same fact

The single fact "Airbnb listing X is operated by host Y" is encoded as:

- **Neo4j (property graph):**
  ```cypher
  (:AccommodationUnit {canonical_id:"d4736edc-906d-4b36-b803-6f3957d7ae6c",
                       granularity:"listing",
                       operator_identity_confidence:"high"})
    -[:OPERATED_BY]->
  (:Operator {operator_id:"airbnb:385064248", name:"Blueground"})
  ```
  Properties live on nodes and edges. There is no schema enforcement; the graph is whatever you put in it.

- **RDF (semantic web):**
  ```turtle
  vaok:unit/d4736edc-906d-4b36-b803-6f3957d7ae6c
      a vaok:AccommodationUnit ;
      vaok:granularity "listing" ;
      vaok:operatorIdentityConfidence "high" ;
      vaok:operatedBy vaok:operator/airbnb_385064248 .

  vaok:operator/airbnb_385064248
      a vaok:Operator ;
      rdfs:label "Blueground" .
  ```
  Every property is a separate triple. Schema and constraints are external (OWL, SHACL). Identifiers are global IRIs, which makes cross-dataset linking explicit.

### 2. Both vs vector embedding of the same operator

The same operator is also a 48-dim vector at index `entity_to_id["operator/airbnb_385064248"]` in `transe_embeddings.npz`. The vector has no human-readable structure - it only supports geometric operations (cosine similarity, vector arithmetic). It cannot be queried by predicate name, but it can rank "which other operators are most like Blueground" in a way the symbolic graph cannot.

## Why all three coexist here

| Question I want to answer | Best representation | Why |
|---|---|---|
| "Which units does operator X run?" | Property graph (Cypher) | Direct path query, fast in Neo4j |
| "Does the graph respect my constraints?" | RDF + SHACL | SHACL was designed for this; no equivalent in plain Cypher |
| "Which operator looks most like operator X across all relations?" | Embedding | Symbolic graph has no notion of "looks like" without hand-crafted similarity |
| "Publish the graph for someone else to load" | RDF Turtle | Stable, standard, parseable by any SPARQL endpoint |

## Trade-offs I hit in this project

- **Property graph is fastest for the operator question.** The main onepager question ("which units operated by the same person?") is a 1-hop Cypher query. In RDF the same answer needs SPARQL + sort + group, which is slower over 15k units.
- **RDF was the only realistic choice for validation.** SHACL gave me 6 shapes in `accommodation_operator_shapes.ttl` with no extra code. Doing the same as ad-hoc Cypher constraints would have been brittle.
- **Embeddings filled a real gap.** Without them, weak listing-establishment candidates only had a distance score (`candidate_establishment_distance_m`). The TransE score (`embedding_score` column in `candidate_scores.csv`) added a structural signal that the symbolic graph cannot produce.
- **Three representations cost duplication.** Adding a new property currently means touching `build_graph.py` (both Neo4j and RDF code paths) and re-exporting triples for embedding training. A single canonical pipeline (e.g. R2RML from the CSV) would be cleaner but was out of scope.

## What I would do differently with more time

- Treat `properties_unified.csv` as the single source of truth and generate Neo4j Cypher loads, RDF, and embedding triples from one R2RML-style mapping. That would remove the duplicated property-emission code in `build_graph.py`.
- Use a graph store that speaks both Cypher *and* SPARQL (e.g. ontotext GraphDB with Cypher plugin, or Memgraph) so the dashboard does not need two query languages.
- Try a richer embedding (RotatE or ComplEx) so symmetry/inverse relations between operator and unit are modeled more faithfully than TransE allows.
