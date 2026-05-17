# Portfolio supplement — service statement and construction examples

This file gathers two short pieces that the portfolio report needs but that
are not written up as a single doc anywhere else in the repo:

1. an explicit one-line statement of the **service** the KG provides
   (Portfolio section 1.2), and
2. **three concrete construction examples** of how particular nodes and
   edges are built from the source datasets (Portfolio section 2.3).

Both are intentionally short — the portfolio body can lift these directly.

---

## 1. Service (section 1.2)

> **Given an operator or accommodation unit, return all co-operated units
> across the four public sources, together with their provenance and an
> identity-confidence label.**

Concretely the service is exposed as:

- the SPARQL query `### 1` in `src/queries.sparql` (top operators by unit count)
- the HTTP endpoints `/api/operator-units` and `/api/entity-evidence` in
  `webapp/app.py`
- the operator-detail view in the dashboard (`webapp/frontend/`)

A user submits an operator name or a unit id; the service returns the set of
units the same operator runs, each annotated with `source_names`,
`operator_name_source`, and `operator_identity_confidence` so the answer can
be audited rather than trusted blindly.

---

## 2. Three construction examples (section 2.3)

The portfolio template asks for three worked examples of how a particular
type of node or edge is constructed from the source data. The three below
cover one node, one inter-source edge, and one rule-derived edge.

### 2.1 Building an `Operator` node from an Airbnb `host_id`

Source: Inside Airbnb `listings.csv`.

For each Airbnb row, `src/construct/resolve_entities.py` (`load_airbnb`, ~L482–L510)
renames `host_id → host_id`, `host_name → operator_name`, and tags
`operator_name_source = "airbnb_host"`. Rows with the same `host_id` collapse
into a single `Operator` node in `src/build_graph.py`, with
`operator_identity_confidence = "high"` because the host id is a stable
platform identifier (see the `OPERATOR_EVIDENCE_LEVELS` table around
`src/construct/resolve_entities.py:L165`).

Result: one `(:Operator {host_id, name, evidence:"airbnb_host"})` node per
distinct Airbnb host, connected to all that host's listings via
`OPERATED_BY`.

### 2.2 Asserting a `LISTING_OF` edge from address + name match

Source: Airbnb listing × merged establishment record (OSM ∪ Wikidata ∪
data.gv.at).

`_classify_listing_match` in `src/construct/resolve_entities.py` (L614–L653) compares
a listing to a nearby establishment using three signals:

- haversine distance (≤ `LISTING_HIGH_CONFIDENCE_MAX_DIST_M`),
- exact operator-name match after normalisation, and
- substring or token overlap of the non-generic part of the venue name.

If distance is within the high-confidence threshold **and** at least one of
(exact operator, phrase match, ≥ 2 token overlap) holds, the function
returns `confidence = "high"` with an evidence string such as
`distance<=35m + name_phrase + token_overlap=hotel,sacher`. Only matches
that return `"high"` or `"medium"` become `LISTING_OF` edges in the graph;
weak proximity-only candidates stay in the unified CSV for audit but are
**not** asserted as facts.

Result: `(:AccommodationUnit:Listing)-[:LISTING_OF {confidence, evidence}]->
(:AccommodationUnit:Establishment)`.

### 2.3 Deriving a `corporateSibling` edge by rule

Source: the asserted graph itself.

`src/rules.yml` defines `shared_chain_corporate_group`:

> For every chain, every pair of operators affiliated with that chain is
> asserted as a corporate sibling pair (`vaok:corporateSibling`).

`src/construct/materialize_rules.py` evaluates this rule by
forward-chaining over the asserted edges: it groups operators by their
`AFFILIATED_WITH` chain, then for every chain emits an undirected
`corporateSibling` edge between each pair of operators in that chain. The
derived triples are written to `graph/inferred_facts.ttl` so they stay
separable from asserted facts.

A second, **recursive** rule (`operator_corporate_network`) then computes
the transitive closure of `corporateSibling` via union-find: each connected
component becomes an `OperatorNetwork` node and every member operator is
linked via `memberOf`. The same closure can be queried directly with the
SPARQL 1.1 property path `vaok:corporateSibling*` — see query `### 4` in
`src/queries.sparql`.

Result (TTL fragment):

```turtle
vaok:op_a vaok:corporateSibling vaok:op_b .
vaok:op_a vaok:memberOf         vaok:network_marriott_intl .
```
