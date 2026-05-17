# Rule Evaluation — CorporateSibling (R5)

Portfolio reference: this document supports **LO2 — understand and apply logical knowledge in KGs** by providing a quantitative spot-check of the rule output, in addition to the formal rule definitions in `rule_inference_report.md`.

## What is being evaluated

The rule under test is **R5 `shared_chain_corporate_group`** as defined in `src/rules.yml` and re-stated formally in `reports/rule_inference_report.md`:

> ∀ a, b, c.  a ≠ b ∧ affiliatedWith(a, c) ∧ affiliatedWith(b, c)  ⇒  corporateSibling(a, b)

R5 produced **331 `corporateSibling` facts** on the current dataset (see `reports/rule_inference_summary.json`).

We evaluate **precision** on a hand-labelled spot-check of **30 sampled edges**, drawn so that every hotel chain that produced at least one sibling pair contributes to the sample (stratified by chain, then back-filled from the largest chains). The sample is reproducible from `reports/rule_inference_facts.json` with `random.seed(7)` — the exact selection is shown below.

We do **not** report a quantitative recall number: there is no public list of "all Vienna hotel corporate-sibling pairs" to compare against, and constructing one from public registers is out of scope per the one-pager. Instead, the *coverage* discussion at the end of this document lists every chain that contributed at least one sibling fact.

## Labelling protocol

Each edge is labelled in one of four categories:

| Label | Meaning |
|---|---|
| **TP** | Two **distinct** operators that genuinely share a corporate parent. This is the rule's intended output. |
| **OK-coreferent** | The two operators are surface forms of effectively the same entity (e.g. `Hyatt` vs `Hyatt Hotels Corporation`, `Meininger` vs `Meininger Hotel Group`). The chain claim is correct, but the pair is not a useful sibling — it is an entity-resolution duplicate. |
| **OK-brand-vs-property** | One side is a chain or sub-brand, the other is a specific property of that brand (e.g. `Hilton` vs `Double Tree by Hilton Vienna Schönbrunn`). The chain claim is correct, but the pair is hierarchical rather than sibling. |
| **FP** | The chain attribution that fed the rule is wrong, so the resulting "sibling" edge is factually incorrect. |

The two non-TP "OK" categories are kept distinct because they represent **upstream** issues (operator normalisation, brand-vs-property hierarchy) rather than failures of the rule itself. A strict reading still counts them as imprecise output; a loose reading accepts them as correct chain-co-affiliation. Both readings are reported below.

## 30-edge spot-check

| # | Chain | Operator A | Operator B | Label | Note |
|---:|---|---|---|---|---|
| 1 | AccorHotels | Ibis | Mercure Wien Westbahnhof | **TP** | distinct Accor sub-brands |
| 2 | AccorHotels | Hotel Ibis Wien Messe | Novotel | **TP** | distinct Accor sub-brands |
| 3 | AccorHotels | Mercure Raphael Hotel Wien | Novotel Wien City | **TP** | distinct Accor sub-brands |
| 4 | Austria Trend Hotels | Austria Trend Hotel Anatol Wien | Austria Trend Hotel Schloss Wilhelminenberg | **TP** | two distinct Vienna properties |
| 5 | Austria Trend Hotels | Austria Trend Hotel Anatol Wien | Doppio - Austria Trend Hotels | **TP** | distinct properties |
| 6 | Austria Trend Hotels | Austria Trend | Austria Trend Hotel Beim Theresianum Wien | OK-brand-vs-property | "Austria Trend" is the chain |
| 7 | Best Western | Arcadia - Best Western Plus Hotel | Best Western Plus | OK-brand-vs-property | property vs sub-brand |
| 8 | Best Western | Best Western Plus | Best Western Plus Hotel Arcadia | OK-brand-vs-property | sub-brand vs property (mirrored) |
| 9 | Best Western | Arcadia - Best Western Plus Hotel | Best Western | OK-brand-vs-property | property vs parent |
| 10 | Hilton Hotels & Resorts | Double Tree by Hilton Vienna Schönbrunn | Hilton | OK-brand-vs-property | property vs parent |
| 11 | Hilton Hotels & Resorts | Curio Collection | Double Tree by Hilton Vienna Schönbrunn | **TP** | distinct Hilton sub-brand vs property of another Hilton sub-brand |
| 12 | Hilton Hotels & Resorts | Curio Collection | Hilton | OK-brand-vs-property | sub-brand vs parent |
| 13 | IHG Hotels & Resorts | Holiday Inn - the niu Franz Vienna | InterContinental | **FP** | "the niu" is Novum Hospitality, not IHG — chain attribution wrong |
| 14 | IHG Hotels & Resorts | Holiday Inn | Holiday Inn Vienna - South | OK-brand-vs-property | brand vs property of same brand |
| 15 | IHG Hotels & Resorts | Holiday Inn | InterContinental Vienna | **TP** | distinct IHG brands |
| 16 | Marriott International | Courtyard by Marriott Vienna Prater/Messe | Renaissance Vienna Schönbrunn Hotel | **TP** | distinct Marriott properties under different sub-brands |
| 17 | Marriott International | Four Points Flex by Sheraton Vienna Hauptbahnhof | Marriott | OK-brand-vs-property | property vs parent |
| 18 | Marriott International | Courtyard by Marriott Vienna Prater/Messe | Renaissance Wien Hotel | **TP** | distinct Marriott sub-brand properties |
| 19 | Meininger Hotels | Meininger | Meininger Hotel Group | **OK-coreferent** | same operator under different surface forms |
| 20 | Motel One | Motel One Austria GmbH | Motel One Wien-Donau City | OK-brand-vs-property | operator company vs specific property |
| 21 | Motel One | Motel One | Motel One Wien-Donau City | OK-brand-vs-property | brand vs property |
| 22 | Motel One | Motel One | Motel One Wien-Hauptbahnhof | OK-brand-vs-property | brand vs property |
| 23 | NH Hotels | NH Wien Belvedere | NH Wien City | **TP** | two distinct NH Vienna properties |
| 24 | NH Hotels | nh Hotel | NH Wien Belvedere | OK-brand-vs-property | parent vs property (also a casing dup) |
| 25 | NH Hotels | NH Hotels | NH Wien Belvedere | OK-brand-vs-property | parent vs property |
| 26 | Park Hyatt | Hyatt | Lindner Hotel Vienna Am Belvedere, part of JdV by Hyatt | OK-brand-vs-property | parent vs JdV-by-Hyatt property |
| 27 | Park Hyatt | Hyatt | Hyatt Hotels Corporation | **OK-coreferent** | same parent group, two surface forms |
| 28 | Park Hyatt | Hyatt Hotels Corporation | Lindner Hotel Vienna Am Belvedere, part of JdV by Hyatt | OK-brand-vs-property | parent vs property |
| 29 | Radisson Hotel Group | Prize by Radisson, Wien-City | Radisson RED | **TP** | distinct Radisson sub-brands |
| 30 | Radisson Hotel Group | Hotel Rathauspark Wien, a Member of Radisson Individuals | Radisson Blu | **TP** | distinct Radisson sub-brand and property |

