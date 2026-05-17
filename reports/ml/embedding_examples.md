# Embedding Examples

Portfolio reference: this document supports **LO1 - understand and apply Knowledge Graph Embeddings**.

It complements `embedding_report.md` (training metrics) by giving the concrete examples the portfolio template asks for:
**5 examples of how a particular type of node or edge is represented**, plus **1 true-positive example** of a predicted link that should be there, **1 false-positive example** of a predicted link that should not be there, and the worked TransE plausibility scores for each.

All numbers below come directly from `models/embeddings/transe_embeddings.npz` and `models/embeddings/transe_mappings.json` after a 6-epoch TransE training run (`embedding_dim = 48`, `entity_count = 22 382`, `relation_count = 7`, `triple_count = 82 929`). They can be reproduced by running `python src/learn/train_embeddings.py` followed by the small inspection snippet at the bottom of this file.

## TransE in one paragraph

A triple `(h, r, t)` is encoded as the constraint `h + r ≈ t` in 48-dim space. The plausibility of a triple is measured by the **TransE distance** `d(h, r, t) = ‖h + r − t‖₂`. Lower is better. The model is trained to push true triples toward low distance and corrupted triples toward higher distance. For each of the five representations below we therefore show the entity (or relation) vector **plus** at least one concrete triple it participates in, with the distance computed for a true tail and an incorrect tail. If the embedding has learned anything useful, the true tail's distance must be lower than the corrupted one's.

## 1. Five concrete representations

### 1.1 Accommodation-unit node (Blueground listing)

- **Entity key:** `unit:142cdf3a-6c55-43b4-9cf8-4d0f8771646f`
- **Plain label:** *"Blueground | Hernals, elev, nr medical univ & U6"*
- **Index in entity matrix:** `7 569`
- **Norm of embedding:** `1.0000` (TransE enforces unit-norm on entity vectors)
- **First six dims:** `[0.103, 0.084, 0.166, -0.092, 0.018, 0.143]`
- **Triple it participates in:** `unit:142cdf3a... → operatedBy → operator:airbnb:385064248` (Blueground)
- **TransE distance for the true tail:** `‖h + r_operatedBy − t_Blueground‖ = 1.2717`
- **TransE distance for a corrupted tail** (`operator:airbnb:151869337`, "Fahmee And Seb And Marc"): `1.5385`

The gap of `0.27` is what the candidate scorer turns into a ranking signal. The unit-norm constraint is what makes cosine-style similarity between two unit vectors equivalent to a linear function of their TransE distance.

### 1.2 Operator node (Blueground)

- **Entity key:** `operator:airbnb:385064248`
- **Plain label:** *"Blueground"* (396 listings in this dataset)
- **Index:** `3 401`
- **Norm:** `1.0000`
- **First six dims:** `[0.170, 0.130, 0.084, -0.045, 0.144, 0.196]`
- **Triple it participates in:** the same triple as 1.1 with the operator on the tail side. Its 0.27 distance gap to the corrupted operator is precisely what shows up in `reports/ml/candidate_scores.csv` as the embedding ranking signal.
- **Geometric reading:** the operator vector lies close to the *centroid* of the unit vectors that have a true `operatedBy` edge to it, offset by `r_operatedBy`. That is what makes operator embeddings useful for **operator-similarity** queries on top of the same model.

### 1.3 District node (Innere Stadt)

- **Entity key:** `district:innere_stadt`
- **Index:** `26`
- **Norm:** `1.0000`
- **First six dims:** `[-0.208, 0.084, -0.143, -0.061, 0.047, 0.023]`
- **Triple:** `unit:e39793d3... → locatedIn → district:innere_stadt`
- **True-tail distance:** `1.3851`
- **Corrupted tail (`district:donaustadt`):** `1.5916`

The 23 district nodes act as soft cluster centroids. Two units in the same district share part of the `+ r_locatedIn` offset, which is one of the structural confounds that explains the false-positive case in §3.

### 1.4 Relation `operatedBy`

- **Relation key:** `operatedBy`
- **Index:** `6`
- **Norm:** `0.9896` (relation vectors are *not* unit-norm under TransE)
- **First six dims:** `[0.192, 0.027, 0.130, -0.226, 0.094, 0.150]`

`operatedBy` is the single most-used relation in our triple file (`30 178 / 82 929` triples, ≈ 36 %). Its near-unit norm and the consistent distance gap observed in §1.1/§1.2 indicate that the model has actually shaped this relation rather than collapsing it to noise. Compare with `locatedIn`, whose norm is `1.2748` - the larger norm reflects the fact that `locatedIn` has to map ~15k unit vectors onto only 23 district vectors and therefore needs a longer translation.

### 1.5 Relation `affiliatedWith`

