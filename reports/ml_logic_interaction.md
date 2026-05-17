# ML and Logic Interaction

Portfolio reference: this document supports **LO12 — describe the connections between Knowledge Graphs (KGs), Machine Learning (ML) and Artificial Intelligence (AI)**, with concrete reference to this project.

## What sits where in the project

| Form of AI | Artifact in this repo | Role |
|---|---|---|
| Symbolic / logic | `ontology/accommodation_operator.owl`, `accommodation_operator_shapes.ttl`, `src/rules.yml`, `src/materialize_rules.py` | Class hierarchy, integrity constraints, forward-chaining inference |
| Statistical / ML | `src/train_embeddings.py` (TransE), `src/score_candidates.py` | Vector representation of every entity and relation; similarity ranking |
| Hybrid wiring | `webapp/app.py` reasoning lab and evidence panels | Surfaces inferred facts alongside embedding suggestions, side by side |

## How they interact today

The two forms are deliberately wired in a **propose / accept** loop, not a single merged model:

1. **Symbolic resolution proposes the candidate set.** `resolve_entities.py` uses distance, token overlap, and explicit operator/host evidence to split listing-establishment pairs into three buckets: asserted as `LISTING_OF`, kept as weak candidates, or dropped. Only the first bucket enters the asserted graph.
2. **The embedding model scores the weak candidates.** `score_candidates.py` reads the trained TransE vectors and computes `embedding_score` and `embedding_suggestion` (`weak`, `review`, `strong_review`) for each weak candidate row. These scores never silently mutate the graph; they are stored in `reports/candidate_scores.csv`.
3. **The rule engine reads the same source-of-truth table.** `materialize_rules.py` derives `ProfessionalOperator`, `CrossDistrictOperator`, etc. and now also `corporateSibling` and `OperatorNetwork` (recursive). Those facts are written to `graph/inferred_facts.ttl` separate from the asserted graph.
4. **The dashboard shows both with provenance.** Every panel in the reasoning lab labels a row as "asserted", "rule-inferred", or "embedding-suggested", so a user can apply their own threshold.

So the embedding is a **ranking oracle** for the symbolic layer; the symbolic layer is a **provenance frame** for the embedding output.

## Concrete examples of the interaction

- *Same chain operator pairs.* The symbolic rule `shared_chain_corporate_group` derives a `vaok:corporateSibling` edge between two operators because both are linked to the same hotel chain. The embedding similarity between those same two operators (cosine of their TransE vectors) gives an independent signal. When the embedding agrees with the rule, confidence in the cluster goes up. When it disagrees, that is a flag for the audit panel — for example, two operators tagged with the same chain in OSM but whose embeddings sit far apart probably have a chain-name collision rather than a real shared chain.
- *Listing-establishment review.* Weak proximity-only candidates (~1k rows in `candidate_scores.csv`) cannot be asserted by the symbolic layer alone. The embedding ranks them. Rows with `embedding_suggestion = strong_review` are exactly the candidates a human curator should look at first. This is ML used to **prioritize** symbolic work, not replace it.
- *Operator similarity for fraud-like patterns.* `operator_similarity.json` groups operators by embedding cosine. If three operators cluster tightly but only one of them carries an explicit chain affiliation, the embedding is suggesting that the other two might be unbranded co-operators. The symbolic rule does not infer this on its own, but it can be made explicit by adding a new rule "treat top-k embedding neighbors as candidate corporate siblings, subject to audit".

## Where they could be coupled more tightly

- **Learn rule thresholds.** `professional_operator` currently uses a hand-picked `threshold: 4`. The right value is empirical — the embedding model already gives a continuous signal of operator "professionalness" via the spread of similar operators. A simple supervised model could pick the threshold that maximizes agreement with a curated set, instead of guessing.
- **Use logic to clean training data.** TransE was trained on all triples in the unified graph including rows with `operator_identity_confidence = low`. A logical filter ("only train on high/medium confidence operator edges") would likely improve evaluation hits@k for the questions the KG actually serves, at the cost of a smaller training set.
- **Use ML to extend SHACL violations into suggestions.** Today SHACL just reports conformance. A trained classifier on past fixes could turn each violation into a suggested fix ("missing `granularity` → most likely `listing`, p=0.94") so the validator becomes an active helper instead of a passive checker.
- **Replace TransE with a neuro-symbolic model.** Models like RuleN or NeuralLP can learn first-order rules directly from the graph. Adopting one would let the KG *discover* candidate rules rather than only apply hand-written ones, and the discovered rules would be reviewable in the same form as `rules.yml`.

## What I would not change

The project deliberately keeps inferred and asserted facts separated. That separation is a feature: it makes provenance auditable, it lets the SHACL validator focus only on what is asserted, and it lets the user reason about the difference between "what the sources say" and "what the system derived". Merging them into a single graph would be more convenient but would erase the boundary that makes the system honest.