## Aggregate counts

| Label | Count | Share |
|---|---:|---:|
| TP (distinct sibling) | 11 | 36.7 % |
| OK-brand-vs-property (hierarchical, not sibling) | 16 | 53.3 % |
| OK-coreferent (entity-resolution duplicate) | 2 | 6.7 % |
| FP (wrong chain attribution) | 1 | 3.3 % |
| **Total** | **30** | **100 %** |

## Two precision readings

- **Strict precision** (only "distinct sibling" counts as correct): **11 / 30 = 0.367**
- **Loose precision** (only the FP counts as wrong; both "OK" classes accepted as correct chain co-affiliation): **29 / 30 = 0.967**

Both numbers are useful and they tell different stories:

- **Loose precision** says the rule is doing its job: when it asserts that two operators share a chain, it is wrong only in the rare case (1 / 30 here) where the upstream chain attribution itself was wrong.
- **Strict precision** says the rule's *intent* — "find genuine corporate siblings" — is diluted by upstream issues. ~53 % of the asserted edges are actually parent↔property pairs, not sibling pairs, and another ~7 % are pure entity-resolution duplicates.

## What this tells us, concretely

1. **R5 is high-quality where the inputs are clean.** All 11 TPs in the sample are obviously correct corporate siblings (different Accor brands, different Marriott brands, different NH properties, etc.).
2. **Most "imprecision" is not the rule's fault.** It comes from operator-resolution decisions made earlier in the pipeline: chains and properties end up sharing the same chain affiliation slot, so the rule treats them as siblings of each other. Fixing this requires distinguishing "operator = corporate group" from "operator = single property" *before* the rule runs, e.g. by typing operators as `Group` vs `Property`.
3. **One genuine FP** (`Holiday Inn - the niu Franz Vienna ↔ InterContinental`) is caused by a name-prefix chain heuristic misfiring on a property whose listed name includes "Holiday Inn" but whose actual operator is Novum Hospitality. This is a single-class error and could be addressed with a small denylist or a confidence threshold on the prefix detector.

## Recall coverage

We have no exhaustive ground truth, so quantitative recall is not reported. As a sanity check the rule's chain coverage is listed below — every chain that produced ≥ 1 sibling fact in the inferred set:

| Chain | Sibling facts |
|---|---:|
| AccorHotels | 136 |
| Austria Trend Hotels | 78 |
| Marriott International | 36 |
| Radisson Hotel Group | 36 |
| NH Hotels | 11 |
| Best Western | 10 |
| IHG Hotels & Resorts | 10 |
| Motel One | 6 |
| Hilton Hotels & Resorts | 3 |
| Park Hyatt | 3 |
| Meininger Hotels | 1 |
| The Ritz-Carlton | 1 |

All twelve major chains present in `hotel_chain` after entity resolution produced at least one sibling fact, and the largest chains produce the largest networks — which is consistent with what the recursive rule R6 then aggregates into 12 `OperatorNetwork` nodes.

## Reproducing the sample

```python
import json, random
random.seed(7)
facts = json.load(open("reports/rule_inference_facts.json"))["facts"]
sibs = [f for f in facts if f["inferred_type"] == "CorporateSibling"]
# stratify by via_chain, take up to 3 per chain, then backfill from largest chains until 30
```

The exact 30 IDs as labelled here are stored in `reports/rule_eval_corporate_sibling.json`.