- **Relation key:** `affiliatedWith`
- **Index:** `0`
- **Norm:** `1.1382`
- **First six dims:** `[-0.106, -0.173, -0.006, 0.306, -0.062, 0.097]`
- **Triple:** `operator:name:accor → affiliatedWith → chain:accorhotels`
- **True-tail distance:** `1.0829`
- **Corrupted tail (`chain:hilton_hotels_resorts`):** `1.3822`

This is the relation that the logic-based layer reuses: `affiliatedWith` is the input to the `shared_chain_corporate_group` rule, which materialises `corporateSibling` edges. The fact that the embedding ranks the right chain ~0.30 lower than a wrong chain even on a tiny six-epoch CPU model is exactly the cross-check the LO12 reflection (`ml_logic_interaction.md`) describes: the symbolic layer asserts the edge from explicit data, and the embedding gives a continuous confirmation that the geometry agrees.

## 2. True-positive predicted link

**Triple proposed by the embedding:**
`unit:d06adf5a-def4-4407-bb53-46d7319b6a90 → listingOf → unit:484a426f-7d32-4178-a260-3c600ccc4846`

**Plain language:** the Airbnb listing *"ArtApartment near Stephansplatz Stylish 2 BR AC"* is the same physical accommodation as the registered establishment *"City Pension Stephansplatz"* (from `data.gv.at`).

**Evidence stacked together:**
- Geographic distance: **20.77 m** (well within the 35 m candidate threshold).
- Token overlap: both names share `stephansplatz`.
- Embedding-ranked plausibility score (normalised, from `reports/ml/candidate_scores.csv`): **0.9956**, ranking it the second-strongest candidate in the entire weak-candidate set (1 097 rows).

**Why this counts as a true positive:** the symbolic layer would not have asserted this link on distance alone (it was kept out of `vienna_accommodation_operator_kg.ttl`). The embedding ranks it above ~99 % of other candidates and the token overlap confirms it. A human curator should accept this match.

## 3. False-positive predicted link

**Pair flagged as similar:** `operator:airbnb:385064248` ("Blueground", 396 units) ↔ `operator:airbnb:151869337` ("Fahmee And Seb And Marc", 55 units)

**Cosine similarity from `reports/ml/operator_similarity.json`:** **0.5453** - Blueground's top-1 most similar operator out of the 120-operator pool.

**Why this is a false positive:** "Blueground" is an internationally branded short-term-rental operator with central management. "Fahmee And Seb And Marc" is a personal-name Airbnb host. There is no public evidence they are operationally related. The embedding's similarity score is a **structural confound**: both operators have very high `unit_count`, both are observed exclusively in the `airbnb` source, and both spread their listings across multiple districts. TransE picks up that shared *structural profile* and treats it as identity.

**What the symbolic layer does about it:** the `shared_chain_corporate_group` and `operator_corporate_network` rules in `materialize_rules.py` only link operators that share an explicit `hotel_chain` value. Since neither of these operators has any chain affiliation, the rule engine refuses to assert a `vaok:corporateSibling` edge - exactly the kind of safety net the LO12 reflection argues for, and exactly the case used to justify keeping the embedding signal **out** of the asserted graph (`graph/vienna_accommodation_operator_kg.ttl`).

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
                  reports/ml/candidate_scores.csv          reports/ml/operator_similarity.json
                       (where TP came from)              (where FP came from)
```

## 5. Honesty about the metrics

Headline metrics for this model (from `embedding_report.md`):

- `both.optimistic.hits_at_10` = **0.261**
- `both.optimistic.hits_at_1`  = **0.056**

These numbers are deliberately modest. The model was trained for 6 epochs on CPU with `embedding_dim = 48`. The portfolio claim is **not** "this model is competitive on link prediction" - it is "the embedding is a useful ranking signal for weak candidate links that the symbolic layer cannot decide on its own". Each of the five representations above shows a positive→negative distance gap of `0.20–0.30`, which is what the candidate scorer turns into the ranked list in `reports/ml/candidate_scores.csv`. The TP/FP pair shows what that ranking gets right and what it gets wrong.

## 6. Reproducing the distance numbers

```python
import numpy as np, json
emb = np.load("models/embeddings/transe_embeddings.npz")
with open("models/embeddings/transe_mappings.json") as f:
    m = json.load(f)
E, R = emb["entity_embeddings"], emb["relation_embeddings"]
e2i, r2i = m["entity_to_id"], m["relation_to_id"]

def d(h_key, r_key, t_key):
    return float(np.linalg.norm(E[e2i[h_key]] + R[r2i[r_key]] - E[e2i[t_key]]))

# §1.1
print(d("unit:142cdf3a-6c55-43b4-9cf8-4d0f8771646f",
        "operatedBy", "operator:airbnb:385064248"))      # 1.2717
print(d("unit:142cdf3a-6c55-43b4-9cf8-4d0f8771646f",
        "operatedBy", "operator:airbnb:151869337"))      # 1.5385
```
