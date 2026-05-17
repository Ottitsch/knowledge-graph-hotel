# `reports/` layout

All generated reports are grouped by topic so a reviewer can map them straight to learning outcomes and to the submission ZIP subfolders.

| Folder | Files | Maps to |
|---|---|---|
| `quality/` | `data_quality_report.md`, `quality_summary.json`, `shacl_validation_report.{txt,ttl}` | LO9, LO5 (validation) |
| `logic/` | `rule_inference_report.md`, `rule_inference_summary.json`, `rule_inference_facts.json`, `rule_eval_corporate_sibling.md`, `rule_eval_corporate_sibling.json` | LO2 - `4 - logic/` |
| `ml/` | `embedding_report.md`, `embedding_examples.md`, `embedding_metrics.json`, `candidate_scores.csv`, `operator_similarity.json` | LO1 - `3 - ML/` |
| `evolution/` | `evolution_report.md`, `evolution_summary.json`, `evolution_changes.json` | LO8 |
| `reflection/` | `data_model_comparison.md`, `scalable_reasoning.md`, `ml_logic_interaction.md`, `financial_kg_comparison.md` | LO4, LO6, LO10, LO12 - `5 - reflection/` |

Reports are written by the scripts under `src/` (see `src/README.md`) via the paths defined in `src/common_paths.py`. Re-running any single script overwrites just its own outputs.
