# Rule Inference Report

- Generated at: 2026-05-17T13:08:34+00:00
- Input rows: 15011
- Rules applied: 6
- Total inferred facts: 2152
- Operator-pair facts (new edges): 331
- Network facts (recursive closure): 12

Portfolio reference: this document supports **LO2 — understand and apply logical knowledge in KGs** and is also the place where the **5 example rules** required by the portfolio template are written out explicitly. The same rules are also implemented as runnable SPARQL queries in `src/queries.sparql` (queries 2, 4, 5, 6).

## Rules in formal form

Each rule is listed with its first-order shape and the number of facts it produced on the current dataset. Two rules are marked specifically:

- ★ **new edge** — R5 emits triples that did not exist in the asserted graph.
- ★ **recursive / new node** — R6 takes a transitive closure over the relation produced by R5 and creates a new node class.

### R1. Professional operator

- **Rule id:** `professional_operator`
- **Description:** Operators with at least three accommodation units in the current dataset.
- **Kind:** Counting rule (forward chaining over operator groups). Adds a type only, no new edges.
- **Facts produced on the current dataset:** 858

```
∀ o, n.  count{u | operatedBy(u, o)} ≥ N  ⇒  ProfessionalOperator(o)
with threshold N = 4.
```

### R2. Cross-district operator

- **Rule id:** `cross_district_operator`
- **Description:** Operators active in at least two Vienna districts.
- **Kind:** Aggregation rule (count distinct districts per operator).
- **Facts produced on the current dataset:** 590

```
∀ o.  |{ d | ∃u. operatedBy(u, o) ∧ locatedIn(u, d) }| ≥ K
    ⇒  CrossDistrictOperator(o)
with threshold K = 2.
```

### R3. Multi-source confirmed establishment

- **Rule id:** `multi_source_confirmed_establishment`
- **Description:** Establishments merged from multiple public sources with strong merge confidence.
- **Kind:** Conjunctive selection over the unified table (provenance-driven).
- **Facts produced on the current dataset:** 278

```
∀ u.  granularity(u) = 'establishment' ∧ mergeConfidence(u) = 'strong'
    ⇒  MultiSourceConfirmedEstablishment(u)
```

### R4. Likely chain-affiliated operator

- **Rule id:** `likely_chain_affiliated_operator`
- **Description:** Operators connected to at least one establishment with a detected hotel-chain affiliation.
- **Kind:** Existential join across the operator/chain bipartite graph.
- **Facts produced on the current dataset:** 83

```
∀ o.  ∃ c.  ∃ u.  operatedBy(u, o) ∧ affiliatedWith(o, c)
    ⇒  LikelyChainAffiliatedOperator(o)
```

### R5. Shared-chain corporate sibling  ★ new edge ★

- **Rule id:** `shared_chain_corporate_group`
- **Description:** For every chain, every pair of operators affiliated with that chain is asserted as a corporate sibling pair (vaok:corporateSibling). This rule emits new edges into the derived graph graph/inferred_facts.ttl, separate from asserted facts.
- **Kind:** Pair-generation rule. Adds NEW edges (vaok:corporateSibling) into the derived graph graph/inferred_facts.ttl. The symmetric counterpart is asserted explicitly to keep SPARQL queries simple.
- **Facts produced on the current dataset:** 331

```
∀ a, b, c.  a ≠ b ∧ affiliatedWith(a, c) ∧ affiliatedWith(b, c)
    ⇒  corporateSibling(a, b) ∧ corporateSibling(b, a)
```

### R6. Operator corporate network  ★ recursive ★ ★ new node ★

- **Rule id:** `operator_corporate_network`
- **Description:** Recursive rule. Treats vaok:corporateSibling as a transitive, symmetric relation and computes the connected components over it. Each component becomes a new OperatorNetwork node, and each member operator is linked via vaok:memberOf. Recursion is bounded by the size of the operator-chain bipartite graph.
- **Kind:** Recursive rule (transitive closure over a symmetric relation), implemented as union-find. Adds NEW nodes (OperatorNetwork) and NEW edges (vaok:memberOf) into graph/inferred_facts.ttl.
- **Facts produced on the current dataset:** 12

```
Base:     ∀ a.   corporateSibling(a, a) ⇒ sameNetwork(a, a)
Step:     ∀ a, b, c.   sameNetwork(a, b) ∧ corporateSibling(b, c)
                       ⇒  sameNetwork(a, c)
Closure:  let C be a connected component under sameNetwork.
          create a fresh node nC of type OperatorNetwork
          ∀ x ∈ C.  memberOf(x, nC)
```

