# Rule Inference Report

- Generated at: 2026-05-17T08:27:21+00:00
- Input rows: 15011
- Rules applied: 6
- Total inferred facts: 1896
- Operator-pair facts (new edges): 331
- Network facts (recursive closure): 12

## Facts by Type

- `CorporateSibling`: 331
- `CrossDistrictOperator`: 590
- `LikelyChainAffiliatedOperator`: 83
- `MultiSourceConfirmedEstablishment`: 278
- `OperatorNetwork`: 12
- `ProfessionalOperator`: 602

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
- The `CorporateSibling` and `OperatorNetwork` rules produce new edges and nodes in `graph/inferred_facts.ttl`,
  kept separate from `graph/vienna_accommodation_operator_kg.ttl` so asserted and inferred facts stay distinguishable.
- The `OperatorNetwork` rule is recursive: it computes the transitive closure over `corporateSibling` edges via union-find.
- This reasoning layer supports portfolio claims around symbolic reasoning, graph evolution, and explainable KG services.
