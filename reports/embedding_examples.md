# Embedding Examples

Portfolio reference: this document supports **LO1 — understand and apply Knowledge Graph Embeddings**.

It complements `embedding_report.md` (training metrics) by giving the concrete examples the portfolio template asks for:
**5 examples of how a particular type of node or edge is represented**, **1 true-positive example** of a predicted link that should be there, and **1 false-positive example** of a predicted link that should not be there.

All numbers below are taken directly from `models/embeddings/transe_embeddings.npz` and `models/embeddings/transe_mappings.json` after a 6-epoch TransE training run (`embedding_dim = 48`, `entity_count = 22 382`, `relation_count = 7`, `triple_count = 82 929`).

## 1. Five concrete representations

Each row below names the entity or relation, its index in the embedding matrix, and the first six dimensions of the normalized 48-dim vector. Norms are 1.0 for entity vectors (TransE entity normalization) and around 1 for relation vectors.

| # | Kind | Label | Index | Norm | First 6 dims (rounded) |
|---|---|---|---:|---:|---|
| 1 | Operator node | `operator:airbnb:385064248` ("Blueground") | 3 401 | 1.000 | `[0.170, 0.130, 0.084, -0.045, 0.144, 0.196]` |
| 2 | Accommodation unit node | `unit:d4736edc-906d-4b36-b803-6f3957d7ae6c` (a Blueground listing in Landstraße) | 19 880 | 1.000 | `[0.093, 0.122, 0.051, 0.076, -0.242, 0.208]` |
| 3 | District node | `district:innere_stadt` | 26 | 1.000 | `[-0.208, 0.084, -0.143, -0.061, 0.047, 0.023]` |
| 4 | Relation | `operatedBy` | 6 | 0.990 | `[0.192, 0.027, 0.130, -0.226, 0.094, 0.150]` |
| 5 | Relation | `listingOf` | 3 | 0.967 | `[0.171, 0.143, 0.014, -0.174, -0.025, -0.182]` |

In TransE, a triple `(head, relation, tail)` is plausible when `head + relation ≈ tail` in 48-dim space. So a low value of `‖head + r − tail‖` is what we treat as "the embedding agrees with this triple".

## 2. True-positive predicted link

**Triple proposed:**
`unit:d06adf5a-def4-4407-bb53-46d7319b6a90 → listingOf → unit:484a426f-7d32-4178-a260-3c600ccc4846`

**Plain language:** the Airbnb listing *"ArtApartment near Stephansplatz Stylish 2 BR AC"* is the same physical accommodation as the registered establishment *"City Pension Stephansplatz"* (from `data.gv.at`).

**Evidence stacked together:**
- Geographic distance: 20.77 m (well within the 35 m candidate threshold).
- Token overlap: both names share `stephansplatz`.
- Embedding score (normalized): **0.9956**, ranking it the second-strongest candidate in the entire weak-candidate set (1 097 rows in `reports/candidate_scores.csv`).

**Why this counts as a true positive:** the symbolic layer would not have asserted this link on distance alone (it was kept out of `vienna_accommodation_operator_kg.ttl`). The embedding ranks it above ~99% of other candidates and the token overlap confirms it. A human curator should accept this match.

## 3. False-positive predicted link

**Pair flagged as similar:**
`operator:airbnb:385064248` ("Blueground", 396 units) ↔ `operator:airbnb:151869337` ("Fahmee And Seb And Marc", 55 units)

**Cosine similarity from `reports/operator_similarity.json`:** **0.5453** — Blueground's top-1 most similar operator out of the 120-operator pool.

**Why this is a false positive:** "Blueground" is an internationally branded short-term-rental operator (managed apartments, central booking platform). "Fahmee And Seb And Marc" is a personal-name Airbnb host. There is no public evidence they are operationally related. The embedding's similarity score comes from a structural confound: both operators have very high `unit_count`, both are observed exclusively in the `airbnb` source, and both operate listings spread across multiple districts. TransE picks up that shared *structural profile* and treats it as identity.

**What the symbolic layer does about it:** the `shared_chain_corporate_group` and `operator_corporate_network` rules in `materialize_rules.py` only link operators that share an explicit `hotel_chain` value. Since neither of these operators has any chain affiliation, the rule engine refuses to assert a `vaok:corporateSibling` edge — exactly the kind of safety net the LO12 reflection (`ml_logic_interaction.md`) argues for.

## 4. How these examples flow through the pipeline

```
properties_unified.csv ──► export_triples.py ──► triples.tsv (82 929 rows)
                                                     │
                                                     ▼
                                             train_embeddings.py
                                                     │
                                                     ▼
                       transe_embeddings.npz  (22 382 × 48 entity matrix)
                                                     │
                                                     ▼
                                            score_candidates.py
                                                     │
                                  ┌──────────────────┴──────────────────┐
                                  ▼                                     ▼
                  reports/candidate_scores.csv          reports/operator_similarity.json
                       (where TP came from)              (where FP came from)
```

## 5. Honesty about the metrics

Headline metrics for this model (from `embedding_report.md`):
- `both.optimistic.hits_at_10` = **0.261**
- `both.optimistic.hits_at_1`  = **0.056**

These numbers are deliberately modest. The model was trained for 6 epochs on CPU with `embedding_dim = 48`. The portfolio claim is **not** "this model is competitive on link prediction" — it is "the embedding is a useful ranking signal for weak candidate links that the symbolic layer cannot decide on its own". Both the TP and the FP above illustrate exactly that: it ranks the right candidate near the top, but its similarity score for arbitrary operator pairs needs to be filtered by symbolic rules before it can be trusted.