## Facts by Type

- `CorporateSibling`: 331
- `CrossDistrictOperator`: 590
- `LikelyChainAffiliatedOperator`: 83
- `MultiSourceConfirmedEstablishment`: 278
- `OperatorNetwork`: 12
- `ProfessionalOperator`: 858

## Sample Facts

- `CorporateSibling` for `Accor Hotels ↔ Hotel Ibis Wien Messe` via `Shared chain corporate group`: {'via_chain': 'AccorHotels', 'operator_a': 'Accor Hotels', 'operator_b': 'Hotel Ibis Wien Messe'}
- `CorporateSibling` for `Accor Hotels ↔ Hotel Novotel Wien City` via `Shared chain corporate group`: {'via_chain': 'AccorHotels', 'operator_a': 'Accor Hotels', 'operator_b': 'Hotel Novotel Wien City'}
- `CorporateSibling` for `Accor Hotels ↔ Ibis` via `Shared chain corporate group`: {'via_chain': 'AccorHotels', 'operator_a': 'Accor Hotels', 'operator_b': 'Ibis'}
- `CorporateSibling` for `Accor Hotels ↔ Ibis Budget` via `Shared chain corporate group`: {'via_chain': 'AccorHotels', 'operator_a': 'Accor Hotels', 'operator_b': 'Ibis Budget'}
- `CorporateSibling` for `Accor Hotels ↔ Ibis Styles` via `Shared chain corporate group`: {'via_chain': 'AccorHotels', 'operator_a': 'Accor Hotels', 'operator_b': 'Ibis Styles'}
- `CorporateSibling` for `Accor Hotels ↔ Mercure Grand Hotel Biedermeier Wien` via `Shared chain corporate group`: {'via_chain': 'AccorHotels', 'operator_a': 'Accor Hotels', 'operator_b': 'Mercure Grand Hotel Biedermeier Wien'}
- `CorporateSibling` for `Accor Hotels ↔ Mercure Raphael Hotel Wien` via `Shared chain corporate group`: {'via_chain': 'AccorHotels', 'operator_a': 'Accor Hotels', 'operator_b': 'Mercure Raphael Hotel Wien'}
- `CorporateSibling` for `Accor Hotels ↔ Mercure Wien Westbahnhof` via `Shared chain corporate group`: {'via_chain': 'AccorHotels', 'operator_a': 'Accor Hotels', 'operator_b': 'Mercure Wien Westbahnhof'}
- `CorporateSibling` for `Accor Hotels ↔ Novotel` via `Shared chain corporate group`: {'via_chain': 'AccorHotels', 'operator_a': 'Accor Hotels', 'operator_b': 'Novotel'}
- `CorporateSibling` for `Accor Hotels ↔ Novotel Suites Wien City` via `Shared chain corporate group`: {'via_chain': 'AccorHotels', 'operator_a': 'Accor Hotels', 'operator_b': 'Novotel Suites Wien City'}
- `CorporateSibling` for `Accor Hotels ↔ Novotel Suites Wien City Donau` via `Shared chain corporate group`: {'via_chain': 'AccorHotels', 'operator_a': 'Accor Hotels', 'operator_b': 'Novotel Suites Wien City Donau'}
- `CorporateSibling` for `Accor Hotels ↔ Novotel Wien City` via `Shared chain corporate group`: {'via_chain': 'AccorHotels', 'operator_a': 'Accor Hotels', 'operator_b': 'Novotel Wien City'}

## Interpretation

- These facts are inferred from explicit rules, not imported directly from the raw sources.
- R5 (`shared_chain_corporate_group`) and R6 (`operator_corporate_network`) produce new edges and nodes
  in `graph/inferred_facts.ttl`, kept separate from `graph/vienna_accommodation_operator_kg.ttl` so
  asserted and inferred facts stay distinguishable.
- R6 is the recursive rule: it computes the transitive closure over the `corporateSibling`
  relation produced by R5 via union-find. This is also the closure exploited by the recursive
  property-path query in `src/queries.sparql` (query 4: `vaok:corporateSibling*`).
- The quantitative evaluation of R5 against a hand-labelled 30-edge gold sample is reported in
  `reports/logic/rule_eval_corporate_sibling.md`.
- This reasoning layer supports portfolio claims around symbolic reasoning, graph evolution,
  and explainable KG services.
