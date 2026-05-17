from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parent
BASE_DIR = SRC_DIR.parent
DATA_DIR = BASE_DIR / "data"
GRAPH_DIR = BASE_DIR / "graph"
ONTOLOGY_DIR = BASE_DIR / "ontology"
REPORTS_DIR = BASE_DIR / "reports"
MODELS_DIR = BASE_DIR / "models"
EMBEDDING_DIR = MODELS_DIR / "embeddings"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
CACHE_DIR = BASE_DIR / "cache"

UNIFIED_DATA_FILE = DATA_DIR / "properties_unified.csv"
RDF_GRAPH_FILE = GRAPH_DIR / "vienna_accommodation_operator_kg.ttl"

# reports/ is grouped into five subfolders so a reviewer can find evidence by topic.
QUALITY_REPORTS_DIR = REPORTS_DIR / "quality"
LOGIC_REPORTS_DIR = REPORTS_DIR / "logic"
ML_REPORTS_DIR = REPORTS_DIR / "ml"
EVOLUTION_REPORTS_DIR = REPORTS_DIR / "evolution"
REFLECTION_REPORTS_DIR = REPORTS_DIR / "reflection"

SHACL_REPORT_TXT = QUALITY_REPORTS_DIR / "shacl_validation_report.txt"
SHACL_REPORT_TTL = QUALITY_REPORTS_DIR / "shacl_validation_report.ttl"
QUALITY_REPORT_MD = QUALITY_REPORTS_DIR / "data_quality_report.md"
QUALITY_REPORT_JSON = QUALITY_REPORTS_DIR / "quality_summary.json"

RULES_FILE = SRC_DIR / "rules.yml"
RULE_REPORT_MD = LOGIC_REPORTS_DIR / "rule_inference_report.md"
RULE_SUMMARY_JSON = LOGIC_REPORTS_DIR / "rule_inference_summary.json"
RULE_FACTS_JSON = LOGIC_REPORTS_DIR / "rule_inference_facts.json"

TRIPLES_FILE = EMBEDDING_DIR / "triples.tsv"
TRIPLES_METADATA_JSON = EMBEDDING_DIR / "triples_metadata.json"
EMBEDDING_MATRIX_FILE = EMBEDDING_DIR / "transe_embeddings.npz"
EMBEDDING_MAPPINGS_JSON = EMBEDDING_DIR / "transe_mappings.json"
EMBEDDING_REPORT_MD = ML_REPORTS_DIR / "embedding_report.md"
EMBEDDING_METRICS_JSON = ML_REPORTS_DIR / "embedding_metrics.json"
CANDIDATE_SCORES_CSV = ML_REPORTS_DIR / "candidate_scores.csv"
OPERATOR_SIMILARITY_JSON = ML_REPORTS_DIR / "operator_similarity.json"

EVOLUTION_REPORT_MD = EVOLUTION_REPORTS_DIR / "evolution_report.md"
EVOLUTION_SUMMARY_JSON = EVOLUTION_REPORTS_DIR / "evolution_summary.json"
EVOLUTION_CHANGES_JSON = EVOLUTION_REPORTS_DIR / "evolution_changes.json"

FINANCIAL_KG_REPORT_MD = REFLECTION_REPORTS_DIR / "financial_kg_comparison.md"


def ensure_directories() -> None:
    for path in [
        DATA_DIR,
        GRAPH_DIR,
        REPORTS_DIR,
        QUALITY_REPORTS_DIR,
        LOGIC_REPORTS_DIR,
        ML_REPORTS_DIR,
        EVOLUTION_REPORTS_DIR,
        REFLECTION_REPORTS_DIR,
        MODELS_DIR,
        EMBEDDING_DIR,
        SNAPSHOTS_DIR,
        CACHE_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def read_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def snapshot_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")
