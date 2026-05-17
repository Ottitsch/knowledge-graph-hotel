"""
Train a TransE embedding model over the exported KG triples.

Reads:  models/embeddings/triples.tsv
Writes: models/embeddings/transe_embeddings.npz
        models/embeddings/transe_mappings.json
        reports/embedding_metrics.json
        reports/embedding_report.md
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from pykeen.pipeline import pipeline
from pykeen.triples import TriplesFactory

from common_paths import (
    EMBEDDING_MATRIX_FILE,
    EMBEDDING_MAPPINGS_JSON,
    EMBEDDING_METRICS_JSON,
    EMBEDDING_REPORT_MD,
    TRIPLES_FILE,
    ensure_directories,
    utc_timestamp,
    write_json,
)


def _flatten_metrics(metric_results) -> dict[str, float]:
    flattened = {}
    for key, value in metric_results.to_flat_dict().items():
        if isinstance(value, (int, float)):
            flattened[str(key)] = float(value)
    return flattened


def _extract_matrix(representation) -> np.ndarray:
    tensor = representation(indices=None)
    return tensor.detach().cpu().numpy()


def build_report(metrics: dict, losses: list[float]) -> str:
    lines = [
        "# Embedding Report",
        "",
        f"- Generated at: {metrics['generated_at']}",
        f"- Model: {metrics['model']}",
        f"- Embedding dimension: {metrics['embedding_dim']}",
        f"- Epochs: {metrics['epochs']}",
        f"- Triple count: {metrics['triple_count']}",
        f"- Entity count: {metrics['entity_count']}",
        f"- Relation count: {metrics['relation_count']}",
        "",
        "## Key Metrics",
        "",
    ]

    for key in sorted(metrics["evaluation_metrics"])[:18]:
        lines.append(f"- `{key}`: {metrics['evaluation_metrics'][key]:.6f}")

    lines.extend(["", "## Training Loss", ""])
    if losses:
        for idx, loss in enumerate(losses[-10:], start=max(len(losses) - 9, 1)):
            lines.append(f"- epoch {idx}: {float(loss):.6f}")
    else:
        lines.append(
            "- Per-epoch losses were not captured by the current PyKEEN version; rerun with a newer"
            " release or hook the training loop to record them."
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This report documents a real KG embedding model trained on the exported triples.",
            "- The embeddings are used as suggestions for weak listing-establishment candidates and similar operators.",
            "- Suggested links remain separate from asserted graph facts.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a TransE embedding model")
    parser.add_argument("--epochs", type=int, default=6)
    parser.add_argument("--embedding-dim", type=int, default=48)
    args = parser.parse_args()

    ensure_directories()
    if not TRIPLES_FILE.exists():
        raise SystemExit(f"Missing triple export: {TRIPLES_FILE}")

    triples_df = pd.read_csv(TRIPLES_FILE, sep="\t")
    triples = triples_df[["head", "relation", "tail"]].astype(str).to_numpy()
    triples_factory = TriplesFactory.from_labeled_triples(triples)
    training, testing, validation = triples_factory.split([0.8, 0.1, 0.1], random_state=42)

    torch.manual_seed(42)
    result = pipeline(
        training=training,
        testing=testing,
        validation=validation,
        model="TransE",
        model_kwargs={"embedding_dim": args.embedding_dim},
        training_kwargs={"num_epochs": args.epochs, "use_tqdm_batch": False},
        random_seed=42,
        device="cpu",
    )

    entity_embeddings = _extract_matrix(result.model.entity_representations[0])
    relation_embeddings = _extract_matrix(result.model.relation_representations[0])
    np.savez_compressed(
        EMBEDDING_MATRIX_FILE,
        entity_embeddings=entity_embeddings,
        relation_embeddings=relation_embeddings,
    )

    entity_labels = sorted(triples_factory.entity_to_id, key=triples_factory.entity_to_id.get)
    relation_labels = sorted(triples_factory.relation_to_id, key=triples_factory.relation_to_id.get)
    mappings = {
        "generated_at": utc_timestamp(),
        "model": "TransE",
        "entity_to_id": {key: int(value) for key, value in triples_factory.entity_to_id.items()},
        "relation_to_id": {key: int(value) for key, value in triples_factory.relation_to_id.items()},
        "entity_labels": entity_labels,
        "relation_labels": relation_labels,
    }
    write_json(EMBEDDING_MAPPINGS_JSON, mappings)

    # PyKEEN exposes per-epoch losses on the training loop, but the attribute name
    # differs by version. Try the documented sources in order, falling back to the
    # pipeline result's losses attribute. Empty losses are harmless but signal a
    # version mismatch worth investigating.
    losses_source = (
        getattr(result.training_loop, "losses", None)
        or getattr(result, "losses", None)
        or []
    )
    losses = [float(loss) for loss in losses_source]
    if not losses:
        print("WARN: no per-epoch losses captured; check PyKEEN version", flush=True)
    metrics = {
        "generated_at": utc_timestamp(),
        "model": "TransE",
        "embedding_dim": int(args.embedding_dim),
        "epochs": int(args.epochs),
        "triple_count": int(len(triples_df)),
        "entity_count": int(len(entity_labels)),
        "relation_count": int(len(relation_labels)),
        "losses": losses,
        "evaluation_metrics": _flatten_metrics(result.metric_results),
    }
    write_json(EMBEDDING_METRICS_JSON, metrics)
    EMBEDDING_REPORT_MD.write_text(build_report(metrics, losses), encoding="utf-8")

    print(f"Wrote {EMBEDDING_MATRIX_FILE}")
    print(f"Wrote {EMBEDDING_MAPPINGS_JSON}")
    print(f"Wrote {EMBEDDING_METRICS_JSON}")
    print(f"Wrote {EMBEDDING_REPORT_MD}")
    print(f"Entity embeddings: {entity_embeddings.shape}")
    print(f"Relation embeddings: {relation_embeddings.shape}")


if __name__ == "__main__":
    main()
