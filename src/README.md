# `src/` layout

The pipeline is grouped into five subpackages by stage. Each script is runnable directly (e.g. `python src/collect/collect_osm.py`); they all add `src/` to `sys.path` so the shared utilities (`common_paths.py`, `kg_utils.py`) remain importable.

| Folder | Stage | Files |
|---|---|---|
| `collect/` | Layer 1 — acquisition | `download_airbnb.py`, `collect_osm.py`, `collect_wikidata.py`, `collect_datagv.py`, `optional_collect_firmenbuch.py` |
| `construct/` | Layer 2 + 3 — resolution + KG building | `resolve_entities.py`, `build_graph.py`, `export_triples.py`, `materialize_rules.py` |
| `learn/` | Layer 3 — embeddings (LO1) | `train_embeddings.py`, `score_candidates.py` |
| `audit/` | cross-cutting — quality + reflection writer | `audit_quality.py`, `validate_graph.py`, `write_financial_comparison.py` |
| `evolve/` | cross-cutting — LO8 snapshots | `version_snapshot.py`, `diff_snapshots.py` |
| (root) | shared / orchestration | `run_pipeline.py`, `common_paths.py`, `kg_utils.py`, `rules.yml`, `queries.cypher`, `queries.sparql` |

To run everything: `python src/run_pipeline.py` (add `--skip-neo4j` if no Neo4j instance is configured).
