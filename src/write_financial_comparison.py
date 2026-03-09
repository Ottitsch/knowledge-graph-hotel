"""
Write a short comparative note connecting the project architecture to financial KG applications.
"""

from common_paths import FINANCIAL_KG_REPORT_MD, ensure_directories


REPORT = """# Financial KG Comparison

## Why this comparison exists

This project is not a financial knowledge graph. However, it shares several structural ideas with financial KG applications discussed in the course.

## Common patterns

- Heterogeneous data integration: financial KGs merge sources such as transactions, customers, institutions, and regulations. This project merges Airbnb, OpenStreetMap, Wikidata, and official city accommodation data.
- Entity-centric analysis: financial KGs connect customers, companies, accounts, and events. This project connects accommodation units, operators, districts, hotel chains, and sources.
- Provenance and confidence: financial KGs need traceable evidence for compliance and audit. This project keeps source provenance, operator-confidence labels, and validation outputs visible.
- Service provision: financial KGs support search, analytics, and compliance workflows. This project supports graph exploration, map views, analytics, rule-based reasoning, and a query assistant.

## Main difference

The difference is domain, not architecture. Financial KGs usually focus on risk, compliance, fraud, regulation, and institutional data. This project focuses on public accommodation data in Vienna and on operator analysis rather than regulated financial entities.

## Portfolio use

This comparison supports LO10 by showing that I can describe how financial KG applications work and how their architectural patterns relate to my own project.
"""


def main() -> None:
    ensure_directories()
    FINANCIAL_KG_REPORT_MD.write_text(REPORT, encoding="utf-8")
    print(f"Wrote {FINANCIAL_KG_REPORT_MD}")


if __name__ == "__main__":
    main()
