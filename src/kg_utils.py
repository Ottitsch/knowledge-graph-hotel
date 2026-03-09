from __future__ import annotations

import re
import unicodedata
from typing import Iterable


SOURCE_LABELS = {
    "airbnb": "InsideAirbnb",
    "osm": "OpenStreetMap",
    "wikidata": "Wikidata",
    "datagv": "data.gv.at",
}


def slugify(value: str) -> str:
    if not isinstance(value, str):
        return "unknown"
    value = re.sub(r"[^\w\s-]", "", value.lower())
    value = re.sub(r"[\s_-]+", "_", value)
    return value.strip("_") or "unknown"


def normalize_name(value: str) -> str:
    if not isinstance(value, str):
        return ""
    value = unicodedata.normalize("NFD", value)
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = value.lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def clean_host_id(raw) -> str:
    value = str(raw).strip()
    if not value or value in {"nan", "None", "0"}:
        return ""
    if value.endswith(".0"):
        value = value[:-2]
    return value


def split_sources(source_names: str) -> list[str]:
    if not isinstance(source_names, str):
        return []
    return [item.strip() for item in source_names.split(",") if item.strip()]


def canonical_source_label(source_name: str) -> str:
    return SOURCE_LABELS.get(source_name, source_name)


def operator_id(operator_name: str, host_id: str, source_names: str) -> str:
    cleaned_host_id = clean_host_id(host_id)
    sources = set(split_sources(source_names))
    if cleaned_host_id and "airbnb" in sources:
        return f"airbnb:{cleaned_host_id}"
    return f"name:{slugify(operator_name)}"


def operator_key_from_row(row) -> str:
    return operator_id(
        str(row.get("operator_name", "")),
        row.get("host_id", ""),
        str(row.get("source_names", row.get("source", ""))),
    )


def unit_entity_label(canonical_id: str) -> str:
    return f"unit:{canonical_id}"


def operator_entity_label(operator_key: str) -> str:
    return f"operator:{operator_key}"


def district_entity_label(district_name: str) -> str:
    return f"district:{slugify(district_name)}"


def source_entity_label(source_name: str) -> str:
    return f"source:{slugify(canonical_source_label(source_name))}"


def chain_entity_label(chain_name: str) -> str:
    return f"chain:{slugify(chain_name)}"


def safe_tokens(*values: Iterable[str]) -> list[str]:
    tokens = []
    seen = set()
    for value in values:
        for token in re.findall(r"[a-z0-9]+", normalize_name(str(value))):
            if len(token) < 3 or token in seen:
                continue
            seen.add(token)
            tokens.append(token)
    return tokens
