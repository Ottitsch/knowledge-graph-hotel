# Data Quality Report

## Snapshot

- Total rows: 15011
- Listing-level rows: 14123
- Establishment-level rows: 888

## Merge Quality

- Multi-source establishments: 265 (29.8%)
- Establishment merge confidence `single`: 610
- Establishment merge confidence `strong`: 278

## Operator Evidence

- Establishment rows using venue-name fallback operators: 715 (80.5%)
- Operator identity confidence `high`: 13761
- Operator identity confidence `low`: 715
- Operator identity confidence `medium`: 535

## Airbnb to Establishment Matching

- Evidence-backed listing links asserted in graph: 215
- Nearby candidates kept out of graph: 1097
- Listings without nearby candidate: 12811
- Linked listing confidence `medium`: 115
- Linked listing confidence `high`: 100

## Top Source Combinations

- `airbnb`: 14123
- `osm`: 299
- `wikidata`: 172
- `datagv`: 152
- `datagv,osm`: 120
- `datagv,osm,wikidata`: 79
- `datagv,wikidata`: 33
- `osm,wikidata`: 33

## Interpretation

- The KG now distinguishes evidence-backed listing-establishment matches from weak proximity-only candidates.
- Operator labels carry explicit provenance and confidence, which makes low-confidence venue-name fallbacks visible instead of implicit.
- This report is intended to be referenced in the course portfolio as evidence of KG quality control.
