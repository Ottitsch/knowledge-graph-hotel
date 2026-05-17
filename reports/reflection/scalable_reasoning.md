# Scalable Reasoning

Portfolio reference: this document supports **LO6 — describe and apply scalable reasoning methods in Knowledge Graphs**, specifically as it applies to this project's rule engine and embedding pipeline.

## Reasoning components in this project

| Component | What it does | Implementation |
|---|---|---|
| Rule materializer | Applies 4 forward-chaining rules to derive new facts | `src/construct/materialize_rules.py` over the unified CSV |
| SHACL validator | Checks 6 shapes over the RDF graph | `src/audit/validate_graph.py` |
| TransE link scorer | Embedding-based ranking of weak candidate links | `src/learn/score_candidates.py` |
| Inferred-fact RDF emitter | Writes derived edges as a separate Turtle file | `src/construct/materialize_rules.py` (writes `graph/inferred_facts.ttl`) |

## Current scale

From the latest `data_quality_report.md` and `embedding_report.md`:

- 15,011 unified rows (14,123 listings + 888 establishments)
- 22,382 RDF entities and ~83k labeled triples
- 7 relation types in the embedding model

End-to-end pipeline runtime on a developer laptop is bounded by the TransE training step, not the rule engine. The rule materializer reasons over a single in-memory pandas DataFrame and finishes in under a second; SHACL validation over ~17 MB of Turtle completes in a few seconds with `pyshacl`.

## How each component scales

### Forward-chaining rule engine

The rules in `src/rules.yml` are pure aggregations over the unified table:

- `professional_operator`: group-by operator, count units, threshold.
- `cross_district_operator`: group-by operator, count distinct districts, threshold.
- `multi_source_confirmed_establishment`: filter rows where `merge_confidence = strong`.
- `likely_chain_affiliated_operator`: filter rows where `hotel_chain` is non-empty.
- `shared_chain_corporate_group` (added in this iteration): pairwise edges between operators sharing a chain.
- `operator_corporate_network` (added in this iteration): connected components over `corporateSibling` edges — this is the recursive rule.

Pure-aggregation rules scale linearly in the number of rows (`O(n)`) with a constant factor set by pandas group-by performance. The recursive rule is bounded by the size of the largest connected component in the operator-chain graph; in this dataset chains are sparse (around 30 distinct chains, most with one operator), so the union-find computation is essentially linear in the number of chain-operator memberships.

### SHACL validation

SHACL validation is shape-by-shape and node-by-node. Each shape's cost is `O(targets × constraints)`. For this graph the dominant shape is `AccommodationUnitShape`, evaluated over ~15k unit nodes with ~6 property constraints, so ~90k constraint checks. `pyshacl` handles this in seconds without inference enabled. If we turned on RDFS or OWL-RL inference closure, cost would grow with the size of the inferred closure — for this dataset that closure is small because we don't use deep hierarchies.

### TransE training and scoring

Training is the most expensive step. Cost per epoch is `O(|triples| × embedding_dim)` for the standard PyKEEN training loop. With 83k triples × 48 dims × 6 epochs the model fits on CPU in a few minutes. Evaluation is `O(|test_triples| × |entities|)` because it ranks all entities per test triple — the dominant term when entity count grows.

Candidate scoring (`score_candidates.py`) is `O(|candidates| × embedding_dim)` for the listing-establishment scoring, plus `O(|top_operators|² × embedding_dim)` for operator-operator cosine similarity (currently capped at 120 operators). That cap is the single most important scalability lever: lifting it to all 5k+ operators is `~40×` more pairs.

## Scaling levers if the dataset grew

| If we scaled up... | The bottleneck would be... | Mitigation |
|---|---|---|
| 10× more listings | Rule engine still fine; embedding training time grows linearly | Move TransE to GPU, batch the operator-similarity step |
| 10× more relations | TransE evaluation grows with entity count | Switch to filtered evaluation, or sample negatives |
| Adding deeper hierarchies (e.g. chain → parent group) | Recursive rule cost grows with component size | Replace union-find with a real graph store (Neo4j or RDF triple store with property paths) |
| Adding stricter SHACL constraints with sh:sparql | Validation runtime grows with constraint complexity | Run SHACL incrementally, only over changed nodes between snapshots |

## Veracity and variety

- **Veracity:** the quality report tracks `operator_identity_confidence` and `merge_confidence`. The recursive corporate-network rule only follows edges between operators that share a chain affiliation backed by OSM or Wikidata, so noisy Airbnb-only host names cannot dominate clusters.
- **Variety:** because the rules consume the unified CSV (not raw source data), adding a new source (e.g. Booking.com if it ever became available) does not change the rule code. The cost is only in entity resolution upstream.

## What I would do differently

- Push the rule engine into the triple store (SPARQL `INSERT WHERE`) so reasoning is colocated with the data and incremental updates become natural.
- Track per-rule wall-clock times so the report can show actual scaling behavior over snapshots, not just complexity arguments.
- Run TransE eval on a held-out evaluation set restricted to operator-relevant relations, so the headline metric matches the service the KG provides.
