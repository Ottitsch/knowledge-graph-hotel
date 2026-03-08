# Data Quality Report

## Snapshot

- Total rows: 15003
- Listing-level rows: 14123
- Establishment-level rows: 880

## Merge Quality

- Multi-source establishments: 267 (30.3%)
- Establishment merge confidence `single`: 599
- Establishment merge confidence `strong`: 281

## Operator Evidence

- Establishment rows using venue-name fallback operators: 707 (80.3%)
- Operator identity confidence `high`: 13761
- Operator identity confidence `low`: 707
- Operator identity confidence `medium`: 535

## Airbnb to Establishment Matching

- Evidence-backed listing links asserted in graph: 221
- Nearby candidates kept out of graph: 1470
- Listings without nearby candidate: 12432
- Linked listing confidence `medium`: 121
- Linked listing confidence `high`: 100

## Top Source Combinations

- `airbnb`: 14123
- `osm`: 296
- `wikidata`: 171
- `datagv`: 146
- `datagv,osm`: 121
- `datagv,osm,wikidata`: 81
- `datagv,wikidata`: 33
- `osm,wikidata`: 32

## Interpretation

- The KG now distinguishes evidence-backed listing-establishment matches from weak proximity-only candidates.
- Operator labels carry explicit provenance and confidence, which makes low-confidence venue-name fallbacks visible instead of implicit.
- This report is intended to be referenced in the course portfolio as evidence of KG quality control.
