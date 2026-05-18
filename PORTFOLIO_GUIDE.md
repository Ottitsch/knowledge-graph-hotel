# Portfolio Guide

This guide maps the portfolio learning outcomes (LOs) declared in the project one-pager to concrete evidence in this repository. It exists so a reviewer can find every claim in one place.

## Focus LOs (planned demonstration "exceeded basic proficiency")

| LO | Description | Evidence |
|---|---|---|
| **LO5** | Design and implement architectures of a Knowledge Graph | `docs/architecture.md` + `docs/architecture.png` (rendered diagram) · `README.md` Pipeline section · `src/run_pipeline.py` · `src/construct/build_graph.py` (dual Neo4j + RDF emission) |
| **LO7** | Apply a system to create a Knowledge Graph | Everything under `src/collect/collect_*.py`, `src/construct/resolve_entities.py`, `src/construct/build_graph.py` · regenerable outputs in `data/`, `graph/`, `models/embeddings/`, `reports/` |
| **LO11** | Apply a system to provide services through a Knowledge Graph | `webapp/app.py` Flask backend · `webapp/templates/index.html` and `webapp/frontend/` dashboard · `src/queries.cypher` · natural-language assistant in `webapp/query_templates.py` |

## Basic-proficiency LOs

| LO | Description | Evidence |
|---|---|---|
| **LO1** | Understand and apply Knowledge Graph Embeddings | `src/learn/train_embeddings.py` (TransE, PyKEEN) · `src/learn/score_candidates.py` · `reports/ml/embedding_report.md` (metrics) · `reports/ml/embedding_examples.md` (5 representations + 1 TP + 1 FP) |
| **LO2** | Understand and apply logical knowledge in KGs | `ontology/accommodation_operator.owl` (OWL class hierarchy) · `ontology/accommodation_operator_shapes.ttl` (SHACL) · `src/rules.yml` (6 rules incl. recursive `operator_corporate_network`) · `src/construct/materialize_rules.py` (forward chaining + union-find transitive closure) · `graph/inferred_facts.ttl` (newly derived edges) · `reports/logic/rule_inference_report.md` (5 rules in formal form) · `reports/logic/rule_eval_corporate_sibling.md` (30-edge precision spot-check: strict 0.367 / loose 0.967) |
| **LO4** | Compare different KG data models | `reports/reflection/data_model_comparison.md` (property graph vs RDF vs vectors, on the same facts) |
| **LO6** | Describe and apply scalable reasoning methods | `reports/reflection/scalable_reasoning.md` (complexity + scaling levers per component) |
| **LO8** | Apply a system to evolve a Knowledge Graph | `src/evolve/version_snapshot.py` · `src/evolve/diff_snapshots.py` · `data/snapshots/` (4 snapshots, latest is the curated `20260517_090000_lecture_demo`) · `reports/evolution/evolution_report.md` (current diff: 1 added unit, 1 removed unit, 1 listing link added, 1 operator label corrected, `rule_fact_delta = 0`, intentionally small for the lecture demo) |
| **LO9** | Describe and design real-world applications of KGs | `README.md` Project Positioning and Data Sources sections · `reports/quality/data_quality_report.md` |
| **LO10** | Describe financial KG applications | `reports/reflection/financial_kg_comparison.md` |
| **LO12** | Describe the connections between KGs, ML, and AI | `reports/reflection/ml_logic_interaction.md` |

## Not included

| LO | Description | Status |
|---|---|---|
| **LO3** | Understand and apply Graph Neural Networks | Out of scope per the one-pager; the project uses TransE only. |

## Where to look first

1. **One-pager scenario and service:** `README.md` top + Project Positioning
2. **End-to-end construction:** `src/run_pipeline.py` and the per-step scripts it calls
3. **Reasoning evidence:** `reports/logic/rule_inference_report.md` and `graph/inferred_facts.ttl`
4. **ML evidence:** `reports/ml/embedding_report.md` and `reports/ml/embedding_examples.md`
5. **Reflection:** the four `reports/*_comparison.md`, `reports/*_reasoning.md`, `reports/*_interaction.md`, `reports/reflection/financial_kg_comparison.md`

## Reproducibility

A reviewer can reproduce every artifact in this repo in two ways.

Local Python:

```bash
pip install -r requirements.txt
python src/run_pipeline.py --skip-neo4j
```

Or via the bundled container (Neo4j + Flask + built frontend in one image, see `Dockerfile` and `docker/entrypoint.sh`):

```bash
docker build -t vienna-kg-dashboard .
docker run --rm -p 8000:8000 -p 7474:7474 -p 7687:7687 vienna-kg-dashboard
```

The full pipeline with Neo4j needs a running instance configured via `.env` when run locally; the container provides one out of the box. The artifacts shipped in `data/`, `graph/`, `models/embeddings/`, `reports/` and `data/snapshots/` are the outputs of the last successful pipeline run.

## Submission ZIP layout

At submission time, copy the files below into a flat ZIP using the template's four subfolders:

| Subfolder | What goes in |
|---|---|
| `2 - construction/` | `src/collect/collect_*.py`, `src/collect/download_airbnb.py`, `src/construct/resolve_entities.py`, `src/construct/build_graph.py`, `src/audit/audit_quality.py`, `src/audit/validate_graph.py`, `src/common_paths.py`, `src/kg_utils.py`, `src/run_pipeline.py`, `requirements.txt`, the four small source files in `data/` (drop the 30 MB Airbnb CSV; link to it in the report instead), `ontology/`, `graph/vienna_accommodation_operator_kg.ttl`, plus a short `readme.md` pointing to `README.md` in the repo root |
| `3 - ML/` | `src/construct/export_triples.py`, `src/learn/train_embeddings.py`, `src/learn/score_candidates.py`, `models/embeddings/`, `reports/ml/embedding_report.md`, `reports/ml/embedding_examples.md`, `reports/ml/candidate_scores.csv`, `reports/ml/operator_similarity.json` |
| `4 - logic/` | `src/rules.yml`, `src/construct/materialize_rules.py`, `ontology/accommodation_operator_shapes.ttl`, `graph/inferred_facts.ttl`, `reports/logic/rule_inference_report.md`, `reports/logic/rule_inference_summary.json`, `reports/logic/rule_eval_corporate_sibling.md`, `reports/logic/rule_eval_corporate_sibling.json`, `reports/quality/shacl_validation_report.txt` |
| `5 - reflection/` | `reports/reflection/data_model_comparison.md`, `reports/reflection/scalable_reasoning.md`, `reports/reflection/ml_logic_interaction.md`, `reports/reflection/financial_kg_comparison.md`, `reports/quality/data_quality_report.md`, `reports/evolution/evolution_report.md`, `data/snapshots/` (a couple of snapshots is enough for evidence) |

The Airbnb CSV is the only file likely to push the ZIP over typical mail/upload limits. It is publicly downloadable via `src/collect/download_airbnb.py`, so the safest pattern is to omit it and link to `https://insideairbnb.com/get-the-data/` in the portfolio report.
